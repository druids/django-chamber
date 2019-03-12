from django.test import TestCase
from django.utils.functional import cached_property
from django.utils.safestring import SafeData, mark_safe

from chamber.utils import get_class_method, keep_spacing, remove_accent

from germanium.decorators import data_provider  # pylint: disable=E0401
from germanium.tools import assert_equal, assert_true  # pylint: disable=E0401

from .datastructures import *  # NOQA
from .decorators import *  # NOQA


class TestClass(object):

    def method(self):
        pass

    @property
    def property_method(self):
        pass

    @cached_property
    def cached_property_method(self):
        pass


class UtilsTestCase(TestCase):

    def test_should_remove_accent_from_string(self):
        assert_equal('escrzyaie', remove_accent('ěščřžýáíé'))

    classes_and_method_names = [
        [TestClass.method, TestClass, 'method'],
        [TestClass.method, TestClass(), 'method'],
        [TestClass.property_method.fget, TestClass, 'property_method'],
        [TestClass.property_method.fget, TestClass(), 'property_method'],
        [TestClass.cached_property_method.func, TestClass, 'cached_property_method'],
        [TestClass.cached_property_method.func, TestClass(), 'cached_property_method'],
    ]

    @data_provider(classes_and_method_names)
    def test_should_return_class_method(self, expected_method, cls_or_inst, method_name):
        assert_equal(expected_method, get_class_method(cls_or_inst, method_name))

    values_for_keep_spacing = [
        ['Hello &lt;b&gt; escaped&lt;/b&gt; <br />world', 'Hello <b> escaped</b> \nworld', True],
        ['Hello <b> escaped</b> <br />world', 'Hello <b> escaped</b> \nworld', False],
        ['Hello &lt;b&gt; escaped&lt;/b&gt; <br />world', 'Hello <b> escaped</b> \r\nworld', True],
        ['Hello <b> escaped</b> <br />world', 'Hello <b> escaped</b> \r\nworld', False],
        ['Hello <b> escaped</b> <br />world', mark_safe('Hello <b> escaped</b> \r\nworld'), True]
    ]

    @data_provider(values_for_keep_spacing)
    def test_should_keep_spacing(self, expected, value, autoescape):
        escaped_value = keep_spacing(value, autoescape)
        assert_equal(expected, escaped_value)
        assert_true(isinstance(escaped_value, SafeData))
