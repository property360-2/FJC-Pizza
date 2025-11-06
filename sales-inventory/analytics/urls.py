"""
URL configuration for analytics app.
"""
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='index'),
    path('components/', views.component_preview_view, name='components'),
]
