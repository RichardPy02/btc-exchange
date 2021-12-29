from django import template

register = template.Library()

@register.simple_tag
def mongo_id(doc):
    print(doc.objects.get("_id"))
    return doc.trader_id