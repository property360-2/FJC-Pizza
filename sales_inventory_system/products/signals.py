"""
Signals for Bill of Materials (BOM) and Inventory Events

Purpose:
- Handles automatic ingredient deduction whenever a payment succeeds.
- Handles automated low-stock notifications (both email triggers and Audit Trail warning entries)
  when stock falls below predefined limits.

Broader System Integration:
- Coordinates events between the 'orders' app (payments) and 'products' app (inventory).
- Logs automated system health status indicators directly to the 'system' app's AuditTrail model.
"""

import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.contrib.auth import get_user_model

from sales_inventory_system.orders.models import Payment
from sales_inventory_system.system.models import AuditTrail
from .models import Ingredient, Product
from .inventory_service import BOMService, IngredientDeductionError

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Payment)
def deduct_ingredients_on_payment(sender, instance, created, **kwargs):
    """
    Automatically deduct ingredients when payment is confirmed.

    This signal is triggered when a Payment object is saved.
    If the payment status changes to 'SUCCESS', we deduct the required
    ingredients from inventory based on the order's recipe.

    Accepts:
        sender: The Payment model class
        instance: The saved Payment instance
        created: Boolean indicating if it was just created
        kwargs: Additional arguments
        
    Returns:
        None
    """
    # Only process on update, not on creation
    if created:
        return

    # Only process when payment is confirmed
    if instance.status != 'SUCCESS':
        return

    # Check if ingredients have already been deducted
    # (to prevent double deduction on multiple saves)
    if hasattr(instance, '_ingredients_deducted'):
        return

    try:
        order = instance.order
        user = instance.processed_by

        # Attempt to deduct ingredients
        result = BOMService.deduct_ingredients_for_order(order, user=user)

        # Mark that we've processed this payment
        instance._ingredients_deducted = True

        logger.info(
            f"Ingredients deducted for order {order.order_number}. "
            f"Total cost: ₱{result['total_cost']}"
        )

    except IngredientDeductionError as e:
        # Log the error but don't fail the payment
        logger.error(
            f"Failed to deduct ingredients for order {instance.order.order_number}: {str(e)}"
        )

    except Exception as e:
        logger.error(
            f"Unexpected error deducting ingredients for order {instance.order.order_number}: {str(e)}"
        )


@receiver(pre_save, sender=Ingredient)
def capture_old_stock_ingredient(sender, instance, **kwargs):
    """
    Capture the ingredient's original stock value before saving so we can check
    if the stock level changed to low in post_save.
    
    Accepts:
        sender: The Ingredient model class
        instance: The Ingredient instance being saved
        kwargs: Additional signal arguments
        
    Returns:
        None
    """
    # NOTE: Captured pre-save current_stock to check for low-stock alert transitions.
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._old_current_stock = old_instance.current_stock
        except sender.DoesNotExist:
            instance._old_current_stock = None
    else:
        instance._old_current_stock = None


@receiver(post_save, sender=Ingredient)
def low_stock_alert_ingredient(sender, instance, created, **kwargs):
    """
    Triggers an email notification and logs an audit trail warning when an ingredient 
    falls below its minimum stock threshold. Uses pre_save cached stock value to avoid 
    spamming email alerts if the item was already below the minimum stock threshold.
    
    Accepts:
        sender: The Ingredient model class
        instance: The saved Ingredient instance
        created: Boolean indicating if it was just created
        kwargs: Additional arguments
        
    Returns:
        None
    """
    # Only alert active ingredients
    if not instance.is_active:
        return
        
    if instance.is_low_stock:
        # Check if it was already low before this save to avoid spamming alerts
        if not created:
            old_stock = getattr(instance, '_old_current_stock', None)
            if old_stock is not None and old_stock < instance.min_stock:
                # Already low, don't spam
                return

        # Create system-generated Audit Trail Warning log
        AuditTrail.objects.create(
            user=None,  # System-generated action
            action='UPDATE',
            model_name='Ingredient',
            record_id=instance.id,
            description=f"⚠️ SYSTEM WARNING: Ingredient '{instance.name}' is low! Stock is {instance.current_stock} {instance.unit} (Min: {instance.min_stock} {instance.unit})",
            data_snapshot={
                'name': instance.name,
                'current_stock': str(instance.current_stock),
                'min_stock': str(instance.min_stock),
                'unit': instance.unit
            }
        )

        # Get active admin email addresses dynamically instead of hardcoding
        User = get_user_model()
        admin_emails = list(User.objects.filter(
            role='ADMIN', 
            is_active=True, 
            is_archived=False
        ).exclude(email='').values_list('email', flat=True))
        
        # Fallback to default email if no active admins with emails exist in system
        if not admin_emails:
            admin_emails = ['junalvior21@gmail.com']

        # Send simulated/real email (printed to terminal console in local dev)
        subject = f"⚠️ [FCJ Pizza Alert] Low Stock: {instance.name}!"
        message = (
            f"Dear Pizza Shop Manager,\n\n"
            f"This is an automated alert from the FCJ Pizza Sales & Inventory System.\n\n"
            f"The following ingredient has fallen below its minimum stock threshold:\n"
            f"• Ingredient: {instance.name}\n"
            f"• Current Stock: {instance.current_stock} {instance.unit}\n"
            f"• Minimum Threshold: {instance.min_stock} {instance.unit}\n\n"
            f"Please check inventory levels and restock as soon as possible to prevent production bottlenecks.\n\n"
            f"Best regards,\n"
            f"FCJ Pizza Automation Engine"
        )
        try:
            send_mail(
                subject,
                message,
                None,
                admin_emails,
                fail_silently=False
            )
            logger.warning(f"Low stock email alert sent for ingredient: {instance.name} to {admin_emails}")
        except Exception as e:
            logger.error(f"Failed to send low stock email: {e}")


@receiver(pre_save, sender=Product)
def capture_old_stock_product(sender, instance, **kwargs):
    """
    Capture the product's original stock value before saving so we can check
    if the stock level changed to low in post_save.
    
    Accepts:
        sender: The Product model class
        instance: The Product instance being saved
        kwargs: Additional signal arguments
        
    Returns:
        None
    """
    # NOTE: Captured pre-save stock to check for low-stock alert transitions.
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._old_stock = old_instance.stock
        except sender.DoesNotExist:
            instance._old_stock = None
    else:
        instance._old_stock = None


@receiver(post_save, sender=Product)
def low_stock_alert_product(sender, instance, created, **kwargs):
    """
    Triggers an email notification and logs an audit trail warning when a product 
    falls below its minimum threshold. Uses pre_save cached stock value to avoid 
    spamming email alerts if the item was already below the minimum threshold.
    
    Accepts:
        sender: The Product model class
        instance: The saved Product instance
        created: Boolean indicating if it was just created
        kwargs: Additional arguments
        
    Returns:
        None
    """
    if instance.is_archived:
        return

    # For manufactured products, the ingredient signal handles it, so we only alert for simple stock items
    if instance.requires_bom:
        return
        
    if instance.is_low_stock:
        # Check if it was already low before this save to avoid spamming alerts
        if not created:
            old_stock = getattr(instance, '_old_stock', None)
            if old_stock is not None and old_stock < instance.threshold:
                # Already low, don't spam
                return

        # Create system-generated Audit Trail Warning log
        AuditTrail.objects.create(
            user=None,  # System-generated action
            action='UPDATE',
            model_name='Product',
            record_id=instance.id,
            description=f"⚠️ SYSTEM WARNING: Product '{instance.name}' is low! Stock is {instance.stock} pcs (Threshold: {instance.threshold} pcs)",
            data_snapshot={
                'name': instance.name,
                'stock': instance.stock,
                'threshold': instance.threshold
            }
        )

        # Get active admin email addresses dynamically instead of hardcoding
        User = get_user_model()
        admin_emails = list(User.objects.filter(
            role='ADMIN', 
            is_active=True, 
            is_archived=False
        ).exclude(email='').values_list('email', flat=True))
        
        # Fallback to default email if no active admins with emails exist in system
        if not admin_emails:
            admin_emails = ['junalvior21@gmail.com']

        # Send simulated/real email (printed to terminal console in local dev)
        subject = f"⚠️ [FCJ Pizza Alert] Low Stock: {instance.name}!"
        message = (
            f"Dear Pizza Shop Manager,\n\n"
            f"This is an automated alert from the FCJ Pizza Sales & Inventory System.\n\n"
            f"The following simple stock product has fallen below its threshold:\n"
            f"• Product: {instance.name}\n"
            f"• Current Stock: {instance.stock} pcs\n"
            f"• Minimum Threshold: {instance.threshold} pcs\n\n"
            f"Please replenish the stock immediately.\n\n"
            f"Best regards,\n"
            f"FCJ Pizza Automation Engine"
        )
        try:
            send_mail(
                subject,
                message,
                None,
                admin_emails,
                fail_silently=False
            )
            logger.warning(f"Low stock email alert sent for product: {instance.name} to {admin_emails}")
        except Exception as e:
            logger.error(f"Failed to send low stock email: {e}")

