from django.contrib import admin
from .models import AuditTrail, Archive


@admin.register(AuditTrail)
class AuditTrailAdmin(admin.ModelAdmin):
    """Audit trail admin - read-only"""

    list_display = ("timestamp", "actor", "action", "entity", "ref_id")
    list_filter = ("action", "entity", "timestamp")
    search_fields = ("entity", "ref_id", "actor__username")
    readonly_fields = ("actor", "entity", "action", "ref_id", "diff", "snapshot", "timestamp")

    def has_add_permission(self, request):
        """Audit trails are created automatically via signals"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Audit trails should not be deleted"""
        return False


@admin.register(Archive)
class ArchiveAdmin(admin.ModelAdmin):
    """Archive admin"""

    list_display = ("entity", "ref_id", "archived_by", "archived_at")
    list_filter = ("entity", "archived_at")
    search_fields = ("entity", "ref_id", "archived_by__username")
    readonly_fields = ("entity", "ref_id", "snapshot", "archived_by", "archived_at")

    def has_add_permission(self, request):
        """Archives are created automatically"""
        return False
