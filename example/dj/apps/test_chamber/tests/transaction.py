from django.test import TransactionTestCase
from django.db import transaction

from chamber.utils.transaction import (
    on_success, transaction_signals, UniqueOnSuccessCallable, TransactionSignalsError, in_atomic_block,
    in_transaction_signals_block
)

from germanium.tools import assert_equal, assert_raises, assert_true, assert_false


__all__ = (
    'TransactionsTestCase',
)


def add_number(numbers_list, number):
    numbers_list.append(number)


class TransactionsTestCase(TransactionTestCase):

    def test_on_success_is_called_after_successful_pass(self):
        numbers_list = []

        with transaction_signals():
            on_success(lambda: add_number(numbers_list, 0))

            assert_equal(len(numbers_list), 0)

        assert_equal(len(numbers_list), 1)

    def test_on_success_is_not_called_after_not_successful_pass(self):
        numbers_list = []
        try:
            with transaction_signals():
                on_success(lambda: add_number(numbers_list, 0))
                assert_equal(len(numbers_list), 0)
                raise Exception()
        except Exception:
            pass

        assert_equal(len(numbers_list), 0)

    def test_on_success_inheritance(self):
        numbers_list = []

        with transaction_signals():
            with transaction_signals():
                on_success(lambda: add_number(numbers_list, 0))

                assert_equal(len(numbers_list), 0)
            assert_equal(len(numbers_list), 0)
            try:
                with transaction_signals():
                    on_success(lambda: add_number(numbers_list, 1))

                    assert_equal(len(numbers_list), 0)
                    raise Exception()
            except Exception:
                pass
            on_success(lambda: add_number(numbers_list, 2))
            assert_equal(len(numbers_list), 0)

        assert_equal(numbers_list, [0, 2])

    def test_on_success_one_time_callable(self):
        numbers_list = []

        class AddNumberOneTimeOnSuccessCallable(UniqueOnSuccessCallable):

            def handle(self):
                self.kwargs_list[-1]['numbers_list'].append(3)

        with transaction_signals():
            for i in range(5):
                on_success(AddNumberOneTimeOnSuccessCallable(numbers_list=numbers_list, number=i))

            assert_equal(len(numbers_list), 0)

        assert_equal(numbers_list, [3])

    def test_on_success_one_time_callable_inheritance(self):
        numbers_list = []

        class AddNumberOneTimeOnSuccessCallable(UniqueOnSuccessCallable):

            def handle(self):
                for kwargs in self.kwargs_list:
                    self.kwargs_list[-1]['numbers_list'].append(kwargs['number'])

        with transaction_signals():
            on_success(AddNumberOneTimeOnSuccessCallable(numbers_list=numbers_list, number=1))
            try:
                with transaction_signals():
                    on_success(AddNumberOneTimeOnSuccessCallable(numbers_list=numbers_list, number=2))

                    assert_equal(len(numbers_list), 0)
                    raise Exception()
            except Exception:
                pass
            with transaction_signals():
                on_success(AddNumberOneTimeOnSuccessCallable(numbers_list=numbers_list, number=3))

                assert_equal(len(numbers_list), 0)
            assert_equal(len(numbers_list), 0)

        assert_equal(numbers_list, [1, 3])

    def test_on_success_should_be_not_be_used_in_atomic_without_transaciton_signal_block(self):
        def on_success_fn():
            pass

        with transaction_signals():
            with transaction.atomic():
                with assert_raises(TransactionSignalsError):
                    on_success(on_success_fn)
                with transaction_signals():
                    on_success(on_success_fn)
                    with transaction.atomic():
                        with assert_raises(TransactionSignalsError):
                            on_success(on_success_fn)


    def test_is_atomic_block_should_return_if_django_atomic_block_is_active(self):
        assert_false(in_atomic_block())

        with transaction.atomic():
            assert_true(in_atomic_block())
            with transaction.atomic():
                assert_true(in_atomic_block())
            assert_true(in_atomic_block())
        assert_false(in_atomic_block())

    def test_on_success_should_called_in_on_success_function_with_the_right_order(self):
        data = []

        def on_success_fn_a():
            with transaction_signals():
                on_success(on_success_fn_c)

            data.append('a')

        def on_success_fn_b():
            data.append('b')

        def on_success_fn_c():
            data.append('c')

        with transaction_signals():
            on_success(on_success_fn_a)
            with transaction_signals():
                on_success(on_success_fn_b)

        assert_equal(data, ['a', 'b', 'c'])

    def test_in_transaction_signals_block_should_return_right_result(self):
        def on_success_fn():
            assert_true(in_transaction_signals_block())

        with transaction_signals():
            assert_true(in_transaction_signals_block())
            on_success(on_success_fn)
            with transaction_signals():
                assert_true(in_transaction_signals_block())
        assert_false(in_transaction_signals_block())
