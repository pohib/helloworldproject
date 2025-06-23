from django.contrib import admin
from django.db import models
from tinymce.widgets import TinyMCE
from .models import Course, Lecture, Test, Question, Answer, Task, UserProgress, UserTestResult, Feedback

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
    list_display = ('title', 'course', 'order', 'is_published')
    list_editable = ('order', 'is_published')
    list_filter = ('course', 'is_published')
    prepopulated_fields = {'slug': ('title',)}
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
    list_display = ('user', 'test', 'score', 'is_passed', 'completed_at')
    list_filter = ('user', 'test__lecture__course', 'is_passed')
    search_fields = ('user__username', 'test__title')

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'category', 'is_processed', 'created_at')
    list_filter = ('category', 'is_processed')
    search_fields = ('name', 'email', 'message')
    actions = ['mark_as_processed']
    
    def mark_as_processed(self, request, queryset):
        queryset.update(is_processed=True)
    mark_as_processed.short_description = "Пометить как обработанные"