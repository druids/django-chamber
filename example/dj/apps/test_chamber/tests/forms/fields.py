from __future__ import unicode_literals

from django.forms import TextInput
from django.test import TransactionTestCase

from germanium.tools import assert_equal, assert_true  # pylint: disable=E0401

from chamber.forms.fields import DecimalField


class DecimalFieldTestCase(TransactionTestCase):

    def test_should_return_correct_widget_attrs(self):
        kwargs = {
            'step': 0.5,
            'min': 1.0,
            'max': 10.0,
        }
        field = DecimalField(**kwargs)
        widget_attrs = field.widget_attrs(TextInput())
        assert_true(len(widget_attrs.keys()) > 0)
        for attr, value in kwargs.items():
            assert_equal(value, widget_attrs[attr])

    def test_should_return_default_attrs(self):
        field = DecimalField()
        widget_attrs = field.widget_attrs(TextInput())
        assert_equal({'step': 'any'}, widget_attrs)
