from django.contrib import admin
from django.conf import settings
from django.db import models
from tinymce.widgets import TinyMCE
from .models import Course, Lecture, Test, Question, Answer, Task, UserProgress, UserTestResult, Feedback, TaskResponse

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 1
    fields = ('text', 'is_correct', 'order')

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    inlines = [AnswerInline]
    list_display = ('text', 'test', 'order')
    list_editable = ('order',)

class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    show_change_link = True
    fields = ('text', 'order')

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]
    list_display = ('title', 'lecture', 'is_published')
    list_editable = ('is_published',)
    list_filter = ('lecture__course', 'is_published')

class TestInline(admin.StackedInline):
    model = Test
    extra = 0
    fields = ('title', 'description', 'is_published')
    show_change_link = True

class LectureInline(admin.StackedInline):
    model = Lecture
    extra = 0
    formfield_overrides = {
        models.TextField: {'widget': TinyMCE()}
    }
    fields = ('title', 'slug', 'content', 'order', 'is_published')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    inlines = [LectureInline]
    list_display = ('title', 'is_active', 'order')
    list_editable = ('is_active', 'order')
    prepopulated_fields = {'slug': ('title',)}


class TaskInline(admin.StackedInline):
    model = Task
    extra = 1
    fields = ('title', 'task_type', 'description', 'flag', 'order', 'max_score')
    formfield_overrides = {
        models.TextField: {'widget': TinyMCE()}
    }

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'lecture', 'task_type', 'order')
    list_editable = ('order',)
    list_filter = ('lecture__course', 'task_type')
    search_fields = ('title', 'description')
    formfield_overrides = {
        models.TextField: {'widget': TinyMCE()}
    }

@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    inlines = [TaskInline, TestInline]
    list_display = ('title', 'course', 'order', 'is_published', 'has_video')
    list_editable = ('order', 'is_published')
    list_filter = ('course', 'is_published')
    prepopulated_fields = {'slug': ('title',)}
    
    fieldsets = (
        (None, {
            'fields': ('course', 'title', 'slug', 'content')
        }),
        ('Дополнительно', {
            'fields': (
                ('video_url', 'duration'),
                ('resources', 'order'),
                'is_published'
            ),
            'classes': ('collapse',)
        }),
    )

    def has_video(self, obj):
        return bool(obj.video_url)
    has_video.boolean = True
    has_video.short_description = 'Есть видео'
    
    formfield_overrides = {
        models.TextField: {'widget': TinyMCE()}
    }

@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'lecture', 'completed', 'last_accessed')
    list_filter = ('user', 'lecture__course', 'completed')
    search_fields = ('user__username', 'lecture__title')

@admin.register(UserTestResult)
class UserTestResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'test', 'score', 'max_score', 'percentage', 'is_passed', 'completed_at')
    list_filter = ('user', 'test__lecture__course', 'is_passed')
    search_fields = ('user__username', 'test__title')
    readonly_fields = ('details_preview',)
    
    def max_score(self, obj):
        return obj.get_max_score()
    max_score.short_description = 'Макс. балл'
    
    def percentage(self, obj):
        return f"{round(obj.score / obj.get_max_score() * 100)}%"
    percentage.short_description = 'Процент'
    
    def details_preview(self, obj):
        if not obj.details:
            return "-"
        preview = []
        for q_id, detail in obj.details.items():
            status = "✓" if detail.get('is_correct') else "✗"
            preview.append(f"{status} Вопрос: {detail.get('question', '')}")
        return "<br>".join(preview)
    details_preview.short_description = "Детали"
    details_preview.allow_tags = True

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'category', 'is_processed', 'created_at')
    list_filter = ('category', 'is_processed')
    search_fields = ('name', 'email', 'message')
    actions = ['mark_as_processed']
    
    def mark_as_processed(self, request, queryset):
        queryset.update(is_processed=True)
    mark_as_processed.short_description = "Пометить как обработанные"

@admin.register(TaskResponse)
class TaskResponseAdmin(admin.ModelAdmin):
    list_display = ('task', 'user', 'submitted_at', 'score', 'is_checked')
    list_filter = ('is_checked', 'task', 'user')
    search_fields = ('answer', 'feedback', 'user__username', 'task__title')
    list_editable = ('score', 'is_checked')
    readonly_fields = ('task', 'user', 'submitted_at')
    fieldsets = (
        (None, {
            'fields': ('task', 'user', 'submitted_at')
        }),
        ('Ответ', {
            'fields': ('answer',)
        }),
        ('Проверка', {
            'fields': ('is_checked', 'score', 'feedback')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if 'score' in form.changed_data or 'feedback' in form.changed_data:
            obj.is_checked = True
        super().save_model(request, obj, form, change)

admin.site.site_header = settings.ADMIN_SITE_HEADER
admin.site.index_title = "Управление учебными материалами"