from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from .models import Order, OrderItem, Payment
from system.models import AuditTrail


@login_required
def order_list(request):
    """Display list of all orders"""
    # Filter by status if provided
    status_filter = request.GET.get('status', '')

    orders = Order.objects.all().select_related('payment').order_by('-created_at')

    if status_filter:
        orders = orders.filter(status=status_filter)

    context = {
        'orders': orders,
        'status_filter': status_filter,
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'orders/list.html', context)


@login_required
def order_detail(request, pk):
    """Display details of a specific order"""
    order = get_object_or_404(Order, pk=pk)

    context = {
        'order': order,
        'items': order.items.all(),
    }
    return render(request, 'orders/detail.html', context)


@login_required
def update_order_status(request, pk):
    """Update the status of an order"""
    if request.method == 'POST':
        try:
            order = get_object_or_404(Order, pk=pk)
            new_status = request.POST.get('status')

            if new_status not in dict(Order.STATUS_CHOICES):
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid status'
                })

            old_status = order.status
            order.status = new_status
            order.processed_by = request.user
            order.save()

            # Create audit log
            AuditTrail.objects.create(
                user=request.user,
                action='UPDATE',
                model_name='Order',
                record_id=order.id,
                description=f'Updated order {order.order_number} status from {old_status} to {new_status}',
                data_snapshot={
                    'order_number': order.order_number,
                    'old_status': old_status,
                    'new_status': new_status
                }
            )

            messages.success(request, f'Order {order.order_number} status updated to {order.get_status_display()}')

            return JsonResponse({
                'success': True,
                'message': f'Order status updated to {order.get_status_display()}',
                'status': new_status
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })

    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
def process_payment(request, pk):
    """Process payment for an order (cashier confirms cash payment)"""
    if request.method == 'POST':
        try:
            order = get_object_or_404(Order, pk=pk)

            # Check if payment already exists
            try:
                payment = order.payment
            except Payment.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Payment record not found for this order'
                })

            # Only process if payment is pending
            if payment.status != 'PENDING':
                return JsonResponse({
                    'success': False,
                    'message': f'Payment is already {payment.get_status_display()}'
                })

            with transaction.atomic():
                # Update payment status
                payment.status = 'SUCCESS'
                payment.processed_by = request.user
                payment.save()

                # Update order status
                order.status = 'IN_PROGRESS'
                order.processed_by = request.user
                order.save()

                # Deduct stock for each item
                for item in order.items.all():
                    product = item.product
                    if product.stock < item.quantity:
                        raise ValueError(f'Insufficient stock for {product.name}')

                    product.stock -= item.quantity
                    product.save()

                    # Create audit log for stock deduction
                    AuditTrail.objects.create(
                        user=request.user,
                        action='UPDATE',
                        model_name='Product',
                        record_id=product.id,
                        description=f'Stock deducted for order {order.order_number}: {product.name} (-{item.quantity})',
                        data_snapshot={
                            'product': product.name,
                            'order_number': order.order_number,
                            'quantity_deducted': item.quantity,
                            'remaining_stock': product.stock
                        }
                    )

                # Create audit log for payment
                AuditTrail.objects.create(
                    user=request.user,
                    action='UPDATE',
                    model_name='Payment',
                    record_id=payment.id,
                    description=f'Payment confirmed for order {order.order_number} (₱{payment.amount})',
                    data_snapshot={
                        'order_number': order.order_number,
                        'amount': str(payment.amount),
                        'method': payment.method
                    }
                )

                messages.success(request, f'Payment processed for order {order.order_number}')

                return JsonResponse({
                    'success': True,
                    'message': 'Payment processed successfully'
                })

        except ValueError as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error processing payment: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Invalid request method'})
