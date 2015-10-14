from functools import wraps

from django.conf import settings
from django.utils import translation


class classproperty(object):

    def __init__(self, fget):
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


def singleton(klass):
    """
    Create singleton from class
    """
    instances = {}

    def getinstance(*args, **kwargs):
        if klass not in instances:
            instances[klass] = klass(*args, **kwargs)
        return instances[klass]
    return getinstance

def translation_activate_block(function=None, language=None):
    """
    Activate language only for one method or function
    """

    def _translation_activate_block(function):
        def _decorator(*args, **kwargs):
            tmp_language = translation.get_language()
            try:
                translation.activate(language or settings.LANGUAGE_CODE)
                return function(*args, **kwargs)
            finally:
                translation.activate(tmp_language)
        return wraps(function)(_decorator)

    if function:
        return _translation_activate_block(function)
    else:
        return _translation_activate_block
