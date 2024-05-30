from django import template
from libgravatar import Gravatar


register = template.Library()


@register.simple_tag
def gravatar_url(email: str, **kwargs):
    return Gravatar(email).get_image(**kwargs)
