from datetime import datetime, timedelta

from django.core.cache import cache
from django.utils.timezone import localtime


class BatchCachedQuerysetIterator:
    """
    Batch iterator that stores last iterated object in the cache.
    The iterator may be used in different processes (running at a different time).
    Iteration will continue from the last complete batch.

    Eq
        iterator = BatchCachedQuerysetIterator(
            User.objects.all(),  # iterated queryset
            'users',             # key used to store last object (cursor) in cache
            batch_size=100,      # size of one iteration
            expiration=10        # expiration of cached cursor in seconds
        )
        # 100 users are returned (if there is more than 100 users)
        list(iterator)

        iterator2 = BatchCachedQuerysetIterator(User.objects.all(), 'users', batch_size=100, expiration=10)
        # next 100 users are returned (users will be sorted by ID)
        list(iterator2)
    """

    def __init__(self, queryset, key, store_cursor_with_exception=False, batch_size=10000, expiration=None):
        """
        Init batch cached queryset iterator
        :param queryset: queryset which you should want to iterate. Queryset should be sortable by ID
        :param key: unique key of your iterator which will be used for cursor caching
        :param store_cursor_with_exception: store cursor in cache if exception will be occurred
        :param batch_size: size of one batch
        :param expiration: expiration in datatime, timedelta or integer (number of seconds) format
        """
        self._batch_size = batch_size
        self._cache_key = f'batch_queryset_iterator_{key}'
        self._count_processed = 0
        self._queryset = queryset.order_by('pk')
        self._cursor = self._cached_cursor = self._get_cursor()
        self._chunked_queryset = self._get_chunked_queryset(self._cursor)
        self._expiration = self._compute_expiration(expiration)
        self._store_cursor_with_exception = store_cursor_with_exception

    def _compute_expiration(self, expiration):
        if isinstance(expiration, datetime):
            return expiration
        elif isinstance(expiration, int):
            return localtime() + timedelta(seconds=expiration)
        elif isinstance(expiration, timedelta):
            return localtime() + expiration
        else:
            raise AttributeError('invalid value of expiration it can be datetime, integer or timedelta')

    def _get_cursor(self):
        return cache.get(self._cache_key)

    def _set_cursor(self):
        if self._cursor != self._cached_cursor:
            cache.set(self._cache_key, self._cursor, (self._expiration - localtime()).total_seconds())
            self._cached_cursor = self._cursor

    def _filter_queryset_by_cursor(self, cursor):
        queryset = self._queryset
        if cursor:
            queryset = queryset.filter(pk__gt=cursor)
        return queryset

    def _get_chunked_queryset(self, cursor):
        return self._filter_queryset_by_cursor(cursor)[:self._batch_size]

    def __iter__(self):
        try:
            for obj in self._get_chunked_queryset(self._cursor):
                yield obj
                self._cursor = obj.pk
            self._set_cursor()
        finally:
            if self._store_cursor_with_exception:
                self._set_cursor()

    def __len__(self):
        return self._get_chunked_queryset(self._cursor).count()

    @property
    def total_number_of_objects(self):
        return self._queryset.count()

    @property
    def remaining_number_of_objects(self):
        return self._filter_queryset_by_cursor(cursor=self._cursor).count()
