from urllib.parse import urlparse

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured


class Domain:

    def __init__(self, name, urlconf=None, user_model=None, url=None, protocol=None, hostname=None, port=None):
        self.name = name
        self.protocol = protocol
        self.hostname = hostname
        self.urlconf = urlconf
        self.port = port

        if url:
            parsed_url = urlparse(url)
            self.protocol, self.hostname, self.port = parsed_url.scheme, parsed_url.hostname, parsed_url.port

        if self.protocol is None:
            raise ImproperlyConfigured('protocol must be set')
        if self.hostname is None:
            raise ImproperlyConfigured('hostname must be set')

        if self.port is None:
            if self.protocol == 'http':
                self.port = 80
            elif self.protocol == 'https':
                self.port = 443
            else:
                raise ImproperlyConfigured('port must be set')
        self.user_model = user_model

    @property
    def url(self):
        return ('{}://{}'.format(self.protocol, self.hostname)
                if (self.protocol == 'http' and self.port == 80) or (self.protocol == 'https' and self.port == 443)
                else '{}://{}:{}'.format(self.protocol, self.hostname, self.port))

    @property
    def user_class(self):
        return apps.get_model(*self.user_model.split('.', 1))


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
