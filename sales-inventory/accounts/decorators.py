from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse


def role_required(allowed_roles):
    """
    Decorator to restrict access based on user roles.

    Usage:
        @role_required(['ADMIN'])
        def admin_view(request):
            ...

        @role_required(['ADMIN', 'CASHIER'])
        def shared_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Check if user is authenticated
            if not request.user.is_authenticated:
                messages.warning(request, "Please log in to continue.")
                return redirect(reverse('accounts:login'))

            # Check if user has required role
            if request.user.role not in allowed_roles:
                messages.error(
                    request,
                    f"Access denied. This page requires one of the following roles: {', '.join(allowed_roles)}"
                )
                return redirect(reverse('accounts:access_denied'))

            # User has correct role, execute view
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
