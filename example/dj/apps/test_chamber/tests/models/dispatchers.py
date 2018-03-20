from __future__ import unicode_literals

from nose.tools import raises  # pylint: disable=E0401

from django.core.exceptions import ImproperlyConfigured
from django.test import TransactionTestCase

from chamber.models.dispatchers import BaseDispatcher, StateDispatcher
from chamber.shortcuts import change_and_save

from germanium.tools import assert_equal  # pylint: disable=E0401

from test_chamber.models import (CSVRecord, TestDispatchersModel, TestFieldsModel,  # pylint: disable=E0401
                                 TestSmartModel)  # pylint: disable=E0401


class DispatchersTestCase(TransactionTestCase):

    def test_state_dispatcher(self):
        m = TestDispatchersModel.objects.create()

        # Moving TestDispatcher model to SECOND state should create new TestSmartModel instance
        assert_equal(TestSmartModel.objects.count(), 0)
        change_and_save(m, state=TestDispatchersModel.STATE.SECOND)
        assert_equal(TestSmartModel.objects.count(), 1)

        # But subsequent saves should not create more instances
        change_and_save(m, state=TestDispatchersModel.STATE.SECOND)
        assert_equal(TestSmartModel.objects.count(), 1)

        # Moving back and forth between the states creates another instance
        change_and_save(m, state=TestDispatchersModel.STATE.FIRST)
        change_and_save(m, state=TestDispatchersModel.STATE.SECOND)
        assert_equal(TestSmartModel.objects.count(), 2)

    def test_property_dispatcher(self):
        # Saving the model should always fire up the one property handler, not the second
        assert_equal(TestFieldsModel.objects.count(), 0)
        TestDispatchersModel.objects.create()
        assert_equal(TestFieldsModel.objects.count(), 1)
        assert_equal(TestDispatchersModel.objects.count(), 1)

    def test_created_dispatcher(self):
        assert_equal(CSVRecord.objects.count(), 0)
        m = TestDispatchersModel.objects.create()
        assert_equal(CSVRecord.objects.count(), 1)
        change_and_save(m, state=TestDispatchersModel.STATE.SECOND)
        assert_equal(CSVRecord.objects.count(), 1)

    @raises(ImproperlyConfigured)
    def test_should_call_dispatcher_with_invalid_value(self):
        model = TestDispatchersModel.objects.create()
        model.state = 3
        field = TestDispatchersModel._meta.get_field('state')  # pylint: disable=W0212
        StateDispatcher(lambda: False, TestDispatchersModel.STATE, field, model.state)(model)

    def _create_model_and_invalid_field(self):
        model = TestDispatchersModel.objects.create()
        model.state = TestDispatchersModel.STATE.SECOND
        return model, TestDispatchersModel._meta.get_field('state')  # pylint: disable=W0212

    @raises(ImproperlyConfigured)
    def test_should_not_call_dispatcher_with_invalid_handler(self):
        model, field = self._create_model_and_invalid_field()
        StateDispatcher(None, TestDispatchersModel.STATE, field, model.state)(model)

    @raises(NotImplementedError)
    def test_should_call_invalid_dispatcher(self):
        class InvalidDispatcher(BaseDispatcher):  # pylint: disable=W0223

            def _validate_init_params(self):
                pass

        InvalidDispatcher(lambda: False)(object())
        BaseDispatcher(lambda: False)
