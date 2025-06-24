import os
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse, Http404
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import Course, Lecture, Test, Question, Answer, UserProgress, UserTestResult, Feedback, Task, Comment, TaskResponse
from .forms import TestSubmissionForm, CodeTaskForm, CTFFlagForm, CommentForm, TaskResponseForm
import requests
from django.contrib import messages

def home(request):
    course = Course.objects.filter(is_active=True).first()
    return render(request, 'home.html', {'course': course})

def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug, is_active=True)
    lectures = course.lectures.filter(is_published=True).order_by('order')
    
    if request.user.is_authenticated:
        completed_lectures = UserProgress.objects.filter(
            user=request.user,
            lecture__in=lectures,
            completed=True
        ).values_list('lecture_id', flat=True)
        
        next_lecture = None
        for lecture in lectures:
            if lecture.id not in completed_lectures:
                next_lecture = lecture
                break
        
        if not next_lecture and lectures:
            next_lecture = lectures.first()
    else:
        completed_lectures = []
        next_lecture = None
    
    return render(request, 'course_detail.html', {
        'course': course,
        'lectures': lectures,
        'completed_lecture_ids': completed_lectures,
        'next_lecture': next_lecture,
        'completed_lectures_count': len(completed_lectures),
    })

@login_required
def lecture_detail(request, course_slug, lecture_slug):
    lecture = get_object_or_404(
        Lecture,
        course__slug=course_slug,
        slug=lecture_slug,
        is_published=True
    )

    lectures = Lecture.objects.filter(
        course=lecture.course, 
        is_published=True
    ).order_by('order')
    
    lecture_list = list(lectures)
    try:
        current_index = lecture_list.index(lecture)
    except ValueError:
        current_index = -1
    
    prev_lecture = lecture_list[current_index - 1] if current_index > 0 else None
    next_lecture = lecture_list[current_index + 1] if current_index < len(lecture_list) - 1 else None
    
    progress, created = UserProgress.objects.get_or_create(
        user=request.user,
        lecture=lecture,
        defaults={'completed': False}
    )
    
    if not progress.completed:
        progress.completed = True
        progress.completed_at = timezone.now()
        progress.save()
    
    tasks = lecture.tasks.all().order_by('order')
    tests = lecture.tests.filter(is_published=True)

    comment_form = CommentForm()
    reply_form = None
    
    comments = Comment.objects.filter(
        lecture=lecture,
        parent__isnull=True
    ).select_related('author').prefetch_related('replies__author')
    
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'comment':
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.lecture = lecture
                comment.author = request.user
                comment.save()
                messages.success(request, 'Комментарий добавлен')
                return redirect(comment.get_absolute_url())
        
        elif form_type == 'reply':
            parent_id = request.POST.get('parent_id')
            try:
                parent_comment = Comment.objects.get(id=parent_id, lecture=lecture)
                reply_form = CommentForm(request.POST)
                if reply_form.is_valid():
                    reply = reply_form.save(commit=False)
                    reply.lecture = lecture
                    reply.author = request.user
                    reply.parent = parent_comment
                    reply.save()
                    messages.success(request, 'Ответ добавлен')
                    return redirect(reply.get_absolute_url())
                else:
                    messages.error(request, 'Ошибка при отправке ответа')
            except Comment.DoesNotExist:
                messages.error(request, 'Родительский комментарий не найден')
    
    return render(request, 'lecture_detail.html', {
        'lecture': lecture,
        'prev_lecture': prev_lecture,
        'next_lecture': next_lecture,
        'tasks': tasks,
        'tests': tests,
        'comments': comments,
        'comment_form': comment_form,
        'reply_form': reply_form if reply_form else CommentForm(),
        'user_progress': progress
    })

@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    
    if comment.author != request.user and not request.user.is_staff:
        messages.error(request, 'Вы не можете удалить этот комментарий')
        return redirect(comment.lecture.get_absolute_url())
    
    if request.method == 'POST':
        lecture_url = comment.lecture.get_absolute_url()
        comment.delete()
        messages.success(request, 'Комментарий удален')
        return redirect(lecture_url)
    
    return render(request, 'confirm_delete.html', {
        'comment': comment,
        'lecture': comment.lecture
    })

@login_required
def test_detail(request, test_id):
    test = get_object_or_404(Test, id=test_id, is_published=True)
    questions = test.questions.all().order_by('order').prefetch_related('answers')
    max_score = sum(q.points for q in questions)
    
    existing_result = UserTestResult.objects.filter(user=request.user, test=test).first()
    
    if request.method == 'POST' and (not existing_result or request.GET.get('retry')):
        form = TestSubmissionForm(request.POST, questions=questions)
        if form.is_valid():
            score = 0
            details = {}
            correct_answers = 0
            
            for question in questions:
                field_name = f'question_{question.id}'
                answer = form.cleaned_data.get(field_name)
                details[str(question.id)] = {
                    'question': question.text,
                    'answer_id': str(answer.id) if answer else None,
                    'is_correct': False
                }
                
                if answer:
                    details[str(question.id)]['answer_text'] = answer.text
                    
                    if answer.is_correct:
                        score += question.points
                        correct_answers += 1
                        details[str(question.id)]['is_correct'] = True
                        details[str(question.id)]['correct_answer'] = answer.text
                    else:
                        correct_answer = question.answers.filter(is_correct=True).first()
                        details[str(question.id)]['correct_answer'] = correct_answer.text if correct_answer else ""
                else:
                    details[str(question.id)]['error'] = "Ответ не выбран"
            
            result, created = UserTestResult.objects.update_or_create(
                user=request.user,
                test=test,
                defaults={
                    'score': score,
                    'details': details,
                    'is_passed': score >= (test.passing_score / 100) * max_score
                }
            )
            
            return render(request, 'test_result.html', {
                'test': test,
                'result': result,
                'score': score,
                'max_score': max_score,
                'correct_answers': correct_answers,
                'total_questions': questions.count(),
                'percentage': round(score / max_score * 100) if max_score > 0 else 0,
                'passing_score_points': (test.passing_score / 100) * max_score
            })
    else:
        form = TestSubmissionForm(questions=questions)
    
    context = {
        'test': test,
        'form': form,
        'existing_result': existing_result,
        'max_score': max_score,
    }
    
    if existing_result:
        context['percentage'] = round(existing_result.score / max_score * 100) if max_score > 0 else 0
    
    return render(request, 'test_detail.html', context)
@login_required
def code_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, task_type='code')
    
    if request.method == 'POST':
        form = CodeTaskForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            return JsonResponse({'success': True})
    else:
        form = CodeTaskForm()
    
    return render(request, 'tasks/code.html', {
        'task': task,
        'form': form
    })

@login_required
def ctf_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, task_type='ctf')
    
    if request.method == 'POST':
        form = CTFFlagForm(request.POST)
        if form.is_valid():
            flag = form.cleaned_data['flag']
            is_correct = flag == task.flag
            
            if is_correct:
                UserProgress.objects.get_or_create(
                    user=request.user,
                    task=task,
                    defaults={'completed': True, 'completed_at': timezone.now()}
                )
            
            return JsonResponse({
                'success': True,
                'is_correct': is_correct
            })
    else:
        form = CTFFlagForm()
    
    return render(request, 'tasks/ctf.html', {
        'task': task,
        'form': form
    })


def lecture_html_view(request, course_slug, lecture_slug):
    lecture = get_object_or_404(
        Lecture,
        course__slug=course_slug,
        slug=lecture_slug,
        is_published=True
    )
    
    html_path = os.path.join(settings.MEDIA_ROOT, 'courses_html', course_slug, f"{lecture_slug}.html")
    
    if os.path.exists(html_path):
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return HttpResponse(html_content)
    else:
        raise Http404("Лекция не найдена")

def contact_view(request):
    if request.method == 'POST':
        errors = {}
        data = request.POST

        name = data.get('name', '').strip()
        if not name:
            errors['name'] = ['Введите ваше имя']

        email = data.get('email', '').strip()
        if not email:
            errors['email'] = ['Введите email']
        else:
            try:
                validate_email(email)
            except ValidationError:
                errors['email'] = ['Введите корректный email']

        message = data.get('message', '').strip()
        if not message:
            errors['message'] = ['Введите сообщение']

        recaptcha_response = data.get('g-recaptcha-response')
        if not recaptcha_response:
            errors['captcha'] = ['Подтвердите, что вы не робот']
        else:
            verify_data = {
                'secret': settings.RECAPTCHA_PRIVATE_KEY,
                'response': recaptcha_response
            }
            r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=verify_data)
            result = r.json()
            if not result.get('success'):
                errors['captcha'] = ['Ошибка проверки reCAPTCHA']
        
        if errors:
            return JsonResponse({'success': False, 'errors': errors})
        
        try:
            feedback = Feedback.objects.create(
                name=name,
                email=email,
                message=message
            )
            
            send_mail(
                f'Новое сообщение от {name}',
                f'Имя: {name}\nEmail: {email}\n\nСообщение:\n{message}',
                settings.DEFAULT_FROM_EMAIL,
                ['vedenyov10@gmail.com'],
                fail_silently=False,
            )
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Неверный метод запроса'})

@login_required
def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    user_response = TaskResponse.objects.filter(task=task, user=request.user).first()
    
    if request.method == 'POST':
        form = TaskResponseForm(request.POST)
        if form.is_valid():
            answer = form.cleaned_data['answer']
            TaskResponse.objects.update_or_create(
                task=task,
                user=request.user,
                defaults={
                    'answer': answer,
                    'is_checked': False
                }
            )
            messages.success(request, 'Ваш ответ успешно сохранен!')
            return redirect('task_detail', task_id=task.id)
    else:
        initial_data = {'answer': user_response.answer if user_response else ''}
        form = TaskResponseForm(initial=initial_data)
    
    return render(request, 'tasks/theory.html', {
        'task': task,
        'user_response': user_response,
        'form': form
    })