from datetime import date, datetime

from django.core.exceptions import FieldError, MultipleObjectsReturned
from django.http.response import Http404
from django.test import TestCase
from django.utils import timezone

from chamber.shortcuts import (
    bulk_change, bulk_change_and_save, bulk_save, change, change_and_save, distinct_field,
    exclude_by_date, filter_by_date, get_object_or_404, get_object_or_none
)

from germanium.tools import assert_equal, assert_is_none, assert_raises  # pylint: disable=E0401

from test_chamber.models import ShortcutsModel, DiffModel


class ShortcutsTestCase(TestCase):

    def test_get_object_or_none(self):
        obj = ShortcutsModel.objects.create(name='test1', datetime=timezone.now(), number=1)
        ShortcutsModel.objects.create(name='test2', datetime=timezone.now(), number=2)
        ShortcutsModel.objects.create(name='test2', datetime=timezone.now(), number=3)

        assert_equal(get_object_or_none(ShortcutsModel, name='test1'), obj)
        assert_is_none(get_object_or_none(ShortcutsModel, name='test3'))
        assert_is_none(get_object_or_none(ShortcutsModel, number='test3'))
        assert_is_none(get_object_or_none(ShortcutsModel, datetime='test3'))

        assert_raises(FieldError, get_object_or_none, ShortcutsModel, non_field='test2')
        assert_raises(MultipleObjectsReturned, get_object_or_none, ShortcutsModel, name='test2')

    def test_get_object_or_404(self):
        obj = ShortcutsModel.objects.create(name='test1', datetime=timezone.now(), number=1)
        ShortcutsModel.objects.create(name='test2', datetime=timezone.now(), number=2)
        ShortcutsModel.objects.create(name='test2', datetime=timezone.now(), number=3)

        assert_equal(get_object_or_404(ShortcutsModel, name='test1'), obj)
        assert_raises(Http404, get_object_or_404, ShortcutsModel, name='test3')
        assert_raises(Http404, get_object_or_404, ShortcutsModel, number='test3')
        assert_raises(Http404, get_object_or_404, ShortcutsModel, datetime='test3')

        assert_raises(FieldError, get_object_or_none, ShortcutsModel, non_field='test2')
        assert_raises(MultipleObjectsReturned, get_object_or_none, ShortcutsModel, name='test2')

    def test_distinct_fields(self):
        ShortcutsModel.objects.create(name='test1', datetime=timezone.now(), number=1)
        ShortcutsModel.objects.create(name='test2', datetime=timezone.now(), number=2)
        ShortcutsModel.objects.create(name='test2', datetime=timezone.now(), number=3)
        assert_equal(tuple(distinct_field(ShortcutsModel, 'name')), (('test1',), ('test2',)))
        assert_equal(list(distinct_field(ShortcutsModel, 'name', flat=True)), ['test1', 'test2'])

    def test_filter_and_exclude_by_date(self):
        ShortcutsModel.objects.create(name='test1', datetime=timezone.now(), number=1)
        ShortcutsModel.objects.create(name='test1', datetime=timezone.now(), number=1)
        ShortcutsModel.objects.create(name='test1', datetime=timezone.make_aware(datetime(2014, 1, 1, 12, 12),
                                                                                 timezone.get_default_timezone()),
                                      number=1)
        assert_equal(filter_by_date(ShortcutsModel, datetime=date.today()).count(), 2)
        assert_equal(filter_by_date(ShortcutsModel, datetime=date(2014, 1, 1)).count(), 1)

        assert_equal(exclude_by_date(ShortcutsModel, datetime=date.today()).count(), 1)
        assert_equal(exclude_by_date(ShortcutsModel, datetime=date(2014, 1, 1)).count(), 2)

    def test_change(self):
        obj = ShortcutsModel.objects.create(name='test1', datetime=timezone.now(), number=1)
        change(obj, name='modified')
        assert_equal(obj.name, 'modified')
        assert_equal(ShortcutsModel.objects.first().name, 'test1')  # instance is changed but NOT saved to DB

    def test_change_and_save(self):
        obj = ShortcutsModel.objects.create(name='test1', datetime=timezone.now(), number=1)
        change_and_save(obj, name='modified')
        assert_equal(obj.name, 'modified')
        assert_equal(ShortcutsModel.objects.first().name, 'modified')  # instance is changed and saved to DB

    def test_change_and_save_with_update_only_changed_fields_should_change_only_defined_fields(self):
        obj = DiffModel.objects.create(name='test', datetime=timezone.now(), number=2)
        DiffModel.objects.filter(pk=obj.pk).update(name='test2')
        obj.change_and_save(number=3, update_only_changed_fields=True)
        obj.refresh_from_db()
        assert_equal(obj.name, 'test2')
        assert_equal(obj.number, 3)

    def test_model_change(self):
        obj = DiffModel.objects.create(name='test', datetime=timezone.now(), number=2)
        DiffModel.objects.filter(pk=obj.pk).update(name='test2')
        obj.change(number=3)
        assert_equal(obj.number, 3)

    def test_bulk_change_and_save(self):
        obj1 = ShortcutsModel.objects.create(name='test1', datetime=timezone.now(), number=1)
        obj2 = ShortcutsModel.objects.create(name='test2', datetime=timezone.now(), number=2)
        bulk_change_and_save([obj1, obj2], name='modified')
        assert_equal(obj1.name, 'modified')
        assert_equal(obj2.name, 'modified')
        assert_equal(ShortcutsModel.objects.first().name, 'modified')  # instance is changed but NOT saved to DB
        assert_equal(ShortcutsModel.objects.last().name, 'modified')  # instance is changed but NOT saved to DB

    def test_bulk_change_and_bulk_save(self):
        obj1 = ShortcutsModel.objects.create(name='test1', datetime=timezone.now(), number=1)
        obj2 = ShortcutsModel.objects.create(name='test2', datetime=timezone.now(), number=2)

        # Bulk change objects
        bulk_change([obj1, obj2], name='modified')
        assert_equal(obj1.name, 'modified')
        assert_equal(obj2.name, 'modified')
        assert_equal(ShortcutsModel.objects.first().name, 'test1')  # instance is changed but NOT saved to DB
        assert_equal(ShortcutsModel.objects.last().name, 'test2')  # instance is changed but NOT saved to DB

        # Bulk save objects
        bulk_save([obj1, obj2])
        assert_equal(ShortcutsModel.objects.first().name, 'modified')  # instance is changed but saved to DB
        assert_equal(ShortcutsModel.objects.last().name, 'modified')  # instance is changed but saved to DB

    def test_queryset_change_and_save(self):
        obj1 = DiffModel.objects.create(name='test', datetime=timezone.now(), number=2)
        obj2 = DiffModel.objects.create(name='test', datetime=timezone.now(), number=2)
        DiffModel.objects.all().change_and_save(name='modified')
        obj1.refresh_from_db()
        obj2.refresh_from_db()
        assert_equal(obj1.name, 'modified')
        assert_equal(obj2.name, 'modified')
