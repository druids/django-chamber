from __future__ import unicode_literals


class FakeObject(object):
    def __init__(self, *args):
        pass

    def __getattr__(self, name):
        return None
