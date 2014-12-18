from django.conf import settings


MAX_FILE_UPLOAD_SIZE = getattr(settings, 'MAX_FILE_UPLOAD_SIZE', 20)
