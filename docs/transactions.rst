Transaction helpers
===================


``chamber.utils.transaction.atomic``
------------------------------------

.. function:: atomic()

        Like django ``transaction.atomic()`` decorator chamber atomic can be used for surrounding method, function or block of code with db atomic block. But because we often uses reversion the atomic is surrounded with ``create_revision`` decorator

.. function:: transaction_signals()

        Decorator that is used for automatic invoking on success signals. Function or handler registered with ``on_success`` function is executed if block of code will not thrown exception.
        Its behaviour is very similar to atomic block, if you will inherit these decorators the event will be invoked until after the completion of last decorated code.

.. function:: atomic_with_signals()

        Combination of ``atomic`` and ``transaction_signals``.

.. function:: on_success()

        Function for on success handlers registration. If thransaction signals are not activated (decorator ``transaction_signals`` is not used) the handler will be invoked immediately.

``chamber.utils.transaction.OnSuccessHandler``
----------------------------------------------

Handler that can be used for implementation tasks that should be called only after successful pass throught code. Hanlder is automatically registered inside its constructior.

.. class:: chamber.utils.transaction.OnSuccessHandler

    .. method:: __init__(using=None, **kwargs)

        Constructor of success handler accepts input data in kwargs and using where you can define database

    .. method:: handle(**kwargs)

        There should be implemented code that will be invoked after success pass though the code


``chamber.utils.transaction.OneTimeOnSuccessHandler``
-----------------------------------------------------

One time handler is registered and called only once. But all input parameters are stored inside list of kwargs.

.. class:: chamber.utils.transaction.OneTimeOnSuccessHandler

    .. method:: handle(**kwargs_list)

        There should be implemented code that will be invoked after success pass though the code. Difference from ``OnSuccessHandler.handle`` is that kwargs is stored inside list in the order how handlers was created

    .. method:: _get_unique_id()

        The uniqueness of the handler must be somehow defined. You must implement this method to define unique identifier of the handler. By default it is identified with has of the class


``chamber.utils.transaction.InstanceOneTimeOnSuccessHandler``
-------------------------------------------------------------

Special type of unique handler that is identified with iteslf and model instance of the input model object.

.. class:: chamber.utils.transaction.InstanceOneTimeOnSuccessHandler

    .. method:: _get_instance()

        Returns instance stored in input kwargs which is refreshed from database to get actual state of the model object

