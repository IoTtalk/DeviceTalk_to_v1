from datetime import timedelta
import logging
import swapper

from authlib.integrations.django_client import OAuth
from authlib.integrations.requests_client import OAuth2Session
from django.conf import settings
from django.contrib.auth import (
    get_user_model,
    login,
)
from django.contrib.auth.views import LogoutView as django_LogoutView
from django.db import transaction
from django.http import QueryDict
from django.shortcuts import (
    redirect,
    render,
)
from django.utils import timezone
from django.utils.translation import gettext
from django.urls import (
    reverse as reverse_url,
    reverse_lazy as reverse_url_lazy,
)
from django.views.generic.base import View
from requests import exceptions as requests_exceptions

from .models import OAuthState
from .settings import xtalk_settings
from .utils import get_url_query

logger = logging.getLogger(__name__)

TEMPLATE_DIRECTORY_PREFIX = 'xtalk'


__all__ = [
    'AuthCallbackView',
    'AuthRedirectionView',
    'LogoutView',
]

oauth2_client = OAuth()
oauth2_client.register(
    name='iottalk',
    client_id=xtalk_settings.OAUTH2_CLIENT_ID,
    client_secret=xtalk_settings.OAUTH2_CLIENT_SECRET,
    server_metadata_url=xtalk_settings.OIDC_DISCOVERY_ENDPOINT,
    client_kwargs={'scope': 'openid', }
)


class AuthRedirectionView(View):
    http_method_names = [
        'get',
    ]

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # Redirect a user to the index page if he/she already logs in
            return redirect(reverse_url('my_admin:index_endpoint'))

        # Redirect a user to the authorization endpoint
        # Ref: https://docs.authlib.org/en/latest/client/oauth2.html#redirect-to-authorization-endpoint # noqa: E501
        authorize_redirect_object = oauth2_client.iottalk.authorize_redirect(
            request,
            redirect_uri=xtalk_settings.OAUTH2_REDIRECT_URI
        )
        query_string = get_url_query(authorize_redirect_object.url)
        with transaction.atomic():
            OAuthState.objects.update_or_create(
                state=query_string['state'][0],
                redirect_query=request.GET.urlencode()
            )
        return authorize_redirect_object


class LogoutView(django_LogoutView):
    http_method_names = [
        'post',
    ]
    next_page = settings.LOGOUT_REDIRECT_URL or reverse_url_lazy('my_admin:index_endpoint')

    def dispatch(self, request, *args, **kwargs):
        """
        Override the default dispath method so we can retrieve the access token id
        stored in the session before session is flushed.

        After we have access token id, we can query the database and then and revoke
        that access token.
        """
        if not xtalk_settings.REVOKE_ACCESSTOKEN_WHEN_LOGOUT:
            return super().dispatch(request, *args, **kwargs)

        try:
            access_token_record = \
                swapper.load_model('xtalk_account', 'AccessToken').objects.get(
                    id=request.session.pop('access_token_id', None)
                )
        except swapper.load_model('xtalk_account', 'AccessToken').DoesNotExist:
            # Just call parent post method if that access token does not exist
            return super().post(request, *args, **kwargs)

        # Create an OAuth 2.0 client provided Authlib
        #
        # Ref: https://tinyurl.com/2rs2594h (OAuth2Session documentation)
        oauth2_client = OAuth2Session(
            client_id=xtalk_settings.OAUTH2_CLIENT_ID,
            client_secret=xtalk_settings.OAUTH2_CLIENT_SECRET,
            revocation_endpoint_auth_method='client_secret_basic'
        )

        try:
            # Revoke the access token
            response = oauth2_client.revoke_token(
                xtalk_settings.OAUTH2_REVOCATION_ENDPOINT,
                token=access_token_record.token,
                token_type_hint='access_token'
            )
            response.raise_for_status()
        except requests_exceptions.Timeout:
            logger.error('Revoke an access token failed due to request timeout')
        except requests_exceptions.TooManyRedirects:
            logger.error('Revoke an access token failed due to too many redirects')
        except (requests_exceptions.HTTPError, requests_exceptions.RequestException) as e:
            logger.error('Revoke an access token failed, %s', e)
        finally:
            # Delete the access token record no matter whether access token revocation is
            # success or not
            access_token_record.delete()

        return super().dispatch(request, *args, **kwargs)


class AuthCallbackView(View):
    http_method_names = [
        'get',
    ]

    def get(self, request, *args, **kwargs):
        # Check if a request has `code` query parameter
        if not request.GET.get('code'):
            # Redirect a user to the index page if he/she already logs in
            if request.user.is_authenticated:
                return redirect(reverse_url('my_admin:index_endpoint'))

            # Redirect a user to the authorization endpoint
            return oauth2_client.iottalk.authorize_redirect(
                request,
                redirect_uri=xtalk_settings.OAUTH2_REDIRECT_URI
            )

        try:
            # Exchange access token with an authorization code with token endpoint
            #
            # Ref: https://docs.authlib.org/en/stable/client/frameworks.html#id1
            token_response = oauth2_client.iottalk.authorize_access_token(request)

            # Parse the received ID token
            user_info = oauth2_client.iottalk.parse_id_token(request, token_response)
        except Exception:
            logger.exception('Exception')

            return render(
                request,
                '{}/error.html'.format(TEMPLATE_DIRECTORY_PREFIX),
                {'error_reason': gettext('Something is broken...'), }
            )

        with transaction.atomic():
            # Use the sub parameter value in the ID token to get an existing user or
            # create a new user.

            # Set first user as admin.
            is_admin = (
                get_user_model()
                .objects
                .filter(is_admin=True)
                .exclude(username=user_info.get('preferred_username', ''))
                .count() == 0
            )

            user_record, _created = get_user_model().objects.update_or_create(
                sub=user_info.get('sub'),
                defaults={
                    'username': user_info.get('preferred_username', ''),
                    'email': user_info.get('email', ''),
                    'is_admin': is_admin,
                }
            )

            # Get or create a refresh token object
            refresh_token_record, refresh_token_record_created = \
                swapper.load_model('xtalk_account', 'RefreshToken').objects.get_or_create(
                    user=user_record,
                    defaults={
                        'token': token_response.get('refresh_token', ''),
                    }
                )

            # If a refresh token object exists and there is another refresh token
            # in the received token, it means the old refresh token should be replaced with
            # a new one.
            if not refresh_token_record_created and token_response.get('refresh_token'):
                refresh_token_record.token = token_response.get('refresh_token')
                refresh_token_record.save()

            # Save a received access token in the database
            access_token_record = \
                swapper.load_model('xtalk_account', 'AccessToken').objects.create(
                    token=token_response.get('access_token'),
                    user=user_record,
                    refresh_token=refresh_token_record,
                    expires_at=(
                        timezone.now()
                        + timedelta(seconds=token_response.get('expires_in', 0))
                    )
                )

            state_record = OAuthState.objects.get(state=request.GET.get('state'))
            query_string = state_record.redirect_query
            state_record.delete()

        request.session['access_token_id'] = access_token_record.id

        # Login an user manually
        login(request, user_record)

        next_url = QueryDict(query_string).get('next')
        if next_url:
            return redirect(next_url)

        return redirect(reverse_url('my_admin:index_endpoint'))
