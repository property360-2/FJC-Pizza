"""
API views for products.

Provides RESTful endpoints for product management.
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, F
import json
from .models import Product
from accounts.decorators import role_required


@require_http_methods(["GET"])
def product_list(request):
    """
    GET /api/products/
    List all products with optional filtering and pagination.

    Query params:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20)
    - search: Search in product name
    - archived: Include archived products (default: false)
    - low_stock: Filter low stock items only
    """
    # Get query parameters
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 20))
    search = request.GET.get('search', '')
    show_archived = request.GET.get('archived', 'false').lower() == 'true'
    low_stock_only = request.GET.get('low_stock', 'false').lower() == 'true'

    # Base queryset
    queryset = Product.objects.all()

    # Apply filters
    if not show_archived:
        queryset = queryset.filter(is_archived=False)

    if search:
        queryset = queryset.filter(name__icontains=search)

    if low_stock_only:
        queryset = queryset.filter(stock__lt=F('threshold'))

    # Order by name
    queryset = queryset.order_by('name')

    # Paginate
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page)

    # Serialize products
    products = []
    for product in page_obj:
        products.append({
            'id': product.id,
            'name': product.name,
            'price': str(product.price),
            'stock': product.stock,
            'threshold': product.threshold,
            'image_url': product.image_url,
            'is_archived': product.is_archived,
            'is_low_stock': product.is_low_stock,
            'is_out_of_stock': product.is_out_of_stock,
            'created_at': product.created_at.isoformat(),
            'updated_at': product.updated_at.isoformat(),
        })

    return JsonResponse({
        'success': True,
        'products': products,
        'pagination': {
            'page': page_obj.number,
            'per_page': per_page,
            'total_pages': paginator.num_pages,
            'total_items': paginator.count,
            'has_next': page_obj.has_next(),
            'has_prev': page_obj.has_previous(),
        }
    })


@require_http_methods(["GET"])
def product_detail(request, product_id):
    """
    GET /api/products/<id>/
    Get a single product by ID.
    """
    try:
        product = Product.objects.get(pk=product_id)

        return JsonResponse({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'price': str(product.price),
                'stock': product.stock,
                'threshold': product.threshold,
                'image_url': product.image_url,
                'is_archived': product.is_archived,
                'is_low_stock': product.is_low_stock,
                'is_out_of_stock': product.is_out_of_stock,
                'created_at': product.created_at.isoformat(),
                'updated_at': product.updated_at.isoformat(),
            }
        })
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Product not found'
        }, status=404)


@csrf_exempt
@require_http_methods(["POST"])
@role_required(['ADMIN'])
def product_create(request):
    """
    POST /api/products/create/
    Create a new product.

    Required fields: name, price
    Optional fields: stock, threshold, image_url
    """
    try:
        data = json.loads(request.body)

        # Validate required fields
        if not data.get('name'):
            return JsonResponse({
                'success': False,
                'error': 'Product name is required'
            }, status=400)

        if not data.get('price'):
            return JsonResponse({
                'success': False,
                'error': 'Product price is required'
            }, status=400)

        # Create product
        product = Product.objects.create(
            name=data['name'],
            price=data['price'],
            stock=data.get('stock', 0),
            threshold=data.get('threshold', 10),
            image_url=data.get('image_url', ''),
        )

        return JsonResponse({
            'success': True,
            'message': 'Product created successfully',
            'product': {
                'id': product.id,
                'name': product.name,
                'price': str(product.price),
                'stock': product.stock,
                'threshold': product.threshold,
                'image_url': product.image_url,
            }
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


@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
@role_required(['ADMIN'])
def product_update(request, product_id):
    """
    PUT/PATCH /api/products/<id>/update/
    Update an existing product.
    """
    try:
        product = Product.objects.get(pk=product_id)
        data = json.loads(request.body)

        # Update fields if provided
        if 'name' in data:
            product.name = data['name']
        if 'price' in data:
            product.price = data['price']
        if 'stock' in data:
            product.stock = data['stock']
        if 'threshold' in data:
            product.threshold = data['threshold']
        if 'image_url' in data:
            product.image_url = data['image_url']

        product.save()

        return JsonResponse({
            'success': True,
            'message': 'Product updated successfully',
            'product': {
                'id': product.id,
                'name': product.name,
                'price': str(product.price),
                'stock': product.stock,
                'threshold': product.threshold,
                'image_url': product.image_url,
            }
        })

    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Product not found'
        }, status=404)
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


@csrf_exempt
@require_http_methods(["POST"])
@role_required(['ADMIN'])
def product_archive(request, product_id):
    """
    POST /api/products/<id>/archive/
    Archive (soft delete) a product.
    """
    try:
        product = Product.objects.get(pk=product_id)
        product.archive()

        return JsonResponse({
            'success': True,
            'message': 'Product archived successfully'
        })

    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Product not found'
        }, status=404)


@csrf_exempt
@require_http_methods(["POST"])
@role_required(['ADMIN'])
def product_unarchive(request, product_id):
    """
    POST /api/products/<id>/unarchive/
    Unarchive a product.
    """
    try:
        product = Product.objects.get(pk=product_id)
        product.unarchive()

        return JsonResponse({
            'success': True,
            'message': 'Product unarchived successfully'
        })

    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Product not found'
        }, status=404)


@csrf_exempt
@require_http_methods(["POST"])
@role_required(['ADMIN'])
def product_adjust_stock(request, product_id):
    """
    POST /api/products/<id>/adjust-stock/
    Adjust product stock.

    Body: {
        "delta": -5,  // negative to decrease, positive to increase
        "reason": "Damaged items"  // optional
    }
    """
    try:
        product = Product.objects.get(pk=product_id)
        data = json.loads(request.body)

        delta = data.get('delta')
        if delta is None:
            return JsonResponse({
                'success': False,
                'error': 'Delta is required'
            }, status=400)

        reason = data.get('reason')
        result = product.adjust_stock(delta, reason)

        if not result['success']:
            return JsonResponse({
                'success': False,
                'error': result['error']
            }, status=400)

        return JsonResponse({
            'success': True,
            'message': 'Stock adjusted successfully',
            'stock': result['new_stock']
        })

    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Product not found'
        }, status=404)
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
