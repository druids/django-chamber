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
    Context object that stores callable and call it after successful pass trough surrounded code block
    with "transaction_signals decorator. Handlers can be unique or standard. Unique callable are registered
    and executed only once.
    """

    def __init__(self):
        self._unique_callable = OrderedDict()
        self._callable_list = []

    def register(self, callable):
        if isinstance(callable, UniqueOnSuccessCallable):
            if hash(callable) in self._unique_callable:
                self._unique_callable.get(hash(callable)).join(callable)
            else:
                self._unique_callable[hash(callable)] = callable
                self._callable_list.append(callable)
        else:
            self._callable_list.append(callable)

    def handle_all(self):
        for callable in self._callable_list:
            callable()

    def join(self, transaction_signals_context):
        for callable in transaction_signals_context._callable_list:
            self.register(callable)


class TransactionSignals(ContextDecorator):
    """
    Context decorator that supports usage python keyword "with".
    Decorator that adds transaction context to the connection on input.
    Finally callables are called on the output.
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


def on_success(callable, using=None):
    """
    Register a callable or a function to be called after successful code pass.
    If transaction signals are not active the callable/function is called immediately.
    :param callable: callable or function that will be called.
    :param using: name of the database
    """

    connection = get_connection(using)
    if getattr(connection, 'transaction_signals_context_list', False):
        connection.transaction_signals_context_list[-1].register(callable)
    else:
        if settings.DEBUG:
            logger.warning(
                'For on success signal should be activated transaction signals via transaction_signals decorator.'
                'Function is called immediately now.'
            )
        callable()


def transaction_signals(using=None):
    """
    Decorator that adds transaction context to the connection on input.
    Finally callable are called on the output.
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


class UniqueOnSuccessCallable:
    """
    One time callable class that is used for performing on success operations.
    Handler is callable only once, but data of all calls are stored inside list (kwargs_list).
    """

    def __init__(self, **kwargs):
        self.kwargs_list = (kwargs,)

    def join(self, callable):
        """
        Joins two unique callable.
        """
        self.kwargs_list += callable.kwargs_list

    def _get_unique_id(self):
        """
        Callable instance hash is generated from class name and the return value of this method.
        The method returns None by default, therefore the class init data doesn't have impact.
        You should implement this method to distinguish callable according to its
        input data (for example Django model instance)
        :return:
        """
        return None

    def __hash__(self):
        return hash((self.__class__, self._get_unique_id()))

    def _get_kwargs(self):
        return self.kwargs_list[-1]

    def __call__(self):
        self.handle()

    def handle(self):
        raise NotImplementedError
