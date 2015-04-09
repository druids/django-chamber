# django-chamber

Utilities library for [django-is-core](https://github.com/matllubos/django-is-core/tree/v1.3).

## Reference

### Forms

#### `chamber.forms.fields.DecimalField`

`django.forms.DecimalField` with `step` parameter and validated `min` and `max` parameters.

#### `chamber.forms.widgets.ReadonlyWidget`

Widget for safe rendering of readonly form values.

### Models

#### `chamber.models.fields.SouthMixin`

Mixin for automatic South migration of custom model fields.

#### `chamber.models.fields.DecimalField`

`django.db.models.DecimalField` with `step`, `min` and `max` parameters. Uses [`chamber.forms.fields.DecimalField`](#chamberformsfieldsdecimalfield) as default form field.

#### `chamber.models.fields.RestrictedFileFieldMixin`

Same as FileField, but you can specify:
* `content_types` - list containing allowed content_types. Example: ['application/pdf', 'image/jpeg']
* `max_upload_size` - a number indicating the maximum file size allowed for upload in MB.
Maximum upload size can be specified in project settings under `MAX_FILE_UPLOAD_SIZE` constant

#### `chamber.models.fields.FileField`

`django.db.models.FileField` with [`RestrictedFileFieldMixin`](#chambermodelsfieldsrestrictedfilefieldmixin) options.

#### `chamber.models.fields.ImageField`

`sorl.thumbnail.ImageField` (fallback to `django.db.models.ImageField`) with [`RestrictedFileFieldMixin`](#chambermodelsfieldsrestrictedfilefieldmixin) options.

#### `chamber.models.fields.CharNullField`

`django.db.models.CharField` that stores `NULL` but returns ''.

### Utils

#### `chamber.utils.datastructures.AbstractEnum`

Base enumeration class with controlled `__getattr__`. 

#### `chamber.utils.datastructures.Enum`

Python's `set` with [`AbstractEnum`](#chamberutilsdatastructuresabstractenum) behaviour.

#### `chamber.utils.datastructures.NumEnum`

Python's `dict` with [`AbstractEnum`](#chamberutilsdatastructuresabstractenum) behaviour.

```
>>> NumEnum('a', 'b')
{'a': 1, 'b': 2}
```

#### `chamber.utils.datastructures.AbstractChoicesEnum`

Base choices class (as used in Model field's `choices` argument).

#### `chamber.utils.datastructures.ChoicesEnum`

`django.utils.datastructures.SortedDict` with [`AbstractEnum`](#chamberutilsdatastructuresabstractenum) and [`AbstractChoicesEnum`](#chamberutilsdatastructuresabstractenum) behaviour. Useful for string based choices.

```
>>> enum = ChoicesEnum(('OK', 'ok'), ('KO', 'ko'))
>>> enum
{'OK': 'ok', 'KO': 'ko'}
>>> enum.OK
'ok'
>>> enum.choices
[('OK', 'ok'), ('KO', 'ko')]
```

#### `chamber.utils.datastructures.ChoicesNumEnum`

`django.utils.datastructures.SortedDict` with [`AbstractEnum`](#chamberutilsdatastructuresabstractenum) and [`AbstractChoicesEnum`](#chamberutilsdatastructuresabstractenum) behaviour. Useful for integer based choices.

```
>>> enum = ChoicesNumEnum(('OK', 'ok', 1), ('KO', 'ko', 2))
>>> enum.KO
2
>>> enum.choices
[(1, 'ok'), (2, 'ko')]
>>> enum.get_label(2)
'ko'
```

#### `chamber.utils.decorators.classproperty`

Ties property to class, usefull for usage in class methods.

```
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

```
@short_description('amount')
def absolute_amount(self):
    return abs(self.amount)
```

is equivalent of

```
def absolute_amount(self):
    return abs(self.amount)
absolute_amount.short_description = 'amount'
```

#### `chamber.utils.forms.formset_has_file_field`

Returns True if passed formset contains FileField (or ImageField).

#### `chamber.utils.http.query_string_from_dict`

Assemble query string from `dict` of parameters.

```
>>> query_string_from_dict({'q': 'query1', 'user': 'test'})
u'q=query1&user=test'
```

### Shortcuts

#### `chamber.shortcuts.get_object_or_none`

Takes Model or QuerySet and arguments and returns instance of Model if exists, `None` otherwise.

```
>>> get_object_or_none(User, pk=1)
<User: Gaul Asterix>
>>> get_object_or_none(User.objects.exclude(pk=1), pk=1) or ''
''
```

#### `chamber.shortcuts.get_object_or_404`

Takes Model or QuerySet and arguments and returns instance of Model if exists, raises `django.http.response.Http404` otherwise.

```
>>> get_object_or_404(User, pk=1)
<User: Gaul Asterix>
>>> get_object_or_404(User.objects.exclude(pk=1), pk=1)
Traceback (most recent call last):
  File "<console>", line 1, in <module>
  File "/var/ve/lib/python2.7/site-packages/chamber/shortcuts.py", line 21, in get_object_or_404
    raise Http404
Http404
```

#### `chamber.shortcuts.distinct_field`

Takes Model or QuerySet and distinction parameters and returns list of unique values.

```
>>> User.objects.filter(last_name='Gaul')
[<User: Gaul Obelix>, <User: Gaul Asterix>]
>>> distinct_field(User.objects.filter(last_name='Gaul'), 'last_name')
[(u'Gaul',)]
```

#### `chamber.shortcuts.filter_or_exclude_by_date`

Takes negate `bool` (True for exclude, False for filter), Model or QuerySet and date parameters and return queryset filtered or excluded by date parameters.

```
>>> Order.objects.values_list('created_at', flat=True)
[datetime.datetime(2014, 4, 6, 15, 56, 16, 727000, tzinfo=<UTC>),
 datetime.datetime(2014, 2, 6, 15, 56, 16, 727000, tzinfo=<UTC>),
 datetime.datetime(2014, 1, 11, 23, 15, 43, 727000, tzinfo=<UTC>)]
>>> filter_or_exclude_by_date(False, Order, created_at=date(2014, 2, 6))
[<Order: MI-1234567>]
>>> filter_or_exclude_by_date(False, Order, created_at=date(2014, 2, 6))[0].created_at
datetime.datetime(2014, 2, 6, 15, 56, 16, 727000, tzinfo=<UTC>)
```

#### `chamber.shortcuts.filter_by_date`

Shortcut for [`chamber.shortcuts.filter_or_exclude_by_date`](#chambershortcutsfilter_or_exclude_by_date) with first parameter False.

#### `chamber.shortcuts.exclude_by_date`

Shortcut for [`chamber.shortcuts.filter_or_exclude_by_date`](#chambershortcutsfilter_or_exclude_by_date) with first parameter True.


## License

See LICENSE file.
