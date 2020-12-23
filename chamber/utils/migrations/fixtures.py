import os

from io import StringIO


from django.db import DEFAULT_DB_ALIAS
from django.core.management import call_command
from django.core.serializers import python, base
from django.core.management.commands import loaddata


class MigrationLoadFixture:

    def __init__(self, migration_file, fixture_dir=None, fixture_filename=None, fixture_type='json'):
        self.migration_file = migration_file
        self.fixture_dir = fixture_dir or os.path.abspath(os.path.join(os.path.dirname(migration_file), 'fixtures'))
        self.fixture_filename = fixture_filename or '%s.%s' % (
            os.path.basename(migration_file).rsplit('.', 1)[0], fixture_type
        )

    def __call__(self, apps, schema_editor):
        def _get_model(model_identifier):
            """
            Helper to look up a model from an "app_label.model_name" string.
            """
            try:
                return apps.get_model(model_identifier)
            except (LookupError, TypeError):
                raise base.DeserializationError("Invalid model identifier: '%s'" % model_identifier)

        get_model_tmp = python._get_model  # pylint: disable=W0212
        try:
            python._get_model = _get_model
            file = os.path.join(self.fixture_dir, self.fixture_filename)
            if not os.path.isfile(file):
                raise IOError('File "%s" does not exists' % file)
            loaddata.Command().handle(
                file, ignore=True, database=DEFAULT_DB_ALIAS, app_label=None, verbosity=0, exclude=[], format='json'
            )
        finally:
            python._get_model = get_model_tmp  # pylint: disable=W0212
