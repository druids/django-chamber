import collections

import copy

from chamber.utils.decorators import singleton


def _should_exclude_field(field_name, fields, exclude):
    return (fields and field_name not in fields) or (exclude and field_name in exclude)


def field_value_from_instance(field, instance):
    """
    Converts a model field to a dictionary
    """
    value = field.value_from_object(instance)
    if isinstance(value, (dict, list)):
        return copy.deepcopy(value)
    else:
        return value


@singleton
class UnknownSingleton:

    def __repr__(self):
        return 'unknown'

    def __bool__(self):
        return False


Unknown = UnknownSingleton()


@singleton
class DeferredSingleton:

    def __repr__(self):
        return 'deferred'

    def __bool__(self):
        return False


Deferred = DeferredSingleton()


def get_model_fields(model):
    return [field for field in model._meta.concrete_fields]  # pylint: disable=W0212


def get_model_field_names(model):
    return [field.name for field in get_model_fields(model)]


def unknown_model_fields_to_dict(instance, fields=None, exclude=None):
    return {
        field_name: Unknown
        for field_name in get_model_field_names(instance)
        if not _should_exclude_field(field_name, fields, exclude)
    }


def model_to_dict(instance, fields=None, exclude=None):
    """
    The same implementation as django model_to_dict but editable fields are allowed
    """
    return {
        field.name: copy.deepcopy(field_value_from_instance(field, instance))
        for field in get_model_fields(instance)  # pylint: disable=W0212
        if not _should_exclude_field(field.name, fields, exclude)
    }


ValueChange = collections.namedtuple('ValueChange', ('initial', 'current'))


class ChangedFields:
    """
    Class stores changed fields and its initial and current values.
    """

    def __init__(self, initial_dict):
        self._initial_dict = initial_dict

    @property
    def initial_values(self):
        return self._initial_dict.copy()

    @property
    def current_values(self):
        return self.get_current_values()

    def get_current_values(self, fields=None):
        raise NotImplementedError

    @property
    def changed_values(self):
        return {k: value_change.current for k, value_change in self.get_diff().items()}

    def get_diff(self, fields=None):
        d1 = self.initial_values
        d2 = self.get_current_values(fields=fields)
        return {k: ValueChange(d1[k], v) for k, v in d2.items() if v != d1[k]}

    def __setitem__(self, key, item):
        raise AttributeError('Object is readonly')

    def __getitem__(self, key):
        return self.get_diff(fields=[key])[key]

    def __bool__(self):
        return bool(self.get_diff())

    def __len__(self):
        return len(self.get_diff())

    def __delitem__(self, key):
        raise AttributeError('Object is readonly')

    def clear(self):
        raise AttributeError('Object is readonly')

    def has_key(self, key):
        return self.has_any_key(key)

    def has_any_key(self, *keys):
        diff = self.get_diff(fields=keys)
        return bool(set(diff.keys()) & set(keys))

    def keys(self):
        return self.get_diff().keys()

    def values(self):
        return self.get_diff().values()

    def items(self):
        return self.get_diff().items()

    def pop(self, *args, **kwargs):
        raise AttributeError('Object is readonly')

    def __cmp__(self, dictionary):
        return self.get_diff() == dictionary

    def __contains__(self, item):
        return self.has_any_key(item)

    def __iter__(self):
        return iter(self.get_diff())

    def __repr__(self):
        return repr(self.get_diff())

    def __str__(self):
        return repr(self.get_diff())


class DynamicChangedFields(ChangedFields):
    """
    Dynamic changed fields are changed with the instance changes.
    """

    def __init__(self, instance):
        super().__init__(
            self._get_unknown_dict(instance)
        )
        self.instance = instance

    def _get_unknown_dict(self, instance):
        return unknown_model_fields_to_dict(instance)

    def get_current_values(self, fields=None):
        deferred_values = {
            field_name: value for field_name, value in self._initial_dict.items()
            if field_name in self.instance.get_deferred_fields()
        }
        current_values = model_to_dict(
            self.instance,
            fields=fields,
            exclude=set(deferred_values.keys())
        )
        current_values.update(deferred_values)
        return current_values

    def get_static_changes(self):
        return StaticChangedFields(self.initial_values, self.current_values)

    def from_db(self, fields=None):
        if fields is None:
            fields = {field_name for field_name, value in self._initial_dict.items() if value is not Deferred}

        self._initial_dict.update(
            model_to_dict(self.instance, fields=set(fields))
        )

        for field_name, value in self._initial_dict.items():
            if value is Unknown:
                self._initial_dict[field_name] = Deferred


class StaticChangedFields(ChangedFields):
    """
    Static changed fields are immutable. The origin instance changes will not have an affect.
    """

    def __init__(self, initial_dict, current_dict):
        super().__init__(initial_dict)
        self._current_dict = current_dict

    def get_current_values(self, fields=None):
        return {k: v for k, v in self._current_dict.items() if fields is None or k in fields}
