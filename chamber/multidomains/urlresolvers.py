from urllib.parse import urlencode

from django.conf import settings

try:
    from django.core.urlresolvers import reverse as django_reverse
except ImportError:
    from django.urls import reverse as django_reverse

from chamber.multidomains import deactivate_auto_registration, activate_auto_registration


def reverse(viewname, site_id=None, add_domain=False, urlconf=None, args=None, kwargs=None, current_app=None,
            qs_kwargs=None):
    from .domain import get_domain

    try:
        deactivate_auto_registration()
        urlconf = (get_domain(site_id).urlconf
                   if site_id is not None and urlconf is None and settings.SITE_ID != site_id
                   else urlconf)
        site_id = settings.SITE_ID if site_id is None else site_id
        domain = get_domain(site_id).url if add_domain else ''
        qs = '?{}'.format(urlencode(qs_kwargs)) if qs_kwargs else ''
        return ''.join((domain, django_reverse(viewname, urlconf, args, kwargs, current_app), qs))
    finally:
        activate_auto_registration()
