from django.forms.widgets import Widget
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape


class ReadonlyWidget(Widget):

    def __init__(self, widget):
        super(ReadonlyWidget, self).__init__()
        self.widget = widget

    def _get_value(self, value):
        if hasattr(self.widget, 'choices'):
            result = dict(self.widget.choices).get(value)
        else:
            result = value
        return result or ''

    def render(self, name, value, attrs=None, choices=()):
        if isinstance(value, (list, tuple)):
            out = ', '.join(self._get_value(value))
        else:
            out = self._get_value(value)
        return mark_safe('<p>%s</p>' % conditional_escape(out))
