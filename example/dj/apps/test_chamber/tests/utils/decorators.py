from django.test import TestCase
from django.utils.translation import get_language

from chamber.utils.decorators import classproperty, singleton, translation_activate_block

from germanium.tools import assert_equal  # pylint: disable=E0401


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
