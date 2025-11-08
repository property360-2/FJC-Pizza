from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.core.paginator import Paginator
from .models import AuditTrail, Archive


def is_admin(user):
    return user.is_authenticated and user.is_admin


@login_required
@user_passes_test(is_admin)
def audit_trail(request):
    """Display system audit trail with filtering"""

    # Get filter parameters
    action_filter = request.GET.get('action', '')
    model_filter = request.GET.get('model', '')
    user_filter = request.GET.get('user', '')

    # Base query
    audit_logs = AuditTrail.objects.all().select_related('user').order_by('-created_at')

    # Apply filters
    if action_filter:
        audit_logs = audit_logs.filter(action=action_filter)

    if model_filter:
        audit_logs = audit_logs.filter(model_name=model_filter)

    if user_filter:
        audit_logs = audit_logs.filter(user__username__icontains=user_filter)

    # Pagination
    paginator = Paginator(audit_logs, 50)  # 50 logs per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Get unique models and actions for filters
    models = AuditTrail.objects.values_list('model_name', flat=True).distinct().order_by('model_name')
    actions = AuditTrail.objects.values_list('action', flat=True).distinct().order_by('action')

    context = {
        'audit_logs': page_obj,
        'models': models,
        'actions': actions,
        'action_filter': action_filter,
        'model_filter': model_filter,
        'user_filter': user_filter,
    }
    return render(request, 'system/audit.html', context)


@login_required
@user_passes_test(is_admin)
def archive_list(request):
    """Display archived items with filtering"""

    # Get filter parameters
    model_filter = request.GET.get('model', '')

    # Base query
    archives = Archive.objects.all().select_related('archived_by').order_by('-created_at')

    # Apply filters
    if model_filter:
        archives = archives.filter(model_name=model_filter)

    # Pagination
    paginator = Paginator(archives, 50)  # 50 archives per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Get unique models for filter
    models = Archive.objects.values_list('model_name', flat=True).distinct().order_by('model_name')

    context = {
        'archives': page_obj,
        'models': models,
        'model_filter': model_filter,
    }
    return render(request, 'system/archive.html', context)
