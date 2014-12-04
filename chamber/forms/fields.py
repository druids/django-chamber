from __future__ import unicode_literals

from django.forms import DecimalField as OriginDecimalField


class DecimalField(OriginDecimalField):

    def __init__(self, *args, **kwargs):
        self.step = kwargs.pop('step', 'any')
        self.min = kwargs.pop('min', None)
        self.max = kwargs.pop('max', None)
        super(DecimalField, self).__init__(*args, **kwargs)

    def widget_attrs(self, widget):
        attrs = super(DecimalField, self).widget_attrs(widget)
        attrs['step'] = self.step
        if self.min is not None:
            attrs['min'] = self.min
        if self.max is not None:
            attrs['max'] = self.max
        return attrs
