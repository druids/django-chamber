from collections import OrderedDict

from django.http.request import QueryDict


def query_string_from_dict(qs_dict):
    qs_prepared_dict = OrderedDict()
    for key, val in qs_dict.items():
        if isinstance(val, list):
            val = '[%s]' % ','.join([str(v) for v in val])
        qs_prepared_dict[key] = val

    qdict = QueryDict('').copy()
    qdict.update(qs_prepared_dict)
    return qdict.urlencode()
