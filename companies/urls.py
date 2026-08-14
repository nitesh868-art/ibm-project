"""Companies URLs"""
from django.urls import path
from . import views

app_name = 'companies'

urlpatterns = [
    path('', views.company_list, name='list'),
    path('<int:pk>/', views.company_detail, name='detail'),
]
