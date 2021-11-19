import codecs

from django.db.models import Model
from django.db.models.fields import Field
from django.db.transaction import get_connection, Atomic

from chamber.utils import remove_accent


class OptionsLazy:

    def __init__(self, name, klass):
        self.name = name
        self.klass = klass

    def __get__(self, instance=None, owner=None):
        return self.klass(owner)


class OptionsBase(type):
    def __new__(cls, *args, **kwargs):
        new_class = super().__new__(cls, *args, **kwargs)
        if new_class.model_class and new_class.meta_name:
            setattr(new_class.model_class, new_class.meta_name, OptionsLazy(new_class.meta_name, new_class))
        return new_class


class Options(metaclass=OptionsBase):

    meta_class_name = None
    meta_name = None
    attributes = None
    model_class = None

    def __init__(self, model):
        self.model = model

        for key, default_value in self._get_attributes(model).items():
            setattr(self, key, self._getattr(key, default_value))

    def _get_attributes(self, model):
        return self.attributes

    def _getattr(self, name, default_value):
        meta_models = [b for b in self.model.__mro__ if issubclass(b, Model)]
        for model in meta_models:
            meta = getattr(model, self.meta_class_name, None)
            if meta:
                value = getattr(meta, name, None)
                if value is not None:
                    return value
        return default_value


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
    getattr(self, '_init_chamber_patch_')(*args, **kwargs)


def remove_accent_errors(exception):
    """
    Implements the 'remove_accent' error handling (for encoding with text encodings only): the unencodable character
    is replaced by an character without accent (characters are converted to ASCII).
    """
    chunk = exception.object[exception.start:exception.end]
    return remove_accent(chunk), exception.end


Field.default_humanized = None
Field._init_chamber_patch_ = Field.__init__  # pylint: disable=W0212
Field.__init__ = field_init

codecs.register_error('remove_accent', remove_accent_errors)


def atomic_pre_commit_enter(self):
    self._enter_chamber_patch_()

    connection = get_connection(self.using)
    # empty savepoints means top level atomic block
    if not connection.savepoint_ids:
        connection.run_pre_commit = []


def atomic_pre_commit_exit(self, exc_type, exc_value, traceback):
    connection = get_connection(self.using)

    if exc_type is None and not connection.needs_rollback:
        if not connection.savepoint_ids:
            # No exception and no rollback, pre_commit hooks can be performed on top level atomic block exit function
            while connection.run_pre_commit:
                sids, callable_hash, func = connection.run_pre_commit.pop(0)
                func()
    else:
        if connection.savepoint_ids:
            sid = connection.savepoint_ids[-1]
            if sid:
                # only current sid is removed from pre commit list
                connection.run_pre_commit = [
                    (sids, callable_hash, func)
                    for (sids, callable_hash, func) in connection.run_pre_commit if sid not in sids
                ]
        else:
            # top level atomic block rollback
            connection.run_pre_commit = []
    self._exit_chamber_patch_(exc_type, exc_value, traceback)


Atomic._enter_chamber_patch_ = Atomic.__enter__
Atomic._exit_chamber_patch_ = Atomic.__exit__
Atomic.__enter__ = atomic_pre_commit_enter
Atomic.__exit__ = atomic_pre_commit_exit
