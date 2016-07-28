from __future__ import unicode_literals

from collections import OrderedDict, MutableSet


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
        self.container = OrderedDict(((item, item) for item in items))
        super(Enum, self).__init__()

    def _get_attr_val(self, name):
        return self.container[name]

    def __iter__(self):
        return self.container.values().__iter__()


class NumEnum(AbstractEnum):

    def __init__(self, *items):
        self.container = OrderedDict()
        super(NumEnum, self).__init__()
        i = 0
        for item in items:
            if len(item) == 2:
                key, i = item
                if not isinstance(i, int):
                    raise ValueError('Last value of item must by integer')
            else:
                key = item
                i += 1

            if i in self.container.values():
                raise ValueError('Index %s already exists, please renumber choices')
            self.container[key] = i

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
        return list(self.container.items())

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

            if i in {j for j, _ in self.container.values()}:
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
        return list(self.container.values())


class OrderedSet(MutableSet):

    def __init__(self, *iterable):
        self.end = end = []
        end += [None, end, end]         # sentinel node for doubly linked list
        self.map = {}                   # key --> [key, prev, next]
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self.map)

    def __contains__(self, key):
        return key in self.map

    def add(self, key):
        if key not in self.map:
            end = self.end
            curr = end[1]
            curr[2] = end[1] = self.map[key] = [key, curr, end]

    def discard(self, key):
        if key in self.map:
            key, prev, next = self.map.pop(key)
            prev[2] = next
            next[1] = prev

    def __iter__(self):
        end = self.end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self.end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def pop(self, last=True):
        if not self:
            raise KeyError('set is empty')
        key = self.end[1][0] if last else self.end[2][0]
        self.discard(key)
        return key

    def __repr__(self):
        if not self:
            return '{}()'.format(self.__class__.__name__,)
        else:
            return '{}({})'.format(self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        return set(self) == set(other)


class AttrString(str):

    def __new__(cls, value, **kwargs):
        obj = str.__new__(cls, value)
        [setattr(obj, k, v) for k, v in kwargs.items()]
        return obj
