"""Accounts URL Configuration"""
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_student, name='register'),
    path('register/student/', views.register_student, name='register_student'),
    path('register/faculty/', views.register_faculty, name='register_faculty'),
    path('login/', views.user_login, name='login'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('logout/', views.user_logout, name='logout'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('profile/', views.profile, name='profile'),
]
