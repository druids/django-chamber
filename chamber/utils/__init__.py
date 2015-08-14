import unicodedata


def remove_diacritics(string_with_diacritics):
    return unicodedata.normalize('NFKD', string_with_diacritics).encode('ASCII', 'ignore')
