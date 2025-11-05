from django.urls import path
from django.views.generic import TemplateView

app_name = 'dashboard'

# Placeholder views for dashboard
urlpatterns = [
    path('', TemplateView.as_view(template_name='analytics/dashboard.html'), name='index'),
]
