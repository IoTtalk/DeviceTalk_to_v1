from django.urls import path

from .views import (
    AuthCallbackView,
    AuthRedirectionView,
    LogoutView,
)

app_name = 'xtalk_account'

urlpatterns = [
    path('auth', AuthRedirectionView.as_view(), name='auth_redirect_endpoint'),
    path(
        'auth/callback',
        AuthCallbackView.as_view(),
        name='oauth2_redirect_endpoint'
    ),
    path('logout', LogoutView.as_view(), name='logout_endpoint'),
]
