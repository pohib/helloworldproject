from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('courses/<slug:slug>/', views.course_detail, name='course_detail'),
    path('courses/<slug:course_slug>/<slug:lecture_slug>/', views.lecture_detail, name='lecture_detail'),
    path('courses/<slug:course_slug>/<slug:lecture_slug>/html/', views.lecture_html_view, name='lecture_html'),
    path('tests/<int:test_id>/', views.test_detail, name='test_detail'),
    path('tasks/<int:task_id>/', views.task_detail, name='task_detail'),
    path('comments/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
]