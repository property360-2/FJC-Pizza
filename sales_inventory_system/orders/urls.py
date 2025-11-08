from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.order_list, name='list'),
    path('<int:pk>/', views.order_detail, name='detail'),
    path('<int:pk>/update-status/', views.update_order_status, name='update_status'),
    path('<int:pk>/process-payment/', views.process_payment, name='process_payment'),
]
