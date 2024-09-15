from collections.abc import Mapping

import mimesis.enums as enums  # noqa
import mimesis.random as random  # noqa
from mimesis import Generic, Locale
from mimesis.builtins import (BrazilSpecProvider, DenmarkSpecProvider,
                              ItalySpecProvider, NetherlandsSpecProvider,
                              PolandSpecProvider, RussiaSpecProvider,
                              UkraineSpecProvider, USASpecProvider)


class _Locale(Mapping):
    def __init__(self):
        self._dict = {}

    def __getitem__(self, locale: str) -> Generic:
        if self._dict.__contains__(locale):
            return self._dict.__getitem__(locale)
        else:
            generator = Generic(Locale(locale))
            self._dict.__setitem__(locale, generator)
            return generator

    def __iter__(self):
        return self._dict.__iter__()

    def __len__(self):
        return self._dict.__len__()


class _Spec(Mapping):
    def __init__(self):
        self._dict = {}

    def __getitem__(self, spec_name: str) -> Generic:
        if self._dict.__contains__(spec_name):
            return self._dict.__getitem__(spec_name)
        else:
            match spec_name:
                case 'brazil':
                    spec = BrazilSpecProvider()
                case 'denmark':
                    spec = DenmarkSpecProvider()
                case 'italy':
                    spec = ItalySpecProvider()
                case 'netherlands':
                    spec = NetherlandsSpecProvider()
                case 'poland':
                    spec = PolandSpecProvider()
                case 'russia':
                    spec = RussiaSpecProvider()
                case 'ukraine':
                    spec = UkraineSpecProvider()
                case 'usa':
                    spec = USASpecProvider()
                case v:
                    raise ValueError(f'"{v}" is not valid spec')

            self._dict.__setitem__(spec_name, spec)
            return spec

    def __iter__(self):
        return self._dict.__iter__()

    def __len__(self):
        return self._dict.__len__()


locale = _Locale()
spec = _Spec()
