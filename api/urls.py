"""API URLs"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'questions', views.QuestionViewSet, basename='questions')
router.register(r'notifications', views.NotificationViewSet, basename='notifications')

app_name = 'api'

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
    path('dashboard-stats/', views.dashboard_stats, name='dashboard_stats'),
    path('study-data/', views.study_data, name='study_data'),
    path('ai-chat/', views.ai_chat, name='ai_chat'),
    path('generate-plan/', views.generate_study_plan, name='generate_plan'),
]
