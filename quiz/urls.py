"""Quiz URLs"""
from django.urls import path
from . import views

app_name = 'quiz'

urlpatterns = [
    path('', views.quiz_home, name='home'),
    path('', views.quiz_home, name='take_test'),           # Alias for dashboard quick action
    path('tests/', views.test_list, name='test_list'),
    path('test/<int:pk>/start/', views.start_test, name='start_test'),
    path('test/<int:pk>/submit/', views.submit_test, name='submit_test'),
    path('attempt/<int:pk>/result/', views.test_result, name='test_result'),
    path('practice/', views.practice_questions, name='practice'),
    path('practice/check/<int:question_id>/', views.check_answer, name='check_answer'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('bookmarks/', views.bookmarks, name='bookmarks'),
    path('bookmark/<int:question_id>/', views.toggle_bookmark, name='toggle_bookmark'),
]
