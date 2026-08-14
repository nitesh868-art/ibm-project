"""Analytics URLs"""
from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.analytics_home, name='home'),
    path('study/', views.study_analytics, name='study'),
    path('placement/', views.placement_analytics, name='placement'),
    path('export/pdf/', views.export_pdf, name='export_pdf'),
    path('export/excel/', views.export_excel, name='export_excel'),
    path('api/chart-data/', views.chart_data, name='chart_data'),
]
