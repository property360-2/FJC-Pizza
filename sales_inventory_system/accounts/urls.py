# ==============================================================================
# FJC-PIZZA SALES & INVENTORY MANAGEMENT SYSTEM
# File: accounts/urls.py
# Purpose: URL Routing patterns for the accounts management app.
# Contains:
#   - Login & Logout endpoints
#   - Staff administration routes (list, create, edit, archive, unarchive, audit)
# How it fits: Defines accessible route endpoints mapping directly to accounts views, 
# exposing staff administration dashboards and login screens to the web router.
# ==============================================================================

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/archive/', views.user_archive, name='user_archive'),
    path('users/<int:pk>/unarchive/', views.user_unarchive, name='user_unarchive'),
    path('users/<int:pk>/audit/', views.user_audit_trail, name='user_audit_trail'),
]
