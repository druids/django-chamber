
class Enum(set):

    def __init__(self, *args):
        super(Enum, self).__init__(args)

    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError

    @property
    def choices(self):
        return [(val, val) for val in self]


class NumericEnum(dict):

    def __init__(self, *args):
        super(NumericEnum, self).__init__()
        i = 1
        for arg in args:
            if arg is not None:
                self[arg] = i
            i += 1

    def __getattr__(self, name):
        if name in self:
            return self[name]
        raise AttributeError

    @property
    def choices(self):
        return [(val, key) for key, val in self.items()]

