import random
from string import (ascii_letters, ascii_lowercase, ascii_uppercase, hexdigits,
                    punctuation)

# categories = [
#     'number',
#     'string',
#     'geo',
#     'system',
#     'software',
#     'network',
#     'web',
#     'crypto',
# ]


class number:
    """Namespace for generating random numbers."""

    @staticmethod
    def integer(a: int, b: int) -> int:
        """Return random integer in range [a, b]."""
        return random.randint(a, b)

    @staticmethod
    def floating(a: float, b: float) -> float:
        """Return random floating point number in range [a, b]."""
        return random.uniform(a, b)

    @staticmethod
    def gauss(mu: float, sigma: float) -> float:
        """Return random floating point number from Gaussian
        distribution.
        """
        return random.gauss(mu, sigma)


class string:
    """Namespace for generating random strings."""

    @staticmethod
    def letters_lowercase(size: int) -> str:
        """Return string of specified `size` that contains random ASCII
        lowercase letters.
        """
        return ''.join(random.choices(ascii_lowercase, k=size))

    @staticmethod
    def letters_uppercase(size: int) -> str:
        """Return string of specified `size` that contains random ASCII
        uppercase letters.
        """
        return ''.join(random.choices(ascii_uppercase, k=size))

    @staticmethod
    def letters(size: int) -> str:
        """Return string of specified `size` that contains random ASCII
        letters.
        """
        return ''.join(random.choices(ascii_letters, k=size))

    @staticmethod
    def punctuation(size: int) -> str:
        """Return string of specified `size` that contains random ASCII
        punctuation characters.
        """
        return ''.join(random.choices(punctuation, k=size))

    @staticmethod
    def hex(size: int) -> str:
        """Return string of specified `size` that contains random hex
        characters.
        """
        return ''.join(random.choices(hexdigits, k=size))
