"""
API views for analytics and reporting.

Provides endpoints for sales metrics, reports, and data visualization.
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Sum, Count, Avg, F, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from orders.models import Order, OrderItem, Payment
from products.models import Product
from accounts.decorators import role_required


@require_http_methods(["GET"])
@role_required(['ADMIN'])
def analytics_overview(request):
    """
    GET /api/analytics/overview/
    Get key performance indicators (KPIs).
    """
    # Total sales (successful payments)
    total_sales = Payment.objects.filter(
        status='SUCCESS'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # Total orders
    total_orders = Order.objects.count()

    # Total products
    total_products = Product.objects.filter(is_archived=False).count()

    # Low stock products
    low_stock_count = Product.objects.filter(
        is_archived=False,
        stock__lt=F('threshold')
    ).count()

    # Out of stock products
    out_of_stock_count = Product.objects.filter(
        is_archived=False,
        stock=0
    ).count()

    # Today's sales
    today = timezone.now().date()
    today_sales = Payment.objects.filter(
        status='SUCCESS',
        processed_at__date=today
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # Today's orders
    today_orders = Order.objects.filter(
        created_at__date=today
    ).count()

    return JsonResponse({
        'success': True,
        'overview': {
            'total_sales': str(total_sales),
            'total_orders': total_orders,
            'total_products': total_products,
            'low_stock_count': low_stock_count,
            'out_of_stock_count': out_of_stock_count,
            'today_sales': str(today_sales),
            'today_orders': today_orders,
        }
    })


@require_http_methods(["GET"])
@role_required(['ADMIN'])
def analytics_sales_by_date(request):
    """
    GET /api/analytics/sales-by-date/
    Get sales grouped by date.

    Query params:
    - days: Number of days to look back (default: 7)
    """
    days = int(request.GET.get('days', 7))
    start_date = timezone.now() - timedelta(days=days)

    # Get daily sales
    daily_sales = Payment.objects.filter(
        status='SUCCESS',
        processed_at__gte=start_date
    ).extra(
        select={'date': 'DATE(processed_at)'}
    ).values('date').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('date')

    sales_data = []
    for item in daily_sales:
        sales_data.append({
            'date': str(item['date']),
            'total_sales': str(item['total']),
            'order_count': item['count'],
        })

    return JsonResponse({
        'success': True,
        'sales_by_date': sales_data
    })


@require_http_methods(["GET"])
@role_required(['ADMIN'])
def analytics_top_products(request):
    """
    GET /api/analytics/top-products/
    Get top-selling products.

    Query params:
    - limit: Number of products to return (default: 10)
    """
    limit = int(request.GET.get('limit', 10))

    # Get top products by total quantity sold
    top_products = OrderItem.objects.filter(
        order__payment__status='SUCCESS'
    ).values(
        'product__id',
        'product__name',
        'product__price'
    ).annotate(
        total_qty=Sum('qty'),
        total_revenue=Sum(F('qty') * F('price_at_purchase'))
    ).order_by('-total_qty')[:limit]

    products_data = []
    for item in top_products:
        products_data.append({
            'product_id': item['product__id'],
            'product_name': item['product__name'],
            'total_qty_sold': item['total_qty'],
            'total_revenue': str(item['total_revenue']),
        })

    return JsonResponse({
        'success': True,
        'top_products': products_data
    })


@require_http_methods(["GET"])
@role_required(['ADMIN'])
def analytics_low_stock(request):
    """
    GET /api/analytics/low-stock/
    Get products with low stock.
    """
    low_stock_products = Product.objects.filter(
        is_archived=False,
        stock__lt=F('threshold')
    ).order_by('stock')

    products_data = []
    for product in low_stock_products:
        products_data.append({
            'id': product.id,
            'name': product.name,
            'stock': product.stock,
            'threshold': product.threshold,
            'is_out_of_stock': product.is_out_of_stock,
        })

    return JsonResponse({
        'success': True,
        'low_stock_products': products_data
    })


@require_http_methods(["GET"])
@role_required(['ADMIN'])
def analytics_payment_methods(request):
    """
    GET /api/analytics/payment-methods/
    Get payment method breakdown.
    """
    payment_stats = Payment.objects.filter(
        status='SUCCESS'
    ).values('method').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')

    methods_data = []
    for item in payment_stats:
        methods_data.append({
            'method': item['method'],
            'total_amount': str(item['total']),
            'count': item['count'],
        })

    return JsonResponse({
        'success': True,
        'payment_methods': methods_data
    })


@require_http_methods(["GET"])
@role_required(['ADMIN'])
def analytics_order_status(request):
    """
    GET /api/analytics/order-status/
    Get order status breakdown.
    """
    status_stats = Order.objects.values('status').annotate(
        count=Count('id')
    ).order_by('-count')

    status_data = []
    for item in status_stats:
        status_data.append({
            'status': item['status'],
            'count': item['count'],
        })

    return JsonResponse({
        'success': True,
        'order_status': status_data
    })
