from datetime import date, datetime, time

from django.http.response import Http404
from django.shortcuts import _get_queryset
from django.utils import timezone
from django.core.exceptions import ValidationError


def get_object_or_none(klass, *args, **kwargs):
    queryset = _get_queryset(klass)
    try:
        return queryset.get(*args, **kwargs)
    except (queryset.model.DoesNotExist, ValueError, ValidationError):
        return None


def get_object_or_404(klass, *args, **kwargs):
    queryset = _get_queryset(klass)
    try:
        return queryset.get(*args, **kwargs)
    except (queryset.model.DoesNotExist, ValueError, ValidationError):
        raise Http404


def distinct_field(klass, *args, **kwargs):
    return _get_queryset(klass).order_by().values_list(*args, **kwargs).distinct()


def filter_or_exclude_by_date(negate, klass, **kwargs):
    filter_kwargs = {}
    for key, date_value in kwargs.items():
        assert isinstance(date_value, date)

        date_range = (
            timezone.make_aware(datetime.combine(date_value, time.min), timezone.get_current_timezone()),
            timezone.make_aware(datetime.combine(date_value, time.max), timezone.get_current_timezone())
        )
        filter_kwargs['%s__range' % key] = date_range

    if negate:
        return _get_queryset(klass).exclude(**filter_kwargs)
    else:
        return _get_queryset(klass).filter(**filter_kwargs)


def filter_by_date(klass, **kwargs):
    return filter_or_exclude_by_date(False, klass, **kwargs)


def exclude_by_date(klass, **kwargs):
    return filter_or_exclude_by_date(True, klass, **kwargs)


def get_model_field_names(model):
    return {
        field.name for field in model._meta.fields
    } | {
        field.attname for field in model._meta.fields
    } | {'pk'}


def change(obj, **changed_fields):
    """
    Changes a given `changed_fields` on object and returns changed object.
    """
    obj_field_names = get_model_field_names(obj)

    for field_name, value in changed_fields.items():
        if field_name not in obj_field_names:
            raise ValueError("'{}' is an invalid field name".format(field_name))
        setattr(obj, field_name, value)
    return obj


def get_update_fields(obj, **changed_fields):
    obj_field_names = get_model_field_names(obj)
    update_fields = []
    for field_name, value in changed_fields.items():
        if field_name not in obj_field_names:
            raise ValueError("'{}' is an invalid field name".format(field_name))

        if getattr(obj, field_name) != value:
            update_fields.append(field_name)
    return update_fields


def change_and_save(obj, update_only_changed_fields=False, save_kwargs=None, **changed_fields):
    """
    Changes a given `changed_fields` on object, saves it and returns changed object.
    """
    from chamber.models import SmartModel

    save_kwargs = save_kwargs if save_kwargs is not None else {}
    if update_only_changed_fields:
        if isinstance(obj, SmartModel):
            save_kwargs['update_only_changed_fields'] = True
        else:
            save_kwargs['update_fields'] = get_update_fields(obj, **changed_fields)

    change(obj, **changed_fields)
    obj.save(**save_kwargs)
    return obj


def bulk_change(iterable, **changed_fields):
    """
    Changes a given `changed_fields` on each object in a given `iterable`, returns the changed objects.
    """
    return [change(obj, **changed_fields) for obj in iterable]


def bulk_change_and_save(iterable, update_only_changed_fields=False, save_kwargs=None, **changed_fields):
    """
    Changes a given `changed_fields` on each object in a given `iterable`, saves objects
    and returns the changed objects.
    """
    return [
        change_and_save(obj, update_only_changed_fields=update_only_changed_fields, save_kwargs=save_kwargs,
                        **changed_fields)
        for obj in iterable
    ]


def bulk_save(iterable):
    """
    Saves a objects in a given `iterable`.
    """
    return [obj.save() for obj in iterable]
