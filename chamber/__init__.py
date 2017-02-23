# Apply patch only if django is installed
try:
    from django.core.exceptions import ImproperlyConfigured
    try:
        #from django.db import models  # NOQA
        from chamber.patch import *  # NOQA
    except ImproperlyConfigured:
        pass
except ImportError as ex:
    pass
