from django import template

register = template.Library()

@register.filter
def format_price(value):
    """Format number with commas"""
    if value is None:
        return "0"
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return str(value)

