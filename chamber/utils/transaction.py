from django.db import transaction


def atomic(func):
    try:
        from reversion.revisions import create_revision

        return transaction.atomic(create_revision()(func))
    except ImportError:

        return transaction.atomic(func)
