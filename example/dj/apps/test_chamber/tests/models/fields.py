from django.core.exceptions import ValidationError
from django.core.files import File
from django.test import TransactionTestCase
from django.utils.translation import ugettext_lazy

from chamber.exceptions import PersistenceException
from chamber.forms import fields as form_fields
from chamber.models.fields import generate_random_upload_path
from chamber.shortcuts import change_and_save

from germanium.decorators import data_provider
from germanium.tools import assert_equal, assert_is_none, assert_false, assert_is_not_none, assert_raises, assert_true

from test_chamber.models import CSVRecord, TestFieldsModel  # pylint: disable=E0401


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
        assert_raises(PersistenceException, change_and_save, self.inst, decimal='2.99')
        assert_raises(PersistenceException, change_and_save, self.inst, decimal='10.00001')
        try:
            change_and_save(self.inst, decimal='11.1')
            assert_true(False, 'Previous `change_and_save` suppose to raise an exception')
        except PersistenceException as ex:
            assert_true('decimal: ' in str(ex), 'Exception message was supposed to contain a field name.')

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

    def test_subchoices_field_value_should_be_empty(self):
        self.inst.state = 4  # setting an invalid value
        try:
            TestFieldsModel._meta.get_field('state_reason').validate(  # pylint: disable=W0212
                TestFieldsModel.STATE_REASON.SUB_NOT_OK_2, self.inst)  # pylint: disable=W0212
            assert_true(False, 'Field validation should raise an error')
        except ValidationError as ex:
            assert_equal(['Value must be empty'], ex.messages)
        assert_is_none(TestFieldsModel._meta.get_field('state_reason').clean(  # pylint: disable=W0212
            TestFieldsModel.STATE_REASON.SUB_NOT_OK_2, self.inst))  # pylint: disable=W0212

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

    def test_file_field_content_type(self):
        # These files can be saved because it has supported type
        for filename in ('all_fields_filled.csv', 'test.pdf'):
            with open('data/{}'.format(filename), 'rb') as f:
                assert_false(self.inst.file)
                self.inst.file.save(filename, File(f))
                assert_true(self.inst.file)
                change_and_save(self.inst, file=None)

        # Image file is not supported
        with open('data/test2.jpg', 'rb') as f:
            assert_false(self.inst.file)
            assert_raises(PersistenceException, self.inst.file.save, 'image.jpeg', File(f))

    def test_image_field_max_upload_size(self):
        # File is can be stored
        with open('data/test2.jpg', 'rb') as f:
            assert_false(self.inst.image)
            self.inst.image.save('test2.jpg', File(f))
            assert_true(self.inst.image)
            change_and_save(self.inst, image=None)

        # File is too large to store
        with open('data/test.jpg', 'rb') as f:
            assert_false(self.inst.image)
            assert_raises(PersistenceException, self.inst.image.save, 'image.jpeg', File(f))

        # File has a wrong extension
        with open('data/test2.jpg', 'rb') as f:
            assert_raises(PersistenceException, self.inst.image.save, 'image.html', File(f))

    def test_should_validate_positive_price_field(self):
        assert_raises(PersistenceException, change_and_save, self.inst, total_price=-100)

    def test_should_check_price_form_field(self):
        field = TestFieldsModel._meta.get_field('price')  # pylint: disable=W0212
        assert_equal(ugettext_lazy('EUR'), field.currency)
        form_field = field.formfield()
        assert_true(isinstance(form_field.widget, form_fields.PriceNumberInput))
        assert_equal(field.currency, form_field.widget.placeholder)

    def test_should_check_total_price_form_field(self):
        field = TestFieldsModel._meta.get_field('total_price')  # pylint: disable=W0212
        assert_equal(ugettext_lazy('CZK'), field.currency)
        form_field = field.formfield()
        assert_true(isinstance(form_field.widget, form_fields.PriceNumberInput))

    model_fields = (
        ('price', ugettext_lazy('EUR'), {'max_digits', 'decimal_places'}),
        ('total_price', ugettext_lazy('CZK'), {'max_digits', 'decimal_places', 'validators'}),
    )

    @data_provider(model_fields)
    def test_should_assert_form_field(self, field_name, currency, kwargs_to_remove):
        field = TestFieldsModel._meta.get_field(field_name)  # pylint: disable=W0212
        assert_equal(currency, field.currency)
        form_field = field.formfield()
        assert_true(isinstance(form_field.widget, form_fields.PriceNumberInput))
        assert_equal(field.currency, form_field.widget.placeholder)
