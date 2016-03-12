from __future__ import unicode_literals


def truncate_fuzzy(string, length):
    """
    Truncates a given string by words up to the length.
    """
    return reduce(lambda txt, word: ' '.join((txt, word)) if len(txt) < length else txt, string.split(), '')[1:]
