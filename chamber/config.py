from django.conf import settings


CHAMBER_MAX_FILE_UPLOAD_SIZE = getattr(settings, 'CHAMBER_MAX_FILE_UPLOAD_SIZE', 20)
CHAMBER_MULTIDOMAINS_OVERTAKER_AUTH_COOKIE_NAME = getattr(settings, 'CHAMBER_MULTIDOMAINS_OVERTAKER_AUTH_COOKIE_NAME',
                                                          None)
