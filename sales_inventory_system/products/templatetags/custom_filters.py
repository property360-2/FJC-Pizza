"""
Custom template filters for products app
"""
from django import template

register = template.Library()


@register.filter
def multiply(value, arg):
    """Multiply value by arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def divide(value, arg):
    """Divide value by arg"""
    try:
        divisor = float(arg) if arg else 1
        return float(value) / divisor if divisor != 0 else 0
    except (ValueError, TypeError):
        return 0


@register.filter
def as_float(value):
    """Convert value to float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0
