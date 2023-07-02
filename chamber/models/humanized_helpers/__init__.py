from django.utils.translation import gettext

from chamber.formatters import natural_number_with_currency


def price_humanized(value, inst, currency=None):
    """
    Return a humanized price
    """
    return (natural_number_with_currency(value, gettext('CZK') if currency is None else currency) if value is not None
            else gettext('(None)'))
