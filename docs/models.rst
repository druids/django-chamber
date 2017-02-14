Models
======

Model Fields
------------

.. class:: chamber.models.fields.DecimalField

Same as ``django.db.models.DecimalField`` but with additional attributes. Uses ``chamber.forms.fields.DecimalField`` as the default form field.

    .. attribute:: min

        A minimal value of the field. An appropriate ``MinValueValidator`` is added automatically. The HTML ``min`` component is added to the form field.

    .. attribute:: max

        A maximal value of the field. An appropriate ``MaxValueValidator`` is added automatically. The HTML ``max`` component is added to the form field.

    .. attribute:: step

        The step between values that is set on the form field.

.. class:: chamber.models.fields.RestrictedFileFieldMixin

Same as FileField, but you can specify:

    .. attribute:: allowed_content_types

        A list containing allowed content types, e.g. ``['application/pdf', 'image/jpeg']``

    .. attribute:: max_upload_size

        A number indicating the maximum file size allowed for upload in MB. The maximum upload size can be specified in project settings as ``MAX_FILE_UPLOAD_SIZE``

.. class:: chamber.models.fields.FileField

The ``django.db.models.FileField`` with ``RestrictedFileFieldMixin`` options.

.. class:: chamber.models.fields.ImageField

``sorl.thumbnail.ImageField`` with fallback to ``django.db.models.ImageField`` when ``sorl`` is not installed. Supports ``RestrictedFileFieldMixin`` options.

.. class:: chamber.models.fields.CharNullField

``django.db.models.CharField`` that stores ``NULL`` but returns ``''`` .

.. class:: chamber.models.fields.PriceField

``chamber.models.fields.DecimalField`` with defaults:

    .. attribute:: currency

        For example ``'CZK'``.

    .. attribute:: decimal_places

        Number of digits reserved for the decimal part of the number.

    .. attribute:: max_digits

        Max number of digits reserved for the field.

    .. attribute:: humanized

        Humanized value for a pretty printing via ``chamber.models.humanized_helpers.price_humanized``

.. class:: chamber.models.fields.PositivePriceField

``chamber.models.fields.PriceField`` with a default ``django.core.validators.MinValueValidator`` set to ``0.00``.

.. class:: chamber.models.fields.SouthMixin

Mixin for automatic South migration of custom model fields.

SmartQuerySet
-------------

SmartModel uses a modified QuerySet by default with some convenience filters.

If you are overriding model manager of a SmartModel, you should
incorporate ``SmartQuerySet`` in order not to lose its benefits and to
follow the Rule of the Least Surprise (everyone using your SmartModel
will assume the custom filters to be there).

1. If the manager is created using the ``QuerySet.as_manager()`` method,
   your custom queryset should subclass ``SmartQuerySet`` instead the
   one from Django.
2. If you have a new manager created by subclassing ``models.Manager``
   from Django, you should override the ``get_queryset`` method as shown
   in Django docs `here`_.

.. class:: chamber.models.SmartQuerySet

    .. method:: fast_distinct()

        Returns same result as regular ``distinct()`` but is much faster especially in PostgreSQL which performs distinct on all DB columns. The optimization is achieved by doing a second query and the ``__in`` operator. If you have queryset ``qs`` of ``MyModel`` then ``fast_distinct()`` equals to calling

        .. code:: python

            MyModel.objects.filter(pk__in=qs.values_list('pk', flat=True))
