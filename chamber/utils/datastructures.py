from django.utils.datastructures import SortedDict


class AbstractEnum(object):

    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError('Missing attribute %s' % name)


class AbstractEnumDict(object):

    def get_label(self, name):
        if name in self:
            return self[name]
        raise AttributeError('Missing attribute %s' % name)


class Enum(set, AbstractEnum):

    def __init__(self, *items):
        super(Enum, self).__init__(items)


class NumEnum(dict, AbstractEnum, AbstractEnumDict):

    def __init__(self, *items):
        super(NumEnum, self).__init__()
        i = 1
        for arg in items:
            if arg is not None:
                self[arg] = i
            i += 1

    def __getattr__(self, name):
        return super(AbstractEnumDict).get_label(name)


class ChoicesEnum(SortedDict, AbstractEnum, AbstractEnumDict):

    def __init__(self, *items):
        super(ChoicesEnum, self).__init__()
        for key, val in items:
            self[key] = val

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
                raise ValueError('Index %s already exists, please renumber choices' % i)
            self[key] = (i, val)

    def __getattr__(self, name):
        if name in self:
            return self[name][0]
        raise AttributeError('Missing attribute %s' % name)

    def get_label(self, i):
        if i in dict(self.values()):
            return self[i]
        raise AttributeError('Missing label for index %s' % i)

    @property
    def choices(self):
        return self.values()
