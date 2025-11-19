from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import F, Q
from django.core.paginator import Paginator
from .models import Product, Ingredient, RecipeItem, RecipeIngredient
from system.models import AuditTrail
import json
from decimal import Decimal

def is_admin(user):
    return user.is_authenticated and user.is_admin

@login_required
@user_passes_test(is_admin)
def product_list(request):
    """List all products with search, filter, and pagination"""

    # Get query parameters
    search = request.GET.get('search', '').strip()
    category = request.GET.get('category', '').strip()
    stock_status = request.GET.get('stock_status', '').strip()
    page_number = request.GET.get('page', 1)

    # Base queryset
    products = Product.objects.filter(is_archived=False)

    # Apply search filter
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(category__icontains=search)
        )

    # Apply category filter
    if category:
        products = products.filter(category=category)

    # Apply stock status filter
    if stock_status == 'low':
        products = products.filter(stock__lt=F('threshold'), stock__gt=0)
    elif stock_status == 'out':
        products = products.filter(stock=0)
    elif stock_status == 'in_stock':
        products = products.filter(stock__gte=F('threshold'))

    # Get all categories for filter dropdown
    categories = Product.objects.filter(
        is_archived=False
    ).values_list('category', flat=True).distinct().order_by('category')
    categories = [c for c in categories if c]  # Remove empty categories

    # Calculate statistics
    low_stock_products = Product.objects.filter(is_archived=False, stock__lt=F('threshold'), stock__gt=0)
    total_count = products.count()

    # Pagination
    paginator = Paginator(products.order_by('category', 'name'), 12)  # 12 products per page
    page_obj = paginator.get_page(page_number)

    # Check if AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Return JSON for AJAX requests
        products_data = []
        for product in page_obj:
            products_data.append({
                'id': product.id,
                'name': product.name,
                'description': product.description or '',
                'price': float(product.price),
                'stock': product.stock,
                'threshold': product.threshold,
                'category': product.category or '',
                'is_low_stock': product.is_low_stock,
                'image_url': product.image.url if product.image else None,
            })

        return JsonResponse({
            'success': True,
            'products': products_data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_count': total_count,
                'has_previous': page_obj.has_previous(),
                'has_next': page_obj.has_next(),
                'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
                'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            }
        })

    # Regular page load
    context = {
        'page_obj': page_obj,
        'products': page_obj,  # For backward compatibility
        'categories': categories,
        'low_stock_count': low_stock_products.count(),
        'total_count': total_count,
        'search': search,
        'selected_category': category,
        'selected_stock_status': stock_status,
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


# ==================== Ingredient Management Views ====================

@login_required
@user_passes_test(is_admin)
def ingredient_list(request):
    """List all ingredients with search and filtering"""
    search = request.GET.get('search', '').strip()
    status = request.GET.get('status', '').strip()
    page_number = request.GET.get('page', 1)

    # Base queryset
    ingredients = Ingredient.objects.all()

    # Apply search filter
    if search:
        ingredients = ingredients.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )

    # Apply status filter
    if status == 'active':
        ingredients = ingredients.filter(is_active=True)
    elif status == 'inactive':
        ingredients = ingredients.filter(is_active=False)
    elif status == 'low':
        ingredients = ingredients.filter(current_stock__lt=F('min_stock'))

    # Order by name
    ingredients = ingredients.order_by('name')

    # Pagination
    paginator = Paginator(ingredients, 20)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'ingredients': page_obj,
        'search': search,
        'status': status,
    }
    return render(request, 'products/ingredient_list.html', context)


@login_required
@user_passes_test(is_admin)
def ingredient_create(request):
    """Create a new ingredient"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            unit = request.POST.get('unit', 'kg')
            cost_per_unit = Decimal(request.POST.get('cost_per_unit', '0.00'))
            current_stock = Decimal(request.POST.get('current_stock', '0.00'))
            min_stock = Decimal(request.POST.get('min_stock', '10.00'))
            variance_allowance = Decimal(request.POST.get('variance_allowance', '10.00'))

            if not name:
                raise ValueError('Ingredient name is required')

            ingredient = Ingredient.objects.create(
                name=name,
                description=description,
                unit=unit,
                cost_per_unit=cost_per_unit,
                current_stock=current_stock,
                min_stock=min_stock,
                variance_allowance=variance_allowance,
                is_active=True
            )

            messages.success(request, f'Ingredient "{ingredient.name}" created successfully!')
            return redirect('products:ingredient_list')

        except Exception as e:
            messages.error(request, f'Error creating ingredient: {str(e)}')

    context = {
        'action': 'Create',
        'units': ['kg', 'g', 'L', 'ml', 'pcs', 'box', 'dozen']
    }
    return render(request, 'products/ingredient_form.html', context)


@login_required
@user_passes_test(is_admin)
def ingredient_edit(request, pk):
    """Edit an existing ingredient"""
    ingredient = get_object_or_404(Ingredient, pk=pk)

    if request.method == 'POST':
        try:
            ingredient.name = request.POST.get('name')
            ingredient.description = request.POST.get('description', '')
            ingredient.unit = request.POST.get('unit', 'kg')
            ingredient.cost_per_unit = Decimal(request.POST.get('cost_per_unit', '0.00'))
            ingredient.current_stock = Decimal(request.POST.get('current_stock', '0.00'))
            ingredient.min_stock = Decimal(request.POST.get('min_stock', '10.00'))
            ingredient.variance_allowance = Decimal(request.POST.get('variance_allowance', '10.00'))
            ingredient.is_active = request.POST.get('is_active') == 'on'
            ingredient.save()

            messages.success(request, f'Ingredient "{ingredient.name}" updated successfully!')
            return redirect('products:ingredient_list')

        except Exception as e:
            messages.error(request, f'Error updating ingredient: {str(e)}')

    context = {
        'ingredient': ingredient,
        'action': 'Edit',
        'units': ['kg', 'g', 'L', 'ml', 'pcs', 'box', 'dozen']
    }
    return render(request, 'products/ingredient_form.html', context)


@login_required
@user_passes_test(is_admin)
def ingredient_delete(request, pk):
    """Delete an ingredient"""
    ingredient = get_object_or_404(Ingredient, pk=pk)
    name = ingredient.name
    ingredient.delete()

    messages.success(request, f'Ingredient "{name}" deleted successfully!')
    return redirect('products:ingredient_list')


# ==================== Recipe/BOM Management Views ====================

@login_required
@user_passes_test(is_admin)
def recipe_edit(request, pk):
    """Edit product recipe/BOM"""
    from django.db import transaction

    product = get_object_or_404(Product, pk=pk)

    # Get or create recipe item
    recipe_item, created = RecipeItem.objects.get_or_create(product=product)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Delete existing ingredients
                recipe_item.ingredients.all().delete()

                # Add new ingredients from form
                ingredients_data = request.POST.getlist('ingredient_id')
                quantities_data = request.POST.getlist('quantity')

                for ing_id, qty in zip(ingredients_data, quantities_data):
                    if ing_id and qty:
                        try:
                            ingredient = Ingredient.objects.get(id=ing_id)
                            RecipeIngredient.objects.create(
                                recipe=recipe_item,
                                ingredient=ingredient,
                                quantity=Decimal(qty)
                            )
                        except (Ingredient.DoesNotExist, ValueError):
                            pass

                messages.success(request, f'Recipe for "{product.name}" updated successfully!')
                return redirect('products:edit', pk=product.id)

        except Exception as e:
            messages.error(request, f'Error updating recipe: {str(e)}')

    # Get all active ingredients
    all_ingredients = Ingredient.objects.filter(is_active=True).order_by('name')

    # Get current recipe ingredients
    recipe_ingredients = recipe_item.ingredients.all()

    context = {
        'product': product,
        'recipe_item': recipe_item,
        'recipe_ingredients': recipe_ingredients,
        'all_ingredients': all_ingredients,
    }
    return render(request, 'products/recipe_form.html', context)
