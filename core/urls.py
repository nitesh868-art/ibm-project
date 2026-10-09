"""Core app URL configuration — Landing page, About, Contact, FAQ"""
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('faq/', views.faq, name='faq'),
    path('features/', views.features, name='features'),
    path('switch-role/<str:role>/', views.switch_role, name='switch_role'),
]
