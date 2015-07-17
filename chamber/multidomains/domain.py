class Domain(object):

    def __init__(self, name, protocol, hostname, urlconf, user_model, port=80):
        self.name = name
        self.protocol = protocol
        self.hostname = hostname
        self.urlconf = urlconf
        self.port = port
        self.user_model = user_model

    @property
    def url(self):
        if self.port == 80:
            return '%s://%s' % (self.protocol, self.hostname)
        else:
            return '%s://%s:%s' % (self.protocol, self.hostname, self.port)

    @property
    def user_class(self):
        from django.apps import apps

        return apps.get_model(*self.user_model.split('.', 1))


def get_current_domain():
    from django.conf import settings

    return settings.DOMAINS.get(settings.SITE_ID)


def get_user_class():
    return get_current_domain().user_class


def get_domain_choices():
    from django.conf import settings

    return [(key, domain.name) for key, domain in settings.DOMAINS.items()]
