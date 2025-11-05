from django.contrib import admin
from .models import Order, OrderItem, Payment


class OrderItemInline(admin.TabularInline):
    """Inline for order items"""
    model = OrderItem
    extra = 0
    readonly_fields = ("subtotal",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Order admin configuration"""

    list_display = ("order_no", "status", "total_amount", "item_count", "created_by", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("order_no",)
    readonly_fields = ("order_no", "total_amount", "item_count", "created_at", "updated_at")
    inlines = [OrderItemInline]

    fieldsets = (
        ("Order Information", {
            "fields": ("order_no", "status", "created_by")
        }),
        ("Summary", {
            "fields": ("total_amount", "item_count")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Payment admin configuration"""

    list_display = ("order", "method", "status", "amount", "processed_by", "processed_at")
    list_filter = ("status", "method", "created_at")
    search_fields = ("order__order_no",)
    readonly_fields = ("processed_at", "created_at", "updated_at")

    fieldsets = (
        ("Payment Information", {
            "fields": ("order", "method", "status", "amount")
        }),
        ("Processing", {
            "fields": ("processed_by", "processed_at")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
