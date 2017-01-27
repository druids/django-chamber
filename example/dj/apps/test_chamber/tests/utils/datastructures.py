from __future__ import unicode_literals

from django.test import TestCase

from chamber.utils.datastructures import ChoicesEnum, ChoicesNumEnum, Enum, NumEnum, OrderedSet

from germanium.tools import assert_equal, assert_raises  # pylint: disable=E0401


class DatastructuresTestCase(TestCase):

    def test_enum(self):
        enum = Enum(
            'A', 'B'
        )
        assert_equal(enum.A, 'A')
        assert_equal(enum.B, 'B')
        with assert_raises(AttributeError):
            enum.C  # pylint: disable=W0104

    def test_num_enum(self):
        enum = NumEnum(
            'A', 'B'
        )
        assert_equal(enum.A, 1)
        assert_equal(enum.B, 2)
        with assert_raises(AttributeError):
            enum.C

    def test_num_enum_with_defined_ids(self):
        enum = NumEnum(
            ('A', 4), ('B', 2), 'C'
        )
        assert_equal(enum.A, 4)
        assert_equal(enum.B, 2)
        assert_equal(enum.C, 3)

    def test_num_enum_same_numbers_should_raise_exception(self):
        with assert_raises(ValueError):
            NumEnum(
                ('A', 1), ('B', 1)
            )

    def test_num_enum_same_generated_numbers_should_raise_exception(self):
        with assert_raises(ValueError):
            NumEnum(
                ('A', 3), ('B', 2), 'C'
            )

    def test_num_enum_invalid_num_raise_exception(self):
        with assert_raises(ValueError):
            NumEnum(
                ('A', 'e'), ('B', 2)
            )

    def test_choices_enum(self):
        choices_num = ChoicesEnum(
            ('A', 'a'),
            ('B', 'b'),
        )
        assert_equal(choices_num.A, 'A')
        assert_equal(choices_num.B, 'B')
        assert_equal(list(choices_num.choices), [('A', 'a'), ('B', 'b')])
        assert_equal(tuple(choices_num.all), ('A', 'B'))
        assert_equal(choices_num.get_label('A'), 'a')
        assert_equal(choices_num.get_label('B'), 'b')

    def test_choices_num_enum(self):
        choices_num = ChoicesNumEnum(
            ('A', 'a'),
            ('B', 'b'),
        )
        assert_equal(choices_num.A, 1)
        assert_equal(choices_num.B, 2)
        assert_equal(list(choices_num.choices), [(1, 'a'), (2, 'b')])
        assert_equal(tuple(choices_num.all), (1, 2))
        assert_equal(choices_num.get_label(1), 'a')
        assert_equal(choices_num.get_label(2), 'b')
        assert_raises(AttributeError, choices_num.get_label, 3)

    def test_choices_num_enum_with_defined_ids(self):
        choices_num = ChoicesNumEnum(
            ('A', 'a', 4),
            ('B', 'b', 2),
            ('C', 'c')
        )
        assert_equal(choices_num.A, 4)
        assert_equal(choices_num.B, 2)
        assert_equal(choices_num.C, 3)
        assert_equal(list(choices_num.choices), [(4, 'a'), (2, 'b'), (3, 'c')])
        assert_equal(tuple(choices_num.all), (4, 2, 3))
        assert_equal(choices_num.get_label(4), 'a')
        assert_equal(choices_num.get_label(2), 'b')
        assert_equal(choices_num.get_label(3), 'c')

    def test_choices_num_enum_same_numbers_should_raise_exception(self):
        with assert_raises(ValueError):
            ChoicesNumEnum(
                ('A', 'a', 1), ('B', 'b', 1)
            )

    def test_choices_num_enum_same_generated_numbers_should_raise_exception(self):
        with assert_raises(ValueError):
            ChoicesNumEnum(
                ('A', 'a', 3), ('B', 'b', 2), ('C', 'c')
            )

    def test_choices_num_enum_invalid_num_raise_exception(self):
        with assert_raises(ValueError):
            ChoicesNumEnum(
                ('A', 'a', 'e'), ('B', 'b', 2)
            )

    def test_ordered_set_keep_order(self):
        ordered_set = OrderedSet(4, 5, 3)
        assert_equal(ordered_set, [4, 5, 3])
        ordered_set.add(8)
        assert_equal(ordered_set, [4, 5, 3, 8])
        assert_equal(ordered_set.pop(), 8)
        assert_equal(ordered_set.pop(False), 4)
        assert_equal(ordered_set, [5, 3])
        ordered_set |= OrderedSet(9, 10)
        assert_equal(ordered_set, [5, 3, 9, 10])
        assert_equal(ordered_set, {5, 3, 9, 10})
        ordered_set |= OrderedSet(5, 9)
        assert_equal(ordered_set, {5, 3, 9, 10})
        ordered_set.discard(9)
        assert_equal(ordered_set, {5, 3, 10})
        ordered_set.add(5)
        ordered_set.add(9)
        assert_equal(ordered_set, {5, 3, 10, 9})
