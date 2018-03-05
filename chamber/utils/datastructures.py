from collections import MutableSet, OrderedDict
from itertools import chain


class AbstractEnum:

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
        self.container = OrderedDict((
            item if isinstance(item, (list, tuple)) else (item, item)
            for item in items
        ))
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


class AbstractChoicesEnum:

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
        for item in items:
            if len(item) == 3:
                key, label, val = item
            elif len(item) == 2:
                key, label = item
                val = key
            self.container[key] = (val, label)

    def get_name(self, i):
        for key, (val, _) in self.container.items():
            if val == i:
                return key
        return None

    def _get_attr_val(self, name):
        return self.container[name][0]

    def _get_choices(self):
        return list(self.container.values())


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


class SubstatesChoicesNumEnum(ChoicesNumEnum):

    def __init__(self, categories):
        assert len(categories) > 0

        self.categories = {}

        super(SubstatesChoicesNumEnum, self).__init__(*(item for item in chain(*categories.values())))

        self.categories = {
            category: [getattr(self, item[0]) for item in subitems] for category, subitems in categories.items()
        }

    def get_allowed_states(self, category):
        return self.categories.get(category, ())


class SequenceChoicesEnumMixin:

    def __init__(self, items, initial_states=None):
        assert len(items) > 0

        self.initial_states = initial_states

        # The last value of every item are omitted and send to ChoicesEnum constructor
        super(SequenceChoicesEnumMixin, self).__init__(*(item[:-1] for item in items if item[0] is not None))

        self.first_choices = self._get_first_choices(items)

        # The last value of every item is used for construction of graph that define allowed next states for every state
        self.sequence_graph = {getattr(self, item[0]): item[-1] for item in items}

    def _get_first_choices(self, items):
        return tuple(getattr(self, key) for key in self.initial_states) if self.initial_states else self.all

    def get_allowed_next_states(self, state, instance):
        if not state:
            return self.first_choices
        else:
            states_or_callable = self.sequence_graph.get(state)
            states = (states_or_callable(instance) if hasattr(states_or_callable, '__call__')
                      else list(states_or_callable))
            return tuple(getattr(self, next_choice) for next_choice in states)


class SequenceChoicesEnum(SequenceChoicesEnumMixin, ChoicesEnum):
    pass


class SequenceChoicesNumEnum(SequenceChoicesEnumMixin, ChoicesNumEnum):
    pass


class OrderedSet(MutableSet):

    def __init__(self, *iterable):
        self.end = end = []
        end += [None, end, end]  # sentinel node for doubly linked list
        self.map = {}  # key --> [key, prev, next]
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
            key, prev_item, next_item = self.map.pop(key)
            prev_item[2] = next_item
            next_item[1] = prev_item

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
