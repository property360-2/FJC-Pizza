from __future__ import annotations

from typing import Iterable

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse


class RoleRequiredMiddleware:
    """Intercepts requests to ensure the user has the required role for a view."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        return self.get_response(request)

    def process_view(self, request: HttpRequest, view_func, view_args, view_kwargs):
        required_roles: Iterable[str] | None = getattr(view_func, "required_roles", None)

        if required_roles is None and hasattr(view_func, "view_class"):
            required_roles = getattr(view_func.view_class, "required_roles", None)

        if not required_roles:
            return None

        if not request.user.is_authenticated:
            return redirect("accounts:login")

        if request.user.role not in required_roles:
            return redirect(reverse("accounts:access_denied"))

        return None
