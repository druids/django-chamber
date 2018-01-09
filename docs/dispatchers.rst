Model Dispatchers
=================

Model dispatchers are a way to reduce complexity of ``_pre_save`` and
``_post_save`` methods of the SmartModel. A common use-case of these
methods is to perform some action based on the change of the model,
e.g. send a notification e-mail when the state of the invoice changes.

Better alternative is to define a handler function encapsulating the
action that should happen when the model changes in a certain way. This
handler is registered on the model using a proper dispatcher.

.. class:: chamber.models.dispatchers.BaseDispatcher

So far, there are two types of dispatchers but you are free to subclass
the ``BaseDispatcher`` class to create your own, see the code as
reference. During save of the model, the ``__call__`` method of all
dispatchers is invoked with following parameters:

1. ``obj`` instance of the model that is being saved
2. ``changed_fields`` list of field names that was changed since the
   last save
3. ``**kwargs`` custom keyword arguments passed to the save method

The moment when the handler should be fired may be important.
Therefore, you can select signal that defines when dispatcher will be infoked. There is two signals:
``chamber.models.signals.dispatcher_pre_save`` or ``chamber.models.signals.dispatcher_post_save``
Both groups are dispatched immediately after the ``_pre_save`` or ``_post_save``
method respectively.

When the handler is fired, it is passed a single argument -- the instance of the SmartModel being saved. Here is an example of a handler registered on a ``User`` model:

::

    def send_email(user):
        # Code that actually sends the e-mail
        send_html_email(recipient=user.email, subject='Your profile was updated')

.. class:: chamber.models.dispatchers.PropertyDispatcher

``PropertyDispatcher`` is a versatile
dispatcher that fires the given handler when a specified property of the
model evaluates to ``True``.

The example shows how to to register the aforementioned ``send_email``
handler to be dispatched after saving the object if the property
``should_send_email`` returns ``True``.

.. code:: python

    class MySmartModel(chamber_models.SmartModel):

        email_sent = models.BooleanField()

        dispatchers = (
            PropertyDispatcher(send_email, 'should_send_email', dispatcher_post_save),
        )

        @property
        def should_send_email(self):
            return not self.email_sent

.. class:: chamber.models.dispatchers.StateDispatcher

``StateDispatcher`` can be used to dispatch a handler when a value of some model field
changes to a specific value.
In the following example, we register a ``my_handler`` function to
be dispatched during the ``_pre_save`` method when the state changes to
``SECOND``.

.. code:: python

    def my_handler(my_smart_model): # Do that useful stuff
        pass

    class MySmartModel(chamber\_models.SmartModel):

        STATE = ChoicesNumEnum(
            ('FIRST', _('first'), 1),
            ('SECOND', _('second'), 2),
        )
        state = models.IntegerField(choices=STATE.choices, default=STATE.FIRST)

        dispatchers = (
            StateDispatcher(my_handler, STATE, state, STATE.SECOND, signal=dispatcher_pre_save),
        )
