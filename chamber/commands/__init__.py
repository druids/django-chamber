from django.core.management.base import BaseCommand

from chamber.importers import BulkCSVImporter, CSVImporter

import pyprind


class ProgressBarStream:
    """
    OutputStream wrapper to remove default linebreak at line endings.
    """

    def __init__(self, stream):
        """
        Wrap the given stream.
        """
        self.stream = stream

    def write(self, *args, **kwargs):
        """
        Call the stream's write method without linebreaks at line endings.
        """
        return self.stream.write(ending="", *args, **kwargs)

    def flush(self):
        """
        Call the stream's flush method without any extra arguments.
        """
        return self.stream.flush()


class ImportCSVCommandMixin:

    def handle(self, *args, **kwargs):
        self.import_csv()


class BulkImportCSVCommand(ImportCSVCommandMixin, BulkCSVImporter, BaseCommand):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bar = None

    def _pre_import_rows(self, row_count):
        self.bar = pyprind.ProgBar(row_count, stream=ProgressBarStream(self.stdout))

    def _post_batch_create(self, created_count, row_count):
        self.bar.update(iterations=created_count)

    def _post_import_rows(self, created_count, updated_count=0):
        self.stdout.write('\nCreated {created} {model_name}.'.format(
            created=created_count,
            model_name=self.model_class._meta.verbose_name_plural  # pylint: disable=W0212
        ))


class ImportCSVCommand(ImportCSVCommandMixin, CSVImporter, BaseCommand):

    def _post_import_rows(self, created_count, updated_count=0):
        self.stdout.write('Created {created} {model_name} and {updated} updated.'.format(
            created=created_count,
            model_name=self.model_class._meta.verbose_name_plural,  # pylint: disable=W0212
            updated=updated_count)
        )
