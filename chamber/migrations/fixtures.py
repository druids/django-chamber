# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from six.moves import cStringIO

from django.core.management import call_command
from django.core.serializers import base, python


class MigrationLoadFixture(object):

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

        python._get_model = _get_model
        file = os.path.join(self.fixture_dir, self.fixture_filename)
        if not os.path.isfile(file):
            raise IOError('File "%s" does not exists' % file)
        call_command('loaddata', file, stdout=cStringIO())
