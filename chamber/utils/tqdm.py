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


class tqdm(original_tqdm):

    monitor_interval = 0

    def __init__(self, *args, **kwargs):
        file = kwargs.pop('file', None)
        if file and isinstance(file, OutputWrapper):
            file = CommandOutputTMDQWrapper(file)
        super().__init__(
            *args,
            file=file,
            ncols=100,
            **kwargs,
        )
