import os
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse, Http404
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import Course, Lecture, Test, Question, Answer, UserProgress, UserTestResult, Feedback, Task
from .forms import TestSubmissionForm, CodeTaskForm, CTFFlagForm, LectureCommentForm
import requests

def home(request):
    courses = Course.objects.filter(is_active=True).order_by('order')
    return render(request, 'home.html', {'courses': courses})

def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug, is_active=True)
    lectures = course.lectures.filter(is_published=True).order_by('order')
    return render(request, 'course_detail.html', {
        'course': course,
        'lectures': lectures
    })

@login_required
def lecture_detail(request, course_slug, lecture_slug):
    lecture = get_object_or_404(
        Lecture,
        course__slug=course_slug,
        slug=lecture_slug,
        is_published=True
    )

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
    comment_form = LectureCommentForm()
    
    if request.method == 'POST' and 'comment' in request.POST:
        comment_form = LectureCommentForm(request.POST)
        if comment_form.is_valid():
            pass
    
    return render(request, 'lecture_detail.html', {
        'lecture': lecture,
        'tasks': tasks,
        'tests': tests,
        'comment_form': comment_form,
        'user_progress': progress
    })

@login_required
def test_detail(request, test_id):
    test = get_object_or_404(Test, id=test_id, is_published=True)
    questions = test.questions.all().order_by('order').prefetch_related('answers')
    
    if request.method == 'POST':
        form = TestSubmissionForm(request.POST, questions=questions)
        if form.is_valid():
            score = 0
            total_questions = questions.count()
            for question in questions:
                answer_id = form.cleaned_data.get(f'question_{question.id}')
                if answer_id:
                    answer = Answer.objects.get(id=answer_id)
                    if answer.is_correct:
                        score += 1
            
            UserTestResult.objects.create(
                user=request.user,
                test=test,
                score=score
            )
            
            return render(request, 'test_result.html', {
                'test': test,
                'score': score,
                'total_questions': total_questions
            })
    else:
        form = TestSubmissionForm(questions=questions)
    
    return render(request, 'test_detail.html', {
        'test': test,
        'form': form
    })

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

@login_required
def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    lecture = task.lecture
    
    if not request.user.is_staff and (not lecture.is_published or not lecture.course.is_active):
        raise Http404("Задание не найдено")
    
    template_map = {
        'quiz': 'tasks/quiz.html',
        'code': 'tasks/code.html',
        'ctf': 'tasks/ctf.html',
        'theory': 'tasks/theory.html',
    }
    
    template_name = template_map.get(task.task_type, 'tasks/theory.html')
    
    forms = {
        'code': CodeTaskForm(),
        'ctf': CTFFlagForm(),
    }
    
    form = forms.get(task.task_type)
    
    if request.method == 'POST':
        if task.task_type == 'code':
            form = CodeTaskForm(request.POST)
            if form.is_valid():
                return JsonResponse({'success': True})
        
        elif task.task_type == 'ctf':
            form = CTFFlagForm(request.POST)
            if form.is_valid():
                is_correct = form.cleaned_data['flag'] == task.flag
                if is_correct:
                    UserProgress.objects.update_or_create(
                        user=request.user,
                        lecture=lecture,
                        defaults={'completed': True, 'completed_at': timezone.now()}
                    )
                return JsonResponse({'success': True, 'is_correct': is_correct})
    
    return render(request, template_name, {
        'task': task,
        'lecture': lecture,
        'form': form,
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