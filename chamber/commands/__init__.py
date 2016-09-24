from django.core.management.base import BaseCommand

from chamber.importers import BulkCSVImporter, CSVImporter


class ImportCSVCommandMixin(object):

    def handle(self, *args, **kwargs):
        self.import_csv()

    @property
    def out_stream(self):
        return self.stdout


class BulkImportCSVCommand(ImportCSVCommandMixin, BulkCSVImporter, BaseCommand):
    pass


class ImportCSVCommand(ImportCSVCommandMixin, CSVImporter, BaseCommand):
    pass
