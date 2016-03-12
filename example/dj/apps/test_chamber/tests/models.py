from __future__ import unicode_literals

from datetime import timedelta

from django.test import TestCase
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
from django.core.exceptions import ValidationError

from germanium.tools import assert_equal, assert_raises, assert_true, assert_false

from test_chamber.models import DiffModel, ComparableModel, TestSmartModel

from chamber.models import Comparator
from chamber.exceptions import PersistenceException


class NameComparator(Comparator):

    def compare(self, a, b):
        return a.name == b.name


class TestProxySmartModel(TestSmartModel):

    def clean_name(self):
        if len(self.name) >= 10:
            raise ValidationError('name must be lower than 10')

    class Meta:
        proxy = True


class TestPreProxySmartModel(TestSmartModel):

    def _pre_save(self, *args, **kwargs):
        self.name = 'test pre save'

    def _pre_delete(self, *args, **kwargs):
        self.name = 'test pre delete'

    class Meta:
        proxy = True


class TestPostProxySmartModel(TestSmartModel):

    def _post_save(self, *args, **kwargs):
        self.name = 'test post save'

    def _post_delete(self, *args, **kwargs):
        self.name = 'test post delete'

    class Meta:
        proxy = True


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

    def test_smart_model_clean_pre_save(self):
        assert_raises(PersistenceException, TestProxySmartModel.objects.create, name=10 * 'a')
        obj = TestProxySmartModel.objects.create(name=9 * 'a')
        obj.name = 11 * 'a'
        assert_raises(PersistenceException, obj.save)
        assert_equal(len(TestProxySmartModel.objects.get(pk=obj.pk).name), 9)
        obj.save(clean_pre_save=False)
        assert_equal(len(TestProxySmartModel.objects.get(pk=obj.pk).name), 11)

    def test_smart_model_clean_post_save(self):
        class PostSaveTestProxySmartModel(TestProxySmartModel):
            class Meta:
                proxy = True

            class SmartMeta:
                clean_pre_save = False
                clean_post_save = True

        assert_false(PostSaveTestProxySmartModel.objects.filter(name=10 * 'a').exists())
        assert_raises(PersistenceException, PostSaveTestProxySmartModel.objects.create, name=10 * 'a')
        assert_true(PostSaveTestProxySmartModel.objects.filter(name=10 * 'a').exists())
        obj = PostSaveTestProxySmartModel.objects.create(name=9 * 'a')
        obj.name = 11 * 'a'
        assert_raises(PersistenceException, obj.save)
        assert_equal(len(PostSaveTestProxySmartModel.objects.get(pk=obj.pk).name), 11)
        obj.name = 12 * 'a'
        obj.save(clean_post_save=False)
        assert_equal(len(PostSaveTestProxySmartModel.objects.get(pk=obj.pk).name), 12)

    def test_smart_model_clean_atomic_post_save(self):
        class AtomicPostSaveTestProxySmartModel(TestProxySmartModel):
            class Meta:
                proxy = True

            class SmartMeta:
                clean_pre_save = False
                clean_post_save = True
                atomic_save = True

        assert_false(AtomicPostSaveTestProxySmartModel.objects.filter(name=10 * 'a').exists())
        assert_raises(PersistenceException, AtomicPostSaveTestProxySmartModel.objects.create, name=10 * 'a')
        assert_false(AtomicPostSaveTestProxySmartModel.objects.filter(name=10 * 'a').exists())
        obj = AtomicPostSaveTestProxySmartModel.objects.create(name=9 * 'a')
        obj.name = 11 * 'a'
        assert_raises(PersistenceException, obj.save)
        assert_equal(len(AtomicPostSaveTestProxySmartModel.objects.get(pk=obj.pk).name), 9)
        obj.name = 12 * 'a'
        obj.save(clean_post_save=False)
        assert_equal(len(AtomicPostSaveTestProxySmartModel.objects.get(pk=obj.pk).name), 12)

    def test_smart_model_clean_pre_delete(self):
        class PreDeleteTestProxySmartModel(TestProxySmartModel):
            class Meta:
                proxy = True

            class SmartMeta:
                clean_pre_save = False
                clean_pre_delete = True

        obj = PreDeleteTestProxySmartModel.objects.create(name=10 * 'a')
        obj_pk = obj.pk
        assert_raises(PersistenceException, obj.delete)
        assert_true(PreDeleteTestProxySmartModel.objects.filter(pk=obj_pk).exists())

        obj = PreDeleteTestProxySmartModel.objects.create(name=10 * 'a')
        obj_pk = obj.pk
        obj.delete(clean_pre_delete=False)
        assert_false(PreDeleteTestProxySmartModel.objects.filter(pk=obj_pk).exists())


    def test_smart_model_clean_post_delete(self):
        class PostDeleteTestProxySmartModel(TestProxySmartModel):
            class Meta:
                proxy = True

            class SmartMeta:
                clean_pre_save = False
                clean_post_delete = True

        obj = PostDeleteTestProxySmartModel.objects.create(name=10 * 'a')
        obj_pk = obj.pk
        assert_raises(PersistenceException, obj.delete)
        assert_false(PostDeleteTestProxySmartModel.objects.filter(pk=obj_pk).exists())

        obj = PostDeleteTestProxySmartModel.objects.create(name=10 * 'a')
        obj_pk = obj.pk
        obj.delete(clean_post_delete=False)
        assert_false(PostDeleteTestProxySmartModel.objects.filter(pk=obj_pk).exists())

    def test_smart_model_clean_atomic_post_delete(self):
        class AtomicPostDeleteTestProxySmartModel(TestProxySmartModel):
            class Meta:
                proxy = True

            class SmartMeta:
                clean_pre_save = False
                clean_post_delete = True
                atomic_delete = True

        obj = AtomicPostDeleteTestProxySmartModel.objects.create(name=10 * 'a')
        obj_pk = obj.pk
        assert_raises(PersistenceException, obj.delete)
        assert_true(AtomicPostDeleteTestProxySmartModel.objects.filter(pk=obj_pk).exists())

        obj = AtomicPostDeleteTestProxySmartModel.objects.create(name=10 * 'a')
        obj_pk = obj.pk
        obj.delete(clean_post_delete=False)
        assert_false(AtomicPostDeleteTestProxySmartModel.objects.filter(pk=obj_pk).exists())

    def test_smart_model_pre_save(self):
        obj = TestPreProxySmartModel.objects.create()
        assert_equal(obj.name, 'test pre save')
        obj.name = 10 * 'a'
        obj.save()
        assert_equal(obj.name, 'test pre save')
        assert_true(TestPreProxySmartModel.objects.filter(name='test pre save').exists())

    def test_smart_model_pre_delete(self):
        obj = TestPreProxySmartModel.objects.create()
        assert_equal(obj.name, 'test pre save')
        obj.delete()
        assert_equal(obj.name, 'test pre delete')

    def test_smart_model_post_save(self):
        assert_raises(PersistenceException, TestPostProxySmartModel.objects.create)
        obj = TestPostProxySmartModel.objects.create(name=10 * 'a')
        assert_equal(obj.name, 'test post save')
        assert_false(TestPreProxySmartModel.objects.filter(name='test post save').exists())
        assert_true(TestPreProxySmartModel.objects.filter(name=10 * 'a').exists())
        obj.save()
        assert_true(TestPreProxySmartModel.objects.filter(name='test post save').exists())
        obj.name = 10 * 'a'
        obj.save()
        assert_equal(obj.name, 'test post save')
        assert_false(TestPreProxySmartModel.objects.filter(name='test post save').exists())

    def test_smart_model_post_delete(self):
        obj = TestPostProxySmartModel.objects.create(name=10 * 'a')
        assert_equal(obj.name, 'test post save')
        obj.delete()
        assert_equal(obj.name, 'test post delete')
