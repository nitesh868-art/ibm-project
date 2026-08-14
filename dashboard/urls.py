"""Dashboard URLs"""
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('faculty/', views.faculty_dashboard, name='faculty'),
    path('admin/', views.admin_dashboard, name='admin'),
    path('admin/activity/', views.activity_log, name='activity_log'),
    path('admin/ai-health/', views.ai_health_check, name='ai_health'),
    path('profile-completion/', views.profile_completion, name='profile_completion'),
    path('certificates/', views.certificates_list, name='certificates'),
    path('certificates/<str:cert_id>/', views.view_certificate, name='view_certificate'),
]


