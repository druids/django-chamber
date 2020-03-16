from nose.tools import raises  # pylint: disable=E0401

from django.core.exceptions import ImproperlyConfigured
from django.test import TransactionTestCase

from chamber.models.dispatchers import BaseDispatcher, StateDispatcher
from chamber.shortcuts import change_and_save
from chamber.utils.transaction import transaction_signals, atomic_with_signals

from germanium.tools import assert_equal  # pylint: disable=E0401

from test_chamber.models import (
    CSVRecord, TestDispatchersModel, TestFieldsModel, TestSmartModel, TestOnDispatchModel
)  # pylint: disable=E0401


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

    def _create_model_and_invalid_field(self):
        model = TestDispatchersModel.objects.create()
        model.state = TestDispatchersModel.STATE.SECOND
        return model, TestDispatchersModel._meta.get_field('state')  # pylint: disable=W0212

    def test_more_test_on_dispatch_instances_should_be_created_if_transaction_signals_is_not_activated(self):
        model = TestDispatchersModel.objects.create()
        assert_equal(TestOnDispatchModel.objects.count(), 1)
        model.change_and_save(state=2)
        assert_equal(TestOnDispatchModel.objects.count(), 2)
        model.change_and_save(state=1)
        assert_equal(TestOnDispatchModel.objects.count(), 3)

    def test_only_one_test_on_dispatch_instances_should_be_created_if_transaction_signals_is_activated(self):
        with transaction_signals():
            model = TestDispatchersModel.objects.create()
            assert_equal(TestOnDispatchModel.objects.count(), 0)
            model.change_and_save(state=2)
            assert_equal(TestOnDispatchModel.objects.count(), 0)
            model.change_and_save(state=1)
            assert_equal(TestOnDispatchModel.objects.count(), 0)
        assert_equal(TestOnDispatchModel.objects.count(), 1)

    def test_atomic_with_signals_should_be_used_as_a_context_manager(self):
        with atomic_with_signals():
            model = TestDispatchersModel.objects.create()
            assert_equal(TestOnDispatchModel.objects.count(), 0)
            model.change_and_save(state=2)
            assert_equal(TestOnDispatchModel.objects.count(), 0)
            model.change_and_save(state=1)
            assert_equal(TestOnDispatchModel.objects.count(), 0)
        assert_equal(TestOnDispatchModel.objects.count(), 1)

    def test_atomic_with_signals_should_be_used_as_a_decorator(self):
        @atomic_with_signals
        def create_and_upldate_test_on_dispatcher_model():
            model = TestDispatchersModel.objects.create()
            assert_equal(TestOnDispatchModel.objects.count(), 0)
            model.change_and_save(state=2)
            assert_equal(TestOnDispatchModel.objects.count(), 0)
            model.change_and_save(state=1)
            assert_equal(TestOnDispatchModel.objects.count(), 0)

        create_and_upldate_test_on_dispatcher_model()
        assert_equal(TestOnDispatchModel.objects.count(), 1)
