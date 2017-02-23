from __future__ import unicode_literals

from six import StringIO

from django.core.management import call_command
from django.test import TestCase

from germanium.tools import assert_equal  # pylint: disable=E0401

from test_chamber.importers import BulkCSVRecordImporter, CSVRecordImporter  # pylint: disable=E0401
from test_chamber.models import CSVRecord  # pylint: disable=E0401


class ImporterTestCase(TestCase):

    def test_records_should_be_bulk_imported_from_csv(self):
        assert_equal(CSVRecord.objects.count(), 0)
        BulkCSVRecordImporter().import_csv()

        assert_equal(CSVRecord.objects.count(), 7)
        assert_equal(CSVRecord.objects.last().name, 'Geordi LaForge')  # Ensure correct value is stored
        assert_equal(CSVRecord.objects.last().number, 888)  # Ensure clean methods work

    def test_records_should_be_imported_without_optional_fields_should_be_bulk_imported_from_csv(self):
        assert_equal(CSVRecord.objects.count(), 0)
        CSVRecordImporter().import_csv(custom_csv_path='data/required_fields_filled.csv')
        assert_equal(CSVRecord.objects.count(), 5)

    def test_records_should_be_imported_from_csv(self):
        assert_equal(CSVRecord.objects.count(), 0)
        BulkCSVRecordImporter().import_csv()

        assert_equal(CSVRecord.objects.count(), 7)
        assert_equal(CSVRecord.objects.last().name, 'Geordi LaForge')  # Ensure correct value is stored
        assert_equal(CSVRecord.objects.last().number, 888)  # Ensure clean methods work

    def test_records_should_be_imported_without_optional_fields_should_be_imported_from_csv(self):
        assert_equal(CSVRecord.objects.count(), 0)
        CSVRecordImporter().import_csv(custom_csv_path='data/required_fields_filled.csv')
        assert_equal(CSVRecord.objects.count(), 5)

    def test_records_should_be_bulk_imported_from_csv_with_command(self):
        assert_equal(CSVRecord.objects.count(), 0)
        call_command('bulk_csv_import', stdout=StringIO(), stderr=StringIO())
        assert_equal(CSVRecord.objects.count(), 7)
        assert_equal(CSVRecord.objects.last().name, 'Geordi LaForge')  # Ensure correct value is stored
        assert_equal(CSVRecord.objects.last().number, 888)  # Ensure clean methods work

    def test_records_should_be_imported_without_optional_fields_should_be_bulk_imported_from_csv_with_command(self):
        assert_equal(CSVRecord.objects.count(), 0)
        call_command('csv_import', stdout=StringIO(), stderr=StringIO())
        assert_equal(CSVRecord.objects.count(), 7)
        assert_equal(CSVRecord.objects.last().name, 'Geordi LaForge')  # Ensure correct value is stored
        assert_equal(CSVRecord.objects.last().number, 888)  # Ensure clean methods work
