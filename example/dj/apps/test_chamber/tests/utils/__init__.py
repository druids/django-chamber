import codecs

from django.test import TestCase
from django.utils.functional import cached_property
from django.utils.safestring import SafeData, mark_safe
from django.utils.functional import cached_property

from chamber.utils import (
    get_class_method, keep_spacing, remove_accent, call_function_with_unknown_input, InvalidFunctionArguments
)

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

    attribute = 'attribute'


class UtilsTestCase(TestCase):

    def test_should_remove_accent_from_string(self):
        assert_equal(remove_accent('ěščřžýáíé'), 'escrzyaie')

    def test_should_remove_accent_from_string_when_unicode_error(self):
        assert_equal(
            codecs.encode('àaáÀAÁ', 'windows-1250', 'remove_accent'),
            'aaáAAÁ'.encode('windows-1250')  # characters "à" "À" are not in charset windows-1250
        )
        assert_equal(
            codecs.encode('ⓓⓙⓐⓝⓖⓞ-ⓒⓗⓐⓜⓑⓔⓡ', 'windows-1250', 'remove_accent'),
            'django-chamber'.encode('windows-1250')
        )

    classes_and_method_names = [
        [TestClass.method, TestClass, 'method'],
        [TestClass.method, TestClass(), 'method'],
        [TestClass.property_method.fget, TestClass, 'property_method'],
        [TestClass.property_method.fget, TestClass(), 'property_method'],
        [TestClass.cached_property_method.func, TestClass, 'cached_property_method'],
        [TestClass.cached_property_method.func, TestClass(), 'cached_property_method'],
        [None, TestClass, 'attribute'],
        [None, TestClass(), 'attribute'],
        [None, TestClass, 'invalid'],
        [None, TestClass(), 'invalid'],
    ]

    @data_provider(classes_and_method_names)
    def test_get_class_method_should_return_right_class_method_or_none(self, expected_method, cls_or_inst, method_name):
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

    def test_call_function_with_unknown_input_should_return_right_response_or_exception(self):
        def test_function(a, b, c):
            assert_equal(a, 3)
            assert_equal(b, 2)
            assert_equal(c, 1)

        call_function_with_unknown_input(test_function, a=3, b=2, c=1)
        call_function_with_unknown_input(test_function, c=1, a=3, b=2)
        call_function_with_unknown_input(test_function, c=1, a=3, b=2, d=8, e=9)

        with assert_raises(InvalidFunctionArguments):
            call_function_with_unknown_input(test_function, a=3, b=2)

    def test_call_function_with_default_values_and_unknown_input_should_return_right_response_or_exception(self):
        def test_function(a, b=5, c=6):
            return a, b, c

        assert_equal(call_function_with_unknown_input(test_function, a=1), (1, 5, 6))
        assert_equal(call_function_with_unknown_input(test_function, c=1, a=2), (2, 5, 1))
        assert_equal(call_function_with_unknown_input(test_function, b=1, a=2), (2, 1, 6))

        with assert_raises(InvalidFunctionArguments):
            call_function_with_unknown_input(test_function, b=2, c=1)
