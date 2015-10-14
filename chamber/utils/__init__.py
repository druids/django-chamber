import unicodedata

from django.utils.functional import cached_property


def remove_diacritics(string_with_diacritics):
    return unicodedata.normalize('NFKD', string_with_diacritics).encode('ASCII', 'ignore')


def get_class_method(cls_or_inst, method_name):
    cls = cls_or_inst
    if not isinstance(cls, type):
        cls = cls_or_inst.__class__
    meth = getattr(cls, method_name, None)
    if isinstance(meth, property):
        meth = meth.fget
    elif isinstance(meth, cached_property):
        meth = meth.func
    return meth
