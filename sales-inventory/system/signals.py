"""
Django signals for automatic audit trail creation.

These signals listen to model changes and automatically create
AuditTrail entries for transparency and compliance.
"""
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.core.serializers import serialize
import json
from .models import AuditTrail, Archive


def get_current_user():
    """
    Get the current user from the request context.
    This is a simple implementation - in production you might use
    django-crum or threading.local() to track the current user.
    """
    import threading
    return getattr(threading.current_thread(), 'user', None)


def model_to_dict(instance):
    """
    Convert a model instance to a dictionary for snapshot storage.
    """
    data = json.loads(serialize('json', [instance]))[0]['fields']
    data['id'] = instance.pk

    # Convert related fields to IDs
    for field in instance._meta.fields:
        if field.is_relation and hasattr(instance, field.name):
            related = getattr(instance, field.name)
            data[field.name] = related.pk if related else None

    return data


def get_model_diff(old_data, new_data):
    """
    Calculate the difference between old and new data.
    Returns a dict with 'before' and 'after' for changed fields.
    """
    diff = {}
    for key in new_data:
        if key in old_data and old_data[key] != new_data[key]:
            diff[key] = {
                'before': old_data[key],
                'after': new_data[key]
            }
    return diff


def create_audit_log(entity, action, ref_id, actor=None, diff=None, snapshot=None):
    """
    Helper function to create an audit trail entry.
    """
    AuditTrail.objects.create(
        entity=entity,
        action=action,
        ref_id=ref_id,
        actor=actor,
        diff=diff or {},
        snapshot=snapshot or {}
    )


# ============================================================================
# PRODUCT SIGNALS
# ============================================================================

@receiver(post_save, sender='products.Product')
def product_post_save(sender, instance, created, **kwargs):
    """Log product creation and updates."""
    from products.models import Product

    action = AuditTrail.Action.CREATE if created else AuditTrail.Action.UPDATE
    snapshot = model_to_dict(instance)
    diff = {}

    if not created:
        # For updates, try to get the diff (this is simplified - in production
        # you'd track the old state in pre_save)
        diff = {}  # Will be populated if we implement pre_save tracking

    create_audit_log(
        entity='product',
        action=action,
        ref_id=instance.pk,
        actor=get_current_user(),
        diff=diff,
        snapshot=snapshot
    )


@receiver(post_delete, sender='products.Product')
def product_post_delete(sender, instance, **kwargs):
    """Log product deletion."""
    create_audit_log(
        entity='product',
        action=AuditTrail.Action.DELETE,
        ref_id=instance.pk,
        actor=get_current_user(),
        snapshot=model_to_dict(instance)
    )


# ============================================================================
# ORDER SIGNALS
# ============================================================================

@receiver(post_save, sender='orders.Order')
def order_post_save(sender, instance, created, **kwargs):
    """Log order creation and updates."""
    action = AuditTrail.Action.CREATE if created else AuditTrail.Action.ORDER_STATUS
    snapshot = model_to_dict(instance)

    create_audit_log(
        entity='order',
        action=action,
        ref_id=instance.pk,
        actor=get_current_user() or instance.created_by,
        snapshot=snapshot
    )


@receiver(post_save, sender='orders.OrderItem')
def order_item_post_save(sender, instance, created, **kwargs):
    """Log order item creation."""
    if created:
        snapshot = model_to_dict(instance)
        create_audit_log(
            entity='order_item',
            action=AuditTrail.Action.CREATE,
            ref_id=instance.pk,
            actor=get_current_user(),
            snapshot=snapshot
        )


# ============================================================================
# PAYMENT SIGNALS
# ============================================================================

@receiver(post_save, sender='orders.Payment')
def payment_post_save(sender, instance, created, **kwargs):
    """Log payment creation and status changes."""
    action = AuditTrail.Action.CREATE if created else AuditTrail.Action.PAYMENT_PROCESS
    snapshot = model_to_dict(instance)

    create_audit_log(
        entity='payment',
        action=action,
        ref_id=instance.pk,
        actor=get_current_user() or instance.processed_by,
        snapshot=snapshot
    )


# ============================================================================
# USER SIGNALS
# ============================================================================

@receiver(post_save, sender='accounts.User')
def user_post_save(sender, instance, created, **kwargs):
    """Log user creation and updates."""
    action = AuditTrail.Action.CREATE if created else AuditTrail.Action.UPDATE
    snapshot = model_to_dict(instance)

    # Don't log password in snapshot
    snapshot.pop('password', None)

    create_audit_log(
        entity='user',
        action=action,
        ref_id=instance.pk,
        actor=get_current_user(),
        snapshot=snapshot
    )


@receiver(post_delete, sender='accounts.User')
def user_post_delete(sender, instance, **kwargs):
    """Log user deletion."""
    snapshot = model_to_dict(instance)
    snapshot.pop('password', None)

    create_audit_log(
        entity='user',
        action=AuditTrail.Action.DELETE,
        ref_id=instance.pk,
        actor=get_current_user(),
        snapshot=snapshot
    )
