from django.conf import settings as django_settings


DEFAULTS = {
    'MAX_FILE_UPLOAD_SIZE': 20,
    'MULTIDOMAINS_OVERTAKER_AUTH_COOKIE_NAME': None,
    'DEFAULT_IMAGE_ALLOWED_CONTENT_TYPES': {'image/jpeg', 'image/png', 'image/gif'},
    'PRIVATE_S3_STORAGE_URL_EXPIRATION': 3600,
    'AWS_S3_ON': getattr(django_settings, 'AWS_S3_ON', False),
    'AWS_REGION': getattr(django_settings, 'AWS_REGION', None),
}


class Settings:

    def __getattr__(self, attr):
        if attr not in DEFAULTS:
            raise AttributeError('Invalid CHAMBER setting: "{}"'.format(attr))

        default = DEFAULTS[attr]
        return getattr(django_settings, 'CHAMBER_{}'.format(attr), default(self) if callable(default) else default)


settings = Settings()
