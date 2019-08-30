import collections

from itertools import chain

from distutils.version import StrictVersion

import django
from django.db import models, transaction
from django.db.models.base import ModelBase
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import cached_property

from chamber.exceptions import PersistenceException
from chamber.patch import Options
from chamber.shortcuts import change_and_save, change, bulk_change_and_save
from chamber.utils.decorators import singleton

from .fields import *  # NOQA exposing classes and functions as a module API
from .signals import dispatcher_post_save, dispatcher_pre_save


def many_to_many_field_to_dict(field, instance):
    if instance.pk is None:
        # If the object doesn't have a primary key yet, just use an empty
        # list for its m2m fields. Calling f.value_from_object will raise
        # an exception.
        return []
    else:
        # MultipleChoiceWidget needs a list of pks, not object instances.
        return list(field.value_from_object(instance).values_list('pk', flat=True))


def should_exclude_field(field, fields, exclude):
    return (fields and field.name not in fields) or (exclude and field.name in exclude)


def field_to_dict(field, instance):
    """
    Converts a model field to a dictionary
    """
    # avoid a circular import
    from django.db.models.fields.related import ManyToManyField

    return (many_to_many_field_to_dict(field, instance) if isinstance(field, ManyToManyField)
            else field.value_from_object(instance))


@singleton
class UnknownSingleton:

    def __repr__(self):
        return 'unknown'

    def __bool__(self):
        return False


Unknown = UnknownSingleton()


def unknown_model_fields_to_dict(instance, fields=None, exclude=None):

    return {
        field.name: Unknown
        for field in chain(instance._meta.concrete_fields, instance._meta.many_to_many)  # pylint: disable=W0212
        if not should_exclude_field(field, fields, exclude)
    }


def model_to_dict(instance, fields=None, exclude=None):
    """
    The same implementation as django model_to_dict but editable fields are allowed
    """

    return {
        field.name: field_to_dict(field, instance)
        for field in chain(instance._meta.concrete_fields, instance._meta.many_to_many)  # pylint: disable=W0212
        if not should_exclude_field(field, fields, exclude)
    }


ValueChange = collections.namedtuple('ValueChange', ('initial', 'current'))


class ChangedFields:
    """
    Class stores changed fields and its initial and current values.
    """

    def __init__(self, initial_dict):
        self._initial_dict = initial_dict

    @property
    def initial_values(self):
        return self._initial_dict

    @property
    def current_values(self):
        raise NotImplementedError

    @property
    def changed_values(self):
        return {k: value_change.current for k, value_change in self.diff.items()}

    @property
    def diff(self):
        d1 = self.initial_values
        d2 = self.current_values
        return {k: ValueChange(v, d2[k]) for k, v in d1.items() if v != d2[k]}

    def __setitem__(self, key, item):
        raise AttributeError('Object is readonly')

    def __getitem__(self, key):
        return self.diff[key]

    def __repr__(self):
        return repr(self.diff)

    def __len__(self):
        return len(self.diff)

    def __delitem__(self, key):
        raise AttributeError('Object is readonly')

    def clear(self):
        raise AttributeError('Object is readonly')

    def has_key(self, k):
        return k in self.diff

    def has_any_key(self, *keys):
        return bool(set(self.keys()) & set(keys))

    def update(self, *args, **kwargs):
        raise AttributeError('Object is readonly')

    def keys(self):
        return self.diff.keys()

    def values(self):
        return self.diff.values()

    def items(self):
        return self.diff.items()

    def pop(self, *args, **kwargs):
        raise AttributeError('Object is readonly')

    def __cmp__(self, dictionary):
        return cmp(self.diff, dictionary)

    def __contains__(self, item):
        return item in self.diff

    def __iter__(self):
        return iter(self.diff)

    def __str__(self):
        return repr(self.diff)


class DynamicChangedFields(ChangedFields):
    """
    Dynamic changed fields are changed with the instance changes.
    """

    def __init__(self, instance):
        super().__init__(
            self._get_unknown_dict(instance) if instance.is_adding else self._get_instance_dict(instance)
        )
        self.instance = instance

    def _get_unknown_dict(self, instance):
        return unknown_model_fields_to_dict(
            instance, fields=(field.name for field in instance._meta.fields)
        )

    def _get_instance_dict(self, instance):
        return model_to_dict(
            instance, fields=(field.name for field in instance._meta.fields)
        )

    @property
    def current_values(self):
        return self._get_instance_dict(self.instance)

    def get_static_changes(self):
        return StaticChangedFields(self.initial_values, self.current_values)


class StaticChangedFields(ChangedFields):
    """
    Static changed fields are immutable. The origin instance changes will not have an affect.
    """

    def __init__(self, initial_dict, current_dict):
        super().__init__(initial_dict)
        self._current_dict = current_dict

    @property
    def current_values(self):
        return self._current_dict


class ComparableModelMixin:

    def equals(self, obj, comparator):
        """
        Use comparator for evaluating if objects are the same
        """
        return comparator.compare(self, obj)


class Comparator:

    def compare(self, a, b):
        """
        Return True if objects are same otherwise False
        """
        raise NotImplementedError


class AuditModel(models.Model):

    created_at = models.DateTimeField(verbose_name=_('created at'), null=False, blank=False, auto_now_add=True,
                                      db_index=True)
    changed_at = models.DateTimeField(verbose_name=_('changed at'), null=False, blank=False, auto_now=True,
                                      db_index=True)

    class Meta:
        abstract = True


class Signal:

    def __init__(self, obj):
        self.connected_functions = []
        self.obj = obj

    def connect(self, fun):
        self.connected_functions.append(fun)

    def send(self):
        [fun(self.obj) for fun in self.connected_functions]


class SmartQuerySetMixin:

    def fast_distinct(self):
        """
        Because standard distinct used on the all fields are very slow and works only with PostgreSQL database
        this method provides alternative to the standard distinct method.
        :return: qs with unique objects
        """
        return self.model.objects.filter(pk__in=self.values_list('pk', flat=True))

    def change_and_save(self, update_only_changed_fields=False, **changed_fields):
        """
        Changes a given `changed_fields` on each object in the queryset, saves objects
        and returns the changed objects in the queryset.
        """
        bulk_change_and_save(self, update_only_changed_fields=update_only_changed_fields, **changed_fields)
        return self.filter()


class SmartQuerySet(SmartQuerySetMixin, models.QuerySet):
    pass


class SmartModelBase(ModelBase):
    """
    Smart model meta class that register dispatchers to the post or pre save signals.
    """

    def __new__(cls, name, bases, attrs):

        new_cls = super().__new__(cls, name, bases, attrs)
        for dispatcher in new_cls.dispatchers:
            dispatcher.connect(new_cls)
        return new_cls


class SmartModel(AuditModel, metaclass=SmartModelBase):

    objects = SmartQuerySet.as_manager()

    dispatchers = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_adding = True
        self.is_changing = False
        self.changed_fields = DynamicChangedFields(self)
        self.post_save = Signal(self)

    @classmethod
    def from_db(cls, db, field_names, values):
        new = super().from_db(db, field_names, values)
        new.is_adding = False
        new.is_changing = True
        new.changed_fields = DynamicChangedFields(new)
        return new

    @property
    def has_changed(self):
        return bool(self.changed_fields)

    @property
    def initial_values(self):
        return self.changed_fields.initial_values

    def full_clean(self, exclude=None, *args, **kwargs):
        errors = {}
        for field in self._meta.fields:
            if (not exclude or field.name not in exclude) and hasattr(self, 'clean_{}'.format(field.name)):
                try:
                    getattr(self, 'clean_{}'.format(field.name))()
                except ValidationError as er:
                    errors[field.name] = er

        if errors:
            raise ValidationError(errors)
        super().full_clean(exclude=exclude, *args, **kwargs)

    def _clean_save(self, *args, **kwargs):
        self._persistence_clean(*args, **kwargs)

    def _clean_delete(self, *args, **kwargs):
        self._persistence_clean(*args, **kwargs)

    def _clean_pre_save(self, *args, **kwargs):
        self._clean_save(*args, **kwargs)

    def _clean_pre_delete(self, *args, **kwargs):
        self._clean_delete(*args, **kwargs)

    def _clean_post_save(self, *args, **kwargs):
        self._clean_save(*args, **kwargs)

    def _clean_post_delete(self, *args, **kwargs):
        self._clean_delete(*args, **kwargs)

    def _persistence_clean(self, *args, **kwargs):
        exclude = kwargs.pop('exclude', None)
        try:
            self.full_clean(exclude=exclude)
        except ValidationError as er:
            if hasattr(er, 'error_dict'):
                raise PersistenceException(', '.join(
                    ('%s: %s' % (key, ', '.join(map(force_text, val))) for key, val in er.message_dict.items())))
            else:
                raise PersistenceException(', '.join(map(force_text, er.messages)))

    def _get_save_extra_kwargs(self):
        return {}

    def _pre_save(self, *args, **kwargs):
        pass

    def _call_pre_save(self, *args, **kwargs):
        self._pre_save(*args, **kwargs)

    def _save(self, update_only_changed_fields=False, is_cleaned_pre_save=None, is_cleaned_post_save=None,
              force_insert=False, force_update=False, using=None, update_fields=None, *args, **kwargs):
        is_cleaned_pre_save = (
            self._smart_meta.is_cleaned_pre_save if is_cleaned_pre_save is None else is_cleaned_pre_save
        )
        is_cleaned_post_save = (
            self._smart_meta.is_cleaned_post_save if is_cleaned_post_save is None else is_cleaned_post_save
        )

        origin = self.__class__

        kwargs.update(self._get_save_extra_kwargs())

        self._call_pre_save(self.is_changing, self.changed_fields, *args, **kwargs)
        if is_cleaned_pre_save:
            self._clean_pre_save(*args, **kwargs)
        dispatcher_pre_save.send(sender=origin, instance=self, change=self.is_changing,
                                 changed_fields=self.changed_fields.get_static_changes(),
                                 *args, **kwargs)
        if not update_fields and update_only_changed_fields:
            update_fields = list(self.changed_fields.keys()) + ['changed_at']
            # remove primary key from updating fields
            if self._meta.pk.name in update_fields:
                update_fields.remove(self._meta.pk.name)
        super().save(force_insert=force_insert, force_update=force_update, using=using,
                                     update_fields=update_fields)

        self._call_post_save(self.is_changing, self.changed_fields, *args, **kwargs)
        if is_cleaned_post_save:
            self._clean_post_save(*args, **kwargs)
        dispatcher_post_save.send(sender=origin, instance=self, change=self.is_changing,
                                  changed_fields=self.changed_fields.get_static_changes(),
                                  *args, **kwargs)
        self.post_save.send()

    def _post_save(self, *args, **kwargs):
        pass

    def _call_post_save(self, *args, **kwargs):
        self._post_save(*args, **kwargs)

    def save_simple(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def save(self, update_only_changed_fields=False, *args, **kwargs):
        if self._smart_meta.is_save_atomic:
            with transaction.atomic():
                self._save(update_only_changed_fields=update_only_changed_fields, *args, **kwargs)
        else:
            self._save(update_only_changed_fields=update_only_changed_fields, *args, **kwargs)
        self.is_adding = False
        self.is_changing = True
        self.changed_fields = DynamicChangedFields(self)

    def _pre_delete(self, *args, **kwargs):
        pass

    def _delete(self, is_cleaned_pre_delete=None, is_cleaned_post_delete=None, *args, **kwargs):
        is_cleaned_pre_delete = (
            self._smart_meta.is_cleaned_pre_delete if is_cleaned_pre_delete is None else is_cleaned_pre_delete
        )
        is_cleaned_post_delete = (
            self._smart_meta.is_cleaned_post_delete if is_cleaned_post_delete is None else is_cleaned_post_delete
        )

        self._pre_delete(*args, **kwargs)

        if is_cleaned_pre_delete:
            self._clean_pre_delete(*args, **kwargs)

        super().delete(*args, **kwargs)

        self._post_delete(*args, **kwargs)

        if is_cleaned_post_delete:
            self._clean_post_delete(*args, **kwargs)

    def _post_delete(self, *args, **kwargs):
        pass

    def delete(self, *args, **kwargs):
        if self._smart_meta.is_delete_atomic:
            with transaction.atomic():
                self._delete(*args, **kwargs)
        else:
            self._delete(*args, **kwargs)

    def refresh_from_db(self, *args, **kwargs):
        super().refresh_from_db(*args, **kwargs)
        for key, value in self.__class__.__dict__.items():
            if isinstance(value, cached_property):
                self.__dict__.pop(key, None)
        self.is_adding = False
        self.is_changing = True
        self.changed_fields = DynamicChangedFields(self)

        if StrictVersion(django.get_version()) < StrictVersion('2.0'):
            for field in [f for f in self._meta.get_fields() if f.is_relation]:
                # For Generic relation related model is None
                # https://docs.djangoproject.com/en/2.1/ref/models/meta/#migrating-from-the-old-api
                cache_key = field.get_cache_name() if field.related_model else field.cache_attr
                if cache_key in self.__dict__:
                    del self.__dict__[cache_key]

        return self

    def change(self, **changed_fields):
        """
        Changes a given `changed_fields` on this object and returns itself.
        :param changed_fields: fields to change
        :return: self
        """
        change(self, **changed_fields)
        return self

    def change_and_save(self, update_only_changed_fields=False, **changed_fields):
        """
        Changes a given `changed_fields` on this object, saves it and returns itself.
        :param update_only_changed_fields: only changed fields will be updated in the database.
        :param changed_fields: fields to change.
        :return: self
        """
        change_and_save(self, update_only_changed_fields=update_only_changed_fields, **changed_fields)
        return self

    class Meta:
        abstract = True


class SmartOptions(Options):

    meta_class_name = 'SmartMeta'
    meta_name = '_smart_meta'
    model_class = SmartModel
    attributes = {
        'is_cleaned_pre_save': True,
        'is_cleaned_post_save': False,
        'is_cleaned_pre_delete': False,
        'is_cleaned_post_delete': False,
        'is_save_atomic': False,
        'is_delete_atomic': False,
    }
