# django-chamber

[![Build
Status](https://travis-ci.org/druids/django-chamber.svg?branch=master)](https://travis-ci.org/druids/django-chamber)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/012d28c820fd4b19a783618c05d7a0a9)](https://www.codacy.com/app/lukas-rychtecky/django-chamber?utm_source=github.com&utm_medium=referral&utm_content=druids/django-chamber&utm_campaign=badger)
[![Coverage
Status](https://coveralls.io/repos/github/druids/django-chamber/badge.svg?branch=master)](https://coveralls.io/github/druids/django-chamber?branch=master)

This library contains useful functions and classes mainly for a web development with Django (form and model fields,
shortcuts, advanced datastructure, decoraters etc.). For more details see examples below.

## Reference

### 1. Forms

#### `chamber.forms.fields.DecimalField`

`django.forms.NumberInput` with `step` parameter and validated `min` and `max` parameters.

#### `chamber.forms.widgets.ReadonlyWidget`

Widget for safe rendering of readonly form values.

#### `chamber.forms.fields.PriceField`

`django.forms.NumberInput` with `currency` as a placeholder.

### 2. Models

#### `chamber.models.fields.SouthMixin`

Mixin for automatic South migration of custom model fields.

#### `chamber.models.fields.DecimalField`

`django.db.models.DecimalField` with `step`, `min` and `max` parameters. Uses [`chamber.forms.fields.DecimalField`](#chamberformsfieldsdecimalfield) as default form field.

#### `chamber.models.fields.RestrictedFileFieldMixin`

Same as FileField, but you can specify:
* `allowed_content_types` - list containing allowed content_types. Example: ['application/pdf', 'image/jpeg']
* `max_upload_size` - a number indicating the maximum file size allowed for upload in MB.
Maximum upload size can be specified in project settings under `MAX_FILE_UPLOAD_SIZE` constant

#### `chamber.models.fields.FileField`

`django.db.models.FileField` with [`RestrictedFileFieldMixin`](#chambermodelsfieldsrestrictedfilefieldmixin) options.

#### `chamber.models.fields.ImageField`

`sorl.thumbnail.ImageField` (fallback to `django.db.models.ImageField`) with [`RestrictedFileFieldMixin`](#chambermodelsfieldsrestrictedfilefieldmixin) options.

#### `chamber.models.fields.CharNullField`

`django.db.models.CharField` that stores `NULL` but returns ''.

#### `chamber.models.fields.PriceField`

`chamber.models.fields.DecimalField` with defaults:

- `currency` as `CZK`
- `decimal_places` as `2`
- `max_digits` as `10`
- `humanized` value for a pretty printing via `chamber.models.humanized_helpers.price_humanized`

#### `chamber.models.fields.PositivePriceField`

`chamber.models.fields.PriceField` with a default `django.core.validators.MinValueValidator` set to `0.00`.


### 3. SmartQuerySet `chamber.models.SmartQuerySet`
SmartModel introduced to Chamber uses by default a modified QuerySet with some convenience filters. 

If you are overriding model manager of a SmartModel, you should incorporate `SmartQuerySet` in order not to lose its benefits and to follow the Rule of the Least Surprise (everyone using your SmartModel will assume the custom filters to be there).

1. If the manager is created using the `QuerySet.as_manager()` method, your custom queryset should subclass `SmartQuerySet` instead the one from Django.
2. If you have a new manager created by subclassing `models.Manager` from Django, you should override the `get_queryset` method as shown in Django docs [here](https://docs.djangoproject.com/en/1.10/topics/db/managers/#calling-custom-queryset-methods-from-the-manager).

List of the added filters follows.

#### 3.1 `fast_distinct()`
Returns same result as regular `distinct()` but is much faster especially in PostgreSQL which performs distinct on all DB columns. The optimization is achieved by doing a second query and the `__in` operator. If you have queryset `qs` of `MyModel` then `fast_distinct()` equals to calling
```python
MyModel.objects.filter(pk__in=qs.values_list('pk', flat=True))
```


### 4. Model Dispatchers

Model dispatchers are a way to reduce complexity of `_pre_save` and `_post_save` methods of the SmartModel. A common use-case of these methods is to perform some action based on the change of the model, e.g. send a notification e-mail when the state of the invoice changes.

Better alternative is to define a handler function encapsulating the action that should happen when the model changes in a certain way. This handler is registered on the model using a proper dispatcher.

So far, there are two types of dispatchers but you are free to subclass the `BaseDispatcher` class to create your own, see the code as reference. During save of the model, the `__call__` method of all dispatchers is invoked with following parameters:

1. `obj` ... instance of the model that is being saved
2. `changed_fields` ... list of field names that was changed since the last save
3. `*args` ... custom arguments passed to the save method (can be used to pass additional arguments to your custom dispatchers)
4. `**kwargs` ... custom keyword arguments passed to the save method

The moment when the handler should be fired may be important. Therefore, you can register the dispatcher either in the `pre_save_dispatchers` group or `post_save_dispatchers` group. Both groups are dispatched immediately after the `_pre_save` or `_post_save` method respectively.

When the handler is fired, it is passed a single argument -- the instance of the SmartModel that is being saved. Here is an example of a handler that is registered on a `User` model:
```python
def send_email(user):
    # Code that actually sends the e-mail
    send_html_email(recipient=user.email, subject='Your profile was updated')
```

#### 4.1 Property Dispatcher
`chamber.models.dispatchers.PropertyDispatcher` is a versatile dispatcher that fires the given handler when a specified property of the model evaluates to `True`.

The example shows how to to register the aforementioned `send_email` handler to be dispatched after saving the object if the property `should_send_email` returns `True`.
```python
class MySmartModel(chamber_models.SmartModel):
    
    email_sent = models.BooleanField()

    post_save_dispatchers = (
        PropertyDispatcher(send_email, 'should_send_email'),
    )
    
    @property
    def should_send_email(self):
        return not self.email_sent
```

#### 4.2 State Dispatcher
In the following example, where we register `my_handler` function to be dispatched during `_pre_save` method when the state changes to `SECOND`. This is done using `chamber.models.dispatchers.StateDispatcher`. 

```python
def my_handler(my_smart_model):
    # Do that useful stuff
    pass


class MySmartModel(chamber_models.SmartModel):

    STATE = ChoicesNumEnum(
        ('FIRST', _('first'), 1),
        ('SECOND', _('second'), 2),
    )
    state = models.IntegerField(choices=STATE.choices, default=STATE.FIRST)

    pre_save_dispatchers = (
        StateDispatcher(my_handler, STATE, state, STATE.SECOND),
    )
```

#### 4.2 State Dispatcher
A common use-case is to perform an action whenever an instance of a particular model is created. `chamber.models.dispatchers.CreatedDispatcher` is provided to accommodate this need. An update of the instance will not trigger the handler.

```python
def my_handler(my_smart_model):
    # Do that useful stuff when a new instance of MySmartModel is created
    pass


class MySmartModel(chamber_models.SmartModel):

    post_save_dispatchers = (
        CreatedDispatcher(my_handler),
    )
```

### Utils

#### `chamber.utils.remove_accent`

```python
remove_accent('ěščřžýáíé') # 'escrzyaie'
```

#### `chamber.utils.get_class_method`

It returns a method of a given class or instance.

#### `chamber.utils.datastructures.AbstractEnum`

Base enumeration class with controlled `__getattr__`. 

#### `chamber.utils.datastructures.Enum`

Python's `set` with [`AbstractEnum`](#chamberutilsdatastructuresabstractenum) behaviour.

#### `chamber.utils.datastructures.NumEnum`

Python's `dict` with [`AbstractEnum`](#chamberutilsdatastructuresabstractenum) behaviour.

```python
NumEnum('a', 'b')  # {'a': 1, 'b': 2}
```

#### `chamber.utils.datastructures.AbstractChoicesEnum`

Base choices class (as used in Model field's `choices` argument).

#### `chamber.utils.datastructures.ChoicesEnum`

`django.utils.datastructures.SortedDict` with [`AbstractEnum`](#chamberutilsdatastructuresabstractenum) and [`AbstractChoicesEnum`](#chamberutilsdatastructuresabstractenum) behaviour. Useful for string based choices.

```python
enum = ChoicesEnum(('OK', 'ok'), ('KO', 'ko'))  # {'OK': 'ok', 'KO': 'ko'}
enum.OK  # 'ok'
enum.choices  # [('OK', 'ok'), ('KO', 'ko')]
```

#### `chamber.utils.datastructures.ChoicesNumEnum`

`django.utils.datastructures.SortedDict` with [`AbstractEnum`](#chamberutilsdatastructuresabstractenum) and [`AbstractChoicesEnum`](#chamberutilsdatastructuresabstractenum) behaviour. Useful for integer based choices.

```python
enum = ChoicesNumEnum(('OK', 'ok', 1), ('KO', 'ko', 2))
enum.KO  # 2
enum.choices  # [(1, 'ok'), (2, 'ko')]
enum.get_label(2)  # 'ko'
```

#### `chamber.utils.decorators.classproperty`

Ties property to class, usefull for usage in class methods.

```python
class RestResource(BaseResource):
    @classproperty
    def csrf_exempt(cls):
        return not cls.login_required

    @classmethod
    def as_view(cls, allowed_methods=None, **initkwargs):
        view.csrf_exempt = cls.csrf_exempt
```

#### `chamber.utils.decorators.singleton`

Class decorator, which allows for only one instance of class to exist.

#### `chamber.utils.decorators.short_description`

Sets `short_description` attribute (this attribute is used by list_display and formulars).

```python
@short_description('amount')
def absolute_amount(self):
    return abs(self.amount)
```

is equivalent of

```python
def absolute_amount(self):
    return abs(self.amount)
absolute_amount.short_description = 'amount'
```

#### `chamber.utils.forms.formset_has_file_field`

Returns True if passed formset contains FileField (or ImageField).

#### `chamber.utils.http.query_string_from_dict`

Assemble query string from `dict` of parameters.

```python
query_string_from_dict({'q': 'query1', 'user': 'test'})  # u'q=query1&user=test'
```

### Shortcuts

#### `chamber.shortcuts.get_object_or_none`

Takes Model or QuerySet and arguments and returns instance of Model if exists, `None` otherwise.

```python
get_object_or_none(User, pk=1)  # <User: Gaul Asterix>
get_object_or_none(User.objects.exclude(pk=1), pk=1) or ''  # ''
```

#### `chamber.shortcuts.get_object_or_404`

Takes Model or QuerySet and arguments and returns instance of Model if exists, raises `django.http.response.Http404` otherwise.

```python
get_object_or_404(User, pk=1)  # <User: Gaul Asterix>
get_object_or_404(User.objects.exclude(pk=1), pk=1)
Traceback (most recent call last):
  File "<console>", line 1, in <module>
  File "/var/ve/lib/python2.7/site-packages/chamber/shortcuts.py", line 21, in get_object_or_404
    raise Http404
Http404
```

#### `chamber.shortcuts.distinct_field`

Takes Model or QuerySet and distinction parameters and returns list of unique values.

```python
User.objects.filter(last_name='Gaul')  # [<User: Gaul Obelix>, <User: Gaul Asterix>]
distinct_field(User.objects.filter(last_name='Gaul'), 'last_name')  # [(u'Gaul',)]
```

#### `chamber.shortcuts.filter_or_exclude_by_date`

Takes negate `bool` (True for exclude, False for filter), Model or QuerySet and date parameters and return queryset filtered or excluded by date parameters.

```python
Order.objects.values_list('created_at', flat=True)  # [datetime.datetime(2014, 4, 6, 15, 56, 16, 727000, tzinfo=<UTC>),
                                                    #  datetime.datetime(2014, 2, 6, 15, 56, 16, 727000, tzinfo=<UTC>),
                                                    #  datetime.datetime(2014, 1, 11, 23, 15, 43, 727000, tzinfo=<UTC>)]
filter_or_exclude_by_date(False, Order, created_at=date(2014, 2, 6))  # [<Order: MI-1234567>]
filter_or_exclude_by_date(False, Order, created_at=date(2014, 2, 6))[0].created_at  # datetime.datetime(2014, 2, 6, 15, 56, 16, 727000, tzinfo=<UTC>)
```

#### `chamber.shortcuts.filter_by_date`

Shortcut for [`chamber.shortcuts.filter_or_exclude_by_date`](#chambershortcutsfilter_or_exclude_by_date) with first parameter False.

#### `chamber.shortcuts.exclude_by_date`

Shortcut for [`chamber.shortcuts.filter_or_exclude_by_date`](#chambershortcutsfilter_or_exclude_by_date) with first parameter True.


Development
-----------

For contribution go to `example` directory and call `make install` to install an example project.

Testing
-------

To run tests go to `example` directory and call `make test`.


## License

See LICENSE file.
