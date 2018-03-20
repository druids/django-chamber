from django.utils import numberformat
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe


def natural_number_with_currency(number, currency, show_decimal_place=True, use_nbsp=True):
    """
    Return a given `number` formatter a price for humans.
    """
    humanized = '{} {}'.format(
        numberformat.format(
            number=number,
            decimal_sep=',',
            decimal_pos=2 if show_decimal_place else 0,
            grouping=3,
            thousand_sep=' ',
            force_grouping=True
        ),
        force_text(currency)
    )
    return mark_safe(humanized.replace(' ', '\u00a0')) if use_nbsp else humanized
