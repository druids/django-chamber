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
                return 'Unserializable value of "{}"'.format(str(type(val)))
