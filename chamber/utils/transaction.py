import logging

from collections import OrderedDict

from django.conf import settings
from django.db import transaction, DEFAULT_DB_ALIAS
from django.db.transaction import get_connection
from django.utils.decorators import ContextDecorator


logger = logging.getLogger(__name__)


def atomic(func):
    """
    Decorator helper that overrides django atomic decorator and automatically adds create revision.
    """
    try:
        from reversion.revisions import create_revision

        return transaction.atomic(create_revision()(func))
    except ImportError:
        return transaction.atomic(func)


class TransactionSignalsContext:
    """
    Context object that stores handlers and call it after successful pass trough surrounded code block
    with "transaction_signals decorator. Handlers can be unique or standard. Unique handlers are registered
    and executed only once.
    """

    def __init__(self):
        self._unique_handlers = OrderedDict()
        self._handlers = []

    def register(self, handler):
        if getattr(handler, 'is_unique', False):
            if hash(handler) in self._unique_handlers:
                self._unique_handlers.get(hash(handler)).join(handler)
            else:
                self._unique_handlers[hash(handler)] = handler
                self._handlers.append(handler)
        else:
            self._handlers.append(handler)

    def handle_all(self):
        for handler in self._handlers:
            handler()

    def join(self, transaction_signals_context):
        for handler in transaction_signals_context._handlers:
            self.register(handler)


class TransactionSignals(ContextDecorator):
    """
    Context decorator that supports usage python keyword "with".
    Decorator that adds transaction context to the connection on input.
    Finally handlers are called on the output.
    """

    def __init__(self, using):
        self.using = using

    def __enter__(self):
        connection = get_connection(self.using)

        if not hasattr(connection, 'transaction_signals_context_list'):
            connection.transaction_signals_context_list = []

        connection.transaction_signals_context_list.append(TransactionSignalsContext())

    def __exit__(self, exc_type, exc_value, traceback):
        connection = get_connection(self.using)
        transaction_signals_context = connection.transaction_signals_context_list.pop()
        if not exc_value:
            if len(connection.transaction_signals_context_list) == 0:
                transaction_signals_context.handle_all()
            else:
                connection.transaction_signals_context_list[-1].join(transaction_signals_context)


def on_success(handler, using=None):
    """
    Register a handler or a function to be called after successful code pass.
    If transaction signals are not active the handler/function is called immediately.
    :param handler: handler or function that will be called.
    :param using: name of the database
    """

    connection = get_connection(using)
    if getattr(connection, 'transaction_signals_context_list', False):
        connection.transaction_signals_context_list[-1].register(handler)
    else:
        if settings.DEBUG:
            logger.warning(
                'For on success signal should be activated transaction signals via transaction_signals decorator.'
                'Function is called immediately now.'
            )
        handler()


def transaction_signals(using=None):
    """
    Decorator that adds transaction context to the connection on input.
    Finally handlers are called on the output.
    :param using: name of the database
    """
    if callable(using):
        return TransactionSignals(DEFAULT_DB_ALIAS)(using)
    else:
        return TransactionSignals(using)


def atomic_with_signals(func):
    """
    Atomic decorator with transaction signals.
    """
    try:
        from reversion.revisions import create_revision

        return transaction.atomic(create_revision()(transaction_signals(func)))
    except ImportError:
        return transaction.atomic(transaction_signals(func))


class OnSuccessHandler:
    """
    Handler class that is used for performing on success operations.
    """

    is_unique = False

    def __init__(self, using=None, **kwargs):
        self.kwargs = kwargs
        on_success(self, using=using)

    def __call__(self):
        self.handle(**self.kwargs)

    def handle(self, **kwargs):
        """
        There should be implemented handler operations.
        :param kwargs: input data that was send during hanlder creation.
        """
        raise NotImplementedError


class OneTimeOnSuccessHandler(OnSuccessHandler):
    """
    One time handler class that is used for performing on success operations.
    Handler is called only once, but data of all calls are stored inside list (kwargs_list).
    """

    is_unique = True

    def __init__(self, using=None, **kwargs):
        self.kwargs_list = (kwargs,)
        on_success(self, using=using)

    def join(self, handler):
        """
        Joins two unique handlers.
        """
        self.kwargs_list += handler.kwargs_list

    def _get_unique_id(self):
        """
        Unique handler must be identified with some was
        :return:
        """
        return None

    def __hash__(self):
        return hash((self.__class__, self._get_unique_id()))

    def __call__(self):
        self.handle(self.kwargs_list)

    def handle(self, kwargs_list):
        raise NotImplementedError


class InstanceOneTimeOnSuccessHandler(OneTimeOnSuccessHandler):
    """
    Use this class to create handler that will be unique per instance and will be called only once per instance.
    """

    def _get_instance(self):
        instance = self.kwargs_list[0]['instance']
        instance.refresh_from_db()
        return instance

    def _get_unique_id(self):
        instance = self.kwargs_list[0]['instance']
        return hash((instance.__class__, instance.pk))
