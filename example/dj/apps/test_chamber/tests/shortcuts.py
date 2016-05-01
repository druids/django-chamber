from __future__ import unicode_literals

from datetime import date, datetime

from django.test import TestCase
from django.core.exceptions import MultipleObjectsReturned, FieldError
from django.utils import timezone
from django.http.response import Http404

from germanium.tools import assert_equal, assert_raises, assert_is_none

from test_chamber.models import ShortcutsModel

from chamber.shortcuts import get_object_or_404, get_object_or_none, distinct_field, filter_by_date, exclude_by_date


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
