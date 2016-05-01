from __future__ import unicode_literals

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
