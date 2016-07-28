from __future__ import unicode_literals

from django.core.validators import MinValueValidator
from django.core.validators import MaxValueValidator
from django.db.models.fields import DecimalField as OriginDecimalField
from django.db.models import FileField as OriginFileField
from django.forms import forms
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _, ugettext
from django.utils.encoding import force_text
from django.db import models

try:
    from sorl.thumbnail import ImageField as OriginImageField
except ImportError:
    from django.db.models import ImageField as OriginImageField

from chamber.forms.fields import DecimalField as DecimalFormField
from chamber import config


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


class RestrictedFileFieldMixin(SouthMixin):
    """
    Same as FileField, but you can specify:
        * content_types - list containing allowed content_types. Example: ['application/pdf', 'image/jpeg']
        * max_upload_size - a number indicating the maximum file size allowed for upload in MB.
    """
    def __init__(self, *args, **kwargs):
        max_upload_size = kwargs.pop('max_upload_size', config.MAX_FILE_UPLOAD_SIZE) * 1024 * 1024

        super(RestrictedFileFieldMixin, self).__init__(*args, **kwargs)
        self.validators.append(RestrictedFileValidator(max_upload_size))

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


class CharNullField(SouthMixin, models.CharField):
    description = "CharField that stores NULL but returns ''"
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        if isinstance(value, models.CharField):
            return value
        else:
            return '' if value is None else value

    def get_prep_value(self, value):
        return None if value == '' else value
