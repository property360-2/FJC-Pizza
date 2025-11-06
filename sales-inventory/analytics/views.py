"""
Views for analytics and reporting.
"""
from django.shortcuts import render
from accounts.decorators import role_required


@role_required(['ADMIN'])
def dashboard_view(request):
    """
    GET /dashboard/
    Analytics dashboard with KPIs and reports.
    """
    return render(request, 'analytics/dashboard.html')


@role_required(['ADMIN'])
def component_preview_view(request):
    """
    GET /dashboard/components/
    Component library preview and documentation.
    """
    return render(request, 'analytics/component_preview.html')
