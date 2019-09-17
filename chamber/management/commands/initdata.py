from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command


class Command(BaseCommand):

    def handle(self, **options):
        if not settings.INITAL_DATA_PATH:
            raise CommandError('Missing "INITAL_DATA_PATH" configuration')
        call_command('loaddata', settings.INITAL_DATA_PATH, stdout=self.stdout, stderr=self.stderr)
