"""
URL configuration for products app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list_view, name='product_list'),
    path('create/', views.product_create_view, name='product_create'),
    path('<int:product_id>/', views.product_detail_view, name='product_detail'),
    path('<int:product_id>/edit/', views.product_edit_view, name='product_edit'),
    path('<int:product_id>/archive/', views.product_archive_view, name='product_archive'),
    path('<int:product_id>/unarchive/', views.product_unarchive_view, name='product_unarchive'),
]
