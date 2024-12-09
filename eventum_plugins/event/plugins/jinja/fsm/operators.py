from typing import Any, Sequence


def len_eq(a: Sequence[Any], b: int) -> bool:
    """Same as len(a) == b."""
    return len(a) == b


def len_gt(a: Sequence[Any], b: int) -> bool:
    """Same as len(a) > b."""
    return len(a) > b


def len_ge(a: Sequence[Any], b: int) -> bool:
    """Same as len(a) >= b."""
    return len(a) >= b


def len_lt(a: Sequence[Any], b: int) -> bool:
    """Same as len(a) < b."""
    return len(a) < b


def len_le(a: Sequence[Any], b: int) -> bool:
    """Same as len(a) <= b."""
    return len(a) <= b
