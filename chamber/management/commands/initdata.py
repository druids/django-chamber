from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.management.commands import loaddata


class Command(loaddata.Command):

    missing_args_message = None

    def add_arguments(self, parser):
        super().add_arguments(parser)
        actions = []
        for action in parser._actions:
            if vars(action)['dest'] != 'args':
                actions.append(action)
        parser._actions = actions

    def handle(self, **options):
        if not settings.INITAL_DATA_PATH:
            raise CommandError('Missing "INITAL_DATA_PATH" configuration')
        super().handle(settings.INITAL_DATA_PATH, **options)
