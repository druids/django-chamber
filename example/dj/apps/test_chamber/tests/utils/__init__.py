# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

from .datastructures import * # NOQA
from .decorators import * # NOQA

from django.test import TestCase

from chamber.utils import remove_accent

from germanium.tools import assert_equal


class UtilsTestCase(TestCase):

    def test_should_remove_accent_from_string(self):
        assert_equal('escrzyaie', remove_accent('ěščřžýáíé'))
