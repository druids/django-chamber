import json
import logging
import platform

from django.http import UnreadablePostError

from chamber.utils.json import ChamberJSONEncoder


def skip_unreadable_post(record):
    if record.exc_info:
        exc_type, exc_value = record.exc_info[:2]
        if isinstance(exc_value, UnreadablePostError):
            return False
    return True


class AppendExtraJSONHandler(logging.StreamHandler):

    DEFAULT_STREAM_HANDLER_VARIABLE_KEYS = {
        'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename', 'module', 'exc_info', 'exc_text',
        'stack_info', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated', 'thread', 'threadName',
        'processName', 'process',
    }
    CUSTOM_STREAM_HANDLER_VARIABLE_KEYS = {'hostname'}

    def emit(self, record):
        extra = {
            k: v
            for k, v in record.__dict__.items()
            if k not in self.DEFAULT_STREAM_HANDLER_VARIABLE_KEYS.union(self.CUSTOM_STREAM_HANDLER_VARIABLE_KEYS)
        }
        record.msg = '{} --- {}'.format(record.msg, json.dumps(extra, cls=ChamberJSONEncoder))
        super().emit(record)


class HostnameFilter(logging.Filter):

    hostname = platform.node()

    def filter(self, record):
        record.hostname = self.hostname
        return True
