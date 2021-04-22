import logging

from collections import OrderedDict

from django.conf import settings
from django.db import transaction, DEFAULT_DB_ALIAS
from django.db.transaction import get_connection

from contextlib import contextmanager, ContextDecorator


logger = logging.getLogger(__name__)


def atomic(using=None, savepoint=True):
    """
    Decorator and context manager that overrides django atomic decorator and automatically adds create revision.
    The _atomic closure is required to achieve save ContextDecorator that nest more inner context decorator.
    More here https://stackoverflow.com/questions/45589718/combine-two-context-managers-into-one
    """

    @contextmanager
    def _atomic(using=None, savepoint=True):
        try:
            from reversion.revisions import create_revision

            with transaction.atomic(using, savepoint), create_revision():
                yield
        except ImportError:
            with transaction.atomic(using, savepoint):
                yield

    if callable(using):
        return _atomic(DEFAULT_DB_ALIAS, savepoint)(using)
    else:
        return _atomic(using, savepoint)


class TransactionSignalsError(Exception):
    pass


class TransactionSignalsContext:
    """
    Context object that stores callable and call it after successful pass trough surrounded code block
    with "transaction_signals decorator. Handlers can be unique or standard. Unique callable are registered
    and executed only once.
    """

    def __init__(self, sid, in_atomic_block):
        self._unique_callable = {}
        self._callable_list = []
        self.sid = sid
        self.in_atomic_block = in_atomic_block

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
        while self._callable_list:
            callable = self._callable_list.pop(0)
            if isinstance(callable, UniqueOnSuccessCallable):
                del self._unique_callable[hash(callable)]
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
        self._using = using

    def __enter__(self):
        connection = get_connection(self._using)
        sid = connection.savepoint_ids[-1] if connection.savepoint_ids else None

        if not hasattr(connection, 'transaction_signals_context_list'):
            connection.transaction_signals_context_list = []

        connection.transaction_signals_context_list.append(
            TransactionSignalsContext(sid, connection.in_atomic_block)
        )

    def __exit__(self, exc_type, exc_value, traceback):
        connection = get_connection(self._using)

        transaction_signals_context = connection.transaction_signals_context_list[-1]
        if not exc_value and not connection.needs_rollback:
            if len(connection.transaction_signals_context_list) == 1:
                transaction_signals_context.handle_all()
            else:
                connection.transaction_signals_context_list[-2].join(transaction_signals_context)

        connection.transaction_signals_context_list.pop()
        if not connection.transaction_signals_context_list:
            del connection.transaction_signals_context_list


def in_transaction_signals_block(using=None):
    """
    Check if transaction signals is active.
    :param using: name of the database
    :return: True/False
    """
    connection = get_connection(using)
    return hasattr(connection, 'transaction_signals_context_list')


def on_success(callable, using=None):
    """
    Register a callable or a function to be called after successful code pass.
    If transaction signals are not active the callable/function is called immediately.
    :param callable: callable or function that will be called.
    :param using: name of the database
    """
    connection = get_connection(using)
    sid = connection.savepoint_ids[-1] if connection.savepoint_ids else None

    if getattr(connection, 'transaction_signals_context_list', False):
        context_list = connection.transaction_signals_context_list[-1]
        if context_list.sid != sid or context_list.in_atomic_block != connection.in_atomic_block:
            raise TransactionSignalsError('on_success cannot be used in atomic block without transaction_signals_block')

        context_list.register(callable)
    else:
        if settings.DEBUG and not in_transaction_signals_block(using):
            logger.warning(
                'For on success signal should be activated transaction signals via transaction_signals decorator.'
                'Function is called immediately now.'
            )
        callable()


def in_atomic_block(using=None):
    """Check if connection is in atomic block"""

    connection = get_connection(using)
    return connection.in_atomic_block


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


def atomic_with_signals(using=None, savepoint=True):
    """
    Atomic decorator and context manager with transaction signals.
    The _atomic_with_signals closure is required to achieve save ContextDecorator that nest more inner context
    decorator. More here https://stackoverflow.com/questions/45589718/combine-two-context-managers-into-one
    """

    @contextmanager
    def _atomic_with_signals(using=None, savepoint=True):
        with atomic(using, savepoint), transaction_signals(using):
            yield

    if callable(using):
        return _atomic_with_signals(DEFAULT_DB_ALIAS, savepoint)(using)
    else:
        return _atomic_with_signals(using, savepoint)


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
