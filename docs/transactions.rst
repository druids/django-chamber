Transaction helpers
===================


``chamber.utils.transaction``
------------------------------------

.. function:: atomic(func)

        Like django ``transaction.atomic()`` decorator chamber atomic can be used for surrounding method, function or block of code with db atomic block. But because we often uses reversion the atomic is surrounded with ``create_revision`` decorator

.. function:: atomic_with_signals(using=None)

        Decorator/context processor that expands Django atomic with automatic invoking on success signals. Function or handler registered with ``on_success`` function is executed if block of code will not thrown exception.
        Its behaviour is very similar to atomic block, if you will inherit these decorators the event will be invoked until after the completion of last decorated code.

.. function:: on_success(callable, using=None)

        Function for on success handlers registration. If transaction signals are not activated (decorator ``transaction_signals`` is not used) the callabe will be invoked immediately.


``chamber.utils.transaction.UniqueOnSuccessCallable``
-----------------------------------------------------

One time callable is registered and called only once. But all input parameters are stored inside list of kwargs.

.. class:: chamber.utils.transaction.OneTimeOnSuccessHandler

    .. method:: handle()

        There should be implemented code that will be invoked after success pass though the code. Difference from ``OnSuccessHandler.handle`` is that kwargs is stored inside list in the order how handlers was created

    .. method:: _get_unique_id()

        The uniqueness of the handler must be somehow defined. You must implement this method to define unique identifier of the handler. By default it is identified with has of the class


``chamber.utils.transaction.InstanceOneTimeOnSuccessHandler``
-------------------------------------------------------------

Special type of unique handler that is identified with iteslf and model instance of the input model object.

.. class:: chamber.utils.transaction.InstanceOneTimeOnSuccessHandler

    .. method:: _get_instance()

        Returns instance stored in input kwargs which is refreshed from database to get actual state of the model object

