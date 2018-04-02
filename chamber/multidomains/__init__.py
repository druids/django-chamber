# The active translations are stored by threadid to make them thread local.
_active = local()


def is_auto_registration_active():
    return getattr(_active, 'auto_registration', True)


def activate_auto_registration():
    if hasattr(_active, 'auto_registration'):
        del _active.auto_registration


def deactivate_auto_registration():
    _active.auto_registration = False
