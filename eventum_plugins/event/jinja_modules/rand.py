import ipaddress
import random
import uuid
from string import (ascii_letters, ascii_lowercase, ascii_uppercase, digits,
                    punctuation)
from typing import Any, Sequence


def choice(items: Sequence) -> Any:
    """Return random item from non empty sequence."""
    return random.choice(items)


def choices(items: Sequence, n: int) -> list:
    """Return `n` random items from non empty sequence."""
    return random.choices(items, k=n)


def weighted_choice(items: Sequence, weights: Sequence[float]) -> Any:
    """Return random item from non empty sequence with `weights`
    probability.
    """
    return random.choices(items, weights=weights, k=1).pop()


def weighted_choices(
    items: Sequence,
    weights: Sequence[float],
    n: int
) -> list:
    """Return `n` random items from non empty sequence with `weights`
    probability.
    """
    return random.choices(items, weights=weights, k=n)


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
        hexdigits = digits + 'abcdef'
        return ''.join(random.choices(hexdigits, k=size))


class network:
    @staticmethod
    def ip_v4() -> str:
        """Return random IPv4 address."""
        return '.'.join(str(random.randint(0, 255)) for _ in range(4))

    @staticmethod
    def ip_v4_private_a() -> str:
        """Return random private IPv4 address of Class A."""
        ipv4_int = random.randint(
            int(ipaddress.IPv4Address('10.0.0.0')),
            int(ipaddress.IPv4Address('10.255.255.255'))
        )
        return str(ipaddress.IPv4Address(ipv4_int))

    @staticmethod
    def ip_v4_private_b() -> str:
        """Return random private IPv4 address of Class B."""
        ipv4_int = random.randint(
            int(ipaddress.IPv4Address('172.16.0.0')),
            int(ipaddress.IPv4Address('172.31.255.255'))
        )
        return str(ipaddress.IPv4Address(ipv4_int))

    @staticmethod
    def ip_v4_private_c() -> str:
        """Return random private IPv4 address of Class C."""
        ipv4_int = random.randint(
            int(ipaddress.IPv4Address('192.168.0.0')),
            int(ipaddress.IPv4Address('192.168.255.255'))
        )
        return str(ipaddress.IPv4Address(ipv4_int))

    @staticmethod
    def ip_v4_public() -> str:
        """Return random public IPv4 address."""
        public_ranges = [
            ('1.0.0.0', '9.255.255.255'),
            ('11.0.0.0', '100.63.255.255'),
            ('100.128.0.0', '126.255.255.255'),
            ('128.0.0.0', '169.253.255.255'),
            ('169.255.0.0', '172.15.255.255'),
            ('172.32.0.0', '191.255.255.255'),
            ('192.0.1.0', '192.0.1.255'),
            ('192.0.3.0', '192.88.98.255'),
            ('192.88.100.0', '192.167.255.255'),
            ('192.169.0.0', '198.17.255.255'),
            ('198.20.0.0', '198.51.99.255'),
            ('198.51.101.0', '203.0.112.255'),
            ('203.0.114.0', '223.255.255.255')
        ]

        start, end = random.choices(
            population=public_ranges,
            weights=[5, 8, 6, 7, 4, 9, 3, 4, 5, 6, 4, 6, 8],
            k=1
        ).pop()
        ipv4_int = random.randint(
            int(ipaddress.IPv4Address(start)),
            int(ipaddress.IPv4Address(end))
        )
        return str(ipaddress.IPv4Address(ipv4_int))

    @staticmethod
    def mac() -> str:
        """Return random MAC address."""
        mac = [random.randint(0x00, 0xff) for _ in range(6)]
        mac_address = ':'.join(map(lambda x: '{:02x}'.format(x), mac))

        return mac_address


class crypto:
    @staticmethod
    def uuid4() -> str:
        """Return universally unique identifier of version 4."""
        return str(uuid.uuid4())

    @staticmethod
    def md5() -> str:
        """Return random MD5 hash."""
        return '{:32x}'.format(random.getrandbits(128))

    @staticmethod
    def sha256() -> str:
        """Return random SHA-256 hash."""
        return '{:64x}'.format(random.getrandbits(256))
