import os

from django.core.management.commands import makemessages


def _remove_pot_creation_date(pofile):
    if os.path.exists(pofile):
        with open(pofile, "rb+") as f:
            lines = f.readlines()
            f.seek(0)
            for line in lines:
                if not line.startswith(b'"POT-Creation-Date: '):
                    f.write(line)
            f.truncate()


class Command(makemessages.Command):
    extra_args = [
        '--keyword=_l',
        '--keyword=_n:1,2',
        '--keyword=_nl:1,2',
        '--keyword=_p:1c,2',
        '--keyword=_np:1c,2,3',
        '--keyword=_pl:1c,2',
        '--keyword=_npl:1c,2,3',
    ]

    xgettext_options = makemessages.Command.xgettext_options + extra_args

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            '--no-creation-date',  action='store_true', dest='no_creation_date', default=False,
            help='Remove POT-Creation-Date from result file.',
        )

    def handle(self, *args, **options):
        self.no_creation_date = options['no_creation_date']
        super().handle(*args, **options)

    def write_po_file(self, potfile, locale):
        super().write_po_file(potfile, locale)
        if self.no_creation_date:
            basedir = os.path.join(os.path.dirname(potfile), locale, 'LC_MESSAGES')
            _remove_pot_creation_date(os.path.join(basedir, '{}.po'.format(self.domain)))
