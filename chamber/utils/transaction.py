import logging

from django.db import transaction, DEFAULT_DB_ALIAS
from django.db.transaction import get_connection
from django.db.transaction import TransactionManagementError

from contextlib import contextmanager


logger = logging.getLogger(__name__)


def pre_commit(func, using=None):
    connection = get_connection(using)

    if connection.in_atomic_block:
        # Transaction in progress; save for execution on commit.
        func_hash = hash(func) if isinstance(func, UniquePreCommitCallable) else None
        if (func_hash is None
                or func_hash not in {func_hash for sids, func_hash, func in connection.run_pre_commit}):
            connection.run_pre_commit.append((set(connection.savepoint_ids), func_hash, func))

    elif not connection.get_autocommit():
        raise TransactionManagementError('pre_commit() cannot be used in manual transaction management')
    else:
        # No transaction in progress and in autocommit mode; execute immediately.
        func()


def smart_atomic(using=None, savepoint=True, ignore_errors=None, reversion=True, reversion_using=None):
    """
    Decorator and context manager that overrides django atomic decorator and automatically adds create revision.
    The _atomic closure is required to achieve save ContextDecorator that nest more inner context decorator.
    More here https://stackoverflow.com/questions/45589718/combine-two-context-managers-into-one
    """

    ignore_errors = () if ignore_errors is None else ignore_errors

    @contextmanager
    def _atomic(using=None, savepoint=True, reversion=True, reversion_using=None):
        try:
            from reversion.revisions import create_revision
        except ImportError:
            reversion = False

        if not reversion:
            @contextmanager  # noqa: F811
            def create_revision(*args, **kwargs):  # noqa: F811
                yield

        error = None
        with transaction.atomic(using, savepoint), create_revision(using=reversion_using):
            try:
                yield
            except ignore_errors as ex:
                error = ex

        if error:
            raise error  # pylint: disable=E0702

    if callable(using):
        return _atomic(DEFAULT_DB_ALIAS, savepoint, reversion, reversion_using)(using)
    else:
        return _atomic(using, savepoint, reversion, reversion_using)


def in_atomic_block(using=None):
    """Check if connection is in atomic block"""

    connection = get_connection(using)
    return connection.in_atomic_block


class UniquePreCommitCallable:
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
