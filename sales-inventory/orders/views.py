"""
Views for order management and POS interface.
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from .models import Order


@role_required(['ADMIN', 'CASHIER'])
def pos_view(request):
    """
    GET /pos/
    Point of Sale interface for cashiers.
    """
    return render(request, 'orders/pos.html')


@role_required(['ADMIN', 'CASHIER'])
def order_queue_view(request):
    """
    GET /orders/queue/
    View all orders in queue (pending and in-progress).
    """
    pending_orders = Order.objects.filter(status='PENDING').order_by('created_at')
    in_progress_orders = Order.objects.filter(status='IN_PROGRESS').order_by('created_at')

    context = {
        'pending_orders': pending_orders,
        'in_progress_orders': in_progress_orders,
    }

    return render(request, 'orders/order_queue.html', context)


@role_required(['ADMIN', 'CASHIER'])
def order_detail_view(request, order_id):
    """
    GET /orders/<id>/
    View order details.
    """
    order = get_object_or_404(Order, pk=order_id)

    context = {
        'order': order,
    }

    return render(request, 'orders/order_detail.html', context)
