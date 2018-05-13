from django.core.management.commands import makemessages


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
