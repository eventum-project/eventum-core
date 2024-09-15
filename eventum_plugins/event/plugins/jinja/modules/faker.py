from collections.abc import Mapping

from faker import Faker


class _Locale(Mapping):
    def __init__(self):
        self._dict = {}

    def __getitem__(self, locale: str) -> Faker:
        if self._dict.__contains__(locale):
            return self._dict.__getitem__(locale)
        else:
            generator = Faker(locale=locale)
            self._dict.__setitem__(locale, generator)
            return generator

    def __iter__(self):
        return self._dict.__iter__()

    def __len__(self):
        return self._dict.__len__()


locale = _Locale()
