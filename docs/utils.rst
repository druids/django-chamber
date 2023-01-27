Utils
=====

Utility Functions
-----------------

.. function:: chamber.utils.remove_accent(string_with_diacritics)

.. code:: python
    remove_accent('ěščřžýáíé') # 'escrzyaie'

.. function:: chamber.utils.get_class_method(cls_or_inst, method_name)

Returns a method of a given class or instance.


.. function:: chamber.utils.forms.formset_has_file_field

Returns True if passed formset contains FileField (or ImageField).

.. function:: chamber.utils.http.query_string_from_dict

Assembles query string from a Python ``dict``.
::

    >>> query_string_from_dict({'q': 'query1', 'user': 'test'})
    u'q=query1&user=test'

Enums
-----

.. class:: chamber.utils.datastructures.AbstractEnum

Base enumeration class with controlled ``__getattr__``.

  .. attribute::  chamber.utils.datastructures.AbstractEnum.all

  Returns all enum values in a tuple.

  .. method::  chamber.utils.datastructures.AbstractEnum.__iter__

  Returns iterator over enum values.

  .. method::  chamber.utils.datastructures.AbstractEnum.get_name

  Returns name of the choice accorting to its value.

  .. method::  chamber.utils.datastructures.AbstractEnum.get_name

  Implementation of in operator. Return ``True`` if value is part of the enum.


.. class:: chamber.utils.datastructures.Enum

Python's ``set`` with ``AbstractEnum`` behaviour. Enum key can be only string type. Key and values can be different.

::

    >>> enum = NumEnum('A', 'B') #  {'A': 'A', 'B': 'B'}
    >>> enum.all
    ('A', 'B')
    >>> 'A' in enum
    True
    >>> list(enum)
    ['A', 'B']
    >>> enum.A
    'A'

    >>> enum = NumEnum(('A', 'a'), ('B', 'b')) #  {'A': 'a', 'B': 'b'}
    >>> enum.all
    ('a', 'b')
    >>> 'a' in enum
    True
    >>> list(enum)
    ['a', 'b']
    >>> enum.A
    'a'


.. class:: chamber.utils.datastructures.NumEnum

Python's ``dict`` with ``AbstractEnum`` behaviour.

::

    >>> enum = NumEnum('A', 'B') #  {'A': 1, 'B': 2}
    >>> enum.all
    (1, 2)
    >>> 1 in enum
    True
    >>> list(enum)
    [1, 2]
    >>> enum.A
    1

    >>> enum = NumEnum(('A', 6), ('B', 5)) #  {'A': 6, 'B': 5}
    >>> enum.all
    (6, 5)
    >>> 5 in enum
    True
    >>> list(enum)
    [6, 5]
    >>> enum.A
    6

.. class:: chamber.utils.datastructures.AbstractChoicesEnum

Base choices class (can be used as a model field's ``choices`` argument).

.. class:: chamber.utils.datastructures.ChoicesEnum

``django.utils.datastructures.SortedDict`` with ``AbstractEnum`` and
``AbstractChoicesEnum`` behaviour. Useful for string based choices.

::

    >>> enum = ChoicesEnum(('OK', 'label ok'), ('KO', 'label ko'))  # {'OK': ('OK', 'label ok), 'ko': ('KO', 'label ko)}
    >>> enum.OK
    'OK'
    >>> enum.choices
    [('OK', 'ok'), ('KO', 'ko')]
    >>> enum.get_label(enum.OK)
    'label ok'

    >>> enum = ChoicesEnum(('OK', 'label ok', 'ok'), ('KO', 'label ko', 'ko'))  #  {'OK': ('ok', 'label ok), 'ko': ('ko', 'label ko)}
    >>> enum.OK
    'ok'
    >>> enum.choices
    [('ok', 'label ok'), ('ko', 'label ko')]
    >>> enum.get_label(enum.OK)
    'label ok'

.. class:: chamber.utils.datastructures.ChoicesNumEnum

``django.utils.datastructures.SortedDict`` with ``AbstractEnum`` and
``AbstractChoicesEnum`` behaviour. Useful for integer-based choices.

::

    >>> enum = ChoicesNumEnum(('OK', 'label ok', 1), ('KO', 'label ko', 2))
    >>> enum.KO
    2
    >>> enum.choices
    [(1, 'ok'), (2, 'ko')]
    >>> enum.get_label(2)
    'ko'

Decorators
----------

.. decorator:: chamber.utils.decorators.classproperty

Decorator that turns a class method into a property of the class.

::

    class RestResource(BaseResource):
        @classproperty
        def csrf_exempt(cls):
            return not cls.login_required

        @classmethod
        def as_view(cls, allowed_methods=None, **initkwargs):
            view.csrf_exempt = cls.csrf_exempt

.. decorator:: chamber.utils.decorators.singleton

Class decorator, which allows for only one instance of class to exist.

.. decorator:: chamber.utils.decorators.short_description

Sets ``short_description`` attribute that is used to render description of a Django form field.

::

    @short_description('amount')
    def absolute_amount(self):
        return abs(self.amount)

is equivalent to

::

    def absolute_amount(self):
        return abs(self.amount)
    absolute_amount.short_description = 'amount'

Tqdm
----

.. class:: chamber.utils.tqdm.tqdm

The class extends ``tqdm`` library (https://tqdm.github.io/). Now the ``tqdm`` context processor can be used with th django commands. Django command stdout writes newline after every write to the stdout which breaks the progress bar::

    # a custom command
    from django.core.management.base import BaseCommand
    from chamber.utils.tqdm import tqdm

    class Command(BaseCommand):

        def handle(self, *args, **options):
            for i in tqdm(range(10), file=self.stdout):
                custom_operation(i)


Logging
-------

.. class:: chamber.logging.AppendExtraJSONHandler

Log handler which writes every extra argument in the log to the output message in a json format::

    # logged message with handler
    logger.log('message', extra={'extra': 'data'})

    # logger output
    message --- {"extra": "data"}


Storages
--------

.. class:: chamber.storages.BaseS3Storage

Class fixes bugs in the boto3 library storage. For example you can write only bytes with the standard boto3 S3Boto3Storage. Strings will raise exception. The chamber BaseS3Storage adds possibility to saves strings to the storage.

.. class:: chamber.storages.BasePrivateS3Storage

Improves boto3 storage with url method. With this method you can generate temporary URL address to the private s3 storage. The URL will expire after ``CHAMBER_PRIVATE_S3_STORAGE_URL_EXPIRATION`` (default value is one day).

Commands
--------

makemessages
^^^^^^^^^^^^

Django makemessages commands is expanded with another keywords which represents transaction strings. This keyword you can use instead of long django functions:

* ``_l`` - instead of ``gettext_lazy``
* ``_n`` - instead of ``ngettext``
* ``_nl`` - instead of ``ngettext_lazy``
* ``_p`` - instead of ``pgettext``
* ``_np`` - instead of ``npgettext``
* ``_pl`` - instead of ``pgettext_lazy``
* ``_npl`` - instead of ``npgettext_lazy``

Second improvement is parameter ``no-creation-date`` which remove ``POT-Creation-Date`` from the result file.

initdata
^^^^^^^^

Init data is command similar to django ``loaddata``. The command automatically loads the file from the path defined in setting ``CHAMBER_INITAL_DATA_PATH``.


