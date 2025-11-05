from django.urls import path
from django.views.generic import TemplateView

app_name = 'orders'

# Placeholder views for POS
urlpatterns = [
    path('pos/', TemplateView.as_view(template_name='orders/pos.html'), name='pos'),
]
