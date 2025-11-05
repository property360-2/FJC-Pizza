from django.shortcuts import redirect
from django.urls import reverse, resolve
from django.contrib import messages


class RoleRequiredMiddleware:
    """
    Middleware to enforce role-based access control for protected URLs.

    Public URLs (no authentication required):
    - /auth/login/
    - /auth/logout/
    - /kiosk/ (all kiosk routes)
    - /api/kiosk/ (kiosk API routes)
    - /admin/ (Django admin has its own auth)

    ADMIN-only URLs:
    - /admin/products/
    - /admin/users/
    - /dashboard/
    - /audit/
    - /archive/
    - /api/users/
    - /api/analytics/

    ADMIN + CASHIER URLs:
    - /pos/
    - /api/orders/
    - /api/products/ (read-only for cashier)
    - /api/payments/
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # URL patterns that don't require authentication
        self.public_urls = [
            '/auth/login/',
            '/auth/logout/',
            '/auth/access-denied/',
            '/kiosk/',
            '/api/kiosk/',
            '/api/health',
            '/api/csrf',
            '/admin/',  # Django admin has its own auth
            '/static/',
            '/media/',
        ]

        # URL patterns that require ADMIN role only
        self.admin_only_urls = [
            '/admin/products/',
            '/admin/users/',
            '/dashboard/',
            '/audit/',
            '/archive/',
            '/api/users/',
            '/api/analytics/',
            '/api/audit/',
            '/api/archive/',
        ]

    def __call__(self, request):
        # Get the current URL path
        path = request.path

        # Check if URL is public (no auth required)
        if any(path.startswith(public_url) for public_url in self.public_urls):
            return self.get_response(request)

        # For protected URLs, check authentication
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in to continue.")
            return redirect(reverse('accounts:login'))

        # Check admin-only URLs
        if any(path.startswith(admin_url) for admin_url in self.admin_only_urls):
            if not request.user.is_admin():
                messages.error(request, "Access denied. Admin privileges required.")
                return redirect(reverse('accounts:access_denied'))

        # Allow request to proceed
        response = self.get_response(request)
        return response
