"""Resume Builder URLs"""
from django.urls import path
from . import views

app_name = 'resume_builder'

urlpatterns = [
    path('', views.resume_home, name='home'),
    path('create/', views.create_resume, name='create'),
    path('<int:pk>/edit/', views.edit_resume, name='edit'),
    path('<int:pk>/preview/', views.preview_resume, name='preview'),
    path('<int:pk>/download/', views.download_resume_pdf, name='download'),
    path('<int:pk>/download/pdf/', views.download_resume_pdf, name='download_pdf'),
    path('<int:pk>/ats-score/', views.ats_score, name='ats_score'),
    path('<int:pk>/ai-suggestions/', views.ai_suggestions, name='ai_suggestions'),
    path('<int:pk>/delete/', views.delete_resume, name='delete'),
    # Section CRUD
    path('<int:resume_pk>/education/add/', views.add_education, name='add_education'),
    path('<int:resume_pk>/experience/add/', views.add_experience, name='add_experience'),
    path('<int:resume_pk>/project/add/', views.add_project, name='add_project'),
    path('<int:resume_pk>/skill/add/', views.add_skill, name='add_skill'),
    path('<int:resume_pk>/certification/add/', views.add_certification, name='add_certification'),
]
