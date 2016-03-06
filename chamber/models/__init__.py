from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.db.models import CharField
from django.db.models import AutoField
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_text

from chamber.exceptions import PersistenceException


class OptionsLazy(object):

    def __init__(self, name, klass):
        self.name = name
        self.klass = klass

    def __get__(self, instance=None, owner=None):
        option = self.klass(owner)
        setattr(owner, self.name, option)
        return option


class Options(object):

    meta_name = 'SmartMeta'

    def __init__(self, model):
        self.model = model

        self.clean_before_save = True
        if hasattr(model, 'SmartMeta'):
            self.clean_before_save = self._getattr('clean_before_save', self.clean_before_save)

    def _getattr(self, name, default_value):
        meta_models = [b for b in self.model.__mro__ if issubclass(b, models.Model)]
        for model in meta_models:
            meta = getattr(model, self.meta_name, None)
            if meta:
                value = getattr(meta, name, None)
                if value is not None:
                    return value
        return default_value


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

    def pre_save(self, *args, **kwargs):
        pass

    def save(self, clean_before_save=None, force_insert=False, force_update=False, using=None,
             update_fields=None, *args, **kwargs):
        clean_before_save = self._smart_meta.clean_before_save if clean_before_save is None else clean_before_save
        change = bool(self.pk)
        changed_fields = set(self.changed_fields)
        self.pre_save(change, changed_fields, *args, **kwargs)
        if clean_before_save:
            try:
                self.full_clean()
            except ValidationError as er:
                if hasattr(er, 'error_dict'):
                    raise PersistenceException(', '.join(
                        ('%s: %s' % (key, ', '.join(map(force_text, val))) for key, val in er.message_dict.items())))
                else:
                    raise PersistenceException(', '.join(map(force_text, er.messages)))
        super(SmartModel, self).save(force_insert=force_insert, force_update=force_update, using=using,
                                     update_fields=update_fields)
        self.post_save(change, changed_fields, *args, **kwargs)

    def post_save(self, *args, **kwargs):
        pass

    class Meta:
        abstract = True

opt_key = '_smart_meta'
setattr(SmartModel, opt_key, OptionsLazy(opt_key, Options))
