from django.core.exceptions import ImproperlyConfigured

from chamber.utils.transaction import on_success, UniqueOnSuccessCallable
from chamber.models.signals import dispatcher_post_save


class BaseHandler:
    """
    Base dispatcher class that can be subclassed to call a handler based on a change in some a SmartModel.
    If you subclass, be sure the __call__ method does not change signature.
    """

    signal = None

    def __init__(self, signal=None):
        self._signal = signal if signal is not None else self.signal

    def connect(self, sender):
        if not self._signal:
            raise ImproperlyConfigured('Handler cannot be connected as dispatcher, because signal is not set')
        self._signal.connect(self, sender=sender)

    def __call__(self, instance, **kwargs):
        """
        `instance` ... instance of the SmartModel where the handler is being called
        Some dispatchers require additional params to evaluate the handler can be dispatched,
        these are hidden in args and kwargs.
        """
        if self.can_handle(instance, **kwargs):
            self._handle(instance, **kwargs)

    def _handle(self, instance, **kwargs):
        self.handle(instance, **kwargs)

    def can_handle(self, instance, **kwargs):
        return True

    def handle(self, instance, **kwargs):
        raise NotImplementedError


class OnSuccessHandler(BaseHandler):
    """
    Handler class that is used for performing on success operations.
    """

    signal = dispatcher_post_save

    def __init__(self, using=None, *args, **kwargs):
        self.using = using
        super().__init__(*args, **kwargs)

    def _handle(self, instance, **kwargs):
        on_success(lambda: self.handle(instance, **kwargs), using=self.using)


class InstanceOneTimeOnSuccessHandlerCallable(UniqueOnSuccessCallable):
    """
    Use this class to create on success caller that will be unique per instance and will be called only once per
    instance.
    """

    def __init__(self, handler, instance):
        super().__init__(instance=instance)
        self.handler = handler

    def _get_instance(self):
        instance = self.kwargs_list[0]['instance']
        return instance.__class__.objects.get(pk=instance.pk)

    def _get_unique_id(self):
        instance = self.kwargs_list[0]['instance']
        return hash((self.handler.__class__, instance.__class__, instance.pk))

    def __call__(self):
        self.handler.handle(instance=self._get_instance())


class InstanceOneTimeOnSuccessHandler(OnSuccessHandler):
    """
    Use this class to create handler that will be unique per instance and will be called only once per instance.
    """

    def _handle(self, instance, **kwargs):
        on_success(InstanceOneTimeOnSuccessHandlerCallable(self, instance), using=self.using)
