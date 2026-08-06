from django import template

register = template.Library()


@register.filter
def readable_name(value):
    """Turn 'light_armour' into 'Light Armour' (unlike |title, which leaves underscores alone)."""
    if not value:
        return value
    return str(value).replace("_", " ").replace("-", " ").title()
