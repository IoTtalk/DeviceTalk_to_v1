from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse as reverse_url
from urllib.parse import urlparse, parse_qs, urlencode
from django.core.handlers.wsgi import WSGIRequest
from django.contrib.auth import get_user_model

__all__ = [
    'get_url_query',
    'check_login'
]


def get_url_query(url):
    parsed_url = urlparse(url)
    return parse_qs(parsed_url.query)


# This is a decorator function
def check_login(func):
    def wrap(*args, **kwargs):
        request = None
        for arg in args:
            if isinstance(arg, WSGIRequest):
                request = arg
                break
#        if request.user.is_authenticated:
        if 1:
            return func(*args, **kwargs)
        else:
            query_string = urlencode({'next': request.path})
            return redirect(
                '%s?%s' % (
                    reverse_url('xtalk_account:auth_redirect_endpoint'),
                    query_string
                )
            )
    return wrap


# This is a decorator function
def check_is_admin(func):
    def wrap(*args, **kwargs):
        request = None
        for arg in args:
            if isinstance(arg, WSGIRequest):
                request = arg
                break


        return func(*args, **kwargs)


        if request.user.is_authenticated:
            user_object = get_user_model().objects.get(username=request.user.username)
            if user_object.is_admin:
                return func(*args, **kwargs)
        else:
            return JsonResponse(
                {'state': 'Invalid user.'},
                status=400
            )
    return wrap
