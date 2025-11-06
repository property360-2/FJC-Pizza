"""
URL configuration for API endpoints.

All API routes are prefixed with /api/
"""
from django.urls import path
from products import api as products_api
from orders import api as orders_api
from orders import kiosk_api
from analytics import api as analytics_api
from system import api as system_api


urlpatterns = [
    # ========================================================================
    # SYSTEM ENDPOINTS
    # ========================================================================
    path('health/', system_api.health_check, name='api_health'),
    path('csrf/', system_api.csrf_token, name='api_csrf'),

    # ========================================================================
    # PRODUCT ENDPOINTS
    # ========================================================================
    path('products/', products_api.product_list, name='api_product_list'),
    path('products/<int:product_id>/', products_api.product_detail, name='api_product_detail'),
    path('products/create/', products_api.product_create, name='api_product_create'),
    path('products/<int:product_id>/update/', products_api.product_update, name='api_product_update'),
    path('products/<int:product_id>/archive/', products_api.product_archive, name='api_product_archive'),
    path('products/<int:product_id>/unarchive/', products_api.product_unarchive, name='api_product_unarchive'),
    path('products/<int:product_id>/adjust-stock/', products_api.product_adjust_stock, name='api_product_adjust_stock'),

    # ========================================================================
    # ORDER ENDPOINTS
    # ========================================================================
    path('orders/', orders_api.order_list, name='api_order_list'),
    path('orders/<int:order_id>/', orders_api.order_detail, name='api_order_detail'),
    path('orders/create/', orders_api.order_create, name='api_order_create'),
    path('orders/<int:order_id>/mark-in-progress/', orders_api.order_mark_in_progress, name='api_order_mark_in_progress'),
    path('orders/<int:order_id>/finish/', orders_api.order_finish, name='api_order_finish'),
    path('orders/<int:order_id>/cancel/', orders_api.order_cancel, name='api_order_cancel'),

    # ========================================================================
    # PAYMENT ENDPOINTS
    # ========================================================================
    path('payments/', orders_api.payment_list, name='api_payment_list'),
    path('payments/<int:payment_id>/mark-success/', orders_api.payment_mark_success, name='api_payment_mark_success'),
    path('payments/<int:payment_id>/mark-failed/', orders_api.payment_mark_failed, name='api_payment_mark_failed'),

    # ========================================================================
    # KIOSK ENDPOINTS (Public)
    # ========================================================================
    path('kiosk/products/', kiosk_api.kiosk_products, name='api_kiosk_products'),
    path('kiosk/checkout/', kiosk_api.kiosk_checkout, name='api_kiosk_checkout'),
    path('kiosk/orders/<str:order_no>/status/', kiosk_api.kiosk_order_status, name='api_kiosk_order_status'),

    # ========================================================================
    # ANALYTICS ENDPOINTS
    # ========================================================================
    path('analytics/overview/', analytics_api.analytics_overview, name='api_analytics_overview'),
    path('analytics/sales-by-date/', analytics_api.analytics_sales_by_date, name='api_analytics_sales_by_date'),
    path('analytics/top-products/', analytics_api.analytics_top_products, name='api_analytics_top_products'),
    path('analytics/low-stock/', analytics_api.analytics_low_stock, name='api_analytics_low_stock'),
    path('analytics/payment-methods/', analytics_api.analytics_payment_methods, name='api_analytics_payment_methods'),
    path('analytics/order-status/', analytics_api.analytics_order_status, name='api_analytics_order_status'),

    # ========================================================================
    # AUDIT & ARCHIVE ENDPOINTS
    # ========================================================================
    path('audit/', system_api.audit_list, name='api_audit_list'),
    path('audit/<int:audit_id>/', system_api.audit_detail, name='api_audit_detail'),
    path('archive/', system_api.archive_list, name='api_archive_list'),
]
