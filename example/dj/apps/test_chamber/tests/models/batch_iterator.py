from datetime import timedelta

from django.core.cache import cache
from django.test import TransactionTestCase
from django.utils.timezone import now

from chamber.models.batch_iterator import BatchCachedQuerysetIterator

from germanium.tools import assert_equal, assert_raises, assert_is_none

from freezegun import freeze_time

from test_chamber.models import TestSmartModel


__all__ = (
    'BatchCachedQuerysetIteratorTestCase',
)


class BatchCachedQuerysetIteratorTestCase(TransactionTestCase):

    def test_batch_cached_iterator_should_return_all_items_and_set_cursor_to_last_element(self):
        test_objs = [TestSmartModel.objects.create(name=str(i)) for i in range(10)]
        iterator = BatchCachedQuerysetIterator(TestSmartModel.objects.all(), 'full', batch_size=100, expiration=10)

        assert_equal(iterator.total_number_of_objects, 10)
        assert_equal(iterator.remaining_number_of_objects, 10)

        iterated_objs = [obj for obj in iterator]

        assert_equal(test_objs, iterated_objs)
        assert_equal(iterator.total_number_of_objects, 10)
        assert_equal(iterator.remaining_number_of_objects, 0)
        assert_equal(cache.get('batch_queryset_iterator_full'), test_objs[-1].pk)

    def test_batch_cached_iterator_should_iterate_over_objects_by_chunks(self):
        test_objs = [TestSmartModel.objects.create(name=str(i)) for i in range(20)]
        iterator = BatchCachedQuerysetIterator(TestSmartModel.objects.all(), 'chunks', batch_size=10, expiration=10)

        assert_equal(iterator.total_number_of_objects, 20)
        assert_equal(iterator.remaining_number_of_objects, 20)

        iterated_objs = [obj for obj in iterator]
        assert_equal(test_objs[:10], iterated_objs)
        assert_equal(iterator.total_number_of_objects, 20)
        assert_equal(iterator.remaining_number_of_objects, 10)
        assert_equal(cache.get('batch_queryset_iterator_chunks'), test_objs[9].pk)

        iterator = BatchCachedQuerysetIterator(TestSmartModel.objects.all(), 'chunks', batch_size=10, expiration=10)
        iterated_objs = [obj for obj in iterator]
        assert_equal(test_objs[10:], iterated_objs)
        assert_equal(iterator.total_number_of_objects, 20)
        assert_equal(iterator.remaining_number_of_objects, 0)
        assert_equal(cache.get('batch_queryset_iterator_chunks'), test_objs[19].pk)

    def test_batch_cached_iterator_should_store_last_cursor_for_raised_exception(self):
        test_objs = [TestSmartModel.objects.create(name=str(i)) for i in range(20)]
        iterator = BatchCachedQuerysetIterator(TestSmartModel.objects.all(), 'exception', batch_size=10, expiration=10)

        with assert_raises(RuntimeError):
            for i, obj in enumerate(iterator):
                if i == 2:
                    raise RuntimeError
        assert_is_none(cache.get('batch_queryset_iterator_exception'))

        iterator = BatchCachedQuerysetIterator(
            TestSmartModel.objects.all(), 'exception', batch_size=10, expiration=10, store_cursor_with_exception=True
        )

        with assert_raises(RuntimeError):
            for i, obj in enumerate(iterator):
                if i == 2:
                    raise RuntimeError
        assert_equal(cache.get('batch_queryset_iterator_exception'), test_objs[1].pk)

        iterator = BatchCachedQuerysetIterator(
            TestSmartModel.objects.all(), 'exception', batch_size=100, expiration=10
        )
        iterated_objs = [obj for obj in iterator]
        assert_equal(test_objs[2:], iterated_objs)

    def test_batch_cached_iterator_should_be_completed_after_exception(self):
        test_objs = [TestSmartModel.objects.create(name=str(i)) for i in range(10)]
        iterator = BatchCachedQuerysetIterator(
            TestSmartModel.objects.all(), 'complete_exception', batch_size=10, expiration=10
        )

        iterated_objects = []
        with assert_raises(RuntimeError):
            for i, obj in enumerate(iterator):
                if i == 2:
                    raise RuntimeError
                else:
                    iterated_objects.append(obj)

        assert_equal(iterator.total_number_of_objects, 10)
        assert_equal(iterator.remaining_number_of_objects, 8)
        iterated_objects += [obj for obj in iterator]
        assert_equal(iterator.total_number_of_objects, 10)
        assert_equal(iterator.remaining_number_of_objects, 0)
        assert_equal(test_objs, iterated_objects)

    def test_batch_cached_iterator_should_expire_cache(self):
        test_objs = [TestSmartModel.objects.create(name=str(i)) for i in range(10)]
        iterator = BatchCachedQuerysetIterator(TestSmartModel.objects.all(), 'expiration', batch_size=5, expiration=5)
        iterated_objs = [obj for obj in iterator]
        assert_equal(cache.get('batch_queryset_iterator_expiration'), test_objs[4].pk)

        with freeze_time(now() + timedelta(seconds=5)):
            iterator = BatchCachedQuerysetIterator(
                TestSmartModel.objects.all(), 'expiration', batch_size=5, expiration=5
            )
            assert_equal(iterated_objs, list(iterator))
