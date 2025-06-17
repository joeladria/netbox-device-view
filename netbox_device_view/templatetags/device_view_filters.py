from django import template

register = template.Library()

@register.filter(name='truncate_hostname_prefix')
def truncate_hostname_prefix(value):
    if not isinstance(value, str):
        return value
    parts = value.split('-', 1)
    if len(parts) > 1:
        return parts[1]  # Return the part after the first dash
    return value     # Return the original string if no dash is found
