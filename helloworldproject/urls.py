from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from core.views import contact_view
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('about/', TemplateView.as_view(template_name='about.html')),
    path('teachers/', TemplateView.as_view(template_name='teachers.html')),
    path('security/', TemplateView.as_view(template_name='security.html')),
    path('faq/', TemplateView.as_view(template_name='faq.html')),
    path('tinymce/', include('tinymce.urls')),
    path('accounts/', include('allauth.urls')),
    path('contact/', contact_view, name='contact'),
    path('users/', include('users.urls')),
    path('', include('core.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
