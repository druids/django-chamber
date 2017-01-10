from __future__ import unicode_literals


def create_test_smart_model_handler(obj):
    from .models import TestSmartModel

    TestSmartModel.objects.create(name='name')


def create_test_fields_model_handler(obj):
    from .models import TestFieldsModel

    TestFieldsModel.objects.create()


def create_test_dispatchers_model_handler(obj):
    from .models import TestDispatchersModel

    TestDispatchersModel.objects.create()
