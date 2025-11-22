"""
Views for Bill of Materials reports and management
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum, F, Avg, Max, Min, Count
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import (
    Ingredient, RecipeItem, StockTransaction, WasteLog,
    PhysicalCount, VarianceRecord
)
from .inventory_service import BOMService
import json
import csv
from io import StringIO


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
    Comprehensive ingredient usage report for all active ingredients.
    Shows usage analytics directly on the page.
    """
    days = int(request.GET.get('days', 30))
    download = request.GET.get('download', '').lower()

    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)

    # Get all active ingredients with usage data
    ingredients = Ingredient.objects.filter(is_active=True).order_by('name')

    usage_summary = []
    total_used = 0
    total_cost = 0

    for ingredient in ingredients:
        # Get stock transactions
        transactions = StockTransaction.objects.filter(
            ingredient=ingredient,
            created_at__gte=start_date,
            created_at__lte=end_date
        ).order_by('-created_at')

        if not transactions.exists():
            continue

        # Calculate totals by transaction type
        total_quantity = 0
        transaction_stats = {}

        for trans in transactions:
            transaction_stats[trans.get_transaction_type_display()] = transaction_stats.get(trans.get_transaction_type_display(), 0) + float(trans.quantity)
            if trans.transaction_type in ['DEDUCTION', 'PREP']:
                total_quantity += float(trans.quantity)

        # Calculate cost
        ingredient_cost = float(ingredient.cost_per_unit) * total_quantity

        usage_summary.append({
            'ingredient': ingredient,
            'total_quantity': total_quantity,
            'cost': ingredient_cost,
            'transaction_stats': transaction_stats,
            'transactions': transactions[:10],  # Latest 10 transactions
            'transactions_count': transactions.count(),
        })

        total_used += total_quantity
        total_cost += ingredient_cost

    # Calculate average cost per unit used
    avg_cost = total_cost / total_used if total_used > 0 else 0

    # Sort data for insights (do this in view, not template)
    sorted_by_cost = sorted(usage_summary, key=lambda x: x['cost'], reverse=True)
    sorted_by_quantity = sorted(usage_summary, key=lambda x: x['total_quantity'], reverse=True)
    top_cost_items = sorted_by_cost[:5]
    top_used_items = sorted_by_quantity[:5]

    # Handle downloads
    if download == 'csv':
        return generate_usage_csv_download(usage_summary, days)
    elif download == 'detailed':
        return generate_usage_detailed_csv(usage_summary, days)

    context = {
        'usage_summary': sorted_by_cost,  # Default sort by cost descending
        'top_cost_items': top_cost_items,
        'top_used_items': top_used_items,
        'days': days,
        'total_used': total_used,
        'total_cost': total_cost,
        'avg_cost': avg_cost,
        'period_start': start_date,
        'period_end': end_date,
        'total_ingredients': len(usage_summary),
    }

    return render(request, 'products/ingredient_usage_report_enhanced.html', context)


def generate_usage_csv_download(usage_summary, days):
    """Generate CSV report for ingredient usage"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="ingredient_usage_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Ingredient', 'Unit', 'Total Used', 'Cost Per Unit', 'Total Cost', 'Transactions'])

    for item in usage_summary:
        writer.writerow([
            item['ingredient'].name,
            item['ingredient'].unit,
            f"{item['total_quantity']:.3f}",
            f"{item['ingredient'].cost_per_unit:.2f}",
            f"{item['cost']:.2f}",
            item['transactions_count']
        ])

    return response


def generate_usage_detailed_csv(usage_summary, days):
    """Generate detailed CSV report with all transactions"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="ingredient_usage_detailed_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Ingredient', 'Date', 'Type', 'Quantity', 'Unit Cost', 'Cost Impact', 'Notes'])

    for item in usage_summary:
        for trans in item['transactions']:
            cost_impact = float(trans.quantity) * float(item['ingredient'].cost_per_unit) if trans.unit_cost else 0
            writer.writerow([
                item['ingredient'].name,
                trans.created_at.strftime("%Y-%m-%d %H:%M"),
                trans.get_transaction_type_display(),
                f"{trans.quantity:.3f}",
                f"{item['ingredient'].cost_per_unit:.2f}",
                f"{cost_impact:.2f}",
                trans.notes or ''
            ])

    return response


@login_required
def variance_analysis_report(request):
    """
    Comprehensive variance analysis report for all active ingredients.
    Shows analytics directly on the page with download option.
    Optimized with database queries to avoid N+1 problem.
    """
    days = int(request.GET.get('days', 30))
    download = request.GET.get('download', '').lower()

    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)

    # Get all variance records for the date range with related ingredient data
    all_variance_records = VarianceRecord.objects.filter(
        period_end__gte=start_date,
        ingredient__is_active=True
    ).select_related('ingredient').order_by('-period_end')

    # If no records exist, return empty state
    if not all_variance_records.exists():
        context = {
            'variance_summary': [],
            'best_performing': [],
            'outside_tolerance': [],
            'days': days,
            'total_records': 0,
            'avg_of_avgs': 0,
            'overall_within_tolerance': 0,
            'period_start': start_date,
            'period_end': end_date,
        }
        if download:
            return render(request, 'products/variance_analysis_report.html', context)
        return render(request, 'products/variance_analysis_report.html', context)

    # Group variance records by ingredient and calculate statistics
    variance_summary = []
    total_records = 0
    within_tolerance_count = 0
    ingredients_data = {}

    # Aggregate data by ingredient
    for record in all_variance_records:
        ing_id = record.ingredient.id
        if ing_id not in ingredients_data:
            ingredients_data[ing_id] = {
                'ingredient': record.ingredient,
                'variances': [],
                'within_tolerance_count': 0,
                'variance_records': [],
            }

        ingredients_data[ing_id]['variances'].append(record.variance_percentage)
        if record.within_tolerance:
            ingredients_data[ing_id]['within_tolerance_count'] += 1

        # Keep only latest 5 records for display
        if len(ingredients_data[ing_id]['variance_records']) < 5:
            ingredients_data[ing_id]['variance_records'].append(record)

    # Calculate statistics for each ingredient
    for ing_id, data in ingredients_data.items():
        variances = data['variances']
        if variances:
            avg_variance = sum(variances) / len(variances)
            max_variance = max(variances)
            min_variance = min(variances)
            within_tolerance = (data['within_tolerance_count'] / len(variances)) * 100

            variance_summary.append({
                'ingredient': data['ingredient'],
                'records_count': len(variances),
                'avg_variance': avg_variance,
                'max_variance': max_variance,
                'min_variance': min_variance,
                'within_tolerance_pct': within_tolerance,
                'variance_records': data['variance_records'],
                'tolerance_threshold_1_5x': float(data['ingredient'].variance_allowance) * 1.5
            })

            total_records += len(variances)
            within_tolerance_count += data['within_tolerance_count']

    # Calculate overall statistics
    if variance_summary:
        avg_of_avgs = sum(v['avg_variance'] for v in variance_summary) / len(variance_summary)
        overall_within_tolerance = (within_tolerance_count / total_records * 100) if total_records > 0 else 0
    else:
        avg_of_avgs = 0
        overall_within_tolerance = 0

    # Sort by avg_variance for insights
    best_performing = sorted(variance_summary, key=lambda x: x['avg_variance'])[:3]
    outside_tolerance = [v for v in variance_summary if v['avg_variance'] > v['ingredient'].variance_allowance]

    # Handle download
    if download == 'csv':
        return generate_variance_csv_download(variance_summary, days)
    elif download == 'detailed':
        return generate_variance_detailed_csv(variance_summary, days)

    context = {
        'variance_summary': variance_summary,
        'best_performing': best_performing,
        'outside_tolerance': outside_tolerance,
        'days': days,
        'total_records': total_records,
        'avg_of_avgs': avg_of_avgs,
        'overall_within_tolerance': overall_within_tolerance,
        'period_start': start_date,
        'period_end': end_date,
    }

    return render(request, 'products/variance_analysis_report.html', context)


def generate_variance_csv_download(variance_summary, days):
    """Generate CSV report for variance analysis"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="variance_analysis_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Ingredient', 'Avg Variance %', 'Max Variance %', 'Min Variance %', 'Within Tolerance %', 'Records'])

    for item in variance_summary:
        writer.writerow([
            item['ingredient'].name,
            f"{item['avg_variance']:.2f}",
            f"{item['max_variance']:.2f}",
            f"{item['min_variance']:.2f}",
            f"{item['within_tolerance_pct']:.2f}",
            item['records_count']
        ])

    return response


def generate_variance_detailed_csv(variance_summary, days):
    """Generate detailed CSV report with all variance records"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="variance_detailed_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Ingredient', 'Period End', 'Theoretical Used', 'Actual Used', 'Variance %', 'Status'])

    for item in variance_summary:
        for record in item['variance_records']:
            writer.writerow([
                item['ingredient'].name,
                record.period_end.strftime("%Y-%m-%d"),
                f"{record.theoretical_used:.3f}",
                f"{record.actual_used:.3f}",
                f"{record.variance_percentage:.2f}",
                'Within Tolerance' if record.within_tolerance else 'Outside Tolerance'
            ])

    return response


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
