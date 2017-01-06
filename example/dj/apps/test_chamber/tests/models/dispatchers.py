from __future__ import unicode_literals

from django.test import TransactionTestCase

from chamber.shortcuts import change_and_save

from germanium.tools import assert_equal  # pylint: disable=E0401

from test_chamber.models import TestDispatchersModel, TestFieldsModel, TestSmartModel  # pylint: disable=E0401


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
