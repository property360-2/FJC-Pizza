from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse


@login_required
def order_list(request):
    """Display list of all orders."""
    return render(request, 'orders/order_list.html', {
        'orders': [],
        'message': 'Order list view - stub'
    })


@login_required
def order_detail(request, pk):
    """Display details of a specific order."""
    return render(request, 'orders/order_detail.html', {
        'order_id': pk,
        'message': f'Order detail view for order {pk} - stub'
    })


@login_required
def update_order_status(request, pk):
    """Update the status of an order."""
    if request.method == 'POST':
        return JsonResponse({
            'success': True,
            'message': f'Order {pk} status updated - stub',
            'order_id': pk
        })
    return render(request, 'orders/update_status.html', {
        'order_id': pk,
        'message': f'Update order {pk} status - stub'
    })


@login_required
def process_payment(request, pk):
    """Process payment for an order."""
    if request.method == 'POST':
        return JsonResponse({
            'success': True,
            'message': f'Payment processed for order {pk} - stub',
            'order_id': pk
        })
    return render(request, 'orders/payment.html', {
        'order_id': pk,
        'message': f'Process payment for order {pk} - stub'
    })
