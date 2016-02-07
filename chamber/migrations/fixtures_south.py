from __future__ import unicode_literals

import inspect
import os

from six.moves import cStringIO

from django.db import models
from django.core.management import call_command


def load_fixture(file_name, orm):
    original_get_model = models.get_model

    def get_model_southern_style(*args):
        try:
            return orm['.'.join(args)]
        except:
            return original_get_model(*args)

    models.get_model = get_model_southern_style

    call_command('loaddata', file_name, stdout=cStringIO())

    models.get_model = original_get_model


def load_fixture_of_migration(migration, orm, fixture_type='json'):
    migration_file = inspect.getfile(migration.__class__)
    fixture_dir = os.path.abspath(os.path.join(os.path.dirname(migration_file), 'fixtures'))
    fixture_filename = '%s.%s' % (
        os.path.basename(migration_file).rsplit('.', 1)[0], fixture_type
    )
    file = os.path.join(fixture_dir, fixture_filename)
    if not os.path.isfile(file):
        raise IOError('File "%s" does not exists' % file)
    load_fixture(file, orm)