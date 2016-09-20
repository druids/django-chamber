from __future__ import unicode_literals

from django.utils.functional import SimpleLazyObject

from is_core.auth_token.middleware import TokenAuthenticationMiddlewares, get_user
from is_core.auth_token import utils
from is_core.auth_token.utils import dont_enforce_csrf_checks
from is_core.auth_token.models import Token
from is_core.utils import header_name_to_django
from is_core import config as is_core_config

from chamber.shortcuts import get_object_or_none
from chamber import config


def get_token(request):
    """
    Returns the token model instance associated with the given request token key.
    If no user is retrieved AnonymousToken is returned.
    """
    if not request.META.get(header_name_to_django(is_core_config.IS_CORE_AUTH_HEADER_NAME)) and config.CHAMBER_MULTIDOMAINS_OVERTAKER_AUTH_COOKIE_NAME:
        ovetaker_auth_token = request.COOKIES.get(config.CHAMBER_MULTIDOMAINS_OVERTAKER_AUTH_COOKIE_NAME)
        token = get_object_or_none(Token, key=ovetaker_auth_token, is_active=True)
        if utils.get_user_from_token(token).is_authenticated():
            return token

    return utils.get_token(request)


class MultiDomainsTokenAuthenticationMiddleware(TokenAuthenticationMiddlewares):
    def process_request(self, request):
        """
        Lazy set user and token
        """
        request.token = get_token(request)
        request.user = SimpleLazyObject(lambda: get_user(request))
        request._dont_enforce_csrf_checks = dont_enforce_csrf_checks(request)
