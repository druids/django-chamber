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


def short_description(description):
    """
    Sets 'short_description' attribute (this attribute is used by list_display and formulars).
    """
    def decorator(func):
        func.short_description = description
        return func
    return decorator