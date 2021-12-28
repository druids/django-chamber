import os

from django.conf import settings

from chamber.importers import BulkCSVImporter, CSVImporter

from .models import CSVRecord


class BulkCSVRecordImporter(BulkCSVImporter):
    model_class = CSVRecord
    fields = ('id', 'name', 'number')
    csv_path = os.path.join(settings.PROJECT_DIR, 'data', 'all_fields_filled.csv')

    def clean_number(self, value):
        # Just to test clean methods are called
        return 888


class CSVRecordImporter(CSVImporter):
    model_class = CSVRecord
    fields = ('id', 'name', 'number')
    csv_path = os.path.join(settings.PROJECT_DIR, 'data', 'all_fields_filled.csv')

    def clean_number(self, value):
        # Just to test clean methods are called
        return 888
