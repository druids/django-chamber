from __future__ import unicode_literals

import six

from django.db import models


class OptionsLazy(object):

    def __init__(self, name, klass):
        self.name = name
        self.klass = klass

    def __get__(self, instance=None, owner=None):
        option = self.klass(owner)
        setattr(owner, self.name, option)
        return option


class OptionsBase(type):
    def __new__(cls, *args, **kwargs):
        new_class = super(OptionsBase, cls).__new__(cls, *args, **kwargs)
        if new_class.model_class and new_class.meta_name:
            setattr(new_class.model_class, new_class.meta_name, OptionsLazy(new_class.meta_name, new_class))
        return new_class


class Options(six.with_metaclass(OptionsBase, object)):

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
        meta_models = [b for b in self.model.__mro__ if issubclass(b, models.Model)]
        for model in meta_models:
            meta = getattr(model, self.meta_class_name, None)
            if meta:
                value = getattr(meta, name, None)
                if value is not None:
                    return value
        return default_value
