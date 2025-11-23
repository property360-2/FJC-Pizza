from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.db import transaction
from django.views.decorators.http import require_http_methods
import json
from decimal import Decimal
from sales_inventory_system.products.models import Product
from sales_inventory_system.products.inventory_service import BOMService
from .models import Order, OrderItem, Payment


def get_cart(request):
    """Get cart from session or initialize empty cart"""
    cart = request.session.get('cart', {})
    return cart


def save_cart(request, cart):
    """Save cart to session"""
    request.session['cart'] = cart
    request.session.modified = True


def calculate_cart_total(cart, products_dict):
    """Calculate total price of items in cart"""
    total = Decimal('0.00')
    for product_id, quantity in cart.items():
        product = products_dict.get(int(product_id))
        if product:
            total += product.price * quantity
    return total


def kiosk_home(request):
    """Display kiosk home page with available products"""
    products = Product.objects.filter(is_archived=False, stock__gt=0).order_by('category', 'name')

    # Check ingredient availability for each product
    unavailable_products = set()
    for product in products:
        availability = BOMService.check_ingredient_availability(product.id)
        if not availability['available']:
            unavailable_products.add(product.id)

    # Add availability flag to products
    for product in products:
        product.is_available_for_order = product.id not in unavailable_products

    cart = get_cart(request)
    cart_count = sum(cart.values())

    context = {
        'products': products,
        'cart_count': cart_count,
    }
    return render(request, 'kiosk/home.html', context)


def cart_view(request):
    """Display shopping cart with items and totals"""
    cart = get_cart(request)

    # Get all products in cart
    product_ids = [int(pid) for pid in cart.keys()]
    products = Product.objects.filter(id__in=product_ids)
    products_dict = {p.id: p for p in products}

    # Build cart items with product details
    cart_items = []
    for product_id, quantity in cart.items():
        product = products_dict.get(int(product_id))
        if product:
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': product.price * quantity
            })

    total = calculate_cart_total(cart, products_dict)

    context = {
        'cart_items': cart_items,
        'total': total,
        'cart_count': sum(cart.values()),
    }
    return render(request, 'kiosk/cart.html', context)


def checkout(request):
    """Handle checkout process and order creation"""
    cart = get_cart(request)

    if not cart:
        messages.warning(request, 'Your cart is empty!')
        return redirect('kiosk:home')

    # Get all products in cart
    product_ids = [int(pid) for pid in cart.keys()]
    products = Product.objects.filter(id__in=product_ids)
    products_dict = {p.id: p for p in products}

    # Build cart items for display
    cart_items = []
    for product_id, quantity in cart.items():
        product = products_dict.get(int(product_id))
        if product:
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': product.price * quantity
            })

    total = calculate_cart_total(cart, products_dict)

    if request.method == 'POST':
        customer_name = request.POST.get('customer_name', 'Guest')
        table_number = request.POST.get('table_number', '')
        payment_method = request.POST.get('payment_method', 'CASH')
        notes = request.POST.get('notes', '')

        try:
            # First, check ingredient availability before creating order
            order_items_data = [
                {'product_id': int(pid), 'quantity': qty}
                for pid, qty in cart.items()
            ]

            availability = BOMService.check_order_availability(order_items_data)
            if not availability['available']:
                # Return error with shortage details
                error_msg = 'Unable to complete order. Ingredient shortages:\n\n'
                for shortage in availability['shortages']:
                    error_msg += f"• {shortage['product']} ({shortage['ingredient']}): "
                    error_msg += f"Need {shortage['needed']:.2f}, Have {shortage['available']:.2f} {shortage['unit']}\n"

                raise ValueError(error_msg.strip())

            with transaction.atomic():
                # Create order
                order = Order.objects.create(
                    customer_name=customer_name,
                    table_number=table_number,
                    notes=notes,
                    status='PENDING'
                )

                # Create order items
                for product_id, quantity in cart.items():
                    product = products_dict.get(int(product_id))
                    if product:
                        # Check stock availability
                        if product.stock < quantity:
                            raise ValueError(f'Insufficient stock for {product.name}')

                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            quantity=quantity
                        )

                # Calculate total
                order.calculate_total()

                # Create payment record
                payment = Payment.objects.create(
                    order=order,
                    method=payment_method,
                    amount=order.total_amount,
                    status='PENDING' if payment_method == 'CASH' else 'SUCCESS'
                )

                # If online payment demo, auto-approve and deduct stock
                if payment_method == 'ONLINE':
                    payment.status = 'SUCCESS'
                    payment.save()

                    # Update order status
                    order.status = 'IN_PROGRESS'
                    order.save()

                    # Deduct stock
                    for item in order.items.all():
                        product = item.product
                        product.stock -= item.quantity
                        product.save()

                # Clear cart
                request.session['cart'] = {}
                request.session.modified = True

                # Check if AJAX request
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': f'Order {order.order_number} placed successfully!',
                        'order_number': order.order_number,
                        'redirect_url': f'/kiosk/order/{order.order_number}/'
                    })

                messages.success(request, f'Order {order.order_number} placed successfully!')
                return redirect('kiosk:order_status', order_number=order.order_number)

        except ValueError as e:
            # Check if AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': str(e)
                })
            messages.error(request, str(e))
        except Exception as e:
            # Check if AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'An error occurred while processing your order.'
                })
            messages.error(request, 'An error occurred while processing your order.')

    context = {
        'cart_items': cart_items,
        'total': total,
        'cart_count': sum(cart.values()),
    }
    return render(request, 'kiosk/checkout.html', context)


def order_status(request, order_number):
    """Display order status for tracking"""
    try:
        order = Order.objects.get(order_number=order_number)

        context = {
            'order': order,
            'items': order.items.all(),
        }
        return render(request, 'kiosk/order_status.html', context)
    except Order.DoesNotExist:
        messages.error(request, 'Order not found!')
        return redirect('kiosk:home')


def add_to_cart(request, product_id):
    """Add product to cart"""
    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, id=product_id, is_archived=False)

            if product.stock <= 0:
                return JsonResponse({
                    'success': False,
                    'message': 'Product is out of stock'
                })

            cart = get_cart(request)

            # Get requested quantity
            quantity = int(request.POST.get('quantity', 1))

            # Check if adding to existing quantity
            current_quantity = cart.get(str(product_id), 0)
            new_quantity = current_quantity + quantity

            # Check stock availability
            if new_quantity > product.stock:
                return JsonResponse({
                    'success': False,
                    'message': f'Only {product.stock} items available in stock'
                })

            # Check ingredient availability
            availability = BOMService.check_ingredient_availability(product_id, new_quantity)
            warning_message = None

            if not availability['available'] and availability['has_recipe']:
                # Build warning message about ingredient shortages
                shortages = availability['shortages']
                warning_message = f"⚠️ Limited ingredients: "
                shortage_list = [f"{s['ingredient']} ({s['available']:.0f}/{s['needed']:.0f} {s['unit']})" for s in shortages[:2]]
                warning_message += ", ".join(shortage_list)
                if len(shortages) > 2:
                    warning_message += f" +{len(shortages) - 2} more"

            cart[str(product_id)] = new_quantity
            save_cart(request, cart)

            cart_count = sum(cart.values())

            response = {
                'success': True,
                'message': f'{product.name} added to cart',
                'cart_count': cart_count
            }

            if warning_message:
                response['warning'] = warning_message

            return JsonResponse(response)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Error adding product to cart'
            })

    return JsonResponse({'success': False, 'message': 'Invalid request'})


def remove_from_cart(request, product_id):
    """Remove product from cart"""
    if request.method == 'POST':
        try:
            cart = get_cart(request)

            if str(product_id) in cart:
                del cart[str(product_id)]
                save_cart(request, cart)

                cart_count = sum(cart.values())

                return JsonResponse({
                    'success': True,
                    'message': 'Product removed from cart',
                    'cart_count': cart_count
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Product not in cart'
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Error removing product from cart'
            })

    return JsonResponse({'success': False, 'message': 'Invalid request'})


def update_cart_quantity(request, product_id):
    """Update quantity of product in cart"""
    if request.method == 'POST':
        try:
            product = get_object_or_404(Product, id=product_id)
            quantity = int(request.POST.get('quantity', 1))

            if quantity < 1:
                return JsonResponse({
                    'success': False,
                    'message': 'Quantity must be at least 1'
                })

            if quantity > product.stock:
                return JsonResponse({
                    'success': False,
                    'message': f'Only {product.stock} items available'
                })

            cart = get_cart(request)
            cart[str(product_id)] = quantity
            save_cart(request, cart)

            # Recalculate totals
            products_dict = {product.id: product}
            total = calculate_cart_total(cart, products_dict)

            return JsonResponse({
                'success': True,
                'message': 'Cart updated',
                'cart_count': sum(cart.values()),
                'subtotal': float(product.price * quantity),
                'total': float(total)
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Error updating cart'
            })

    return JsonResponse({'success': False, 'message': 'Invalid request'})


def get_cart_json(request):
    """Return cart data as JSON for modal"""
    cart = get_cart(request)
    return JsonResponse(cart)


def get_cart_details(request):
    """Get cart items with product details for modal display"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_ids = [int(pid) for pid in data.get('product_ids', [])]

            products = Product.objects.filter(id__in=product_ids)
            products_dict = {}

            for product in products:
                products_dict[str(product.id)] = {
                    'id': product.id,
                    'name': product.name,
                    'price': float(product.price),
                    'image': product.image.url if product.image else None,
                    'stock': product.stock
                }

            return JsonResponse({
                'success': True,
                'products': products_dict
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Error fetching cart details'
            })

    return JsonResponse({'success': False, 'message': 'Invalid request'})


def search_order(request):
    """Search for order by order number"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_number = data.get('order_number', '').strip()

            if not order_number:
                return JsonResponse({
                    'success': False,
                    'message': 'Please provide an order number'
                })

            try:
                order = Order.objects.get(order_number=order_number)
                items = []

                for order_item in order.items.all():
                    items.append({
                        'quantity': order_item.quantity,
                        'product_name': order_item.product_name,
                        'product_price': float(order_item.product_price),
                        'subtotal': float(order_item.quantity * order_item.product_price)
                    })

                return JsonResponse({
                    'success': True,
                    'order': {
                        'order_number': order.order_number,
                        'customer_name': order.customer_name,
                        'table_number': order.table_number,
                        'status': order.status,
                        'total_amount': float(order.total_amount),
                        'items': items
                    }
                })
            except Order.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Order not found'
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Error searching order'
            })

    return JsonResponse({'success': False, 'message': 'Invalid request'})
