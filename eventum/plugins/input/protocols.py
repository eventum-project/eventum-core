from typing import Annotated, Iterator, Protocol, TypeAlias

import numpy as np
from numpy.typing import NDArray

IdentifiedTimestamps: TypeAlias = Annotated[
    NDArray,
    np.dtype([('timestamp', 'datetime64[us]'), ('id', 'uint16')])
]


class SupportsIdentifiedTimestampsSizedIterate(Protocol):
    """Protocol for iterating over identified timestamps. Defines an
    interface for objects capable of yielding timestamp arrays with
    associated plugin identifiers of specified size.
    """

    def iterate(
        self,
        size: int,
        skip_past: bool = True
    ) -> Iterator[IdentifiedTimestamps]:
        """Iterate over arrays of identified timestamps.

        Parameters
        ----------
        size : int
            Number of timestamps to yield for each iteration, actual
            number can be lower than specified, see `generate` method
            of `InputPlugin` for details

        skip_past : bool, default=True
            Wether to skip past timestamps before starting iteration

        Yields
        ------
        IdentifiedTimestamps
            Array of timestamps with plugin ids

        Raises
        ------
        ValueError
            If parameter "size" is less than 1
        """
        ...


class SupportsIdentifiedTimestampsIterate(Protocol):
    """Protocol for iterating over identified timestamps. Defines an
    interface for objects capable of yielding timestamp arrays with
    associated plugin identifiers.
    """

    def iterate(
        self,
        skip_past: bool = True
    ) -> Iterator[IdentifiedTimestamps]:
        """Iterate over arrays of identified timestamps.

        Parameters
        ----------
        skip_past : bool, default=True
            Wether to skip past timestamps before starting iteration

        Yields
        ------
        IdentifiedTimestamps
            Array of timestamps with plugin ids
        """
        ...
