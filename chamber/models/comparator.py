class ComparableModelMixin:

    def equals(self, obj, comparator):
        """
        Use comparator for evaluating if objects are the same
        """
        return comparator.compare(self, obj)


class Comparator:

    def compare(self, a, b):
        """
        Return True if objects are same otherwise False
        """
        raise NotImplementedError
