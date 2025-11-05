from django.db import models
from django.conf import settings


class AuditTrail(models.Model):
    """
    Audit trail for tracking all system actions.

    Automatically created via Django signals for transparency.
    Records who did what, when, and what changed.
    """

    class Action(models.TextChoices):
        CREATE = "CREATE", "Create"
        UPDATE = "UPDATE", "Update"
        DELETE = "DELETE", "Delete"
        ARCHIVE = "ARCHIVE", "Archive"
        UNARCHIVE = "UNARCHIVE", "Unarchive"
        STOCK_ADJUST = "STOCK_ADJUST", "Stock Adjustment"
        PAYMENT_PROCESS = "PAYMENT_PROCESS", "Payment Processed"
        ORDER_STATUS = "ORDER_STATUS", "Order Status Change"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_actions",
        help_text="User who performed the action"
    )

    entity = models.CharField(
        max_length=50,
        help_text="Entity type (product, order, payment, user, etc.)"
    )

    action = models.CharField(
        max_length=20,
        choices=Action.choices,
        help_text="Action performed"
    )

    ref_id = models.IntegerField(
        help_text="ID of the affected record"
    )

    diff = models.JSONField(
        default=dict,
        blank=True,
        help_text="Changes made (before/after values)"
    )

    snapshot = models.JSONField(
        default=dict,
        blank=True,
        help_text="Full snapshot of record after action"
    )

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_trail"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["entity", "ref_id"]),
            models.Index(fields=["actor"]),
            models.Index(fields=["action"]),
            models.Index(fields=["timestamp"]),
        ]

    def __str__(self):
        actor_name = self.actor.username if self.actor else "System"
        return f"{actor_name} - {self.get_action_display()} on {self.entity} #{self.ref_id}"


class Archive(models.Model):
    """
    Archive for soft-deleted or archived records.

    Stores full JSON snapshot to allow restoration if needed.
    """

    entity = models.CharField(
        max_length=50,
        help_text="Entity type (product, order, user, etc.)"
    )

    ref_id = models.IntegerField(
        help_text="Original ID of the archived record"
    )

    snapshot = models.JSONField(
        help_text="Full JSON snapshot of the archived record"
    )

    archived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="archives_created",
        help_text="User who archived the record"
    )

    archived_at = models.DateTimeField(auto_now_add=True)

    reason = models.TextField(
        blank=True,
        help_text="Optional reason for archiving"
    )

    class Meta:
        db_table = "archives"
        ordering = ["-archived_at"]
        indexes = [
            models.Index(fields=["entity", "ref_id"]),
            models.Index(fields=["archived_by"]),
        ]

    def __str__(self):
        return f"Archived {self.entity} #{self.ref_id}"
