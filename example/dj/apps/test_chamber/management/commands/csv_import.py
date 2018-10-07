from chamber.commands import ImportCSVCommand

from test_chamber.models import CSVRecord  # pylint: disable=E0401


class Command(ImportCSVCommand):
    model_class = CSVRecord
    fields = ('id', 'name', 'number')
    csv_path = 'data/all_fields_filled.csv'

    def clean_number(self, value):
        # Just to test clean methods are called
        return 888
