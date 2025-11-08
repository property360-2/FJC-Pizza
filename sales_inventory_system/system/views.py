from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse


@login_required
def audit_trail(request):
    """Display system audit trail."""
    return render(request, 'system/audit_trail.html', {
        'audit_logs': [],
        'message': 'Audit trail view - stub'
    })


@login_required
def archive_list(request):
    """Display archived items."""
    return render(request, 'system/archive_list.html', {
        'archives': [],
        'message': 'Archive list view - stub'
    })
