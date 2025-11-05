"""
API views for system operations (audit trails, archives).

Provides endpoints for viewing audit logs and managing archived records.
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from .models import AuditTrail, Archive
from accounts.decorators import role_required


@require_http_methods(["GET"])
@role_required(['ADMIN'])
def audit_list(request):
    """
    GET /api/audit/
    List audit trail entries.

    Query params:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 50)
    - entity: Filter by entity type
    - action: Filter by action
    - actor: Filter by actor username
    """
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 50))
    entity = request.GET.get('entity', '')
    action = request.GET.get('action', '')
    actor = request.GET.get('actor', '')

    # Base queryset
    queryset = AuditTrail.objects.all()

    # Apply filters
    if entity:
        queryset = queryset.filter(entity=entity)

    if action:
        queryset = queryset.filter(action=action)

    if actor:
        queryset = queryset.filter(actor__username__icontains=actor)

    # Order by timestamp descending (newest first)
    queryset = queryset.order_by('-timestamp')

    # Paginate
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page)

    # Serialize audit entries
    audit_entries = []
    for entry in page_obj:
        audit_entries.append({
            'id': entry.id,
            'actor': entry.actor.username if entry.actor else 'System',
            'entity': entry.entity,
            'action': entry.action,
            'ref_id': entry.ref_id,
            'diff': entry.diff,
            'snapshot': entry.snapshot,
            'timestamp': entry.timestamp.isoformat(),
        })

    return JsonResponse({
        'success': True,
        'audit_entries': audit_entries,
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
@role_required(['ADMIN'])
def audit_detail(request, audit_id):
    """
    GET /api/audit/<id>/
    Get a single audit entry by ID.
    """
    try:
        entry = AuditTrail.objects.get(pk=audit_id)

        return JsonResponse({
            'success': True,
            'audit_entry': {
                'id': entry.id,
                'actor': entry.actor.username if entry.actor else 'System',
                'entity': entry.entity,
                'action': entry.action,
                'ref_id': entry.ref_id,
                'diff': entry.diff,
                'snapshot': entry.snapshot,
                'timestamp': entry.timestamp.isoformat(),
            }
        })

    except AuditTrail.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Audit entry not found'
        }, status=404)


@require_http_methods(["GET"])
@role_required(['ADMIN'])
def archive_list(request):
    """
    GET /api/archive/
    List archived records.

    Query params:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 50)
    - entity: Filter by entity type
    """
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 50))
    entity = request.GET.get('entity', '')

    # Base queryset
    queryset = Archive.objects.all()

    # Apply filters
    if entity:
        queryset = queryset.filter(entity=entity)

    # Order by archived_at descending (newest first)
    queryset = queryset.order_by('-archived_at')

    # Paginate
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page)

    # Serialize archive entries
    archive_entries = []
    for entry in page_obj:
        archive_entries.append({
            'id': entry.id,
            'entity': entry.entity,
            'ref_id': entry.ref_id,
            'archived_by': entry.archived_by.username if entry.archived_by else 'System',
            'archived_at': entry.archived_at.isoformat(),
            'reason': entry.reason,
            'snapshot': entry.snapshot,
        })

    return JsonResponse({
        'success': True,
        'archive_entries': archive_entries,
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
def health_check(request):
    """
    GET /api/health/
    Health check endpoint.
    """
    return JsonResponse({
        'success': True,
        'status': 'healthy',
        'service': 'FJC-Pizza Sales & Inventory System'
    })


@require_http_methods(["GET"])
def csrf_token(request):
    """
    GET /api/csrf/
    Get CSRF token for AJAX requests.
    """
    from django.middleware.csrf import get_token
    return JsonResponse({
        'success': True,
        'csrf_token': get_token(request)
    })
