Shortcuts
=========

This is a collection of Django-styled shotcut function.

.. function:: chamber.shortcuts.get_object_or_none

Takes a Model or a QuerySet and some filter keyword arguments and returns an instance
of the Model if it exists, ``None`` otherwise. Similar to ``get_object_or_404`` in Django.

::

    >>> get_object_or_none(User, pk=1)
    <User: Gaul Asterix>
    >>> get_object_or_none(User.objects.exclude(pk=1), pk=1) or ''

.. function:: chamber.shortcuts.get_object_or_404

Takes a Model or a QuerySet and some filter keyword arguments and returns an instance
of the Model if it exists, raises ``django.http.response.Http404`` otherwise.

::

    >>> get_object_or_404(User, pk=1)
    <User: Gaul Asterix>
    >>> get_object_or_404(User.objects.exclude(pk=1), pk=1)
    Traceback (most recent call last):
      File "<console>", line 1, in <module>
      File "/var/ve/lib/python2.7/site-packages/chamber/shortcuts.py", line 21, in get_object_or_404
        raise Http404
    Http404

.. function:: chamber.shortcuts.distinct_field

Takes a Model or a QuerySet. The rest of the args are the fields whose unique values should be returned.

::

    >>> User.objects.filter(last_name='Gaul')
    [<User: Gaul Obelix>, <User: Gaul Asterix>]
    >>> distinct_field(User.objects.filter(last_name='Gaul'), 'last_name')
    [(u'Gaul',)]

.. function:: chamber.shortcuts.filter_or_exclude_by_date

Takes a ``bool`` (True for exclude, False for filter), Model or
QuerySet and date parameters and return queryset filtered or excluded by
these date parameters.

::

    >>> Order.objects.values_list('created_at', flat=True)
    [datetime.datetime(2014, 4, 6, 15, 56, 16, 727000, tzinfo=<UTC>),
     datetime.datetime(2014, 2, 6, 15, 56, 16, 727000, tzinfo=<UTC>),
     datetime.datetime(2014, 1, 11, 23, 15, 43, 727000, tzinfo=<UTC>)]
    >>> filter_or_exclude_by_date(False, Order, created_at=date(2014, 2, 6))
    [<Order: MI-1234567>]
    >>> filter_or_exclude_by_date(False, Order, created_at=date(2014, 2, 6))[0].created_at
    datetime.datetime(2014, 2, 6, 15, 56, 16, 727000, tzinfo=<UTC>)

.. function:: chamber.shortcuts.filter_by_date

Shortcut for ``chamber.shortcuts.filter_or_exclude_by_date`` with first parameter False.

.. function:: chamber.shortcuts.exclude_by_date

Shortcut for ``chamber.shortcuts.filter_or_exclude_by_date`` with first parameter True.
