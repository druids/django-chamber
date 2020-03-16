from django.test import TestCase
from django.utils.translation import get_language

from chamber.utils.decorators import classproperty, singleton, translation_activate_block
from chamber.utils.transaction import atomic, atomic_with_signals

from germanium.tools import assert_equal, assert_raises, assert_false  # pylint: disable=E0401

from test_chamber.models import CSVRecord


class ObjectWithClassProperty(object):

    @classproperty
    @classmethod
    def class_method_property(cls):
        return 1


@singleton
class SingletonObject(object):

    num_singletons = 0

    def __init__(self):
        self.num_singletons += 1
        super(self.__class__, self).__init__()

    def get_count_singletons(self):
        return self.num_singletons


class DecoratorsTestCase(TestCase):

    def test_class_property(self):
        assert_equal(ObjectWithClassProperty.class_method_property, 1)
        assert_equal(ObjectWithClassProperty().class_method_property, 1)

    def test_singleton(self):
        singleton = SingletonObject()
        assert_equal(singleton.num_singletons, 1)
        singleton = SingletonObject()
        assert_equal(singleton.num_singletons, 1)

    def test_translation_activate_block(self):

        @translation_activate_block(language='en')
        def en_block():
            assert_equal(get_language(), 'en')

        assert_equal(get_language(), 'cs')
        en_block()
        assert_equal(get_language(), 'cs')

    def test_atomic_should_be_to_use_as_a_decorator(self):
        @atomic
        def change_object_and_raise_exception():
            CSVRecord.objects.create(
                name='test',
                number=1
            )
            raise RuntimeError('test')

        with assert_raises(RuntimeError):
            change_object_and_raise_exception()

        assert_false(CSVRecord.objects.exists())

    def test_atomic_should_be_to_use_as_a_context_manager(self):
        with assert_raises(RuntimeError):
            with atomic():
                CSVRecord.objects.create(
                    name='test',
                    number=1
                )
                raise RuntimeError('test')

        assert_false(CSVRecord.objects.exists())

    def test_atomic_with_signals_should_be_to_use_as_a_decorator(self):
        @atomic_with_signals
        def change_object_and_raise_exception():
            CSVRecord.objects.create(
                name='test',
                number=1
            )
            raise RuntimeError('test')

        with assert_raises(RuntimeError):
            change_object_and_raise_exception()

        assert_false(CSVRecord.objects.exists())

    def test_atomic_with_signals_should_be_to_use_as_a_context_manager(self):
        with assert_raises(RuntimeError):
            with atomic_with_signals():
                CSVRecord.objects.create(
                    name='test',
                    number=1
                )
                raise RuntimeError('test')

        assert_false(CSVRecord.objects.exists())
