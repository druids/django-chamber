from collections import OrderedDict


class AbstractEnum(object):

    def _has_attr(self, name):
        return name in self.container

    def _get_attr_val(self, name):
        return name

    def __getattr__(self, name):
        if self._has_attr(name):
            return self._get_attr_val(name)
        raise AttributeError('Missing attribute %s' % name)


class Enum(AbstractEnum):

    def __init__(self, *items):
        self.container = set(items)
        super(Enum, self).__init__()

    def __iter__(self):
        return self.container.__iter__()


class NumEnum(AbstractEnum):

    def __init__(self, *items):
        self.container = dict()
        super(NumEnum, self).__init__()
        i = 1
        for item in items:
            if len(item) == 2:
                key, i = item
                if i in self.container.values():
                    raise ValueError('Index %s already exists, please renumber choices' % i)
                self.container[key] = i
            else:
                self.container[item] = i
                i += 1

    def _get_attr_val(self, name):
        return self.container[name]


class AbstractChoicesEnum(object):

    def _get_labels_dict(self):
        return dict(self._get_choices())

    def _get_choices(self):
        raise NotImplementedError

    @property
    def choices(self):
        return self._get_choices()

    @property
    def all(self):
        return (key for key, _ in self._get_choices())

    def get_label(self, name):
        labels = dict(self._get_choices())
        if name in labels:
            return labels[name]
        raise AttributeError('Missing label with index %s' % name)


class ChoicesEnum(AbstractChoicesEnum, AbstractEnum):

    def __init__(self, *items):
        self.container = OrderedDict()
        super(ChoicesEnum, self).__init__()
        for key, val in items:
            self.container[key] = val

    def _get_choices(self):
        return self.container.items()

    def _get_labels_dict(self):
        return self.container


class ChoicesNumEnum(AbstractChoicesEnum, AbstractEnum):

    def __init__(self, *items):
        self.container = OrderedDict()
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

            if i in (j for j, _ in self.container.values()):
                raise ValueError('Index %s already exists, please renumber choices')
            self.container[key] = (i, val)

    def get_name(self, i):
        for key, (number, _) in self.container.items():
            if number == i:
                return key
        return None

    def _get_attr_val(self, name):
        return self.container[name][0]

    def _get_choices(self):
        return self.container.values()
