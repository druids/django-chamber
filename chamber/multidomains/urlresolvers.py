from urllib.parse import urlencode

from django.conf import settings
from django.urls import reverse as django_reverse



def reverse(viewname, site_id=None, add_domain=False, urlconf=None, args=None, kwargs=None, current_app=None,
            qs_kwargs=None):
    from .domain import get_domain

    urlconf = (get_domain(site_id).urlconf
               if site_id is not None and urlconf is None and settings.SITE_ID != site_id
               else urlconf)
    site_id = settings.SITE_ID if site_id is None else site_id
    domain = get_domain(site_id).url if add_domain else ''
    qs = '?{}'.format(urlencode(qs_kwargs)) if qs_kwargs else ''
    return ''.join((domain, django_reverse(viewname, urlconf, args, kwargs, current_app), qs))
