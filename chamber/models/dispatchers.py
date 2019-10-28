import types

from collections import defaultdict

from django.core.exceptions import ImproperlyConfigured

from .handlers import BaseHandler


class BaseDispatcher:
    """
    Base dispatcher class that can be subclassed to call a handler based on a change in some a SmartModel.
    If you subclass, be sure the __call__ method does not change signature.
    """

    signal = None

    def __init__(self, handler, signal=None):
        self.handler = handler
        assert (isinstance(handler, types.FunctionType)
                or isinstance(handler, BaseHandler)), 'Handler must be function or instance of ' \
                                                      'chamber.models.handlers.BaseHandler, {}: {}'.format(self,
                                                                                                           handler)
        self._connected = defaultdict(list)
        self._signal = signal if signal is not None else self.signal

    def connect(self, sender):
        self._signal.connect(self, sender=sender)

    def __call__(self, instance, **kwargs):
        """
        `instance` ... instance of the SmartModel where the handler is being called
        Some dispatchers require additional params to evaluate the handler can be dispatched,
        these are hidden in args and kwargs.
        """
        if self._can_dispatch(instance, **kwargs):
            self.handler(instance=instance, **kwargs)

    def _can_dispatch(self, instance, *args, **kwargs):
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

    def __init__(self, handler, property_name, signal=None):
        self.property_name = property_name
        super().__init__(handler, signal)

    def _can_dispatch(self, instance, **kwargs):
        return getattr(instance, self.property_name)


class CreatedDispatcher(BaseDispatcher):
    """
    Calls registered handler if and only if an instance of the model is being created.
    """

    def _can_dispatch(self, instance, changed, **kwargs):
        return not changed


class StateDispatcher(BaseDispatcher):
    """
    Use this class to register a handler for transition of a model to a certain state.
    """

    def _validate_init_params(self):
        super()._validate_init_params()
        if self.field_value not in {value for value, _ in self.enum.choices}:
            raise ImproperlyConfigured('Enum of FieldDispatcher does not contain {}.'.format(self.field_value))

    def __init__(self, handler, enum, field, field_value, signal=None):
        self.enum = enum
        self.field = field
        self.field_value = field_value
        super().__init__(handler, signal=signal)

    def _can_dispatch(self, instance, changed, changed_fields, *args, **kwargs):
        return (
            self.field.get_attname() in changed_fields and
            getattr(instance, self.field.get_attname()) == self.field_value
        )
