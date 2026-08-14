from django import template

register = template.Library()

@register.filter(name='split')
def split(value, arg):
    """Splits string by delimiter."""
    if not value:
        return []
    return [item.strip() for item in value.split(arg)]


@register.filter(name='get_item')
def get_item(dictionary, key):
    """Gets an item from a dictionary or dict-like object using bracket indexing."""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.filter(name='get_attr')
def get_attr(obj, attr_name):
    """Gets an attribute from an object."""
    if obj and hasattr(obj, attr_name):
        return getattr(obj, attr_name)
    return None
