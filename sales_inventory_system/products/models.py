from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

class Product(models.Model):
    """Product model for inventory management"""

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    threshold = models.IntegerField(
        default=10,
        validators=[MinValueValidator(0)],
        help_text="Minimum stock level before low-stock alert"
    )
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    category = models.CharField(max_length=100, blank=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        """Check if product stock is below threshold"""
        return self.stock < self.threshold

    @property
    def is_available(self):
        """Check if product is available for ordering"""
        return not self.is_archived and self.stock > 0
