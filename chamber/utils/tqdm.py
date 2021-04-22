from django.core.management.base import OutputWrapper

from tqdm import tqdm as original_tqdm


class CommandOutputTMDQWrapper:
    """
    Wrapper around stdout/stderr
    """

    def __init__(self, out):
        self._out = out

    def __getattr__(self, name):
        return getattr(self._out, name)

    def isatty(self):
        return hasattr(self._out, 'isatty') and self._out.isatty()

    def write(self, msg):
        self._out.write(msg, ending='')


def tqdm(*args, **kwargs):
    file = kwargs.pop('file', None)
    if file and isinstance(file, OutputWrapper):
        file = CommandOutputTMDQWrapper(file)

    return original_tqdm(
        *args,
        file=file,
        ncols=100,
        **kwargs
    )
