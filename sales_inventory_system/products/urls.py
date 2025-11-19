from django.urls import path
from . import views
from . import bom_views

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='list'),
    path('create/', views.product_create, name='create'),
    path('<int:pk>/edit/', views.product_edit, name='edit'),
    path('<int:pk>/archive/', views.product_archive, name='archive'),

    # Ingredient Management
    path('ingredients/', views.ingredient_list, name='ingredient_list'),
    path('ingredients/create/', views.ingredient_create, name='ingredient_create'),
    path('ingredients/<int:pk>/edit/', views.ingredient_edit, name='ingredient_edit'),
    path('ingredients/<int:pk>/delete/', views.ingredient_delete, name='ingredient_delete'),

    # Recipe Management
    path('<int:pk>/recipe/', views.recipe_edit, name='recipe_edit'),

    # BOM (Bill of Materials) routes
    path('bom/dashboard/', bom_views.bom_dashboard, name='bom_dashboard'),
    path('bom/usage-report/', bom_views.ingredient_usage_report, name='bom_usage_report'),
    path('bom/variance-analysis/', bom_views.variance_analysis_report, name='bom_variance'),
    path('bom/low-stock/', bom_views.low_stock_report, name='bom_low_stock'),
    path('bom/waste/', bom_views.waste_report, name='bom_waste'),
    path('api/ingredient-availability/', bom_views.api_ingredient_availability, name='api_ingredient_availability'),
]
