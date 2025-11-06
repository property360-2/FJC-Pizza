"""
Views for product management.

Admin-only views for CRUD operations on products.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Product
from accounts.decorators import role_required


@role_required(['ADMIN'])
def product_list_view(request):
    """
    GET /admin/products/
    List all products with search and pagination.
    """
    # Get query parameters
    search = request.GET.get('search', '')
    show_archived = request.GET.get('archived', '') == 'true'
    page_number = request.GET.get('page', 1)

    # Base queryset
    queryset = Product.objects.all()

    # Apply filters
    if not show_archived:
        queryset = queryset.filter(is_archived=False)

    if search:
        queryset = queryset.filter(Q(name__icontains=search))

    # Order by name
    queryset = queryset.order_by('name')

    # Paginate
    paginator = Paginator(queryset, 20)
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'search': search,
        'show_archived': show_archived,
        'total_products': queryset.count(),
    }

    return render(request, 'products/product_list.html', context)


@role_required(['ADMIN'])
def product_create_view(request):
    """
    GET/POST /admin/products/create/
    Create a new product.
    """
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name', '').strip()
        price = request.POST.get('price', '')
        stock = request.POST.get('stock', 0)
        threshold = request.POST.get('threshold', 10)
        image_url = request.POST.get('image_url', '').strip()

        # Validate
        if not name:
            messages.error(request, 'Product name is required')
            return redirect('product_create')

        if not price:
            messages.error(request, 'Product price is required')
            return redirect('product_create')

        try:
            # Create product
            product = Product.objects.create(
                name=name,
                price=price,
                stock=stock,
                threshold=threshold,
                image_url=image_url,
            )

            messages.success(request, f'Product "{product.name}" created successfully')
            return redirect('product_list')

        except Exception as e:
            messages.error(request, f'Error creating product: {str(e)}')
            return redirect('product_create')

    return render(request, 'products/product_form.html', {'action': 'Create'})


@role_required(['ADMIN'])
def product_edit_view(request, product_id):
    """
    GET/POST /admin/products/<id>/edit/
    Edit an existing product.
    """
    product = get_object_or_404(Product, pk=product_id)

    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name', '').strip()
        price = request.POST.get('price', '')
        stock = request.POST.get('stock', 0)
        threshold = request.POST.get('threshold', 10)
        image_url = request.POST.get('image_url', '').strip()

        # Validate
        if not name:
            messages.error(request, 'Product name is required')
            return redirect('product_edit', product_id=product_id)

        if not price:
            messages.error(request, 'Product price is required')
            return redirect('product_edit', product_id=product_id)

        try:
            # Update product
            product.name = name
            product.price = price
            product.stock = stock
            product.threshold = threshold
            product.image_url = image_url
            product.save()

            messages.success(request, f'Product "{product.name}" updated successfully')
            return redirect('product_list')

        except Exception as e:
            messages.error(request, f'Error updating product: {str(e)}')
            return redirect('product_edit', product_id=product_id)

    context = {
        'product': product,
        'action': 'Edit',
    }

    return render(request, 'products/product_form.html', context)


@role_required(['ADMIN'])
def product_archive_view(request, product_id):
    """
    POST /admin/products/<id>/archive/
    Archive (soft delete) a product.
    """
    product = get_object_or_404(Product, pk=product_id)

    if request.method == 'POST':
        product.archive()
        messages.success(request, f'Product "{product.name}" archived successfully')

    return redirect('product_list')


@role_required(['ADMIN'])
def product_unarchive_view(request, product_id):
    """
    POST /admin/products/<id>/unarchive/
    Unarchive a product.
    """
    product = get_object_or_404(Product, pk=product_id)

    if request.method == 'POST':
        product.unarchive()
        messages.success(request, f'Product "{product.name}" restored successfully')

    return redirect('product_list')


@role_required(['ADMIN'])
def product_detail_view(request, product_id):
    """
    GET /admin/products/<id>/
    View product details.
    """
    product = get_object_or_404(Product, pk=product_id)

    context = {
        'product': product,
    }

    return render(request, 'products/product_detail.html', context)
