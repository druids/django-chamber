from __future__ import unicode_literals

from django.utils.functional import SimpleLazyObject
from django.contrib.auth.models import AnonymousUser

from is_core.auth_token.utils import get_user as origin_get_user, dont_enforce_csrf_checks
from is_core.auth_token.middleware import TokenAuthenticationMiddlewares, get_token

from chamber.shortcuts import get_object_or_none

from chamber.multidomains.domain import get_current_domain


def get_user(request):
    if not hasattr(request, '_cached_user'):
        user = origin_get_user(request)
        if user.is_authenticated():
            child_user = get_object_or_none(
                get_current_domain().user_class, pk=user.pk
            )
            if child_user is not None:
                user = child_user
            else:
                user = AnonymousUser()
        request._cached_user = user
    return request._cached_user


class MultiDomainsTokenAuthenticationMiddleware(TokenAuthenticationMiddlewares):
    def process_request(self, request):
        """
        Lazy set user and token
        """
        request.token = SimpleLazyObject(lambda: get_token(request))
        request.user = SimpleLazyObject(lambda: get_user(request))
        request._dont_enforce_csrf_checks = dont_enforce_csrf_checks(request)
