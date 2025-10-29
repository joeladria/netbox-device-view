from django import template

register = template.Library()

@register.filter(name='get_hostname_last_segment')
def get_hostname_last_segment(value):
    if not isinstance(value, str):
        return value
    parts = value.split('-')
    if parts: 
        return parts[-1] 
    return value
