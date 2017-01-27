from __future__ import unicode_literals

from django.db.models.fields import Field


def field_init(self, *args, **kwargs):
    """
    Patches a Django Field's `__init__` method for easier usage of optional `kwargs`. It defines a `humanized` attribute
    on a field for better display of its value.
    """
    humanize_func = kwargs.pop('humanized', None)
    if humanize_func:
        def humanize(val, inst, *args, **kwargs):
            return humanize_func(val, inst, field=self, *args, **kwargs)
        self.humanized = humanize
    else:
        self.humanized = self.default_humanized
    self._init_chamber_patch_(*args, **kwargs)


Field.default_humanized = None
Field._init_chamber_patch_ = Field.__init__  # pylint: disable=W0212
Field.__init__ = field_init
