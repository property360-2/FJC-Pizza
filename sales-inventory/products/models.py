from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Product(models.Model):
    """
    Product model for inventory management.

    Features:
    - Stock tracking with low-stock alerts
    - Soft delete (archiving) instead of hard delete
    - Image support for kiosk display
    - Price and stock validation
    """

    name = models.CharField(
        max_length=200,
        help_text="Product name"
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Product price"
    )

    stock = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Current stock quantity"
    )

    threshold = models.IntegerField(
        default=10,
        validators=[MinValueValidator(0)],
        help_text="Low stock alert threshold"
    )

    image_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Product image URL (CDN or external)"
    )

    is_archived = models.BooleanField(
        default=False,
        help_text="Archived products are hidden from kiosk/POS"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_archived"]),
            models.Index(fields=["stock"]),
        ]

    def __str__(self):
        return f"{self.name} (Stock: {self.stock})"

    @property
    def is_low_stock(self) -> bool:
        """Check if product stock is below threshold"""
        return self.stock < self.threshold

    @property
    def is_out_of_stock(self) -> bool:
        """Check if product is out of stock"""
        return self.stock <= 0

    def adjust_stock(self, delta: int, reason: str = None) -> dict:
        """
        Adjust stock by delta amount.

        Args:
            delta: Amount to add (positive) or subtract (negative)
            reason: Optional reason for adjustment (for audit trail)

        Returns:
            dict with stock_before and stock_after
        """
        stock_before = self.stock
        self.stock += delta
        self.save()

        return {
            "stock_before": stock_before,
            "stock_after": self.stock,
            "delta": delta,
            "reason": reason
        }

    def archive(self):
        """Soft delete product"""
        self.is_archived = True
        self.save()

    def unarchive(self):
        """Restore archived product"""
        self.is_archived = False
        self.save()
