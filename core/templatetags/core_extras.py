from django import template
import json

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Safely get an item from a dictionary."""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def to_json(value):
    """Serialize a dictionary or list to JSON string."""
    try:
        return json.dumps(value)
    except Exception:
        return "null"
