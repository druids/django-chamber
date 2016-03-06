from __future__ import unicode_literals

from datetime import timedelta

from django.test import TestCase
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone

from germanium.tools import assert_equal, assert_raises, assert_true, assert_false

from test_chamber.models import DiffModel, ComparableModel, CleanedSmartModel, NotCleanedSmartModel

from chamber.models import Comparator
from chamber.exceptions import PersistenceException


class NameComparator(Comparator):

    def compare(self, a, b):
        return a.name == b.name


class ModelsTestCase(TestCase):

    def test_model_diff(self):
        obj = DiffModel.objects.create(name='test', datetime=timezone.now(), number=2)
        assert_false(obj.has_changed)
        obj.name = 'test2'
        assert_true(obj.has_changed)
        assert_equal(obj.changed_fields, {'name'})
        assert_equal(obj.get_field_diff('name'), ('test', 'test2'))

        obj.name = 'test'
        assert_false(obj.has_changed)
        assert_false(obj.changed_fields)

        obj.name = 'test2'
        obj.number = 3
        obj.datetime = obj.datetime + timedelta(days=2)
        assert_true(obj.has_changed)
        assert_equal(obj.changed_fields, {'name', 'number', 'datetime'})

        obj.save()
        assert_false(obj.has_changed)
        assert_false(obj.changed_fields)

    def test_comparator(self):
        obj1 = ComparableModel.objects.create(name='test')
        obj2 = ComparableModel.objects.create(name='test')
        obj3 = ComparableModel.objects.create(name='test2')
        comparator = NameComparator()

        assert_true(obj1.equals(obj2, comparator))
        assert_true(obj2.equals(obj1, comparator))

        assert_false(obj1.equals(obj3, comparator))
        assert_false(obj3.equals(obj1, comparator))

    def test_cleaned_smart_model(self):
        assert_raises(PersistenceException, CleanedSmartModel.objects.create, name=9 * 'a')
        obj = CleanedSmartModel.objects.create(name=10 * 'a')
        obj.name = 9 * 'a'
        assert_raises(PersistenceException, obj.save)
        assert_equal(obj.number, 11)
        obj.name = 12 * 'a'
        obj.number = 10
        assert_raises(PersistenceException, obj.save)
        assert_equal(obj.number, 10)

    def test_not_cleaned_smart_model(self):
        obj = NotCleanedSmartModel.objects.create(name=9 * 'a')
        assert_equal(obj.number, 11)
        obj.number = 10
        assert_raises(PersistenceException, obj.save)
        assert_equal(obj.number, 10)