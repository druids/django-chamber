from django.test import TransactionTestCase
from django.db import transaction

from django.db.transaction import on_commit

from chamber.utils.transaction import UniquePreCommitCallable, in_atomic_block, pre_commit, smart_atomic

from test_chamber.models import TestSmartModel

from germanium.tools import assert_equal, assert_raises, assert_true, assert_false


__all__ = (
    'TransactionsTestCase',
)


def add_number(numbers_list, number):
    numbers_list.append(number)


class TransactionsTestCase(TransactionTestCase):

    def test_pre_commit_without_atomic_should_be_called_immediately(self):
        numbers_list = []

        pre_commit(lambda: add_number(numbers_list, 1))
        assert_equal(numbers_list, [1])

    def test_pre_commit_should_be_called_before_on_commit(self):
        numbers_list = []

        with transaction.atomic():
            on_commit(lambda: add_number(numbers_list, 2))
            pre_commit(lambda: add_number(numbers_list, 1))
            assert_equal(len(numbers_list), 0)

        assert_equal(numbers_list, [1, 2])

    def test_pre_commit_should_not_be_called_for_rollback(self):
        numbers_list = []

        with assert_raises(RuntimeError):
            with transaction.atomic():
                on_commit(lambda: add_number(numbers_list, 2))
                pre_commit(lambda: add_number(numbers_list, 1))
                assert_equal(len(numbers_list), 0)
                raise RuntimeError

        assert_equal(numbers_list, [])

    def test_pre_commit_should_call_only_not_failed_pre_commit_hooks(self):
        numbers_list = []

        with transaction.atomic():
            with transaction.atomic():
                pre_commit(lambda: add_number(numbers_list, 0))

                assert_equal(len(numbers_list), 0)
            assert_equal(len(numbers_list), 0)
            with assert_raises(RuntimeError):
                with transaction.atomic():
                    pre_commit(lambda: add_number(numbers_list, 1))

                    assert_equal(len(numbers_list), 0)
                    raise RuntimeError
            pre_commit(lambda: add_number(numbers_list, 2))
            assert_equal(len(numbers_list), 0)

        assert_equal(numbers_list, [0, 2])

    def test_pre_commit_should_call_one_time_callable_only_once(self):
        numbers_list = []

        class AddNumberOneTimePreCommitCallable(UniquePreCommitCallable):

            def handle(self):
                self.kwargs_list[-1]['numbers_list'].append(3)

        with transaction.atomic():
            for i in range(5):
                pre_commit(AddNumberOneTimePreCommitCallable(numbers_list=numbers_list, number=i))

            assert_equal(len(numbers_list), 0)

        assert_equal(numbers_list, [3])

    def test_pre_commit_should_call_one_time_callable_only_once_for_not_failed_blocks(self):
        numbers_list = []

        class AddNumberOneTimePreCommitCallable(UniquePreCommitCallable):

            def handle(self):
                for kwargs in self.kwargs_list:
                    self.kwargs_list[-1]['numbers_list'].append(kwargs['number'])

        with transaction.atomic():
            pre_commit(AddNumberOneTimePreCommitCallable(numbers_list=numbers_list, number=1))
            with assert_raises(RuntimeError):
                with transaction.atomic():
                    pre_commit(AddNumberOneTimePreCommitCallable(numbers_list=numbers_list, number=2))

                    assert_equal(len(numbers_list), 0)
                    raise RuntimeError
            with transaction.atomic():
                pre_commit(AddNumberOneTimePreCommitCallable(numbers_list=numbers_list, number=3))

                assert_equal(len(numbers_list), 0)
            assert_equal(len(numbers_list), 0)

        assert_equal(numbers_list, [1])

    def test_pre_commit_should_called_with_the_right_order(self):
        data = []

        def pre_commit_fn_a():
            pre_commit(pre_commit_fn_c)
            data.append('a')

        def pre_commit_fn_b():
            data.append('b')

        def pre_commit_fn_c():
            data.append('c')

        with transaction.atomic():
            pre_commit(pre_commit_fn_a)
            with transaction.atomic():
                pre_commit(pre_commit_fn_b)

        assert_equal(data, ['a', 'b', 'c'])

    def test_chamber_atomic_should_ignore_errors(self):
        with assert_raises(RuntimeError):
            with smart_atomic():
                TestSmartModel.objects.create(name='test')
                raise RuntimeError
        assert_false(TestSmartModel.objects.exists())

        with assert_raises(RuntimeError):
            with smart_atomic(ignore_errors=(RuntimeError,)):
                TestSmartModel.objects.create(name='test')
                raise RuntimeError
        assert_true(TestSmartModel.objects.exists())
