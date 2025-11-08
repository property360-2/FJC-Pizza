from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Order, OrderItem, Payment
from products.models import Product
from system.models import AuditTrail


@login_required
def order_list(request):
    """Display list of all orders with search, filter, and pagination"""

    # Get query parameters
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '').strip()
    page_number = request.GET.get('page', 1)

    # Base queryset
    orders = Order.objects.all().select_related('payment').prefetch_related('items__product')

    # Apply search filter
    if search:
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(customer_name__icontains=search) |
            Q(table_number__icontains=search)
        )

    # Apply status filter
    if status_filter:
        orders = orders.filter(status=status_filter)

    # Order by most recent
    orders = orders.order_by('-created_at')

    # Pagination
    paginator = Paginator(orders, 20)  # 20 orders per page
    page_obj = paginator.get_page(page_number)

    # Check if AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Return JSON for AJAX requests
        orders_data = []
        for order in page_obj:
            # Get item summary
            items_list = [f"{item.quantity}x {item.product.name}" for item in order.items.all()]
            items_summary = ", ".join(items_list[:2])  # First 2 items
            if len(items_list) > 2:
                items_summary += f", +{len(items_list) - 2} more"

            orders_data.append({
                'id': order.id,
                'order_number': order.order_number,
                'customer_name': order.customer_name,
                'table_number': order.table_number or '-',
                'items_summary': items_summary,
                'total_amount': float(order.total_amount),
                'status': order.status,
                'status_display': order.get_status_display(),
                'created_at': order.created_at.strftime('%b %d, %Y %I:%M %p'),
                'payment_status': order.payment.status if hasattr(order, 'payment') else 'PENDING',
            })

        return JsonResponse({
            'success': True,
            'orders': orders_data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_previous': page_obj.has_previous(),
                'has_next': page_obj.has_next(),
                'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
                'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            }
        })

    context = {
        'page_obj': page_obj,
        'orders': page_obj,  # For backward compatibility
        'search': search,
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

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': f'Payment processed for order {order.order_number}'
                    })
                else:
                    messages.success(request, f'Payment processed for order {order.order_number}')
                    return redirect('cashier_pos')

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


@login_required
def pos_create_order(request):
    """POS interface for cashiers to create orders directly"""
    products = Product.objects.filter(is_archived=False).order_by('category', 'name')

    if request.method == 'POST':
        try:
            customer_name = request.POST.get('customer_name', 'Walk-in Customer')
            table_number = request.POST.get('table_number', '')
            notes = request.POST.get('notes', '')
            payment_method = request.POST.get('payment_method', 'CASH')

            # Get cart items from POST data
            cart_items = []
            for key in request.POST:
                if key.startswith('quantity_'):
                    product_id = int(key.replace('quantity_', ''))
                    quantity = int(request.POST.get(key, 0))
                    if quantity > 0:
                        cart_items.append({'product_id': product_id, 'quantity': quantity})

            if not cart_items:
                messages.error(request, 'Please add at least one item to the order.')
                return redirect('orders:pos_create_order')

            with transaction.atomic():
                # Create order
                order = Order.objects.create(
                    customer_name=customer_name,
                    table_number=table_number,
                    notes=notes,
                    status='IN_PROGRESS',  # POS orders go directly to IN_PROGRESS
                    processed_by=request.user
                )

                total_amount = 0

                # Create order items and deduct stock
                for item_data in cart_items:
                    product = Product.objects.get(id=item_data['product_id'])
                    quantity = item_data['quantity']

                    # Check stock
                    if product.stock < quantity:
                        raise ValueError(f'Insufficient stock for {product.name}. Available: {product.stock}')

                    # Create order item
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity
                    )

                    # Deduct stock immediately
                    product.stock -= quantity
                    product.save()

                    total_amount += product.price * quantity

                    # Create audit log for stock deduction
                    AuditTrail.objects.create(
                        user=request.user,
                        action='UPDATE',
                        model_name='Product',
                        record_id=product.id,
                        description=f'Stock deducted for POS order {order.order_number}: {product.name} (-{quantity})',
                        data_snapshot={
                            'product': product.name,
                            'order_number': order.order_number,
                            'quantity_deducted': quantity,
                            'remaining_stock': product.stock
                        }
                    )

                # Update order total
                order.calculate_total()

                # Create payment record (already successful)
                Payment.objects.create(
                    order=order,
                    method=payment_method,
                    amount=order.total_amount,
                    status='SUCCESS',
                    processed_by=request.user
                )

                # Create audit log for order creation
                AuditTrail.objects.create(
                    user=request.user,
                    action='CREATE',
                    model_name='Order',
                    record_id=order.id,
                    description=f'POS order created: {order.order_number}',
                    data_snapshot={
                        'order_number': order.order_number,
                        'customer_name': customer_name,
                        'total_amount': str(order.total_amount),
                        'payment_method': payment_method
                    }
                )

                messages.success(request, f'Order {order.order_number} created successfully!')
                return redirect('cashier_pos')

        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error creating order: {str(e)}')

    # Group products by category for display
    from itertools import groupby
    products_by_category = {}
    for category, items in groupby(products, key=lambda p: p.category or 'Other'):
        products_by_category[category] = list(items)

    context = {
        'products': products,
        'products_by_category': products_by_category,
    }
    return render(request, 'orders/pos_create.html', context)
