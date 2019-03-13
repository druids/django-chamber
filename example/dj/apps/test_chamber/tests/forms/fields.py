from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import TextInput, ValidationError
from django.test import TransactionTestCase

from germanium.tools import assert_equal, assert_true, assert_raises, assert_not_raises  # pylint: disable=E0401

from chamber.forms.fields import DecimalField, RestrictedFileField


__all__ = (
    'FormFieldsTestCase',
)


class FormFieldsTestCase(TransactionTestCase):

    def test_decimal_field_should_return_correct_widget_attrs(self):
        kwargs = {
            'step': 0.5,
            'min': 1.0,
            'max': 10.0,
        }
        field = DecimalField(**kwargs)
        widget_attrs = field.widget_attrs(TextInput())
        assert_true(len(widget_attrs.keys()) > 0)
        for attr, value in kwargs.items():
            assert_equal(value, widget_attrs[attr])

    def test_decimal_field_should_return_default_attrs(self):
        field = DecimalField()
        widget_attrs = field.widget_attrs(TextInput())
        assert_equal({'step': 'any'}, widget_attrs)

    def test_restricted_file_field_should_raise_validation_error_for_invalid_files(self):
        field = RestrictedFileField(allowed_content_types=('image/jpeg', 'application/pdf'), max_upload_size=1)

        # Invalid file type
        with open('data/all_fields_filled.csv', 'rb') as f:
            with assert_raises(ValidationError):
                field.clean(SimpleUploadedFile('all_fields_filled.pdf', f.read()))

        # Invalid size
        with open('data/test.jpg', 'rb') as f:
            with assert_raises(ValidationError):
                field.clean(SimpleUploadedFile('test.jpg', f.read()))

        # Invalid file suffix
        with open('data/test.pdf', 'rb') as f:
            with assert_raises(ValidationError):
                field.clean(SimpleUploadedFile('test.csv', f.read()))

        # Valid file
        with open('data/test.pdf', 'rb') as f:
            with assert_not_raises(ValidationError):
                field.clean(SimpleUploadedFile('test.pdf', f.read()))
