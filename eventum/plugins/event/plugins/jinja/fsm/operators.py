from typing import Sequence


def len_eq(a: Sequence, b: int) -> bool:
    """Same as len(a) == b."""
    return len(a) == b


def len_gt(a: Sequence, b: int) -> bool:
    """Same as len(a) > b."""
    return len(a) > b


def len_ge(a: Sequence, b: int) -> bool:
    """Same as len(a) >= b."""
    return len(a) >= b


def len_lt(a: Sequence, b: int) -> bool:
    """Same as len(a) < b."""
    return len(a) < b


def len_le(a: Sequence, b: int) -> bool:
    """Same as len(a) <= b."""
    return len(a) <= b
