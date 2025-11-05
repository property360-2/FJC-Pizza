"""
API views for orders and payments.

Provides RESTful endpoints for order management and payment processing.
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q
from django.db import transaction
import json
from .models import Order, OrderItem, Payment
from products.models import Product
from accounts.decorators import role_required


@require_http_methods(["GET"])
@role_required(['ADMIN', 'CASHIER'])
def order_list(request):
    """
    GET /api/orders/
    List all orders with optional filtering and pagination.

    Query params:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20)
    - status: Filter by status (PENDING, IN_PROGRESS, FINISHED, CANCELLED)
    - order_no: Search by order number
    """
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 20))
    status = request.GET.get('status', '')
    order_no = request.GET.get('order_no', '')

    # Base queryset
    queryset = Order.objects.all()

    # Apply filters
    if status:
        queryset = queryset.filter(status=status)

    if order_no:
        queryset = queryset.filter(order_no__icontains=order_no)

    # Order by created_at descending (newest first)
    queryset = queryset.order_by('-created_at')

    # Paginate
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page)

    # Serialize orders
    orders = []
    for order in page_obj:
        orders.append({
            'id': order.id,
            'order_no': order.order_no,
            'status': order.status,
            'total_amount': str(order.total_amount),
            'item_count': order.item_count,
            'created_by': order.created_by.username if order.created_by else 'Kiosk',
            'created_at': order.created_at.isoformat(),
            'updated_at': order.updated_at.isoformat(),
        })

    return JsonResponse({
        'success': True,
        'orders': orders,
        'pagination': {
            'page': page_obj.number,
            'per_page': per_page,
            'total_pages': paginator.num_pages,
            'total_items': paginator.count,
            'has_next': page_obj.has_next(),
            'has_prev': page_obj.has_previous(),
        }
    })


@require_http_methods(["GET"])
def order_detail(request, order_id):
    """
    GET /api/orders/<id>/
    Get a single order by ID with items and payment.
    """
    try:
        order = Order.objects.get(pk=order_id)

        # Get order items
        items = []
        for item in order.items.all():
            items.append({
                'id': item.id,
                'product_id': item.product.id,
                'product_name': item.product.name,
                'qty': item.qty,
                'price_at_purchase': str(item.price_at_purchase),
                'subtotal': str(item.subtotal),
            })

        # Get payment if exists
        payment_data = None
        if hasattr(order, 'payment'):
            payment = order.payment
            payment_data = {
                'id': payment.id,
                'method': payment.method,
                'status': payment.status,
                'amount': str(payment.amount),
                'processed_by': payment.processed_by.username if payment.processed_by else None,
                'processed_at': payment.processed_at.isoformat() if payment.processed_at else None,
            }

        return JsonResponse({
            'success': True,
            'order': {
                'id': order.id,
                'order_no': order.order_no,
                'status': order.status,
                'total_amount': str(order.total_amount),
                'item_count': order.item_count,
                'created_by': order.created_by.username if order.created_by else 'Kiosk',
                'created_at': order.created_at.isoformat(),
                'updated_at': order.updated_at.isoformat(),
                'items': items,
                'payment': payment_data,
            }
        })

    except Order.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Order not found'
        }, status=404)


@csrf_exempt
@require_http_methods(["POST"])
def order_create(request):
    """
    POST /api/orders/create/
    Create a new order with items.

    Body: {
        "items": [
            {"product_id": 1, "qty": 2},
            {"product_id": 2, "qty": 1}
        ],
        "payment_method": "CASH" or "ONLINE_DEMO"
    }
    """
    try:
        data = json.loads(request.body)

        # Validate items
        items_data = data.get('items', [])
        if not items_data:
            return JsonResponse({
                'success': False,
                'error': 'At least one item is required'
            }, status=400)

        payment_method = data.get('payment_method', 'CASH')
        if payment_method not in ['CASH', 'ONLINE_DEMO']:
            return JsonResponse({
                'success': False,
                'error': 'Invalid payment method'
            }, status=400)

        # Create order and items in a transaction
        with transaction.atomic():
            # Create order
            order = Order.objects.create(
                created_by=request.user if request.user.is_authenticated else None
            )

            # Create order items
            total_amount = 0
            for item_data in items_data:
                product_id = item_data.get('product_id')
                qty = item_data.get('qty', 1)

                try:
                    product = Product.objects.get(pk=product_id, is_archived=False)
                except Product.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': f'Product {product_id} not found or archived'
                    }, status=404)

                # Check stock availability
                if product.stock < qty:
                    return JsonResponse({
                        'success': False,
                        'error': f'Insufficient stock for {product.name}. Available: {product.stock}, Requested: {qty}'
                    }, status=400)

                # Create order item
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    qty=qty
                )

                total_amount += product.price * qty

            # Create payment
            payment = Payment.objects.create(
                order=order,
                method=payment_method,
                amount=total_amount
            )

        return JsonResponse({
            'success': True,
            'message': 'Order created successfully',
            'order': {
                'id': order.id,
                'order_no': order.order_no,
                'total_amount': str(order.total_amount),
                'payment_id': payment.id,
            }
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@role_required(['ADMIN', 'CASHIER'])
def order_mark_in_progress(request, order_id):
    """
    POST /api/orders/<id>/mark-in-progress/
    Mark order as in progress.
    """
    try:
        order = Order.objects.get(pk=order_id)
        order.mark_in_progress()

        return JsonResponse({
            'success': True,
            'message': 'Order marked as in progress'
        })

    except Order.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Order not found'
        }, status=404)


@csrf_exempt
@require_http_methods(["POST"])
@role_required(['ADMIN', 'CASHIER'])
def order_finish(request, order_id):
    """
    POST /api/orders/<id>/finish/
    Mark order as finished.
    """
    try:
        order = Order.objects.get(pk=order_id)
        order.finish()

        return JsonResponse({
            'success': True,
            'message': 'Order finished'
        })

    except Order.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Order not found'
        }, status=404)


@csrf_exempt
@require_http_methods(["POST"])
@role_required(['ADMIN', 'CASHIER'])
def order_cancel(request, order_id):
    """
    POST /api/orders/<id>/cancel/
    Cancel an order.
    """
    try:
        order = Order.objects.get(pk=order_id)
        order.cancel()

        return JsonResponse({
            'success': True,
            'message': 'Order cancelled'
        })

    except Order.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Order not found'
        }, status=404)


# ============================================================================
# PAYMENT API
# ============================================================================

@require_http_methods(["GET"])
@role_required(['ADMIN', 'CASHIER'])
def payment_list(request):
    """
    GET /api/payments/
    List all payments.
    """
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 20))
    status = request.GET.get('status', '')

    queryset = Payment.objects.all()

    if status:
        queryset = queryset.filter(status=status)

    queryset = queryset.order_by('-created_at')

    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page)

    payments = []
    for payment in page_obj:
        payments.append({
            'id': payment.id,
            'order_no': payment.order.order_no,
            'method': payment.method,
            'status': payment.status,
            'amount': str(payment.amount),
            'processed_by': payment.processed_by.username if payment.processed_by else None,
            'processed_at': payment.processed_at.isoformat() if payment.processed_at else None,
        })

    return JsonResponse({
        'success': True,
        'payments': payments,
        'pagination': {
            'page': page_obj.number,
            'per_page': per_page,
            'total_pages': paginator.num_pages,
            'total_items': paginator.count,
        }
    })


@csrf_exempt
@require_http_methods(["POST"])
@role_required(['ADMIN', 'CASHIER'])
def payment_mark_success(request, payment_id):
    """
    POST /api/payments/<id>/mark-success/
    Mark payment as successful and deduct inventory.
    """
    try:
        payment = Payment.objects.get(pk=payment_id)
        payment.mark_success(processed_by=request.user)

        return JsonResponse({
            'success': True,
            'message': 'Payment processed successfully'
        })

    except Payment.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Payment not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@role_required(['ADMIN', 'CASHIER'])
def payment_mark_failed(request, payment_id):
    """
    POST /api/payments/<id>/mark-failed/
    Mark payment as failed.
    """
    try:
        payment = Payment.objects.get(pk=payment_id)
        payment.mark_failed()

        return JsonResponse({
            'success': True,
            'message': 'Payment marked as failed'
        })

    except Payment.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Payment not found'
        }, status=404)
