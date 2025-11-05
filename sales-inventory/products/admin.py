from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Product admin configuration"""

    list_display = ("name", "price", "stock", "threshold", "is_low_stock", "is_archived", "updated_at")
    list_filter = ("is_archived", "created_at")
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Product Information", {
            "fields": ("name", "price", "image_url")
        }),
        ("Inventory", {
            "fields": ("stock", "threshold")
        }),
        ("Status", {
            "fields": ("is_archived",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def is_low_stock(self, obj):
        """Display low stock status"""
        return obj.is_low_stock
    is_low_stock.boolean = True
    is_low_stock.short_description = "Low Stock"
