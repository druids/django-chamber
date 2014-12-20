from django.utils.datastructures import SortedDict


class SmartDict(SortedDict):

    def __getattr__(self, name):
        if name in self:
            return self[name]
        raise AttributeError


class Enum(set):

    def __init__(self, *items):
        super(Enum, self).__init__(items)

    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError


class NumeEnum(dict):

    def __init__(self, *items):
        super(NumeEnum, self).__init__()
        i = 1
        for arg in items:
            if arg is not None:
                self[arg] = i
            i += 1

    def __getattr__(self, name):
        if name in self:
            return self[name]
        raise AttributeError


class ChoicesEnum(SortedDict):

    def __init__(self, *items):
        super(ChoicesEnum, self).__init__()
        for key, val in items:
            self[key] = val

    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError

    def get_label(self, name):
        if name in self:
            return self[name]
        raise AttributeError

    @property
    def choices(self):
        return self.items()


class ChoicesNumEnum(SortedDict):

    def __init__(self, *items):
        super(ChoicesNumEnum, self).__init__()
        i = 0
        for item in items:
            if len(item) == 3:
                key, val, i = item
                if not isinstance(i, int):
                    raise ValueError('Last value of item must by integer')
            elif len(item) == 2:
                key, val = item
                i += 1
            else:
                raise ValueError('Wrong input data format')

            if i in (j for j, _ in self.values()):
                raise ValueError('Index %s already exists, please renumber choices')
            self[key] = (i, val)

    def __getattr__(self, name):
        if name in self:
            return self[name][0]
        raise AttributeError

    def get_label(self, i):
        if i in dict(self.values()):
            return self[i]
        raise AttributeError

    @property
    def choices(self):
        return self.values()
