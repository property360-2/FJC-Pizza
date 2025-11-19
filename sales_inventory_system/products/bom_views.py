"""
Views for Bill of Materials reports and management
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Sum, F
from django.utils import timezone
from datetime import timedelta
from .models import (
    Ingredient, RecipeItem, StockTransaction, WasteLog,
    PhysicalCount, VarianceRecord
)
from .inventory_service import BOMService
import json


@login_required
def bom_dashboard(request):
    """
    Main BOM dashboard showing inventory status and key metrics.
    """
    # Low stock ingredients
    low_stock = BOMService.get_low_stock_ingredients()[:5]

    # Recent waste
    recent_waste = WasteLog.objects.select_related('ingredient').order_by('-waste_date')[:5]

    # Stock transactions this week
    week_ago = timezone.now() - timedelta(days=7)
    recent_transactions = StockTransaction.objects.filter(
        created_at__gte=week_ago
    ).select_related('ingredient').order_by('-created_at')[:10]

    # Variance overview
    today = timezone.now()
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    variance_records = VarianceRecord.objects.filter(
        period_end__gte=month_start
    ).select_related('ingredient').order_by('within_tolerance')[:5]

    # Calculate total waste cost this month
    month_waste = WasteLog.objects.filter(
        waste_date__gte=month_start
    ).aggregate(total_cost=Sum(F('quantity') * F('ingredient__cost_per_unit')))

    context = {
        'low_stock_count': Ingredient.objects.filter(
            Q(current_stock__lt=F('min_stock')) & Q(is_active=True)
        ).count(),
        'low_stock_ingredients': low_stock,
        'recent_waste': recent_waste,
        'recent_transactions': recent_transactions,
        'variance_issues': variance_records,
        'total_ingredients': Ingredient.objects.filter(is_active=True).count(),
        'month_waste_cost': month_waste['total_cost'] or 0,
    }

    return render(request, 'products/bom_dashboard.html', context)


@login_required
def ingredient_usage_report(request):
    """
    Generate ingredient usage report for a specified period.
    """
    ingredient_id = request.GET.get('ingredient_id')
    days = int(request.GET.get('days', 30))

    if not ingredient_id:
        ingredients = Ingredient.objects.filter(is_active=True).values('id', 'name')
        context = {'ingredients': ingredients}
        return render(request, 'products/ingredient_usage_report.html', context)

    try:
        report = BOMService.get_ingredient_usage_report(ingredient_id, days=days)

        # Convert Decimal to float for JSON serialization
        context = {
            'report': report,
            'ingredient_id': ingredient_id,
            'days': days,
        }

        return render(request, 'products/ingredient_usage_detail.html', context)
    except Ingredient.DoesNotExist:
        context = {
            'error': 'Ingredient not found',
            'ingredients': Ingredient.objects.filter(is_active=True).values('id', 'name')
        }
        return render(request, 'products/ingredient_usage_report.html', context)


@login_required
def variance_analysis_report(request):
    """
    Generate variance analysis report comparing theoretical vs actual usage.
    """
    ingredient_id = request.GET.get('ingredient_id')
    days = int(request.GET.get('days', 30))

    if not ingredient_id:
        ingredients = Ingredient.objects.filter(is_active=True).values('id', 'name')
        context = {'ingredients': ingredients}
        return render(request, 'products/variance_analysis.html', context)

    try:
        # Get the variance analysis
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        variance_data = BOMService.calculate_variance(
            ingredient_id,
            period_start=start_date,
            period_end=end_date
        )

        # Get ingredient details
        ingredient = Ingredient.objects.get(id=ingredient_id)

        # Get all variance records for this ingredient
        variance_records = VarianceRecord.objects.filter(
            ingredient_id=ingredient_id,
            period_end__gte=start_date
        ).order_by('-period_end')

        # Calculate statistics
        all_variances = variance_records.values_list('variance_percentage', flat=True)
        if all_variances:
            avg_variance = sum(all_variances) / len(all_variances)
            max_variance = max(all_variances)
            min_variance = min(all_variances)
        else:
            avg_variance = max_variance = min_variance = 0

        context = {
            'variance_data': variance_data,
            'ingredient': ingredient,
            'variance_records': variance_records,
            'avg_variance': avg_variance,
            'max_variance': max_variance,
            'min_variance': min_variance,
            'days': days,
            'ingredient_id': ingredient_id,
        }

        return render(request, 'products/variance_detail.html', context)

    except Ingredient.DoesNotExist:
        context = {
            'error': 'Ingredient not found',
            'ingredients': Ingredient.objects.filter(is_active=True).values('id', 'name')
        }
        return render(request, 'products/variance_analysis.html', context)


@login_required
def low_stock_report(request):
    """
    Report of all ingredients below minimum stock level.
    """
    low_stock_ingredients = BOMService.get_low_stock_ingredients()

    # Calculate total value of low stock
    total_value = sum(
        ing.current_stock * ing.cost_per_unit
        for ing in low_stock_ingredients
    )

    # Get recent transactions for context
    week_ago = timezone.now() - timedelta(days=7)
    recent_purchases = StockTransaction.objects.filter(
        transaction_type='PURCHASE',
        created_at__gte=week_ago
    ).select_related('ingredient').count()

    context = {
        'low_stock_ingredients': low_stock_ingredients,
        'total_count': low_stock_ingredients.count(),
        'total_value': total_value,
        'recent_purchases': recent_purchases,
    }

    return render(request, 'products/low_stock_report.html', context)


@login_required
def waste_report(request):
    """
    Report of waste, spoilage, and freebies.
    """
    days = int(request.GET.get('days', 30))
    waste_type = request.GET.get('waste_type', 'ALL')

    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)

    waste_logs = WasteLog.objects.filter(
        waste_date__gte=start_date,
        waste_date__lte=end_date
    ).select_related('ingredient', 'reported_by')

    if waste_type != 'ALL':
        waste_logs = waste_logs.filter(waste_type=waste_type)

    waste_logs = waste_logs.order_by('-waste_date')

    # Aggregate by type
    waste_by_type = {}
    total_cost = 0
    for waste in waste_logs:
        waste_t = waste.get_waste_type_display()
        if waste_t not in waste_by_type:
            waste_by_type[waste_t] = {
                'count': 0,
                'quantity': 0,
                'cost': 0
            }
        waste_by_type[waste_t]['count'] += 1
        waste_by_type[waste_t]['quantity'] += float(waste.quantity)
        waste_by_type[waste_t]['cost'] += float(waste.cost_impact)
        total_cost += float(waste.cost_impact)

    context = {
        'waste_logs': waste_logs[:20],  # Show latest 20
        'waste_by_type': waste_by_type,
        'total_cost': total_cost,
        'days': days,
        'waste_type': waste_type,
        'waste_types': WasteLog.WASTE_TYPES,
    }

    return render(request, 'products/waste_report.html', context)


@login_required
def api_ingredient_availability(request):
    """
    API endpoint to check ingredient availability for a product.
    """
    product_id = request.GET.get('product_id')
    quantity = int(request.GET.get('quantity', 1))

    if not product_id:
        return JsonResponse({'error': 'product_id required'}, status=400)

    availability = BOMService.check_ingredient_availability(product_id, quantity)

    return JsonResponse({
        'available': availability['available'],
        'has_recipe': availability['has_recipe'],
        'shortages': availability['shortages'],
        'total_shortages': availability['total_shortages']
    })
