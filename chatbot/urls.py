"""Chatbot URLs"""
from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('', views.chatbot_home, name='home'),
    path('', views.chatbot_home, name='chat'),         # Alias: chatbot:chat for dashboard
    path('ask/', views.ask_ai, name='ask'),
    path('history/', views.chat_history, name='history'),
    path('clear/', views.clear_history, name='clear'),
    path('daily-reco/', views.daily_recommendations, name='daily_reco'),  # Dashboard widget
]
