from django import template

register = template.Library()


@register.filter
def div(value, arg):
    """Divide the value by the argument"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0


@register.filter(name='subtract')
def subtract(value, arg):
    return value - arg