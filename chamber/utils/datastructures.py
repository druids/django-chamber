import re

from collections import MutableSet, OrderedDict
from itertools import chain


ENUM_KEY_PATTERN = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]*$')


class AbstractEnum:

    def __init__(self, *items):
        for k, _ in items:
            if not isinstance(k, str):
                raise ValueError('Enum key "{}" must be string'.format(k))
            if not ENUM_KEY_PATTERN.match(k):
                raise ValueError('Enum key "{}" has invalid format'.format(k))

        self._container = OrderedDict(items)
        self._reverse_container = {item[1]: item[0] for item in items}

    def _has_attr(self, name):
        return name in self._container

    def __getattr__(self, name):
        if self._has_attr(name):
            return self._container[name]
        raise AttributeError('Missing attribute %s' % name)

    def __copy__(self, *args, **kwargs):
        # Enum is immutable
        return self

    def __deepcopy__(self, *args, **kwargs):
        # Enum is immutable
        return self

    def __contains__(self, item):
        return item in self._reverse_container

    def __iter__(self):
        return self._container.values().__iter__()

    @property
    def all(self):
        return tuple(self)

    def get_name(self, val):
        return self._reverse_container.get(val)


class Enum(AbstractEnum):

    def __init__(self, *items):
        super().__init__(*(
            item if isinstance(item, (list, tuple)) else (item, item)
            for item in items
        ))


class NumEnum(Enum):

    def __init__(self, *items):
        used_ids = set()

        enum_items = []
        i = 0
        for item in items:
            if len(item) == 2:
                key, i = item
                if not isinstance(i, int):
                    raise ValueError('Choice value of item must by integer')
            else:
                key = item
                i += 1

            if i in used_ids:
                raise ValueError('Index %s already exists, please renumber choices')

            used_ids.add(i)
            enum_items.append((key, i))
        super().__init__(*enum_items)


class AbstractChoicesEnum:

    def __init__(self, *items):
        enum_items = []
        for item in items:
            assert len(item) in {2, 3}, 'Choice item array length must be two or three'

            if len(item) == 3:
                enum_items.append((item[0], item[2]))
            else:
                enum_items.append(item[0])

        super().__init__(*enum_items)
        self.choices = tuple(
            (k, items[i][1]) for i, k in enumerate(self._container.values())
        )

    def _get_labels_dict(self):
        return dict(self.choices)

    def get_label(self, name):
        labels = self._get_labels_dict()
        if name in labels:
            return labels[name]
        raise AttributeError('Missing label with index %s' % name)


class ChoicesEnum(AbstractChoicesEnum, Enum):
    pass


class ChoicesNumEnum(AbstractChoicesEnum, NumEnum):
    pass


class SubstatesChoicesNumEnum(ChoicesNumEnum):

    def __init__(self, categories):
        assert len(categories) > 0

        self.categories = {}

        super().__init__(*(item for item in chain(*categories.values())))

        self.categories = {
            category: [getattr(self, item[0]) for item in subitems] for category, subitems in categories.items()
        }

    def get_allowed_states(self, category):
        return self.categories.get(category, ())

    def get_category(self, key):
        for category, items in self.categories.items():
            if key in items:
                return category
        return None


class SequenceChoicesEnumMixin:

    def __init__(self, items, initial_states=None):
        assert len(items) > 0

        self.initial_states = initial_states

        # The last value of every item are omitted and send to ChoicesEnum constructor
        super().__init__(*(item[:-1] for item in items if item[0] is not None))

        self.first_choices = self._get_first_choices(items)

        # The last value of every item is used for construction of graph that define allowed next states for every state
        self.sequence_graph = {getattr(self, item[0]): item[-1] for item in items}

    def _get_first_choices(self, items):
        return tuple(getattr(self, key) for key in self.initial_states) if self.initial_states else self

    def get_allowed_next_states(self, state, instance):
        if not state:
            return self.first_choices
        else:
            states_or_callable = self.sequence_graph.get(state)
            states = (
                states_or_callable(instance) if hasattr(states_or_callable, '__call__')
                else list(states_or_callable)
            )
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
