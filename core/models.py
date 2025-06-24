from django.db import models
from django.utils.translation import gettext_lazy as _
from tinymce.models import HTMLField
from django.contrib.auth import get_user_model
from django.urls import reverse
import os
from django.conf import settings
from django.core.exceptions import ValidationError

User = get_user_model()

class Course(models.Model):
    title = models.CharField(_('Название'), max_length=200)
    slug = models.SlugField(_('URL'), max_length=200, unique=True)
    description = HTMLField(_('Описание'))
    short_description = models.TextField(_('Краткое описание'), max_length=300)
    image = models.ImageField(
        _('Изображение'), 
        upload_to='courses/covers/',
        help_text=_('Рекомендуемый размер: 1200x600px')
    )
    difficulty = models.PositiveSmallIntegerField(
        _('Сложность'), 
        choices=[(1, 'Начинающий'), (2, 'Средний'), (3, 'Продвинутый')],
        default=1
    )
    is_active = models.BooleanField(_('Активный'), default=True)
    order = models.PositiveIntegerField(_('Порядок'), default=0)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    duration = models.PositiveIntegerField(
        _('Длительность (минуты)'), 
        default=0,
        help_text=_('Общая продолжительность курса в минутах')
    )

    class Meta:
        verbose_name = _('курс')
        verbose_name_plural = _('Курсы')
        ordering = ['order']
        constraints = [
            models.CheckConstraint(
                check=models.Q(difficulty__gte=1) & models.Q(difficulty__lte=3),
                name='difficulty_range'
            )
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('course_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        course_dir = os.path.join(settings.MEDIA_ROOT, 'courses_html', self.slug)
        os.makedirs(course_dir, exist_ok=True)

    @property
    def total_lectures(self):
        return self.lectures.count()


class Lecture(models.Model):
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='lectures', 
        verbose_name=_('Курс')
    )
    title = models.CharField(_('Название'), max_length=200)
    slug = models.SlugField(_('URL'), max_length=200)
    content = HTMLField(_('Содержание'))
    video_url = models.URLField(
        _('Ссылка на видео'), 
        blank=True, 
        null=True,
        help_text=_('URL видео с YouTube или другого сервиса')
    )
    duration = models.PositiveIntegerField(
        _('Длительность (минуты)'), 
        default=0
    )
    order = models.PositiveIntegerField(_('Порядок'), default=0)
    is_published = models.BooleanField(_('Опубликовано'), default=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    resources = models.FileField(
        _('Дополнительные материалы'),
        upload_to='lectures/resources/',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = _('лекция')
        verbose_name_plural = _('Лекции')
        ordering = ['order']
        unique_together = ('course', 'slug')
        constraints = [
            models.UniqueConstraint(
                fields=['course', 'order'],
                name='unique_lecture_order_per_course'
            )
        ]

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    def get_absolute_url(self):
        return reverse('lecture_detail', kwargs={
            'course_slug': self.course.slug,
            'lecture_slug': self.slug
        })

    def clean(self):
        if self.order < 0:
            raise ValidationError({'order': _('Порядок не может быть отрицательным')})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        self.save_as_html()

    def save_as_html(self):
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{self.title} | {self.course.title}</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="/static/css/lecture.css" rel="stylesheet">
        </head>
        <body>
            <article class="lecture-container">
                <header>
                    <h1>{self.title}</h1>
                    <p class="course-title">{self.course.title}</p>
                </header>
                <div class="lecture-content">
                    {self.content}
                </div>
                {f'<div class="video-container"><iframe src="{self.video_url}" frameborder="0" allowfullscreen></iframe></div>' if self.video_url else ''}
            </article>
        </body>
        </html>
        """
        
        course_dir = os.path.join(settings.MEDIA_ROOT, 'courses_html', self.course.slug)
        os.makedirs(course_dir, exist_ok=True)
        file_path = os.path.join(course_dir, f"{self.slug}.html")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)


class Task(models.Model):
    class TaskType(models.TextChoices):
        QUIZ = 'quiz', _('Тест')
        CODE = 'code', _('Код')
        CTF = 'ctf', _('CTF задание')
        THEORY = 'theory', _('Теоретическое задание')

    lecture = models.ForeignKey(
        Lecture,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name=_('Лекция'),
        blank=True, null=True
    )
    title = models.CharField(_('Название'), max_length=200)
    description = HTMLField(_('Описание'))
    task_type = models.CharField(
        _('Тип задания'),
        max_length=10,
        choices=TaskType.choices,
        default=TaskType.THEORY
    )
    flag = models.CharField(
        _('Флаг (для CTF)'), 
        max_length=200, 
        blank=True, 
        null=True,
        help_text=_('Флаг в формате FLAG{...}')
    )
    order = models.PositiveIntegerField(_('Порядок'), default=0)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    max_score = models.PositiveIntegerField(
        _('Максимальный балл'),
        default=10
    )

    class Meta:
        verbose_name = _('задание')
        verbose_name_plural = _('Задания')
        ordering = ['order']
        constraints = [
            models.CheckConstraint(
                check=models.Q(max_score__gte=1) & models.Q(max_score__lte=100),
                name='max_score_range'
            )
        ]

    def __str__(self):
        return f"{self.lecture.title} - {self.title}"

    def clean(self):
        if self.task_type == 'ctf' and not self.flag:
            raise ValidationError(
                {'flag': _('Для CTF заданий необходимо указать флаг')}
            )


class Test(models.Model):
    lecture = models.ForeignKey(
        Lecture, 
        on_delete=models.CASCADE, 
        related_name='tests', 
        verbose_name=_('Лекция'),
        null=True,
        blank=True,
    )
    title = models.CharField(_('Название'), max_length=200)
    description = HTMLField(_('Описание'))
    is_published = models.BooleanField(_('Опубликовано'), default=True)
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    time_limit = models.PositiveIntegerField(
        _('Лимит времени (минуты)'),
        default=30,
        help_text=_('Время на прохождение теста в минутах')
    )
    passing_score = models.PositiveIntegerField(
        _('Проходной балл (%)'),
        default=60,
        help_text=_('Минимальный процент для успешного прохождения')
    )

    class Meta:
        verbose_name = _('тест')
        verbose_name_plural = _('Тесты')
        ordering = ['created_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(passing_score__gte=1) & models.Q(passing_score__lte=100),
                name='passing_score_range'
            )
        ]

    def __str__(self):
        return f"{self.lecture.title} - {self.title}"


class Question(models.Model):
    test = models.ForeignKey(
        Test, 
        on_delete=models.CASCADE, 
        related_name='questions', 
        verbose_name=_('Тест')
    )
    text = HTMLField(_('Текст вопроса'))
    order = models.PositiveIntegerField(_('Порядок'), default=0)
    points = models.PositiveIntegerField(
        _('Баллы за вопрос'),
        default=1
    )

    class Meta:
        verbose_name = _('вопрос')
        verbose_name_plural = _('Вопросы')
        ordering = ['order']

    def __str__(self):
        return f"{self.test.title} - вопрос #{self.order}"


class Answer(models.Model):
    question = models.ForeignKey(
        Question, 
        on_delete=models.CASCADE, 
        related_name='answers', 
        verbose_name=_('Вопрос')
    )
    text = models.TextField(_('Текст ответа'))
    is_correct = models.BooleanField(_('Правильный ответ'), default=False)
    order = models.PositiveIntegerField(_('Порядок'), default=0)
    explanation = models.TextField(
        _('Объяснение ответа'),
        blank=True,
        null=True,
        help_text=_('Пояснение почему ответ правильный/неправильный')
    )

    class Meta:
        verbose_name = _('ответ')
        verbose_name_plural = _('Ответы')
        ordering = ['order']

    def __str__(self):
        return self.text


class UserProgress(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name=_('Пользователь')
    )
    lecture = models.ForeignKey(
        Lecture, 
        on_delete=models.CASCADE, 
        verbose_name=_('Лекция'),
        null=True,
        blank=True
    )
    completed = models.BooleanField(_('Завершено'), default=False)
    completed_at = models.DateTimeField(_('Дата завершения'), null=True, blank=True)
    last_accessed = models.DateTimeField(
        _('Последний доступ'),
        auto_now=True
    )
    notes = models.TextField(
        _('Заметки пользователя'),
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = _('прогресс пользователя')
        verbose_name_plural = _('Прогресс пользователей')
        unique_together = ('user', 'lecture')
        indexes = [
            models.Index(fields=['user', 'completed']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.lecture.title}"


class UserTestResult(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name=_('Пользователь')
    )
    test = models.ForeignKey(
        Test, 
        on_delete=models.CASCADE, 
        verbose_name=_('Тест')
    )
    score = models.PositiveIntegerField(_('Баллы'))
    completed_at = models.DateTimeField(_('Дата завершения'), auto_now_add=True)
    details = models.JSONField(
        _('Детали результатов'),
        default=dict,
        blank=True
    )
    is_passed = models.BooleanField(
        _('Пройден успешно'),
        default=False
    )
    
    @property
    def max_score(self):
        return self.get_max_score()
    
    @property
    def percentage(self):
        return round(self.score / self.max_score * 100)

    class Meta:
        verbose_name = _('результат теста')
        verbose_name_plural = _('Результаты тестов')
        ordering = ['-completed_at']
        indexes = [
            models.Index(fields=['user', 'test']),
        ]

    def save(self, *args, **kwargs):
        if self.test:
            passing_score = (self.test.passing_score / 100) * self.get_max_score()
            self.is_passed = self.score >= passing_score
        super().save(*args, **kwargs)

    def get_max_score(self):
        if not hasattr(self, '_max_score'):
            self._max_score = sum(q.points for q in self.test.questions.all())
        return self._max_score

    def __str__(self):
        return f"{self.user.username} - {self.test.title} ({self.score}/{self.get_max_score()})"

class Comment(models.Model):
    lecture = models.ForeignKey(
        Lecture, 
        on_delete=models.CASCADE, 
        related_name='comments',
        verbose_name=_('Лекция')
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_('Автор')
    )
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies',
        verbose_name=_('Родительский комментарий')
    )
    text = models.TextField(_('Текст комментария'))
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Дата обновления'), auto_now=True)
    is_pinned = models.BooleanField(_('Закреплено'), default=False)

    class Meta:
        verbose_name = _('комментарий')
        verbose_name_plural = _('Комментарии')
        ordering = ['-is_pinned', 'created_at']
        indexes = [
            models.Index(fields=['lecture', 'parent']),
        ]

    def __str__(self):
        return f'Комментарий от {self.author.username} к лекции "{self.lecture.title}"'

    def clean(self):
        if self.parent and self.parent.lecture != self.lecture:
            raise ValidationError(
                {'parent': 'Родительский комментарий должен относиться к той же лекции'}
            )

    def get_absolute_url(self):
        return f"{self.lecture.get_absolute_url()}?comment={self.id}"
    
class Feedback(models.Model):
    name = models.CharField(_('Имя'), max_length=100)
    email = models.EmailField(_('Email'))
    message = models.TextField(_('Сообщение'))
    created_at = models.DateTimeField(_('Дата создания'), auto_now_add=True)
    is_processed = models.BooleanField(_('Обработано'), default=False)
    response = models.TextField(
        _('Ответ администратора'),
        blank=True,
        null=True
    )
    response_date = models.DateTimeField(
        _('Дата ответа'),
        blank=True,
        null=True
    )
    category = models.CharField(
        _('Категория'),
        max_length=50,
        choices=[
            ('bug', 'Ошибка на сайте'),
            ('suggestion', 'Предложение'),
            ('question', 'Вопрос'),
            ('other', 'Другое')
        ],
        default='question'
    )

    class Meta:
        verbose_name = _('обратная связь')
        verbose_name_plural = _('Обратная связь')
        ordering = ['-created_at']
        permissions = [
            ('can_respond', 'Может отвечать на обращения'),
        ]

    def __str__(self):
        return f'Сообщение от {self.name} ({self.email})'

class TaskResponse(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='responses')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    answer = models.TextField(verbose_name='Ответ ученика')
    submitted_at = models.DateTimeField(auto_now_add=True)
    score = models.PositiveIntegerField(null=True, blank=True, verbose_name='Оценка')
    feedback = models.TextField(blank=True, null=True, verbose_name='Комментарий преподавателя')
    is_checked = models.BooleanField(default=False, verbose_name='Проверено')

    class Meta:
        verbose_name = 'Ответ на задание'
        verbose_name_plural = 'Ответы на задания'
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Ответ {self.user.username} на задание {self.task.title}"