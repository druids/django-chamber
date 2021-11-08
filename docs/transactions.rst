Transaction helpers
===================


``chamber.utils.transaction.atomic``
------------------------------------

.. function:: smart_atomic(using=None, savepoint=True, ignore_errors=None, reversion=True)

        Like django ``transaction.smart_atomic()`` decorator chamber atomic can be used for surrounding method, function or block of code with db atomic block. But because we often uses reversion the atomic is surrounded with ``create_revision`` decorator. Reversion can be turned off with ``reversion`` argument

.. function:: pre_commit(callable, using=None)

        Similar to django ``on_commit`` helper, but callable function is called before the data is saved to the database. Of no atomic bloc is activated callable is called imediatelly


``chamber.utils.transaction.UniquePreCommitCallable``
-----------------------------------------------------

One time callable is registered and called only once. But all input parameters are stored inside list of kwargs.

.. class:: chamber.utils.transaction.OneTimePreCommitHandler

    .. method:: handle()

        There should be implemented code that will be invoked after success pass though the code. Difference from ``PreCommitHandler.handle`` is that kwargs is stored inside list in the order how handlers was created

    .. method:: _get_unique_id()

        The uniqueness of the handler must be somehow defined. You must implement this method to define unique identifier of the handler. By default it is identified with has of the class


``chamber.utils.transaction.InstanceOneTimePreCommitHandler``
-------------------------------------------------------------

Special type of unique handler that is identified with iteslf and model instance of the input model object.

.. class:: chamber.utils.transaction.InstanceOneTimePreCommitHandler

    .. method:: _get_instance()

        Returns instance stored in input kwargs which is refreshed from database to get actual state of the model object

