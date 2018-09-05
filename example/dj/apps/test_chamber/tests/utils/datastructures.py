from django.test import TestCase

from chamber.utils.datastructures import ChoicesEnum, ChoicesNumEnum, Enum, NumEnum, OrderedSet

from germanium.tools import assert_equal, assert_raises, assert_is_none, assert_in, assert_not_in


class DatastructuresTestCase(TestCase):

    def test_enum_should_contain_only_defined_values(self):
        enum = Enum(
            'A', 'B'
        )
        assert_equal(enum.A, 'A')
        assert_equal(enum.B, 'B')
        assert_equal(list(enum), ['A', 'B'])
        assert_equal(enum.all, ('A', 'B'))
        assert_equal(enum.get_name('A'), 'A')
        with assert_raises(AttributeError):
            enum.C  # pylint: disable=W0104
        assert_is_none(enum.get_name('C'))
        assert_in('A', enum)
        assert_in(enum.A, enum)
        assert_not_in('C', enum)

    def test_enum_with_distinct_key_and_value_should_contain_only_defined_values(self):
        enum = Enum(
            ('A', 'c'), ('B', 'd')
        )
        assert_equal(enum.A, 'c')
        assert_equal(enum.B, 'd')
        assert_equal(list(enum), ['c', 'd'])
        assert_equal(enum.all, ('c', 'd'))
        assert_equal(enum.get_name('c'), 'A')
        with assert_raises(AttributeError):
            enum.C  # pylint: disable=W0104
        assert_is_none(enum.get_name('f'))
        assert_in('c', enum)
        assert_in(enum.A, enum)
        assert_not_in('A', enum)

    def test_auto_gemerated_num_enum_should_contain_only_defined_values(self):
        enum = NumEnum(
            'A', 'B'
        )
        assert_equal(enum.A, 1)
        assert_equal(enum.B, 2)
        assert_equal(list(enum), [1, 2])
        assert_equal(enum.all, (1, 2))
        assert_equal(enum.get_name(1), 'A')
        with assert_raises(AttributeError):
            enum.C  # pylint: disable=W0104
        assert_is_none(enum.get_name(3))
        assert_in(1, enum)
        assert_in(enum.A, enum)
        assert_not_in('A', enum)

    def test_num_enum_with_defined_ids_should_return_valid_values(self):
        enum = NumEnum(
            ('A', 4), ('B', 2), 'C'
        )
        assert_equal(enum.A, 4)
        assert_equal(enum.B, 2)
        assert_equal(enum.C, 3)
        assert_equal(list(enum), [4, 2, 3])

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

    def test_num_enum_invalid_num_should_raise_exception(self):
        with assert_raises(ValueError):
            NumEnum(
                ('A', 'e'), ('B', 2)
            )

    def test_choices_enum_should_return_right_values_and_choices(self):
        choices_num = ChoicesEnum(
            ('A', 'label a'),
            ('B', 'label b'),
        )
        assert_equal(choices_num.A, 'A')
        assert_equal(choices_num.B, 'B')
        assert_equal(list(choices_num.choices), [('A', 'label a'), ('B', 'label b')])
        assert_equal(choices_num.all, ('A', 'B'))
        assert_equal(choices_num.get_label('A'), 'label a')
        assert_equal(choices_num.get_label('B'), 'label b')

    def test_choices_enum_with_distinct_key_and_value_should_return_right_values_and_choices(self):
        choices_num = ChoicesEnum(
            ('A', 'label a', 'c'),
            ('B', 'label b', 'd'),
        )
        assert_equal(choices_num.A, 'c')
        assert_equal(choices_num.B, 'd')
        assert_equal(list(choices_num.choices), [('c', 'label a'), ('d', 'label b')])
        assert_equal(choices_num.all, ('c', 'd'))
        assert_equal(choices_num.get_label('c'), 'label a')
        assert_equal(choices_num.get_label('d'), 'label b')

    def test_choices_num_enum_should_return_right_values_and_choices(self):
        choices_num = ChoicesNumEnum(
            ('A', 'label a'),
            ('B', 'label b'),
        )
        assert_equal(choices_num.A, 1)
        assert_equal(choices_num.B, 2)
        assert_equal(list(choices_num.choices), [(1, 'label a'), (2, 'label b')])
        assert_equal(tuple(choices_num.all), (1, 2))
        assert_equal(choices_num.get_label(1), 'label a')
        assert_equal(choices_num.get_label(2), 'label b')
        assert_raises(AttributeError, choices_num.get_label, 3)

    def test_choices_num_enum_with_defined_ids_should_return_right_values_and_choices(self):
        choices_num = ChoicesNumEnum(
            ('A', 'label a', 4),
            ('B', 'label b', 2),
            ('C', 'label c')
        )
        assert_equal(choices_num.A, 4)
        assert_equal(choices_num.B, 2)
        assert_equal(choices_num.C, 3)
        assert_equal(list(choices_num.choices), [(4, 'label a'), (2, 'label b'), (3, 'label c')])
        assert_equal(choices_num.all, (4, 2, 3))
        assert_equal(choices_num.get_label(4), 'label a')
        assert_equal(choices_num.get_label(2), 'label b')
        assert_equal(choices_num.get_label(3), 'label c')

    def test_choices_num_enum_same_numbers_should_raise_exception(self):
        with assert_raises(ValueError):
            ChoicesNumEnum(
                ('A', 'label a', 1), ('B', 'label b', 1)
            )

    def test_choices_num_enum_same_generated_numbers_should_raise_exception(self):
        with assert_raises(ValueError):
            ChoicesNumEnum(
                ('A', 'label a', 3), ('B', 'label b', 2), ('C', 'label c')
            )

    def test_choices_num_enum_invalid_num_raise_exception(self):
        with assert_raises(ValueError):
            ChoicesNumEnum(
                ('A', 'label a', 'e'), ('B', 'label b', 2)
            )

    def test_enum_key_should_have_right_format(self):
        with assert_raises(ValueError):
            Enum(
                1, 2
            )
        with assert_raises(ValueError):
            Enum(
                '1A', 'B'
            )
        with assert_raises(ValueError):
            Enum(
                'A-B', 'B'
            )
        Enum(
            'A_B_3', 'B'
        )

    def test_ordered_set_should_keep_order(self):
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
