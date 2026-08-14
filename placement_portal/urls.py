"""
Main URL Configuration for AI Placement Preparation & Smart Study Planner Portal
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Core Landing Page
    path('', include('core.urls')),

    # Authentication
    path('accounts/', include('accounts.urls')),

    # Dashboard
    path('dashboard/', include('dashboard.urls')),

    # Study Planner
    path('study-planner/', include('studyplanner.urls')),

    # Placement Preparation
    path('placement/', include('placement.urls')),

    # Resume Builder
    path('resume/', include('resume_builder.urls')),

    # Interview Practice
    path('interview/', include('interview.urls')),

    # Quiz & Mock Tests
    path('quiz/', include('quiz.urls')),

    # Companies
    path('companies/', include('companies.urls')),

    # Analytics
    path('analytics/', include('analytics.urls')),

    # Notifications
    path('notifications/', include('notifications.urls')),

    # AI Chatbot
    path('chatbot/', include('chatbot.urls')),

    # REST API
    path('api/v1/', include('api.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom Admin Site Header
admin.site.site_header = "AI Placement Portal — Admin"
admin.site.site_title = "Placement Portal Admin"
admin.site.index_title = "Welcome to the Admin Panel"
