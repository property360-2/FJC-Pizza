from __future__ import annotations

from functools import wraps
from typing import Sequence

from django.contrib.auth.decorators import login_required


def role_required(roles: Sequence[str]):
    """Ensure the current user matches one of the allowed roles."""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            return view_func(request, *args, **kwargs)

        _wrapped_view = login_required(_wrapped_view)
        setattr(_wrapped_view, "required_roles", list(roles))
        return _wrapped_view

    return decorator
