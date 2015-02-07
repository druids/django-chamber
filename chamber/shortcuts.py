from django.http.response import Http404
from django.shortcuts import _get_queryset


def get_object_or_none(klass, *args, **kwargs):
    queryset = _get_queryset(klass)
    try:
        return queryset.get(*args, **kwargs)
    except (queryset.model.DoesNotExist, ValueError):
        return None


def get_object_or_404(klass, *args, **kwargs):
    queryset = _get_queryset(klass)
    try:
        return queryset.get(*args, **kwargs)
    except (queryset.model.DoesNotExist, ValueError):
        raise Http404


def distinct_field(klass, *args, **kwargs):
    return _get_queryset(klass).order_by().values_list(*args, **kwargs).distinct()