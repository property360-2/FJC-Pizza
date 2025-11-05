from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings
from decimal import Decimal
from datetime import datetime


class Order(models.Model):
    """
    Order model representing a customer transaction.

    Lifecycle:
    PENDING -> IN_PROGRESS -> FINISHED
         \-> CANCELLED
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        FINISHED = "FINISHED", "Finished"
        CANCELLED = "CANCELLED", "Cancelled"

    order_no = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique order identifier (e.g., K-20251105-00101)"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text="Order status"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders_created",
        help_text="User who created the order (null for kiosk orders)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["order_no"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.order_no} - {self.get_status_display()}"

    def generate_order_no(self):
        """Generate unique order number: K-YYYYMMDD-NNNNN"""
        today = datetime.now().strftime("%Y%m%d")
        # Get today's order count
        count = Order.objects.filter(
            order_no__startswith=f"K-{today}"
        ).count() + 1
        return f"K-{today}-{count:05d}"

    @property
    def total_amount(self) -> Decimal:
        """Calculate total amount from order items"""
        return sum(item.subtotal for item in self.items.all())

    @property
    def item_count(self) -> int:
        """Get total item count"""
        return sum(item.qty for item in self.items.all())

    def mark_in_progress(self):
        """Move order to IN_PROGRESS status"""
        self.status = self.Status.IN_PROGRESS
        self.save()

    def finish(self):
        """Mark order as FINISHED"""
        self.status = self.Status.FINISHED
        self.save()

    def cancel(self):
        """
        Cancel order and restore stock if payment was successful.
        This should trigger audit trail and stock restoration.
        """
        if self.status != self.Status.CANCELLED:
            # Restore stock for each item
            for item in self.items.all():
                item.product.adjust_stock(item.qty, reason=f"Order {self.order_no} cancelled")

            self.status = self.Status.CANCELLED
            self.save()


class OrderItem(models.Model):
    """
    Individual items within an order.
    Stores price at purchase time for audit purposes.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="order_items"
    )

    qty = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Quantity ordered"
    )

    price_at_purchase = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Product price at time of purchase"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_items"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.product.name} x{self.qty}"

    @property
    def subtotal(self) -> Decimal:
        """Calculate subtotal for this item"""
        return self.price_at_purchase * self.qty

    def save(self, *args, **kwargs):
        """Auto-populate price_at_purchase if not set"""
        if not self.price_at_purchase:
            self.price_at_purchase = self.product.price
        super().save(*args, **kwargs)


class Payment(models.Model):
    """
    Payment record for an order.

    Payment flow:
    - Cash: Created as PENDING -> Cashier marks SUCCESS -> triggers stock deduction
    - Online: Created and immediately marked SUCCESS (demo) -> triggers stock deduction
    """

    class Method(models.TextChoices):
        CASH = "CASH", "Cash"
        ONLINE_DEMO = "ONLINE_DEMO", "Online (Demo)"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="payment"
    )

    method = models.CharField(
        max_length=20,
        choices=Method.choices,
        help_text="Payment method"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text="Payment status"
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Payment amount"
    )

    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments_processed",
        help_text="User who processed the payment (for cash payments)"
    )

    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When payment was successfully processed"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payments"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["method"]),
        ]

    def __str__(self):
        return f"Payment for {self.order.order_no} - {self.get_status_display()}"

    def mark_success(self, processed_by=None):
        """
        Mark payment as successful and trigger inventory deduction.

        This should:
        1. Set status to SUCCESS
        2. Record processed_at timestamp
        3. Deduct inventory for all order items
        4. Move order to IN_PROGRESS
        """
        from django.utils import timezone

        if self.status != self.Status.SUCCESS:
            self.status = self.Status.SUCCESS
            self.processed_at = timezone.now()
            if processed_by:
                self.processed_by = processed_by
            self.save()

            # Deduct inventory
            for item in self.order.items.all():
                item.product.adjust_stock(
                    -item.qty,
                    reason=f"Order {self.order.order_no} paid"
                )

            # Move order to IN_PROGRESS
            self.order.mark_in_progress()

    def mark_failed(self):
        """Mark payment as failed"""
        self.status = self.Status.FAILED
        self.save()
