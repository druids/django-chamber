# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

from .datastructures import * # NOQA
from .decorators import * # NOQA

from django.utils.functional import cached_property
from django.test import TestCase

from chamber.utils import remove_accent, get_class_method

from germanium.anotations import data_provider # NOQA
from germanium.tools import assert_equal # NOQA


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
