"""Placement Preparation URLs"""
from django.urls import path
from . import views

app_name = 'placement'

urlpatterns = [
    path('', views.placement_home, name='home'),
    path('', views.placement_home, name='skill_gap'),     # Alias — full page at placement:home
    path('progress/', views.progress, name='readiness'),  # Alias — readiness from progress view
    path('aptitude/', views.aptitude, name='aptitude'),
    path('reasoning/', views.reasoning, name='reasoning'),
    path('verbal/', views.verbal, name='verbal'),
    path('programming/', views.programming, name='programming'),
    path('programming/<str:language>/', views.programming_by_language, name='programming_by_language'),
    path('company/<int:pk>/questions/', views.company_questions, name='company_questions'),
    path('mock-tests/', views.mock_tests, name='mock_tests'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('progress/', views.progress, name='progress'),
]
