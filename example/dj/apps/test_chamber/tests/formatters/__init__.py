from django.test import TestCase

from chamber.formatters import natural_number_with_currency

from germanium.decorators import data_provider  # pylint: disable=E0401
from germanium.tools import assert_equal  # pylint: disable=E0401


class FormattersTestCase(TestCase):

    numbers_with_currencies = (
        (100.00, 'CZK', False, False, '100 CZK'),
        (100.00, 'CZK', True, False, '100,00 CZK'),
        (100.00, 'CZK', False, True, '100\xa0CZK'),
        (1000000.00, 'CZK', False, True, '1\xa0000\xa0000\xa0CZK'),
    )

    @data_provider(numbers_with_currencies)
    def test_should_return_natural_number_with_currency(self, number, currency, show_decimal_place, use_nbsp, expected):
        assert_equal(expected, natural_number_with_currency(number, currency, show_decimal_place, use_nbsp))
