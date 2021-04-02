from django.db import transaction
from django.db import connections
from django.urls import get_resolver, set_urlconf

from chamber.utils.transaction import transaction_signals


def get_view_from_request_or_none(request):
    try:
        if hasattr(request, 'urlconf'):
            urlconf = request.urlconf
            set_urlconf(urlconf)
            resolver = get_resolver(urlconf)
        else:
            resolver = get_resolver()
        return resolver.resolve(request.path_info)
    except Resolver404:
        return None


class TransactionSignalsMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        get_response = self.get_response

        non_atomic_requests = getattr(get_view_from_request_or_none(request), '_non_atomic_requests', set())
        for db in connections.all():
            if db.settings_dict.get('CHAMBER_ATOMIC_REQUESTS', False) and db.alias not in non_atomic_requests:
                get_response = transaction.atomic(using=db.alias)(
                    transaction_signals(using=db.alias)(
                        get_response
                    )
                )
        return get_response(request)

