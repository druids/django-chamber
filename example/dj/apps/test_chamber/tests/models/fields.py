from django.test import TransactionTestCase

from chamber.shortcuts import change_and_save
from chamber.models.fields import generate_random_upload_path
from germanium.tools import assert_equal, assert_raises, assert_true, assert_is_none

from chamber.exceptions import PersistenceException

from test_chamber.models import TestFieldsModel, CSVRecord


class ModelFieldsTestCase(TransactionTestCase):

    def setUp(self):
        self.inst = TestFieldsModel()
        super(ModelFieldsTestCase, self).setUp()

    def test_random_file_path_should_be_generated_from_class_name(self):
        instance = CSVRecord()
        filename = 'filename.txt'
        path = generate_random_upload_path(instance, filename)
        assert_true(path.startswith('csvrecord/'))
        assert_true(path.endswith('/{}'.format(filename)))

    def test_decimal_field(self):
        change_and_save(self.inst, decimal=3)
        assert_equal(self.inst.decimal, 3)
        assert_raises(PersistenceException, change_and_save, self.inst, decimal=2.99)
        assert_raises(PersistenceException, change_and_save, self.inst, decimal=10.00001)

    def test_subchoices_field(self):
        change_and_save(self.inst, state_reason=TestFieldsModel.STATE_REASON.SUB_OK_2)
        assert_equal(self.inst.state_reason, TestFieldsModel.STATE_REASON.SUB_OK_2)
        assert_raises(PersistenceException, change_and_save, self.inst,
                      state_reason=TestFieldsModel.STATE_REASON.SUB_NOT_OK_1)

        # Change state and substate should work
        change_and_save(self.inst, state=TestFieldsModel.STATE.NOT_OK,
                        state_reason=TestFieldsModel.STATE_REASON.SUB_NOT_OK_2)
        assert_equal(self.inst.state, TestFieldsModel.STATE.NOT_OK)
        assert_equal(self.inst.state_reason, TestFieldsModel.STATE_REASON.SUB_NOT_OK_2)

    def test_prev_value_field(self):
        # In case of `add`, value of state is copied to state_prev
        change_and_save(self.inst, state=TestFieldsModel.STATE.OK,
                        state_reason=TestFieldsModel.STATE_REASON.SUB_OK_1)
        assert_equal(self.inst.state, TestFieldsModel.STATE.OK)
        assert_equal(self.inst.state_prev, TestFieldsModel.STATE.OK)

        # Later, old value of state is stored in state_prev
        change_and_save(self.inst, state=TestFieldsModel.STATE.NOT_OK,
                        state_reason=TestFieldsModel.STATE_REASON.SUB_NOT_OK_1)
        assert_equal(self.inst.state_prev, TestFieldsModel.STATE.OK)

    def test_sequence_choices_num_enum(self):
        # Only the first state is valid when field is null because it is the initial state
        assert_is_none(self.inst.state_graph)
        assert_raises(PersistenceException, change_and_save, self.inst, state_graph=TestFieldsModel.GRAPH.SECOND)
        assert_raises(PersistenceException, change_and_save, self.inst, state_graph=TestFieldsModel.GRAPH.THIRD)
        change_and_save(self.inst, state_graph=TestFieldsModel.GRAPH.FIRST)
        assert_equal(self.inst.state_graph, TestFieldsModel.GRAPH.FIRST)

        # Than one can switch only to second state
        assert_raises(PersistenceException, change_and_save, self.inst, state_graph=TestFieldsModel.GRAPH.THIRD)
        change_and_save(self.inst, state_graph=TestFieldsModel.GRAPH.SECOND)
        assert_equal(self.inst.state_graph, TestFieldsModel.GRAPH.SECOND)

        # We cannot go back to first but we can go to the third state
        assert_raises(PersistenceException, change_and_save, self.inst, state_graph=TestFieldsModel.GRAPH.FIRST)
        change_and_save(self.inst, state_graph=TestFieldsModel.GRAPH.THIRD)
        assert_equal(self.inst.state_graph, TestFieldsModel.GRAPH.THIRD)
