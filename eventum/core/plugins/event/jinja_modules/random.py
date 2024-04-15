import random


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
