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


SmartModel
----------

``chamber.models.SmartModel`` improved django Model class with several features that simplify development of complex applications

.. class:: chamber.models.SmartModel

    .. attribute:: dispatchers

        List of defined pre or post save dispatchers. More obout it will find _dispatchers

    .. attribute:: has_changed

        Returns ``True`` or ``False`` depending on whether instance field values were changed

    .. attribute:: initial_values

        Returns initial values of the object from loading instance from database. It should represent actual state of the object in the database

    .. attribute:: is_adding

        Returns ``True`` or ``False`` depending on whether model instance will be inserting or updating in the database

    .. attribute:: is_changing

        Returns ``True`` or ``False`` depending on whether model instance will be updating or inserting in the database

    .. attribute:: initial_values

        Returns dict initial values of all instance fields that were loaded from the database. If object is not stored in the database the values will be ``Unknown`` which is similar object to ``None`` value

    .. attribute:: changed_fields

        Returns ``ChangedFields`` instance that contains information which fields have been changed and how

    .. method:: clean_<field_name>()

        Like a django form field you can use your own method named by field name for cleaning input value. You can too raise ``ValidationError`` if input value is invalid

    .. method:: _pre_save(change, changed_fields, *args, **kwargs)

        Method that is called before saving instance. You can here change instance structure or call some operations before saving object. Parameter ``change`` has True value if model instance existed before save was called, otherwise False.
        Parameter ``changed_fields`` contains name of changed fields and its original and current values. Changes in the method body have no effect on ``changed_fields`` property.

    .. method:: _post_save(change, changed_fields, *args, **kwargs)

        Method that is called after saving instance. You can here change instance structure or call some operations after saving object. Parameter ``change`` has True value if model instance existed before save was called, otherwise False.
        Parameter ``changed_fields`` contains name of changed fields and its original and current values. Changes in the method body have no effect on ``changed_fields`` property.

    .. method:: _pre_delete()

        Method that is called before removing instance. You can here change instance structure or call some operations before removing object

    .. method:: _post_delete()

        Method that is called after removing instance. You can here change instance structure or call some operations after removing object

    .. method:: refresh_from_db()

        There is used implementation from django ``refresh_from_db`` method with small change that method returns refreshed instance

    .. method:: change(**changed_fields)

        Update instance field values with values sent in ``changed_fields``

    .. method:: change_and_save(update_only_changed_fields=False, **changed_fields)

        Update instance field values with values sent in ``changed_fields`` and finally instance is saved. If you want to update only changed fields in the database you can use parameter ``update_only_changed_fields`` to achieve it

    .. method:: full_clean(exclude=None, *args, **kwargs)

        The original django full_clean method is improved with calling extra clean_{field} methods on the model (it is similar to django forms clean methods::

            class CustomModel(SmartModel):

                name = models.CharField(max_length=100)

                def clean_name(self):
                    if len(self.name) >= 10:
                        raise ValidationError('name must be lower than 10')

        The method ``clean_name`` will be automatically called when the ``full_clean`` method is triggered and ValidationError will be added to the field error.

    .. method:: get_locked_instance()

        The method returns the new instance of the self object which is locked in the database with ``select_for_update``. Method must be used in the django atomic block.


SmartAuditModel
----------

SmartModel with two extra fields `created_at` and `changed_at` to log when the model was created or updated.

.. class:: chamber.models.SmartAuditModel

    .. attribute:: created_at

        Because our experience has shown us that datetime of creation is very useful this field ``django.models.DateTimeField`` with ``auto_add_no`` set to ``True`` is added to every model that inherits from ``SmartModel``

    .. attribute:: changed_at

        This model field is same case as ``created_at`` with the difference that there is used ``auto_now=True`` therefore every date and time of change is stored here.

SmartMeta
---------

SmartMeta similar like django meta is defined inside ``SmartModel`` and is accessible via ``_smart_meta`` attribute. Its purpose is define default ``SmartModel`` behavior.

.. class:: SmartMeta

    .. attribute:: is_cleaned_pre_save

        Defines if ``SmartModel`` will be automatically validated before saving. Default value is ``False``

    .. attribute:: is_cleaned_post_save

        Defines if ``SmartModel`` will be automatically validated after saving. Default value is ``False``

    .. attribute:: is_cleaned_pre_delete

        Defines if ``SmartModel`` will be automatically validated before removing. Default value is ``False``

    .. attribute:: is_cleaned_post_delete

        Defines if ``SmartModel`` will be automatically validated after removing. Default value is ``False``

    .. attribute:: is_save_atomic

        Defines if ``SmartModel`` will be saved in transaction atomic block ``False``

    .. attribute:: is_delete_atomic

        Defines if ``SmartModel`` will be removed in transaction atomic block ``False``

.. code:: python

    class SmartModelWithMeta(SmartModel):

        class SmartMeta:
            is_cleaned_pre_save = True
            is_cleaned_pre_delete = True

The default configuration for all smart models can be defined in your settings with setting `CHAMBER_SMART_MODEL_ATTRIBUTES`:

.. code:: python

    CHAMBER_SMART_MODEL_ATTRIBUTES = {
        'is_cleaned_pre_save': True,
        'is_cleaned_post_save': False,
        'is_cleaned_pre_delete': False,
        'is_cleaned_post_delete': False,
        'is_save_atomic': False,
        'is_delete_atomic': False,
    }


Unknown
-------

``chamber.models.Unknown`` is singleton that is used for initial field values if object is not stored in the database. The purpose is distinguish ``None`` value from ``Unknown`` value because ``None`` can be stored in the database as a normal value. The ``Unknown`` behavior is same as ``None``.


ChangedFields
-------------

``chamber.models.ChangedFields`` is dict-like class that is used for storing which fields of model instance were changed

::

    >>> user = User.objects.get(last_name='Gaul')
    >>> user.last_name = 'Goul'
    >>> 'last_name' in user.changed_fields
    True
    >>> 'first_name' in user.changed_fields
    False
    >>> user.changed_fields.has_any_key('first_name', 'last_name')
    True
    >>> user.changed_fields['last_name'].initial
    'Gaul'
    >>> user.changed_fields['last_name'].current
    'Goul'
    >>> user.changed_fields.keys()
    ['last_name']

.. class:: ChangedFields

    .. attribute:: initial_values

         Return initial values of the model instance

    .. attribute:: current_values

         Return current values of the model instance

    .. attribute:: diff

         Return only changed values of the model instance

    .. method:: has_key(k)

         Return if field ``k`` was changed

    .. method:: has_any_key(*keys)

         Return if any of the fields ``keys`` were changed

    .. method:: keys()

         Return all names of the changed fields

    .. method:: values()

         Return list of ``ValueChange`` of all changed fields. Where ``ValueChange`` is POJO object that contains field value before changed and value after change (``initial`` and ``current`` attribute)

    .. method:: items()

         Return dict of changed fields where key is field name and value is ``ValueChange`


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

    .. method:: change_and_save(update_only_changed_fields=False, **changed_fields)

        Changes selected fields on the selected queryset and saves it and returns changed objects in the queryset. Difference from update is that there is called save method on the instance, but it is slower. If you want to update only changed fields in the database you can use parameter ``update_only_changed_fields`` to achieve it

    .. method:: first(**field_names)

        Method is only shortcut to ``Model.objects.order_by('field_name').first()``. With this method you can use ``Model.objects.first('field_name')``

    .. method:: last(**field_names)

        Method is only shortcut to ``Model.objects.order_by('field_name').last()``. With this method you can use ``Model.objects.last('field_name')``
