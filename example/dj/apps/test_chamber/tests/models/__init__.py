from datetime import timedelta

from django.db import OperationalError
from django.core.exceptions import ValidationError
from django.test import TransactionTestCase
from django.utils import timezone

from chamber.exceptions import PersistenceException
from chamber.models import DynamicChangedFields, Comparator, Unknown, Deferred

from germanium.tools import assert_equal, assert_false, assert_raises, assert_true  # pylint: disable=E0401

from test_chamber.models import ComparableModel, DiffModel, RelatedSmartModel, TestSmartModel  # pylint: disable=E0401

from .dispatchers import *  # NOQA
from .fields import *  # NOQA
from .humanized_helpers import *  # NOQA


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

    def __init__(self, **kwargs):
        self.name = None
        super(TestPreProxySmartModel, self).__init__(**kwargs)

    def _pre_save(self, *args, **kwargs):
        self.name = 'test pre save'

    def _pre_delete(self, *args, **kwargs):
        self.name = 'test pre delete'

    class Meta:
        proxy = True


class TestPostProxySmartModel(TestSmartModel):

    def __init__(self, **kwargs):
        self.name = None
        super(TestPostProxySmartModel, self).__init__(**kwargs)

    def _post_save(self, *args, **kwargs):
        self.name = 'test post save'

    def _post_delete(self, *args, **kwargs):
        self.name = 'test post delete'

    class Meta:
        proxy = True


class ModelsTestCase(TransactionTestCase):

    def test_smart_model_initial_values_should_be_unknown_for_not_saved_instance(self):
        obj = DiffModel(name='test', datetime=timezone.now(), number=2)
        assert_true(obj.has_changed)
        assert_true(obj.changed_fields)
        assert_equal(set(obj.changed_fields.keys()), {'created_at', 'changed_at', 'id', 'datetime', 'name', 'number'})
        assert_true(obj.is_adding)
        assert_false(obj.is_changing)
        assert_true(all(v is Unknown for v in obj.initial_values.values()))
        assert_true(all(not bool(v) for v in obj.initial_values.values()))

        obj.save()
        assert_false(obj.has_changed)
        assert_false(obj.changed_fields)
        assert_false(obj.is_adding)
        assert_true(obj.is_changing)
        assert_true(all(v is not Unknown for v in obj.initial_values.values()))

        obj = DiffModel.objects.get(pk=obj.pk)
        assert_false(obj.has_changed)
        assert_false(obj.changed_fields)
        assert_false(obj.is_adding)
        assert_true(obj.is_changing)
        assert_true(all(v is not Unknown for v in obj.initial_values.values()))

        assert_equal(str(Unknown), 'unknown')

    def test_smart_model_initial_values_should_be_deferred_for_partly_loaded_instance(self):
        obj = DiffModel.objects.only('name').get(
            pk=DiffModel.objects.create(name='test', datetime=timezone.now(), number=2).pk
        )

        assert_false(obj.has_changed)
        assert_false(obj.changed_fields)
        assert_false(obj.is_adding)
        assert_true(obj.is_changing)
        assert_true(all(v is Deferred for k, v in obj.initial_values.items() if k not in {'id', 'name'}))
        assert_true(all(not bool(v) for k, v in obj.initial_values.items() if k not in {'id', 'name'}))

        assert_equal(obj.number, 2)
        assert_false(obj.has_changed)
        assert_false(obj.changed_fields)
        assert_equal(obj.initial_values['number'], 2)

        obj.datetime = timezone.now()
        assert_equal(obj.initial_values['datetime'], Deferred)
        assert_true(obj.changed_fields)
        assert_equal(obj.changed_fields.keys(), {'datetime'})
        assert_equal(str(Deferred), 'deferred')

    def test_smart_model_changed_fields(self):
        obj = TestProxySmartModel.objects.create(name='a')
        changed_fields = DynamicChangedFields(obj)
        assert_equal(len(changed_fields), 4)
        changed_fields.from_db()
        assert_equal(len(changed_fields), 0)
        obj.name = 'b'
        assert_equal(len(changed_fields), 1)
        assert_equal(changed_fields['name'].initial, 'a')
        assert_equal(changed_fields['name'].current, 'b')
        assert_equal(changed_fields.changed_values, {'name': 'b'})
        assert_equal(str(changed_fields), "{'name': ValueChange(initial='a', current='b')}")
        assert_true(changed_fields.has_key('name'))
        assert_false(changed_fields.has_key('changed_at'))
        assert_equal(list(changed_fields.values()), [changed_fields['name']])
        assert_equal(changed_fields.keys(), {'name'})

        static_changed_fields = changed_fields.get_static_changes()
        obj.save()

        # Initial values is not changed
        assert_equal(len(changed_fields), 2)
        assert_equal(len(static_changed_fields), 1)
        assert_equal(set(changed_fields.keys()), {'name', 'changed_at'})
        assert_equal(set(static_changed_fields.keys()), {'name'})
        assert_equal(changed_fields['name'].initial, 'a')
        assert_equal(changed_fields['name'].current, 'b')

        assert_true(changed_fields.has_any_key('name', 'crated_at'))
        assert_false(changed_fields.has_any_key('invalid', 'crated_at'))

        assert_raises(AttributeError, changed_fields.__delitem__, 'name')
        assert_raises(AttributeError, changed_fields.clear)
        assert_raises(AttributeError, changed_fields.pop, 'name')
        assert_raises(AttributeError, changed_fields.__setitem__, 'name', 'value')

        obj.name = 'b'

    def test_model_diff(self):
        obj = DiffModel.objects.create(name='test', datetime=timezone.now(), number=2)
        assert_false(obj.has_changed)
        obj.name = 'test2'
        assert_true(obj.has_changed)
        assert_equal(set(obj.changed_fields.keys()), {'name'})
        assert_equal((obj.changed_fields['name'].initial, obj.changed_fields['name'].current), ('test', 'test2'))

        obj.name = 'test'
        assert_false(obj.has_changed)
        assert_false(obj.changed_fields)

        obj.name = 'test2'
        obj.number = 3
        obj.datetime = obj.datetime + timedelta(days=2)
        assert_true(obj.has_changed)
        assert_equal(set(obj.changed_fields.keys()), {'name', 'number', 'datetime'})

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

    def test_should_raise_exception_due_calling_default_comparator(self):
        obj1 = ComparableModel.objects.create(name='test')
        obj2 = ComparableModel.objects.create(name='test')

        assert_raises(NotImplementedError, obj1.equals, obj2, Comparator())

    def test_smart_model_clean_pre_save(self):
        assert_raises(PersistenceException, TestProxySmartModel.objects.create, name=10 * 'a')
        obj = TestProxySmartModel.objects.create(name=9 * 'a')
        obj.name = 11 * 'a'
        assert_raises(PersistenceException, obj.save)
        assert_equal(len(TestProxySmartModel.objects.get(pk=obj.pk).name), 9)
        obj.save(is_cleaned_pre_save=False)
        assert_equal(len(TestProxySmartModel.objects.get(pk=obj.pk).name), 11)

    def test_smart_model_clean_post_save(self):
        class PostSaveTestProxySmartModel(TestProxySmartModel):
            class Meta:
                proxy = True
                verbose_name = 'testmodel'
                verbose_name_plural = 'testmodels'

            class SmartMeta:
                is_cleaned_pre_save = False
                is_cleaned_post_save = True

        assert_false(PostSaveTestProxySmartModel.objects.filter(name=10 * 'a').exists())
        assert_raises(PersistenceException, PostSaveTestProxySmartModel.objects.create, name=10 * 'a')
        assert_true(PostSaveTestProxySmartModel.objects.filter(name=10 * 'a').exists())
        obj = PostSaveTestProxySmartModel.objects.create(name=9 * 'a')
        obj.name = 11 * 'a'
        assert_raises(PersistenceException, obj.save)
        assert_equal(len(PostSaveTestProxySmartModel.objects.get(pk=obj.pk).name), 11)
        obj.name = 12 * 'a'
        obj.save(is_cleaned_post_save=False)
        assert_equal(len(PostSaveTestProxySmartModel.objects.get(pk=obj.pk).name), 12)

    def test_smart_model_clean_atomic_post_save(self):
        class AtomicPostSaveTestProxySmartModel(TestProxySmartModel):
            class Meta:
                proxy = True
                verbose_name = 'testmodel'
                verbose_name_plural = 'testmodels'

            class SmartMeta:
                is_cleaned_pre_save = False
                is_cleaned_post_save = True
                is_save_atomic = True

        assert_false(AtomicPostSaveTestProxySmartModel.objects.filter(name=10 * 'a').exists())
        assert_raises(PersistenceException, AtomicPostSaveTestProxySmartModel.objects.create, name=10 * 'a')
        assert_false(AtomicPostSaveTestProxySmartModel.objects.filter(name=10 * 'a').exists())
        obj = AtomicPostSaveTestProxySmartModel.objects.create(name=9 * 'a')
        obj.name = 11 * 'a'
        assert_raises(PersistenceException, obj.save)
        assert_equal(len(AtomicPostSaveTestProxySmartModel.objects.get(pk=obj.pk).name), 9)
        obj.name = 12 * 'a'
        obj.save(is_cleaned_post_save=False)
        assert_equal(len(AtomicPostSaveTestProxySmartModel.objects.get(pk=obj.pk).name), 12)

    def test_smart_model_clean_pre_delete(self):
        class PreDeleteTestProxySmartModel(TestProxySmartModel):
            class Meta:
                proxy = True
                verbose_name = 'testmodel'
                verbose_name_plural = 'testmodels'

            class SmartMeta:
                is_cleaned_pre_save = False
                is_cleaned_pre_delete = True

        obj = PreDeleteTestProxySmartModel.objects.create(name=10 * 'a')
        obj_pk = obj.pk
        assert_raises(PersistenceException, obj.delete)
        assert_true(PreDeleteTestProxySmartModel.objects.filter(pk=obj_pk).exists())

        obj = PreDeleteTestProxySmartModel.objects.create(name=10 * 'a')
        obj_pk = obj.pk
        obj.delete(is_cleaned_pre_delete=False)
        assert_false(PreDeleteTestProxySmartModel.objects.filter(pk=obj_pk).exists())

    def test_smart_model_clean_post_delete(self):
        class PostDeleteTestProxySmartModel(TestProxySmartModel):
            class Meta:
                proxy = True
                verbose_name = 'testmodel'
                verbose_name_plural = 'testmodels'

            class SmartMeta:
                is_cleaned_pre_save = False
                is_cleaned_post_delete = True

        obj = PostDeleteTestProxySmartModel.objects.create(name=10 * 'a')
        obj_pk = obj.pk
        assert_raises(PersistenceException, obj.delete)
        assert_false(PostDeleteTestProxySmartModel.objects.filter(pk=obj_pk).exists())

        obj = PostDeleteTestProxySmartModel.objects.create(name=10 * 'a')
        obj_pk = obj.pk
        obj.delete(is_cleaned_post_delete=False)
        assert_false(PostDeleteTestProxySmartModel.objects.filter(pk=obj_pk).exists())

    def test_smart_model_clean_atomic_post_delete(self):
        class AtomicPostDeleteTestProxySmartModel(TestProxySmartModel):
            class Meta:
                proxy = True
                verbose_name = 'testmodel'
                verbose_name_plural = 'testmodels'

            class SmartMeta:
                is_cleaned_pre_save = False
                is_cleaned_post_delete = True
                is_delete_atomic = True

        obj = AtomicPostDeleteTestProxySmartModel.objects.create(name=10 * 'a')
        obj_pk = obj.pk
        assert_raises(PersistenceException, obj.delete)
        assert_true(AtomicPostDeleteTestProxySmartModel.objects.filter(pk=obj_pk).exists())

        obj = AtomicPostDeleteTestProxySmartModel.objects.create(name=10 * 'a')
        obj_pk = obj.pk
        obj.delete(is_cleaned_post_delete=False)
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

    def test_smart_queryset_fast_distinct(self):
        t = TestSmartModel.objects.create(name='name')
        RelatedSmartModel.objects.create(test_smart_model=t)
        RelatedSmartModel.objects.create(test_smart_model=t)
        qs = TestSmartModel.objects.filter(test_smart_models__test_smart_model=t)
        assert_equal(qs.count(), 2)
        assert_equal(tuple(qs.values_list('pk', flat=True)), (t.pk, t.pk))
        assert_equal(qs.fast_distinct().count(), 1)

    def test_smart_queryset_fast_distinct_should_keep_ordering(self):
        TestSmartModel.objects.create(name='a')
        TestSmartModel.objects.create(name='b')
        TestSmartModel.objects.create(name='c')

        assert_equal(
            list(TestSmartModel.objects.order_by('name').fast_distinct().values_list('name', flat=True)),
            ['a', 'b', 'c']
        )
        assert_equal(
            list(TestSmartModel.objects.order_by('-name').fast_distinct().values_list('name', flat=True)),
            ['c', 'b', 'a']
        )

    def test_smart_model_first_and_last_with_order(self):
        test3 = TestSmartModel.objects.create(name='3')
        test2 = TestSmartModel.objects.create(name='2')
        test1 = TestSmartModel.objects.create(name='1')

        assert_equal(TestSmartModel.objects.first('id'), test3)
        assert_equal(TestSmartModel.objects.last('id'), test1)

        assert_equal(TestSmartModel.objects.first('name'), test1)
        assert_equal(TestSmartModel.objects.last('name'), test3)

        assert_equal(TestSmartModel.objects.filter(name='2').first(), test2)
        assert_equal(TestSmartModel.objects.filter(name='2').last(), test2)

    def test_smart_model_str_method(self):
        obj = TestSmartModel.objects.create(name='1')
        assert_equal(str(obj), 'test smart model #{}'.format(obj.pk))

        unstored_obj = TestSmartModel(name='1')
        assert_equal(str(unstored_obj), 'test smart model #None')

    def test_smart_model_get_locked_instance(self):
        not_saved_obj = TestSmartModel()

        assert_raises(OperationalError, not_saved_obj.get_locked_instance)

        obj = TestSmartModel.objects.create(name='1')
        assert_equal(obj, obj.get_locked_instance())
