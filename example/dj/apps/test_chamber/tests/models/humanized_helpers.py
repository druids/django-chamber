from django.test import TestCase

from chamber.models.humanized_helpers import price_humanized

from germanium.decorators import data_provider  # pylint: disable=E0401
from germanium.tools import assert_equal  # pylint: disable=E0401


class HumanizedHelpersTestCase(TestCase):

    numbers_with_currencies = (
        (100.00, 'CZK', '100,00\xa0CZK'),
        (1000000.00, 'EUR', '1\xa0000\xa0000,00\xa0EUR'),
        (1000000.00, None, '1\xa0000\xa0000,00\xa0CZK'),
        (None, None, '(None)'),
    )

    @data_provider(numbers_with_currencies)
    def test_should_return_price_humanized(self, number, currency, expected):
        assert_equal(expected, price_humanized(number, None, currency))
