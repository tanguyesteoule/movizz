from django import template

register = template.Library()

@register.filter
def keyvalue(dict, key):
    return dict[key]

@register.filter
def index(indexable, i):
    return indexable[i]