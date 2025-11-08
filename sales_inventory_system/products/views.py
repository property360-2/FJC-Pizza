from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import F
from .models import Product
from system.models import AuditTrail
import json

def is_admin(user):
    return user.is_authenticated and user.is_admin

@login_required
@user_passes_test(is_admin)
def product_list(request):
    """List all products"""
    products = Product.objects.filter(is_archived=False)
    low_stock_products = products.filter(stock__lt=F('threshold'))

    context = {
        'products': products,
        'low_stock_count': low_stock_products.count(),
    }
    return render(request, 'products/list.html', context)

@login_required
@user_passes_test(is_admin)
def product_create(request):
    """Create a new product"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        price = request.POST.get('price')
        stock = request.POST.get('stock', 0)
        threshold = request.POST.get('threshold', 10)
        category = request.POST.get('category', '')
        image = request.FILES.get('image')

        product = Product.objects.create(
            name=name,
            description=description,
            price=price,
            stock=stock,
            threshold=threshold,
            category=category,
            image=image
        )

        # Create audit log
        AuditTrail.objects.create(
            user=request.user,
            action='CREATE',
            model_name='Product',
            record_id=product.id,
            description=f'Created product: {product.name}',
            data_snapshot={'name': name, 'price': str(price), 'stock': stock}
        )

        messages.success(request, f'Product "{product.name}" created successfully!')
        return redirect('products:list')

    return render(request, 'products/form.html', {'action': 'Create'})

@login_required
@user_passes_test(is_admin)
def product_edit(request, pk):
    """Edit an existing product"""
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        old_stock = product.stock

        product.name = request.POST.get('name')
        product.description = request.POST.get('description', '')
        product.price = request.POST.get('price')
        product.stock = request.POST.get('stock', 0)
        product.threshold = request.POST.get('threshold', 10)
        product.category = request.POST.get('category', '')

        if request.FILES.get('image'):
            product.image = request.FILES.get('image')

        product.save()

        # Create audit log
        description = f'Updated product: {product.name}'
        if old_stock != int(product.stock):
            description += f' (Stock: {old_stock} → {product.stock})'

        AuditTrail.objects.create(
            user=request.user,
            action='UPDATE',
            model_name='Product',
            record_id=product.id,
            description=description,
            data_snapshot={
                'name': product.name,
                'price': str(product.price),
                'stock': product.stock,
                'old_stock': old_stock
            }
        )

        messages.success(request, f'Product "{product.name}" updated successfully!')
        return redirect('products:list')

    context = {'product': product, 'action': 'Edit'}
    return render(request, 'products/form.html', context)

@login_required
@user_passes_test(is_admin)
def product_archive(request, pk):
    """Archive a product"""
    product = get_object_or_404(Product, pk=pk)
    product.is_archived = True
    product.save()

    # Create audit log
    AuditTrail.objects.create(
        user=request.user,
        action='ARCHIVE',
        model_name='Product',
        record_id=product.id,
        description=f'Archived product: {product.name}',
        data_snapshot={'name': product.name, 'price': str(product.price)}
    )

    messages.success(request, f'Product "{product.name}" archived successfully!')
    return redirect('products:list')
