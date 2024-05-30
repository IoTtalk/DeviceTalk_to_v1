from datetime import timedelta
import swapper

from authlib.integrations.requests_client import OAuth2Session
from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
)
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


from .settings import xtalk_settings

__all__ = [
    'AbstractAccessToken',
    'AbstractRefreshToken',
    'AbstractUser',
    'AccessToken',
    'RefreshToken',
    'UserManager',
]


# Set custom app prefix.
#
# Ref: https://github.com/openwisp/django-swappable-models#api-documentation
swapper.set_app_prefix('xtalk_account', 'xtalk')


class UserManager(BaseUserManager):
    def get_by_sub(self, sub: str):
        return self.get(sub=sub)

    def create_user(self, username: str, **kwargs):
        raise NotImplementedError('You can not create user')

    def create_superuser(self, username: str, **kwargs):
        raise NotImplementedError('You can not create superuser')


class AbstractUser(AbstractBaseUser):
    """
    Simplest user model for X-Talk project.

    This model inherits the `AbstractBaseUser` model provided by Django and it do have a
    password field. But since we are using OpenID Connect to outsource authentication
    process to an OpenID Provider, we can not get the password of an End-User so we
    need to set an unusable password on each End-User or database will complain
    (This has been implemented in the custom `save` method).

    Be caution, this model does not have any permission related information,
    e.g. superuser, staff.

    If your X-Talk needs to store permission-related information, you should consider using
    a custom user model which subclasses this class and the ``PermissionsMixin`` class
    provided by Django. For more information about ``PermissionsMixin``, please check it at:
    https://tinyurl.com/nbcrm366 (``PermissionsMixin``)

    Also, this example also uses the default authentication backend ``ModelBackend``, if you
    want more control about authentication behavior, consider using a customized one.

    Fields:

    - :attr:`sub`: The subject identifier of an end-user. It is a unique identifier of
                   of an end-user.
    - :attr:`username`: The username of an end-user provided by an OpenID Provider.
                         Be caution, this field is not guaranteed to be unique
                         since Relying Party can not know the deletion of an end-user
                         on an OpenID Provider.
    - :attr:`email`: The email address of an end-user provided by an OpenID Provider.
                      This field is neither guaranteed to be unique and it has the same
                      reason as the `username` field.
    - :attr:`created_at`: An end-user created time.
    - :attr:`updated_at`: An end-user updated time.
    - :attr:`last_login`: An end-user last login time.

    Notes for subclassing this class:

    - Do not remove any field defined in this class.
    - If you need to overwrite the `save` method, remember to call the same method defined
      the in parent class.
    """
    class Meta(AbstractBaseUser.Meta):
        # Ref: https://docs.djangoproject.com/en/3.2/topics/db/models/#abstract-base-classes
        abstract = True

    # Ref: https://tinyurl.com/ubsy2knn (USERNAME_FIELD)
    USERNAME_FIELD = 'sub'
    EMAIL_FIELD = 'email'

    sub = models.CharField(
        _('subject identifier'),
        max_length=255,
        unique=True
    )
    username = models.CharField(
        _('username'),
        max_length=100,
    )
    email = models.EmailField(
        _('email'),
    )
    created_at = models.DateTimeField(
        _('created time'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('updated time'),
        auto_now=True
    )

    objects = UserManager()

    def save(self, *args, **kwargs):
        """
        Since we use OpenID Connect to outsource authentication process to
        an OpenID Provider, it is impossible to get the raw password of an End-User,
        we need to mark an authenticated user with unusable password, or the
        database will complain.
        """
        self.set_unusable_password()

        return super().save(*args, **kwargs)


class AbstractRefreshToken(models.Model):
    """
    Simplest refresh token model for an X-Talk project.

    This model is an abstract class so you can subclass it.

    Fields:

    - :attr:`user_id`: The ID of the user where this refresh token belongs.
    - :attr:`token`: The refresh token.
    - :attr:`created_at`: A refresh token created time.
    - :attr:`updated_at`: A refresh token updated time.

    Attributes provided by foreign key:

    - :attr:`user`: The user instance where this refresh token belongs.

    Notes for subclassing this class:

    - Do not remove any field defined in this class.
    """
    class Meta:
        abstract = True

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)s',
        related_query_name='%(app_label)s_%(class)s'
    )
    token = models.TextField(_('refresh token'))
    created_at = models.DateTimeField(
        _('created time'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('updated time'),
        auto_now=True
    )


class AbstractAccessToken(models.Model):
    """
    Simplest access token model for an X-Talk project.

    This model is an abstract class so you can subclass it.

    Fields:

    - :attr:`user_id`: The ID of the user where this access token belongs.
    - :attr:`refresh_token_id`: The ID of the refresh token where the access token belongs.
    - :attr:`token`: The access token.
    - :attr:`expires_at`: An access token expired time.
    - :attr:`created_at`: An access token created time.
    - :attr:`updated_at`: An access token updated time.

    Attributes provided by foreign key:

    - :attr:`user`: The user instance where this access token belongs.
    - :attr:`refresh_token`: The refresh token instance where this access token belongs.

    Notes for subclassing this class:

    - Do not remove any field defined in this class.
    """
    class Meta:
        abstract = True

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)ss',
        related_query_name='%(app_label)s_%(class)ss'
    )
    refresh_token = models.ForeignKey(
        swapper.get_model_name('xtalk_account', 'RefreshToken'),
        on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)ss',
        related_query_name='%(app_label)s_%(class)ss'
    )

    token = models.TextField(_('access token'))
    expires_at = models.DateTimeField(_('expired time'))
    created_at = models.DateTimeField(
        _('created time'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('updated time'),
        auto_now=True
    )


class OAuthState(models.Model):
    state = models.CharField(
        max_length=100,
        blank=False
    )
    redirect_query = models.CharField(
        max_length=500,
        blank=False
    )

    def __str__(self):
        return self.state


class User(AbstractUser):
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin


class AccessToken(AbstractAccessToken):
    class Meta(AbstractAccessToken.Meta):
        verbose_name = 'Access token'
        verbose_name_plural = 'Access tokens'

    dummy_field = models.TextField(default='When the is enthusiasm is gone')

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    def refresh(self):
        oauth2_client = OAuth2Session(
            client_id=xtalk_settings.OAUTH2_CLIENT_ID,
            client_secret=xtalk_settings.OAUTH2_CLIENT_SECRET,
            scope='openid'
        )

        token_response = oauth2_client.refresh_token(
            url=xtalk_settings.OAUTH2_TOKEN_ENDPOINT,
            refresh_token=self.refresh_token.token)
        self.refresh_token.token = token_response.get('refresh_token')

        # Create a new access token record
        AccessToken.objects.create(
            token=token_response.get('access_token'),
            expires_at=(
                timezone.now()
                + timedelta(seconds=token_response.get('expires_in', 0))
            ),
            user=self.user,
            refresh_token=self.refresh_token
        )


class RefreshToken(AbstractRefreshToken):
    class Meta(AbstractRefreshToken.Meta):
        verbose_name = 'Refresh token'
        verbose_name_plural = 'Refresh tokens'
