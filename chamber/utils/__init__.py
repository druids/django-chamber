import inspect
import unicodedata

from importlib import import_module

from django.apps import AppConfig
from django.utils.functional import cached_property
from django.utils.html import escape
from django.utils.safestring import SafeData, mark_safe
from django.utils.text import normalize_newlines


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
    return meth


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


def call_method_with_unknown_input(method, **fun_kwargs):
    method_kwargs_names = inspect.getargspec(method)[0][1:]

    method_kwargs = {arg_name: fun_kwargs[arg_name] for arg_name in method_kwargs_names if arg_name in fun_kwargs}

    if len(method_kwargs_names) == len(method_kwargs):
        return method(**method_kwargs)
    else:
        raise RuntimeError('Invalid method parameters')


def generate_container_app_config(name,):
    name_prefix, _, app_name = name.split('.')

    label = '{}_{}'.format(name_prefix, app_name)
    cls_name = '{}{}AppConfig'.format(name_prefix.title(), app_name.title())

    cls = type(cls_name, (AppConfig,), {'name': name, 'label': label})

    return cls(name, import_module(cls.name))


ContainerAppConfig = generate_container_app_config
