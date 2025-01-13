from typing import Annotated, Iterator, Protocol, TypeAlias

import numpy as np
from numpy.typing import NDArray

TimestampIdArray: TypeAlias = Annotated[
    NDArray,
    np.dtype([('timestamp', 'datetime64[us]'), ('id', 'uint16')])
]


class TimestampIterator(Protocol):
    def iterate(
        self,
        size: int,
        skip_past: bool = True
    ) -> Iterator[TimestampIdArray]:
        """Iterate over timestamps.

        Parameters
        ----------
        size : int
            Number of timestamps to yield for each iteration

        skip_past : bool, default=True
            Wether to skip past timestamps before starting iteration

        Yields
        ------
        TimestampIdArray
            Array of timestamps with plugin ids

        Raises
        ------
        ValueError
            If parameter "size" is less than 1
        """
        ...
