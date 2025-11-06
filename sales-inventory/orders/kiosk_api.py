"""
API views for kiosk interface.

Public-facing APIs for customer self-service ordering.
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
import json
from .models import Order, OrderItem, Payment
from products.models import Product


@require_http_methods(["GET"])
def kiosk_products(request):
    """
    GET /api/kiosk/products/
    Get all available products for kiosk (non-archived, in-stock).
    """
    products = Product.objects.filter(
        is_archived=False,
        stock__gt=0
    ).order_by('name')

    product_list = []
    for product in products:
        product_list.append({
            'id': product.id,
            'name': product.name,
            'price': str(product.price),
            'stock': product.stock,
            'image_url': product.image_url,
            'is_low_stock': product.is_low_stock,
        })

    return JsonResponse({
        'success': True,
        'products': product_list
    })


@csrf_exempt
@require_http_methods(["POST"])
def kiosk_checkout(request):
    """
    POST /api/kiosk/checkout/
    Create a new order from kiosk.

    Body: {
        "items": [
            {"product_id": 1, "qty": 2},
            {"product_id": 2, "qty": 1}
        ],
        "payment_method": "ONLINE_DEMO"
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

        payment_method = data.get('payment_method', 'ONLINE_DEMO')
        if payment_method not in ['ONLINE_DEMO']:
            return JsonResponse({
                'success': False,
                'error': 'Only online payment is supported for kiosk orders'
            }, status=400)

        # Create order and items in a transaction
        with transaction.atomic():
            # Create order (no user for kiosk orders)
            order = Order.objects.create(created_by=None)

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
                        'error': f'Product {product_id} not found or unavailable'
                    }, status=404)

                # Check stock availability
                if product.stock < qty:
                    return JsonResponse({
                        'success': False,
                        'error': f'Insufficient stock for {product.name}. Available: {product.stock}'
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
                amount=total_amount,
                status='PENDING'  # Kiosk orders start as PENDING
            )

        return JsonResponse({
            'success': True,
            'message': 'Order created successfully',
            'order_no': order.order_no,
            'total_amount': str(order.total_amount),
            'qr_code_url': f'/kiosk/order/{order.order_no}/',  # URL for tracking
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


@require_http_methods(["GET"])
def kiosk_order_status(request, order_no):
    """
    GET /api/kiosk/orders/<order_no>/status/
    Get order status by order number (for QR code tracking).
    """
    try:
        order = Order.objects.get(order_no=order_no)

        # Get order items
        items = []
        for item in order.items.all():
            items.append({
                'product_name': item.product.name,
                'qty': item.qty,
                'subtotal': str(item.subtotal),
            })

        # Get payment status
        payment_status = None
        if hasattr(order, 'payment'):
            payment_status = order.payment.status

        return JsonResponse({
            'success': True,
            'order': {
                'order_no': order.order_no,
                'status': order.status,
                'total_amount': str(order.total_amount),
                'item_count': order.item_count,
                'created_at': order.created_at.isoformat(),
                'items': items,
                'payment_status': payment_status,
            }
        })

    except Order.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Order not found'
        }, status=404)
