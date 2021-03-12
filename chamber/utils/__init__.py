import inspect
import unicodedata

from importlib import import_module

from django.apps import AppConfig
from django.utils.functional import cached_property
from django.utils.html import escape
from django.utils.safestring import SafeData, mark_safe
from django.utils.text import normalize_newlines


class InvalidFunctionArguments(Exception):
    pass


def remove_accent(string_with_diacritics):
    """
    Removes a diacritics from a given string"
    """
    return unicodedata.normalize('NFKD', string_with_diacritics).encode('ASCII', 'ignore').decode('ASCII')


def get_class_method(cls_or_inst, method_name):
    """
    Returns a method from a given class or instance. When the method doest not exist, it returns `None`. Also works with
    properties and cached properties.
    """
    cls = cls_or_inst if isinstance(cls_or_inst, type) else cls_or_inst.__class__
    meth = getattr(cls, method_name, None)
    if isinstance(meth, property):
        meth = meth.fget
    elif isinstance(meth, cached_property):
        meth = meth.func
    return meth if callable(meth) else None


def keep_spacing(value, autoescape=True):
    """
    When a given `str` contains multiple spaces it keeps first space and others are replaces by &nbsp;. Newlines
    converts into HTML's <br>.
    """
    autoescape = autoescape and not isinstance(value, SafeData)
    value = normalize_newlines(value)
    if autoescape:
        value = escape(value)
    return mark_safe(value.replace('  ', ' &nbsp;').replace('\n', '<br />'))


def call_function_with_unknown_input(function, **kwargs):
    """
    Call function and use kwargs from input if function requires them.
    :param function: function to call.
    :param kwargs: function input kwargs or extra kwargs which will not be used.
    :return: function result or raised InvalidFunctionArguments exception.
    """
    function_kwargs_names = set(inspect.signature(function).parameters.keys())

    required_function_kwargs_names = set(
        k for k, v in inspect.signature(function).parameters.items() if v.default is v.empty
    )

    function_kwargs = {k: v for k, v in kwargs.items() if k in function_kwargs_names}
    if required_function_kwargs_names <= set(function_kwargs.keys()):
        return function(**function_kwargs)
    else:
        raise InvalidFunctionArguments(
            'Function {} missing required arguments {}'.format(
                function, ', '.join(required_function_kwargs_names - set(function_kwargs.keys()))
            )
        )


def generate_container_app_config(name,):
    name_prefix, _, app_name = name.split('.')

    label = '{}_{}'.format(name_prefix, app_name)
    cls_name = '{}{}AppConfig'.format(name_prefix.title(), app_name.title())

    cls = type(cls_name, (AppConfig,), {'name': name, 'label': label})

    return cls(name, import_module(cls.name))


ContainerAppConfig = generate_container_app_config
