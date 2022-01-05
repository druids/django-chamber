# Apply patch only if django is installed
try:
    from django.core.exceptions import ImproperlyConfigured
    try:
        from chamber.patch import *  # NOQA
    except ImproperlyConfigured:
        pass
except ImportError:
    pass
