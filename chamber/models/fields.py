from __future__ import unicode_literals

import magic  # pylint: disable=E0401
import os
from uuid import uuid4 as uuid

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import FileField as OriginFileField
from django.db.models.fields import DecimalField as OriginDecimalField
from django.forms import forms
from django.template.defaultfilters import filesizeformat
from django.utils.encoding import force_text
from django.utils.translation import ugettext

from chamber import config
from chamber.forms.fields import DecimalField as DecimalFormField
from chamber.utils.datastructures import SequenceChoicesEnumMixin, SubstatesChoicesNumEnum


try:
    from sorl.thumbnail import ImageField as OriginImageField
except ImportError:
    from django.db.models import ImageField as OriginImageField


class SouthMixin(object):

    def south_field_triple(self):
        from south.modelsinspector import introspector
        cls_name = '%s.%s' % (self.__class__.__module__, self.__class__.__name__)
        args, kwargs = introspector(self)
        return (cls_name, args, kwargs)


class DecimalField(SouthMixin, OriginDecimalField):

    def __init__(self, *args, **kwargs):
        self.step = kwargs.pop('step', 'any')
        self.min = kwargs.pop('min', None)
        self.max = kwargs.pop('max', None)
        kwargs['validators'] = kwargs.get('validators', [])
        if self.min is not None:
            kwargs['validators'].append(MinValueValidator(self.min))
        if self.max is not None:
            kwargs['validators'].append(MaxValueValidator(self.max))
        super(DecimalField, self).__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        defaults = {
            'form_class': DecimalFormField,
            'step': self.step,
            'min': self.min,
            'max': self.max,
        }
        defaults.update(kwargs)
        return super(DecimalField, self).formfield(**defaults)


class RestrictedFileValidator(object):

    def __init__(self, max_upload_size):
        self.max_upload_size = max_upload_size

    def __call__(self, data):
        if data.size > self.max_upload_size:
            raise forms.ValidationError(
                ugettext('Please keep filesize under {max}. Current filesize {current}').format(
                    max=filesizeformat(self.max_upload_size),
                    current=filesizeformat(data.size)
                )
            )
        else:
            return data


class AllowedContentTypesFileValidator(object):

    def __init__(self, content_types):
        self.content_types = content_types

    def __call__(self, data):
        with magic.Magic(flags=magic.MAGIC_MIME_TYPE) as m:
            mime_type = m.id_buffer(data.file.read(1024))
            data.file.seek(0)
            if mime_type not in self.content_types:
                raise ValidationError(
                    ugettext('Unsupported file type')
                )
        return data


class RestrictedFileFieldMixin(SouthMixin):
    """
    Same as FileField, but you can specify:
        * allowed_content_types - list of allowed content types. Example: ['application/json', 'image/jpeg']
        * max_upload_size - a number indicating the maximum file size allowed for upload in MB.
    """
    def __init__(self, *args, **kwargs):
        max_upload_size = kwargs.pop('max_upload_size', config.CHAMBER_MAX_FILE_UPLOAD_SIZE) * 1024 * 1024
        allowed_content_types = kwargs.pop('allowed_content_types', None)
        super(RestrictedFileFieldMixin, self).__init__(*args, **kwargs)
        self.validators.append(RestrictedFileValidator(max_upload_size))
        if allowed_content_types:
            self.validators.append(AllowedContentTypesFileValidator(allowed_content_types))

    def get_filename(self, filename):
        """
        removes UTF chars from filename
        """
        from unidecode import unidecode
        return super(RestrictedFileFieldMixin, self).get_filename(unidecode(force_text(filename)))


class FileField(RestrictedFileFieldMixin, OriginFileField):
    pass


class ImageField(RestrictedFileFieldMixin, OriginImageField):
    pass


def generate_random_upload_path(instance, filename):
    """
    Pass this function to upload_to argument of FileField to store the file on an unguessable path.
    The format of the path is class_name/hash/original_filename.
    """
    return os.path.join(instance.__class__.__name__.lower(), uuid().hex, filename)


class PrevValuePositiveIntegerField(models.PositiveIntegerField):

    def __init__(self, *args, **kwargs):
        self.copy_field_name = kwargs.pop('copy_field_name', None)
        super(PrevValuePositiveIntegerField, self).__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        if add or hasattr(model_instance, 'changed_fields') and self.copy_field_name in model_instance.changed_fields:
            setattr(
                model_instance, self.attname,
                getattr(model_instance, self.copy_field_name)
                if add else model_instance.initial_values[self.copy_field_name]
            )
        return super(PrevValuePositiveIntegerField, self).pre_save(model_instance, add)


class SubchoicesPositiveIntegerField(models.PositiveIntegerField):

    empty_values = ()

    def __init__(self, *args, **kwargs):
        self.enum = kwargs.pop('enum', None)
        self.subchoices_field_name = kwargs.pop('subchoices_field_name', None)
        assert self.enum is None or isinstance(self.enum, SubstatesChoicesNumEnum)
        if self.enum:
            kwargs['choices'] = self.enum.choices
        super(SubchoicesPositiveIntegerField, self).__init__(*args, **kwargs)

    def _get_subvalue(self, model_instance):
        return getattr(model_instance, self.subchoices_field_name)

    def clean(self, value, model_instance):
        if self.enum and self._get_subvalue(model_instance) not in self.enum.categories:
            return None
        else:
            return super(SubchoicesPositiveIntegerField, self).clean(value, model_instance)

    def _raise_error_if_value_should_be_empty(self, value, subvalue):
        if self.enum and subvalue not in self.enum.categories and value is not None:
            raise ValidationError(ugettext('Value must be empty'))

    def _raise_error_if_value_not_allowed(self, value, subvalue, model_instance):
        allowed_values = self.enum.get_allowed_states(getattr(model_instance, self.subchoices_field_name))
        if subvalue in self.enum.categories and value not in allowed_values:
            raise ValidationError(ugettext('Allowed choices are {}.').format(
                ', '.join(('{} ({})'.format(*(self.enum.get_label(val), val)) for val in allowed_values))
            ))

    def validate(self, value, model_instance):
        if not self.enum:
            return

        self._raise_error_if_value_should_be_empty(value, self._get_subvalue(model_instance))
        self._raise_error_if_value_not_allowed(value, self._get_subvalue(model_instance), model_instance)


class EnumSequenceFieldMixin(object):

    # TODO Once SmartWidget mixin is not in is-core, add formfield method with the appropriate widget
    def __init__(self, *args, **kwargs):
        self.enum = kwargs.pop('enum', None)
        self.prev_field_name = kwargs.pop('prev_field', None)
        assert self.enum is None or isinstance(self.enum, SequenceChoicesEnumMixin)
        if self.enum:
            kwargs['choices'] = self.enum.choices
        super(EnumSequenceFieldMixin, self).__init__(*args, **kwargs)

    def validate(self, value, model_instance):
        super(EnumSequenceFieldMixin, self).validate(value, model_instance)
        if self.enum:
            prev_value = model_instance.pk and model_instance.initial_values[self.attname] or None
            allowed_next_values = self.enum.get_allowed_next_states(prev_value, model_instance)
            if self.name in model_instance.changed_fields and value not in allowed_next_values:
                raise ValidationError(
                    ugettext('Allowed choices are {}.').format(
                        ', '.join(('{} ({})'.format(*(self.enum.get_label(val), val)) for val in allowed_next_values))))


class EnumSequencePositiveIntegerField(EnumSequenceFieldMixin, models.PositiveIntegerField):
    pass


class EnumSequenceCharField(EnumSequenceFieldMixin, models.CharField):
    pass
