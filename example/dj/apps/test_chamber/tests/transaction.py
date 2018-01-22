from __future__ import unicode_literals

from django.test import TestCase

from chamber.utils.transaction import (
    on_success, transaction_signals, OnSuccessHandler, OneTimeOnSuccessHandler
)

from germanium.tools import assert_equal  # pylint: disable=E0401


def add_number(numbers_list, number):
    numbers_list.append(number)


class TransactionsTestCase(TestCase):

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

        assert_equal(numbers_list, [0,2])

    def test_on_success_handler(self):
        numbers_list = []

        class AddNumberOnSuccessHandler(OnSuccessHandler):

            def handle(self, numbers_list, number):
                numbers_list.append(number)

        with transaction_signals():
            AddNumberOnSuccessHandler(numbers_list=numbers_list, number=1)
            AddNumberOnSuccessHandler(numbers_list=numbers_list, number=2)

            assert_equal(len(numbers_list), 0)

        assert_equal(numbers_list, [1, 2])

    def test_on_success_one_time_handler(self):
        numbers_list = []

        class AddNumberOneTimeOnSuccessHandler(OneTimeOnSuccessHandler):

            def handle(self, kwargs_list):
                kwargs_list[-1]['numbers_list'].append(3)

        with transaction_signals():
            for i in range(5):
                AddNumberOneTimeOnSuccessHandler(numbers_list=numbers_list, number=i)

            assert_equal(len(numbers_list), 0)

        assert_equal(numbers_list, [3])

    def test_on_success_one_time_handler_inheritance(self):
        numbers_list = []

        class AddNumberOneTimeOnSuccessHandler(OneTimeOnSuccessHandler):

            def handle(self, kwargs_list):
                for kwargs in kwargs_list:
                    kwargs_list[-1]['numbers_list'].append(kwargs['number'])

        with transaction_signals():
            AddNumberOneTimeOnSuccessHandler(numbers_list=numbers_list, number=1)
            try:
                with transaction_signals():
                    AddNumberOneTimeOnSuccessHandler(numbers_list=numbers_list, number=2)

                    assert_equal(len(numbers_list), 0)
                    raise Exception()
            except Exception:
                pass
            with transaction_signals():
                AddNumberOneTimeOnSuccessHandler(numbers_list=numbers_list, number=3)

                assert_equal(len(numbers_list), 0)
            assert_equal(len(numbers_list), 0)

        assert_equal(numbers_list, [1, 3])
