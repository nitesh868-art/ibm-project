"""Study Planner URLs"""
from django.urls import path
from . import views

app_name = 'studyplanner'

urlpatterns = [
    path('', views.planner_home, name='home'),
    path('', views.planner_home, name='planner'),  # Alias for dashboard quick action
    path('subjects/', views.subject_list, name='subjects'),
    path('subjects/add/', views.add_subject, name='add_subject'),
    path('subjects/<int:pk>/edit/', views.edit_subject, name='edit_subject'),
    path('subjects/<int:pk>/delete/', views.delete_subject, name='delete_subject'),
    path('subjects/<int:pk>/topics/', views.topic_list, name='topics'),
    path('topics/add/<int:subject_id>/', views.add_topic, name='add_topic'),
    path('topics/<int:pk>/update-status/', views.update_topic_status, name='update_topic_status'),
    path('plans/', views.study_plans, name='plans'),
    path('plans/generate/', views.generate_ai_plan, name='generate_ai_plan'),
    path('pomodoro/', views.pomodoro, name='pomodoro'),
    path('goals/', views.goals, name='goals'),
    path('goals/add/', views.add_goal, name='add_goal'),
    path('goals/<int:pk>/complete/', views.complete_goal, name='complete_goal'),
    path('log/', views.study_log, name='log'),
    path('log/add/', views.add_study_log, name='add_study_log'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('materials/', views.study_materials, name='materials'),
    path('materials/upload/', views.upload_notes, name='upload_notes'),
    path('materials/<int:pk>/explain/', views.explain_notes, name='explain_notes'),
]

