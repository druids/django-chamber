from django.utils.functional import SimpleLazyObject

from auth_token import utils  # pylint: disable=E0401
from auth_token.config import settings as auth_token_settings  # pylint: disable=E0401
from auth_token.middleware import TokenAuthenticationMiddleware, get_user  # pylint: disable=E0401
from auth_token.models import AuthorizationToken  # pylint: disable=E0401
from auth_token.utils import dont_enforce_csrf_checks, header_name_to_django  # pylint: disable=E0401

from chamber.config import settings
from chamber.shortcuts import get_object_or_none


def get_token(request):
    """
    Returns the token model instance associated with the given request token key.
    If no user is retrieved AnonymousToken is returned.
    """
    if (not request.META.get(header_name_to_django(auth_token_settings.HEADER_NAME))
            and settings.MULTIDOMAINS_OVERTAKER_AUTH_COOKIE_NAME):
        ovetaker_auth_token = request.COOKIES.get(settings.MULTIDOMAINS_OVERTAKER_AUTH_COOKIE_NAME)
        token = get_object_or_none(AuthorizationToken, key=ovetaker_auth_token, is_active=True)
        if utils.get_user_from_token(token).is_authenticated:
            return token

    return utils.get_token(request)


class MultiDomainsTokenAuthenticationMiddleware(TokenAuthenticationMiddleware):

    def process_request(self, request):
        """
        Lazy set user and token
        """
        request.token = get_token(request)
        request.user = SimpleLazyObject(lambda: get_user(request))
        request._dont_enforce_csrf_checks = dont_enforce_csrf_checks(request)  # pylint: disable=W0212
