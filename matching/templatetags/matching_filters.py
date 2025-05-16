from django import template
from itertools import zip_longest

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using the key"""
    return dictionary.get(key)

@register.filter
def zip(a, b):
    """Zip two lists together"""
    return list(zip_longest(a, b, fillvalue=None))

@register.filter
def zip_lists(a, b):
    """Zip two lists together"""
    if a is None or b is None:
        return []
    return zip(a, b)

@register.filter
def split(value, arg):
    """Split the value by the argument"""
    return value.split(arg)

@register.filter
def cut(value, arg):
    """Remove the argument from the value"""
    return value.replace(arg, '')

@register.filter
def get_item(lst, index):
    """Get item from list by index"""
    try:
        return lst[index]
    except:
        return None

@register.filter
def get_attr(obj, attr):
    """Get attribute from object"""
    try:
        return getattr(obj, attr)
    except:
        return None 