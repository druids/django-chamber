from django.core.exceptions import ImproperlyConfigured


class Domain:

    def __init__(self, name, protocol, hostname, urlconf, user_model, port=None):
        self.name = name
        self.protocol = protocol
        self.hostname = hostname
        self.urlconf = urlconf
        if port is None and protocol == 'http':
            self.port = 80
        elif port is None and protocol == 'https':
            self.port = 443
        elif port is None:
            raise ImproperlyConfigured('Port must be set')
        else:
            self.port = port
        self.user_model = user_model

    @property
    def url(self):
        return ('{}://{}'.format(self.protocol, self.hostname)
                if (self.protocol == 'http' and self.port == 80) or (self.protocol == 'https' and self.port == 443)
                else '{}://{}:{}'.format(self.protocol, self.hostname, self.port))

    @property
    def user_class(self):
        try:
            from django.apps import apps
            get_model = apps.get_model
        except ImportError:
            from django.db.models.loading import get_model

        return get_model(*self.user_model.split('.', 1))


def get_domain(site_id):
    from django.conf import settings

    if site_id in settings.DOMAINS:
        return settings.DOMAINS.get(site_id)
    else:
        raise ImproperlyConfigured('Domain with ID "{}" does not exists'.format(site_id))


def get_current_domain():
    from django.conf import settings

    return get_domain(settings.SITE_ID)


def get_user_class():
    return get_current_domain().user_class


def get_domain_choices():
    from django.conf import settings

    return [(key, domain.name) for key, domain in settings.DOMAINS.items()]
