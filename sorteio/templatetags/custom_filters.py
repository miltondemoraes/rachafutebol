from django import template

register = template.Library()

@register.filter
def avg_attr(queryset, attr):
    items = [getattr(item, attr) for item in queryset if hasattr(item, attr)]
    return sum(items) / len(items) if items else 0