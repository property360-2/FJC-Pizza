"""
URL configuration for orders app.
"""
from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = 'orders'

urlpatterns = [
    path('pos/', views.pos_view, name='pos'),
    path('orders/queue/', views.order_queue_view, name='order_queue'),
    path('orders/<int:order_id>/', views.order_detail_view, name='order_detail'),
    path('kiosk/', TemplateView.as_view(template_name='orders/kiosk.html'), name='kiosk'),
]
