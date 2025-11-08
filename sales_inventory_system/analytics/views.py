from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse


@login_required
def dashboard(request):
    """Display analytics dashboard."""
    return render(request, 'analytics/dashboard.html', {
        'total_sales': 0,
        'total_orders': 0,
        'message': 'Analytics dashboard - stub'
    })


@login_required
def sales_data_api(request):
    """API endpoint for sales data."""
    return JsonResponse({
        'success': True,
        'data': [],
        'message': 'Sales data API - stub'
    })
