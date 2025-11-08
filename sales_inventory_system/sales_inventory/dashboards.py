"""
Dashboard views for different user roles
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import F, Sum, Count, Q
from products.models import Product
from orders.models import Order, Payment
from decimal import Decimal

def is_admin(user):
    return user.is_authenticated and user.is_admin

def is_cashier(user):
    return user.is_authenticated and user.is_cashier

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Admin dashboard with overview statistics"""

    # Get statistics
    total_products = Product.objects.filter(is_archived=False).count()
    low_stock_products = Product.objects.filter(
        is_archived=False,
        stock__lt=F('threshold')
    )
    low_stock_count = low_stock_products.count()

    # Order statistics
    pending_orders = Order.objects.filter(status='PENDING').count()
    in_progress_orders = Order.objects.filter(status='IN_PROGRESS').count()
    today_orders = Order.objects.filter(
        created_at__date=timezone.now().date()
    ).count()

    # Revenue statistics
    total_revenue = Payment.objects.filter(
        status='SUCCESS'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    today_revenue = Payment.objects.filter(
        status='SUCCESS',
        created_at__date=timezone.now().date()
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Recent orders
    recent_orders = Order.objects.all()[:5]

    context = {
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'low_stock_products': low_stock_products[:5],
        'pending_orders': pending_orders,
        'in_progress_orders': in_progress_orders,
        'today_orders': today_orders,
        'total_revenue': total_revenue,
        'today_revenue': today_revenue,
        'recent_orders': recent_orders,
    }

    return render(request, 'dashboards/admin.html', context)


@login_required
@user_passes_test(is_cashier)
def cashier_pos(request):
    """Cashier POS interface"""

    # Get pending and in-progress orders
    pending_orders = Order.objects.filter(status='PENDING').select_related('payment')
    in_progress_orders = Order.objects.filter(status='IN_PROGRESS')

    context = {
        'pending_orders': pending_orders,
        'in_progress_orders': in_progress_orders,
    }

    return render(request, 'dashboards/pos.html', context)


from django.utils import timezone
