from django.urls import path
from . import kiosk_views

urlpatterns = [
    path('', kiosk_views.kiosk_home, name='home'),
    path('cart/', kiosk_views.cart_view, name='cart'),
    path('checkout/', kiosk_views.checkout, name='checkout'),
    path('order/<str:order_number>/', kiosk_views.order_status, name='order_status'),
    path('add-to-cart/<int:product_id>/', kiosk_views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:product_id>/', kiosk_views.remove_from_cart, name='remove_from_cart'),
]
