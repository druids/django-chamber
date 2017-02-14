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

.. class:: chamber.utils.datastructures.Enum
Python's ``set`` with ``AbstractEnum`` behaviour.

.. class:: chamber.utils.datastructures.NumEnum
Python's ``dict`` with ``AbstractEnum`` behaviour.

::

    >>> NumEnum('a', 'b')
    {'a': 1, 'b': 2}

.. class:: chamber.utils.datastructures.AbstractChoicesEnum
Base choices class (can be used as a model field's ``choices`` argument).

.. class:: chamber.utils.datastructures.ChoicesEnum
``django.utils.datastructures.SortedDict`` with ``AbstractEnum`` and
``AbstractChoicesEnum`` behaviour. Useful for string based choices.

::

    >>> enum = ChoicesEnum(('OK', 'ok'), ('KO', 'ko'))
    >>> enum
    {'OK': 'ok', 'KO': 'ko'}
    >>> enum.OK
    'ok'
    >>> enum.choices
    [('OK', 'ok'), ('KO', 'ko')]

.. class:: chamber.utils.datastructures.ChoicesNumEnum

``django.utils.datastructures.SortedDict`` with ``AbstractEnum`` and
``AbstractChoicesEnum`` behaviour. Useful for integer-based choices.

::

    >>> enum = ChoicesNumEnum(('OK', 'ok', 1), ('KO', 'ko', 2))
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
