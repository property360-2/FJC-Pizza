from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.db.models import Sum, Count, F, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from orders.models import Order, Payment, OrderItem
from products.models import Product
from .forecasting import forecast_sales


def is_admin(user):
    return user.is_authenticated and user.is_admin


@login_required
@user_passes_test(is_admin)
def dashboard(request):
    """Display analytics dashboard with comprehensive sales data"""

    # Date ranges
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Total revenue (all time)
    total_revenue = Payment.objects.filter(
        status='SUCCESS'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Revenue by period
    today_revenue = Payment.objects.filter(
        status='SUCCESS',
        created_at__date=today
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    week_revenue = Payment.objects.filter(
        status='SUCCESS',
        created_at__date__gte=week_ago
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    month_revenue = Payment.objects.filter(
        status='SUCCESS',
        created_at__date__gte=month_ago
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Order statistics
    total_orders = Order.objects.count()
    today_orders = Order.objects.filter(created_at__date=today).count()
    week_orders = Order.objects.filter(created_at__date__gte=week_ago).count()

    pending_orders = Order.objects.filter(status='PENDING').count()
    in_progress_orders = Order.objects.filter(status='IN_PROGRESS').count()
    completed_orders = Order.objects.filter(status='FINISHED').count()

    # Average order value
    avg_order_value = Payment.objects.filter(
        status='SUCCESS'
    ).aggregate(avg=Sum('amount'))['avg'] or Decimal('0.00')

    if total_orders > 0:
        avg_order_value = total_revenue / total_orders

    # Top selling products
    top_products = OrderItem.objects.values(
        'product__name',
        'product__price'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('subtotal')
    ).order_by('-total_quantity')[:10]

    # Low stock products
    low_stock_products = Product.objects.filter(
        is_archived=False,
        stock__lt=F('threshold')
    ).order_by('stock')[:10]

    # Recent orders
    recent_orders = Order.objects.select_related('payment').order_by('-created_at')[:10]

    context = {
        # Revenue metrics
        'total_revenue': total_revenue,
        'today_revenue': today_revenue,
        'week_revenue': week_revenue,
        'month_revenue': month_revenue,

        # Order metrics
        'total_orders': total_orders,
        'today_orders': today_orders,
        'week_orders': week_orders,
        'pending_orders': pending_orders,
        'in_progress_orders': in_progress_orders,
        'completed_orders': completed_orders,
        'avg_order_value': avg_order_value,

        # Product metrics
        'top_products': top_products,
        'low_stock_products': low_stock_products,

        # Recent activity
        'recent_orders': recent_orders,
    }
    return render(request, 'analytics/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def sales_data_api(request):
    """API endpoint for sales data (for charts)"""
    period = request.GET.get('period', 'week')  # day, week, month

    today = timezone.now().date()

    if period == 'day':
        # Last 24 hours by hour
        data = []
        for hour in range(24):
            hour_start = timezone.now().replace(hour=hour, minute=0, second=0, microsecond=0)
            hour_end = hour_start + timedelta(hours=1)

            revenue = Payment.objects.filter(
                status='SUCCESS',
                created_at__gte=hour_start,
                created_at__lt=hour_end
            ).aggregate(total=Sum('amount'))['total'] or 0

            data.append({
                'label': f'{hour:02d}:00',
                'value': float(revenue)
            })

    elif period == 'week':
        # Last 7 days
        data = []
        for i in range(7):
            day = today - timedelta(days=6-i)
            revenue = Payment.objects.filter(
                status='SUCCESS',
                created_at__date=day
            ).aggregate(total=Sum('amount'))['total'] or 0

            data.append({
                'label': day.strftime('%a'),
                'value': float(revenue)
            })

    else:  # month
        # Last 30 days
        data = []
        for i in range(30):
            day = today - timedelta(days=29-i)
            revenue = Payment.objects.filter(
                status='SUCCESS',
                created_at__date=day
            ).aggregate(total=Sum('amount'))['total'] or 0

            data.append({
                'label': day.strftime('%m/%d'),
                'value': float(revenue)
            })

    return JsonResponse({
        'success': True,
        'data': data
    })


@login_required
@user_passes_test(is_admin)
def sales_forecast(request):
    """Display sales forecasting using Holt-Winters Exponential Smoothing"""

    # Get parameters from request (with defaults)
    days_back = int(request.GET.get('days_back', 30))
    days_ahead = int(request.GET.get('days_ahead', 7))

    # Validate parameters
    days_back = max(7, min(days_back, 90))  # Between 7 and 90 days
    days_ahead = max(1, min(days_ahead, 30))  # Between 1 and 30 days

    # Generate forecast
    forecast_result = forecast_sales(days_back=days_back, days_ahead=days_ahead)

    context = {
        'forecast_result': forecast_result,
        'days_back': days_back,
        'days_ahead': days_ahead,
    }

    return render(request, 'analytics/forecast.html', context)
