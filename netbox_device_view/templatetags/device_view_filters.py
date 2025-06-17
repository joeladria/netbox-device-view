from django import template

register = template.Library()

@register.filter(name='get_hostname_last_segment')
def get_hostname_last_segment(value):
    if not isinstance(value, str):
        return value
    parts = value.split('-')
    if parts: # Check if parts is not empty
        return parts[-1]  # Return the last segment
    return value     # Return the original string if split results in empty or no dash
