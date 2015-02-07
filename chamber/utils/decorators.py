class classproperty(object):

    def __init__(self, fget):
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


def singleton(klass):

    instances = {}

    def getinstance(*args, **kwargs):
        if klass not in instances:
            instances[klass] = klass(*args, **kwargs)
        return instances[klass]
    return getinstance

