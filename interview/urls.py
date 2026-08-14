"""Interview Practice URLs"""
from django.urls import path
from . import views

app_name = 'interview'

urlpatterns = [
    path('', views.interview_home, name='home'),
    path('', views.interview_home, name='start'),  # Alias for dashboard quick action
    path('practice/', views.practice, name='practice'),
    path('ai-practice/', views.ai_practice, name='ai_practice'),
    path('evaluate-answer/', views.evaluate_answer, name='evaluate_answer'),
    path('tips/', views.interview_tips, name='tips'),
    path('hr-questions/', views.hr_questions, name='hr_questions'),
    path('technical/', views.technical_questions, name='technical'),
]
