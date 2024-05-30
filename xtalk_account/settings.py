import itertools

from django.conf import settings as django_settings

from .exceptions import (
    XTalkTemplateImproperlyConfigured,
)


__all__ = [
    'xtalk_settings',
]


_SETTING_PREFIX = 'XTALK'


OPTIONAL_SETTINGS = {
    'REVOKE_ACCESSTOKEN_WHEN_LOGOUT': True,
}

# TODO: Consider adding validator to validate the setting value
REQUIRED_SETTINGS = [
    'OAUTH2_REDIRECT_URI',
    'OAUTH2_CLIENT_ID',
    'OAUTH2_CLIENT_SECRET',
    'OAUTH2_REVOCATION_ENDPOINT',
    'OAUTH2_TOKEN_ENDPOINT',
    'OIDC_DISCOVERY_ENDPOINT',
]


class XTalkSettings:
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = super().__new__(cls)

        return cls._instance

    def __getattr__(self, attribute):
        s = '{}_{}'.format(_SETTING_PREFIX, attribute)

        if attribute not in self._settings:
            raise AttributeError('Invalid setting: {}'.format(s))

        return getattr(django_settings, s, self._optional_settings.get(attribute))

    def __init__(self, required_settings: list, optional_settings: dict):
        for required_setting in required_settings:
            s = '{}_{}'.format(_SETTING_PREFIX, required_setting)

            if not getattr(django_settings, s, None):
                raise XTalkTemplateImproperlyConfigured(
                    '{} setting must be set'.format(s)
                )

        self._settings = list(
            itertools.chain(required_settings, [s for s in optional_settings.keys()])
        )
        self._optional_settings = optional_settings


xtalk_settings = XTalkSettings(REQUIRED_SETTINGS, OPTIONAL_SETTINGS)
