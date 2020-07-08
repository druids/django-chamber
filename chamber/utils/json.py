from django.core.serializers.json import DjangoJSONEncoder


class ChamberJSONEncoder(DjangoJSONEncoder):

    def default(self, val):
        if isinstance(val, bytes):
            return {
                '__type__': bytes.__name__,
                '__value__': [x for x in val],
            }
        else:
            try:
                return super().default(val)
            except TypeError:
                # https://github.com/python/cpython/blob/v3.8.3/Lib/json/encoder.py#L160-L180
                return 'Unserializable value of "{}"'.format(str(type(val)))
            except ValueError as ex:
                # https://github.com/django/django/blob/2.2.14/django/core/serializers/json.py#L81-L104
                return str(ex)
