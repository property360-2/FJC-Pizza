from django.shortcuts import render
from django.http import HttpResponse, JsonResponse


def kiosk_home(request):
    """Display kiosk home page."""
    return render(request, 'orders/kiosk/home.html', {
        'message': 'Kiosk home page - stub'
    })


def cart_view(request):
    """Display shopping cart."""
    return render(request, 'orders/kiosk/cart.html', {
        'cart': [],
        'total': 0,
        'message': 'Shopping cart view - stub'
    })


def checkout(request):
    """Handle checkout process."""
    if request.method == 'POST':
        return JsonResponse({
            'success': True,
            'message': 'Checkout processed - stub',
            'order_number': 'ORD-STUB-001'
        })
    return render(request, 'orders/kiosk/checkout.html', {
        'message': 'Checkout page - stub'
    })


def order_status(request, order_number):
    """Display order status for a given order number."""
    return render(request, 'orders/kiosk/order_status.html', {
        'order_number': order_number,
        'status': 'pending',
        'message': f'Order status for {order_number} - stub'
    })


def add_to_cart(request, product_id):
    """Add product to cart."""
    if request.method == 'POST':
        return JsonResponse({
            'success': True,
            'message': f'Product {product_id} added to cart - stub',
            'product_id': product_id
        })
    return HttpResponse(f'Add product {product_id} to cart - stub')


def remove_from_cart(request, product_id):
    """Remove product from cart."""
    if request.method == 'POST':
        return JsonResponse({
            'success': True,
            'message': f'Product {product_id} removed from cart - stub',
            'product_id': product_id
        })
    return HttpResponse(f'Remove product {product_id} from cart - stub')
