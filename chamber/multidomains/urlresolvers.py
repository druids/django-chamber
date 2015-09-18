try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

from django.conf import settings
from django.core import urlresolvers


def reverse(viewname, site_id=None, add_domain=False, urlconf=None, args=None, kwargs=None, prefix=None,
            current_app=None, qs_kwargs=None):
    urlconf = (settings.DOMAINS.get(site_id).urlconf
               if site_id is not None and urlconf is None and settings.SITE_ID != site_id
               else urlconf)
    site_id = settings.SITE_ID if site_id is None else site_id
    domain = settings.DOMAINS.get(site_id).url if add_domain else ''
    qs = '?%s' % urlencode(qs_kwargs) if qs_kwargs else ''
    return ''.join((domain, urlresolvers.reverse(viewname, urlconf, args, kwargs, prefix, current_app), qs))