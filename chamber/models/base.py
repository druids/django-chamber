from django.db import transaction, models, OperationalError
from django.db.models.manager import BaseManager
from django.db.models.base import ModelBase
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import cached_property

from chamber.exceptions import PersistenceException
from chamber.patch import Options
from chamber.shortcuts import change_and_save, change, bulk_change_and_save

from .changed_fields import DynamicChangedFields
from .signals import dispatcher_post_save, dispatcher_pre_save


class SmartQuerySetMixin:

    def fast_distinct(self):
        """
        Because standard distinct used on the all fields are very slow and works only with PostgreSQL database
        this method provides alternative to the standard distinct method.
        :return: qs with unique objects
        """
        qs = self.model.objects.filter(pk__in=self.values('pk'))
        if self.query.order_by:
            qs = qs.order_by(*self.query.order_by)
        return qs

    def change_and_save(self, update_only_changed_fields=False, **changed_fields):
        """
        Changes a given `changed_fields` on each object in the queryset, saves objects
        and returns the changed objects in the queryset.
        """
        bulk_change_and_save(self, update_only_changed_fields=update_only_changed_fields, **changed_fields)
        return self.filter()

    def first(self, *field_names):
        """
        Adds possibility to set order fields to default Django first method.
        """
        if field_names:
            return self.order_by(*field_names).first()
        else:
            return super().first()

    def last(self, *field_names):
        """
        Adds possibility to set order fields to default Django last method.
        """
        if field_names:
            return self.order_by(*field_names).last()
        else:
            return super().last()


class SmartQuerySet(SmartQuerySetMixin, models.QuerySet):
    pass


class SmartManager(BaseManager.from_queryset(SmartQuerySet)):
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


class AuditModel(models.Model):

    created_at = models.DateTimeField(
        verbose_name=_('created at'),
        null=False,
        blank=False,
        auto_now_add=True,
        db_index=True
    )
    changed_at = models.DateTimeField(
        verbose_name=_('changed at'),
        null=False,
        blank=False,
        auto_now=True,
        db_index=True
    )

    class Meta:
        abstract = True


class SmartModel(AuditModel, metaclass=SmartModelBase):

    objects = SmartManager()

    dispatchers = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_adding = True
        self.is_changing = False
        self._changed_fields = DynamicChangedFields(self)

    class Meta:
        abstract = True

    def __str__(self):
        return '{} #{}'.format(self._meta.verbose_name, self.pk)

    @classmethod
    def from_db(cls, db, field_names, values):
        new = super().from_db(db, field_names, values)
        new.is_adding = False
        new.is_changing = True
        updating_fields = [
            f.name for f in cls._meta.concrete_fields
            if len(values) == len(cls._meta.concrete_fields) or f.attname in field_names
        ]
        new._changed_fields.from_db(fields=updating_fields)
        return new

    @property
    def has_changed(self):
        return bool(self._changed_fields)

    @property
    def changed_fields(self):
        return self._changed_fields

    @property
    def initial_values(self):
        return self._changed_fields.initial_values

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
                raise PersistenceException(
                    ', '.join(
                        ('%s: %s' % (key, ', '.join(map(str, val))) for key, val in er.message_dict.items())
                    ),
                    error_dict=er.message_dict
                )
            else:
                raise PersistenceException(', '.join(map(str, er.messages)))

    def _get_save_extra_kwargs(self):
        return {}

    def _pre_save(self, changed, changed_fields, *args, **kwargs):
        """
        :param change: True if model instance was changed, False if was created
        :param changed_fields: fields that was changed before _pre_save was called (changes in the method do not
                affect it)
        """
        pass

    def _call_pre_save(self, changed, changed_fields, *args, **kwargs):
        self._pre_save(changed, changed_fields, *args, **kwargs)

    def _save(self, update_only_changed_fields=False, is_cleaned_pre_save=None, is_cleaned_post_save=None,
              force_insert=False, force_update=False, using=None, update_fields=None, *args, **kwargs):
        """
        Save of SmartModel has the following sequence:
        * pre-save methods are called
        * pre-save validation is invoked (it can be turned off)
        * pre-save signals are called
        * model is saved, model changed fields are reset, is_adding is not False and is_changing has True value
        * post-save methods are called
        * post-save validation is invoked (it is turned off by default)
        * post-save signals are invoked
        """
        is_cleaned_pre_save = (
            self._smart_meta.is_cleaned_pre_save if is_cleaned_pre_save is None else is_cleaned_pre_save
        )
        is_cleaned_post_save = (
            self._smart_meta.is_cleaned_post_save if is_cleaned_post_save is None else is_cleaned_post_save
        )

        origin = self.__class__

        kwargs.update(self._get_save_extra_kwargs())

        self._call_pre_save(
            changed=self.is_changing, changed_fields=self.changed_fields.get_static_changes(), *args, **kwargs
        )
        if is_cleaned_pre_save:
            self._clean_pre_save(*args, **kwargs)
        dispatcher_pre_save.send(
            sender=origin, instance=self, changed=self.is_changing,
            changed_fields=self.changed_fields.get_static_changes(),
            *args, **kwargs
        )

        post_save_changed_fields = self.changed_fields.get_static_changes()

        if not update_fields and update_only_changed_fields:
            update_fields = list(post_save_changed_fields.keys()) + ['changed_at']
            # remove primary key from updating fields
            if self._meta.pk.name in update_fields:
                update_fields.remove(self._meta.pk.name)

        # Changed fields must be cached before save, for post_save and signal purposes
        post_save_is_changing = self.is_changing

        self.save_simple(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

        self._call_post_save(
            changed=post_save_is_changing, changed_fields=post_save_changed_fields, *args, **kwargs
        )
        if is_cleaned_post_save:
            self._clean_post_save(*args, **kwargs)
        dispatcher_post_save.send(
            sender=origin, instance=self, changed=post_save_is_changing, changed_fields=post_save_changed_fields,
            *args, **kwargs
        )

    def _post_save(self, changed, changed_fields, *args, **kwargs):
        """
        :param change: True if model instance was changed, False if was created
        :param changed_fields: fields that was changed before _post_save was called (changes in the method do not
               affect it)
         """
        pass

    def _call_post_save(self, changed, changed_fields, *args, **kwargs):
        self._post_save(changed, changed_fields, *args, **kwargs)

    def save_simple(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.is_adding = False
        self.is_changing = True
        self._changed_fields.from_db()

    def save(self, update_only_changed_fields=False, *args, **kwargs):
        if self._smart_meta.is_save_atomic:
            with transaction.atomic():
                self._save(update_only_changed_fields=update_only_changed_fields, *args, **kwargs)
        else:
            self._save(update_only_changed_fields=update_only_changed_fields, *args, **kwargs)

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

    def refresh_from_db(self, using=None, fields=None):
        super().refresh_from_db(using=using, fields=fields)
        for key, value in self.__class__.__dict__.items():
            if isinstance(value, cached_property):
                self.__dict__.pop(key, None)
        self.is_adding = False
        self.is_changing = True

        self._changed_fields.from_db(fields={
            f.name for f in self._meta.concrete_fields if not fields or f.attname in fields or f.name in fields
        })

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

    def get_locked_instance(self):
        """
        Lock object and reload it from database.
        :return: reloaded locked object from database
        """
        if not self.pk:
            raise OperationalError('Unsaved object cannot be locked')

        return self.__class__.objects.filter(pk=self.pk).select_for_update().get()


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
