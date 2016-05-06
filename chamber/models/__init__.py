from __future__ import unicode_literals

import six

from django.core.exceptions import ValidationError
from django.db.models import CharField
from django.db import models, transaction
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_text

from chamber.exceptions import PersistenceException
from chamber.patch import Options


def model_to_dict(instance, fields=None, exclude=None):
    """
    The same implementation as django model_to_dict but editable fields are allowed
    """
    # avoid a circular import
    from django.db.models.fields.related import ManyToManyField

    opts = instance._meta
    data = {}
    for f in opts.concrete_fields + opts.many_to_many:
        if fields and f.name not in fields:
            continue
        if exclude and f.name in exclude:
            continue
        if isinstance(f, ManyToManyField):
            # If the object doesn't have a primary key yet, just use an empty
            # list for its m2m fields. Calling f.value_from_object will raise
            # an exception.
            if instance.pk is None:
                data[f.name] = []
            else:
                # MultipleChoiceWidget needs a list of pks, not object instances.
                data[f.name] = list(f.value_from_object(instance).values_list('pk', flat=True))
        else:
            data[f.name] = f.value_from_object(instance)
    return data


class ModelDiffMixin(object):
    """
    A model mixin that tracks model fields' values and provide some useful api
    to know what fields have been changed.
    """

    def __init__(self, *args, **kwargs):
        super(ModelDiffMixin, self).__init__(*args, **kwargs)
        self.__initial = self._dict

    @property
    def initial_values(self):
        return self.__initial

    @property
    def diff(self):
        d1 = self.__initial
        d2 = self._dict
        diffs = [(k, (v, d2[k])) for k, v in d1.items() if v != d2[k]]
        return dict(diffs)

    @property
    def has_changed(self):
        return bool(self.diff)

    @property
    def changed_fields(self):
        return set(self.diff.keys())

    def get_field_diff(self, field_name):
        """
        Returns a diff for field if it's changed and None otherwise.
        """
        return self.diff.get(field_name, None)

    def save(self, *args, **kwargs):
        """
        Saves model and set initial state.
        """
        super(ModelDiffMixin, self).save(*args, **kwargs)
        self.__initial = self._dict

    @property
    def _dict(self):
        return model_to_dict(self, fields=[field.name for field in
                             self._meta.fields])


class ComparableModelMixin(object):

    def equals(self, obj, comparator):
        """
        Use comparator for evaluating if objects are the same
        """
        return comparator.compare(self, obj)


class Comparator(object):

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


class SmartModel(ModelDiffMixin, AuditModel):

    def full_clean(self, *args, **kwargs):
        errors = {}
        for field in self._meta.fields:
            if hasattr(self, 'clean_%s' % field.name):
                try:
                    getattr(self, 'clean_%s' % field.name)()
                except ValidationError as er:
                    errors[field.name] = er.messages

        if errors:
            raise ValidationError(errors)
        super(SmartModel, self).full_clean(*args, **kwargs)

    def _clean_save(self):
        self._persistence_clean()

    def _clean_delete(self):
        self._persistence_clean()

    def _clean_pre_save(self):
        self._clean_save()

    def _clean_pre_delete(self):
        self._clean_delete()

    def _clean_post_save(self):
        self._clean_save()

    def _clean_post_delete(self):
        self._clean_delete()

    def _persistence_clean(self):
        try:
            self.full_clean()
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

    def _save(self, is_cleaned_pre_save=None, is_cleaned_post_save=None, force_insert=False, force_update=False, using=None,
              update_fields=None, *args, **kwargs):
        is_cleaned_pre_save = (
            self._smart_meta.is_cleaned_pre_save if is_cleaned_pre_save is None else is_cleaned_pre_save
        )
        is_cleaned_post_save = (
            self._smart_meta.is_cleaned_post_save if is_cleaned_post_save is None else is_cleaned_post_save
        )

        change = bool(self.pk)
        changed_fields = set(self.changed_fields)
        kwargs.update(self._get_save_extra_kwargs())

        self._pre_save(change, changed_fields, *args, **kwargs)

        if is_cleaned_pre_save:
            self._clean_pre_save()

        super(SmartModel, self).save(force_insert=force_insert, force_update=force_update, using=using,
                                     update_fields=update_fields)

        self._post_save(change, changed_fields, *args, **kwargs)

        if is_cleaned_post_save:
            self._clean_post_save()

    def _post_save(self, *args, **kwargs):
        pass

    def save(self, *args, **kwargs):
        if self._smart_meta.is_save_atomic:
            with transaction.atomic():
                self._save(*args, **kwargs)
        else:
            self._save(*args, **kwargs)

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
            self._clean_pre_delete()

        super(SmartModel, self).delete(*args, **kwargs)

        self._post_delete(*args, **kwargs)

        if is_cleaned_post_delete:
            self._clean_post_delete()

    def _post_delete(self, *args, **kwargs):
        pass

    def delete(self, *args, **kwargs):
        if self._smart_meta.is_delete_atomic:
            with transaction.atomic():
                self._delete(*args, **kwargs)
        else:
            self._delete(*args, **kwargs)

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
