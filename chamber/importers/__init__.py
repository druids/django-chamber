import csv
import io
import os

from django.conf import settings

import pyprind


try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest


def simple_count(filename, encoding):
    # Encoding must be passed to match encoding used in the importer.
    lines = 0
    with io.open(filename, encoding=encoding) as f:
        for _ in f:
            lines += 1
    return lines


class DummyOutputStream(io.StringIO):

    def write(self, *args, **kwargs):
        super(DummyOutputStream, self).write(*args)


class AbstractCSVImporter:
    """
    Abstract CSV importer provides an easy way to implement loading a CSV file into a Django model.
        * To alter or validate field value, define clean_field_name() method in a similar manner as in Django forms.
        * The class implements __call__ method to allow calling concrete importers as regular functions.
        * __call__ accepts custom CSV path to import different CSV files with the same instance of the importer.
        * all class properties can be set dynamically with getters.
    """

    skip_header = True  # By default first line of CSV is assumed to contain headers and is skipped
    fields = ()  # Must correspond to columns in the CSV but columns set dynamically in clean methods can be appended.
    csv_path = ''  # Path to the CSV file relative to Django PROJECT_DIR
    delimiter = ';'
    encoding = 'utf-8'

    def __call__(self, csv_path):
        """csv_path is a required parameter as calling the function without CSV does not make sense"""
        self.import_csv(custom_csv_path=csv_path)

    def import_csv(self, custom_csv_path=None):
        with io.open(self.get_filename(custom_csv_path=custom_csv_path), encoding=self.get_encoding()) as f:
            reader = csv.reader(f, delimiter=self.get_delimiter())
            if self.get_skip_header():
                next(reader, None)
            self.import_rows(
                reader,
                row_count=simple_count(self.get_filename(custom_csv_path=custom_csv_path), encoding=self.get_encoding())
            )

    def import_rows(self, reader, row_count=0):
        raise NotImplementedError

    @property
    def out_stream(self):
        """
        By default, output stream is essentially turned off by supplying dummy StringIO.
        Override this property if you want to direct output somewhere, e.g. in Django commands.
        """
        return DummyOutputStream()

    def get_filename(self, custom_csv_path=None):
        return os.path.join(settings.PROJECT_DIR, custom_csv_path or self.get_csv_path())

    def get_csv_path(self):
        """Override this in case you need to set the CSV path dynamically."""
        return self.csv_path

    def get_encoding(self):
        return self.encoding

    def get_delimiter(self):
        return str(self.delimiter)

    def get_skip_header(self):
        return self.skip_header

    def get_fields(self):
        return self.fields

    def get_fields_dict(self, row):
        """
        Returns a dict of field name and cleaned value pairs to initialize the model.
        Beware, it aligns the lists of fields and row values with Nones to allow for adding fields not found in the CSV.
        Whitespace around the value of the cell is stripped.
        """
        return {k: getattr(self, 'clean_{}'.format(k), lambda x: x)(v.strip() if isinstance(v, str)
                                                                    else None)
                for k, v in zip_longest(self.get_fields(), row)}

    def _pre_import_rows(self, row_count):
        pass

    def _post_import_rows(self, created_count, updated_count=0):
        pass


class BulkCSVImporter(AbstractCSVImporter):

    delete_existing_objects = False  # Set to true if you want to delete all records in the model table
    batch_size = 10000

    def create_batch(self, chunk):
        return len(self.model_class.objects.bulk_create(chunk))

    def import_rows(self, reader, row_count=0):
        self._pre_import_rows(row_count)

        if self.get_delete_existing_objects():
            self.model_class.objects.all().delete()

        if self.get_skip_header():
            row_count -= 1

        batch, created = [], 0

        for i, row in enumerate(reader):
            if i % self.get_batch_size() == 0 and i > 0:
                created += self.create_batch(batch)
                self._post_batch_create(self.get_batch_size(), row_count)
                del batch[:]
            if any(row):  # Skip blank lines
                batch.append(self.model_class(**self.get_fields_dict(row)))
        created += self.create_batch(batch)
        self._post_batch_create(len(batch), row_count)

        self._post_import_rows(created)

        return created

    def get_delete_existing_objects(self):
        return self.delete_existing_objects

    def get_batch_size(self):
        return self.batch_size

    def _post_batch_create(self, created_count, row_count):
        pass


class CSVImporter(AbstractCSVImporter):

    query_fields = ()  # Fields used to get existing instances of the model in update_or_create, by default all fields
    update_fields = ()  # Fields that should be set by the update_or_create method

    def import_rows(self, reader, row_count=0):
        self._pre_import_rows(row_count)
        created_flags = [self.row_to_model(row) for row in reader if any(row)]
        self._post_import_rows(sum(created_flags), len(created_flags) - sum(created_flags))

    def row_to_model(self, row):
        fields_dict = self.get_fields_dict(row)
        _, created = self.model_class.objects.update_or_create(
            defaults=self.get_update_dict(fields_dict),
            **self.get_query_dict(fields_dict)
        )
        return created

    def get_query_fields(self):
        return self.query_fields or self.fields

    def get_update_fields(self):
        return self.update_fields

    def get_query_dict(self, fields_dict):
        return {k: v for k, v in fields_dict.items() if k in self.get_query_fields()}

    def get_update_dict(self, fields_dict):
        return {k: v for k, v in fields_dict.items() if k in self.get_update_fields()}
