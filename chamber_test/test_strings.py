from __future__ import unicode_literals

import unittest

from ddt import ddt, data, unpack

from germanium.tools import assert_equal

from chamber.strings import truncate_fuzzy


@ddt
class TestStringsFunctions(unittest.TestCase):

    @data(
        ('Hello my name is Foo.', 8, 'Hello my'),
        ('It is shorter', 14, 'It is shorter'),
    )
    @unpack
    def test_should_truncate_fuzzy(self, string, length, expected):
        assert_equal(truncate_fuzzy(string, length), expected)
