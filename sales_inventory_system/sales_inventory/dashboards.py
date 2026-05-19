# ==============================================================================
# FJC-PIZZA SALES & INVENTORY MANAGEMENT SYSTEM
# File: sales_inventory/dashboards.py
# Purpose: Dashboard views for different user roles (Admin & Cashier).
# Contains:
#   - User verification helpers: is_admin, is_cashier
#   - Admin Dashboard View: admin_dashboard
#   - Cashier Point of Sale (POS) View: cashier_pos
# How it fits: This file bridges system data models (Products, Orders, Payments) 
# and user interfaces by aggregating key statistics, active/pending metrics, and 
# status counts into digestible dashboard and POS contexts for role-restricted templates.
# ==============================================================================

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from django.utils import timezone
from sales_inventory_system.products.models import Product
from sales_inventory_system.orders.models import Order, Payment
from decimal import Decimal

def is_admin(user):
    """
    Verify whether the provided user is authenticated and carries the Admin role.
    
    Accepts:
        user (User): The user model instance to inspect.
        
    Returns:
        bool: True if the user is authenticated and is an admin; otherwise, False.
    """
    return user.is_authenticated and user.is_admin


def is_cashier(user):
    """
    Verify whether the provided user is authenticated and carries the Cashier role.
    
    Accepts:
        user (User): The user model instance to inspect.
        
    Returns:
        bool: True if the user is authenticated and is a cashier; otherwise, False.
    """
    return user.is_authenticated and user.is_cashier


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """
    Aggregate system-wide statistics to compile and render the Admin Dashboard interface.
    The view calculates product counts, identifies low stock levels (accounting for 
    BOM dependencies via Product.calculated_stock), collects active order statuses 
    (pending, in progress), and aggregates revenue (today vs lifetime) from successfully 
    processed payments.
    
    Accepts:
        request (HttpRequest): Current active HTTP request session.
        
    Returns/Renders:
        HttpResponse: Renders the 'dashboards/admin.html' template with a populated 
        context containing product and order counts, recent logs, and revenue metrics.
    """

    # Get statistics
    total_products = Product.objects.filter(is_archived=False).count()

    # Get low stock products using calculated_stock (accounts for BOM products)
    all_active_products = Product.objects.filter(is_archived=False).select_related(
        'recipe'
    ).prefetch_related(
        'recipe__ingredients__ingredient'
    )
    low_stock_products_list = [p for p in all_active_products if p.calculated_stock < p.threshold]
    low_stock_count = len(low_stock_products_list)
    low_stock_products = low_stock_products_list[:5]

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
    """
    Manage, format, and render the Cashier POS (Point of Sale) operator panel.
    Retrieves and displays lists of orders grouped by status (pending, in_progress, 
    finished) and computes real-time daily metrics such as completed order count, 
    total processed orders, and cumulative success-state revenue.
    
    Accepts:
        request (HttpRequest): Current active HTTP request session.
        
    Returns/Renders:
        HttpResponse: Renders the 'dashboards/pos.html' template with complete order lists
        and POS operational metrics.
    """

    # Get orders by status with prefetch for efficiency
    pending_orders = Order.objects.filter(status='PENDING').select_related('payment').prefetch_related('items__product').order_by('-created_at')
    in_progress_orders = Order.objects.filter(status='IN_PROGRESS').prefetch_related('items__product').order_by('-created_at')
    finished_orders = Order.objects.filter(status='FINISHED').prefetch_related('items__product').order_by('-created_at')[:10]  # Last 10 finished

    # Today's statistics
    today = timezone.now().date()
    today_orders_count = Order.objects.filter(created_at__date=today).count()
    today_completed = Order.objects.filter(status='FINISHED', created_at__date=today).count()
    today_revenue = Payment.objects.filter(status='SUCCESS', created_at__date=today).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    context = {
        'pending_orders': pending_orders,
        'in_progress_orders': in_progress_orders,
        'finished_orders': finished_orders,
        'today_orders_count': today_orders_count,
        'today_completed': today_completed,
        'today_revenue': today_revenue,
        'pending_count': pending_orders.count(),
    }

    return render(request, 'dashboards/pos.html', context)

