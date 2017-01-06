from __future__ import unicode_literals

import inspect

from django.core.exceptions import ImproperlyConfigured


class BaseDispatcher(object):
    """
    Base dispatcher class that can be subclassed to call a handler based on a change in some a SmartModel.
    If you subclass, be sure the __call__ method does not change signature.
    """
    def _validate_init_params(self):
        raise NotImplementedError

    def __init__(self, handler, *args, **kwargs):
        self.handler = handler
        self._validate_init_params()

    def __call__(self, obj, *args, **kwargs):
        """
        `obj` ... instance of the SmartModel where the handler is being called
        Some dispatchers require additional params to evaluate the handler can be dispatched,
        these are hidden in args and kwargs.
        """
        if self._can_dispatch(obj, *args, **kwargs):
            self.handler(obj)

    def _can_dispatch(self, obj, *args, **kwargs):
        raise NotImplementedError


class PropertyDispatcher(BaseDispatcher):
    """
    Use this class to register a handler to dispatch during save if the given property evaluates to True.
    """

    def _validate_init_params(self):
        """
        No validation is done as it would require to pass the whole model to the dispatcher.
        If the property is not defined, a clear error is shown at runtime.
        """
        pass

    def __init__(self, handler, property_name):
        self.property_name = property_name
        super(PropertyDispatcher, self).__init__(handler, property_name)

    def _can_dispatch(self, obj, *args, **kwargs):
        return getattr(obj, self.property_name)


class StateDispatcher(BaseDispatcher):

    """
    Use this class to register a handler for transition of a model to a certain state.
    """
    def _validate_init_params(self):
        if self.field_value not in {value for value, _ in self.enum.choices}:
            raise ImproperlyConfigured('Enum of FieldDispatcher does not contain {}.'.format(self.field_value))
        if not hasattr(self.handler, '__call__'):
            raise ImproperlyConfigured('Handler of FieldDispatcher must be callable.')
        if (len(inspect.getargspec(self.handler).args) != 1 or  # pylint: disable=W1505
                inspect.getargspec(self.handler).keywords):  # pylint: disable=W1505
            raise ImproperlyConfigured('Handler of FieldDispatcher must be a function of one parameter.')

    def __init__(self, handler, enum, field, field_value):
        self.enum = enum
        self.field = field
        self.field_value = field_value

        super(StateDispatcher, self).__init__(handler, enum, field, field_value)

    def _can_dispatch(self, obj, changed_fields, *args, **kwargs):
        return self.field.get_attname() in changed_fields and getattr(obj, self.field.get_attname()) == self.field_value
