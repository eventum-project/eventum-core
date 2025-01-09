from collections import deque
from dataclasses import dataclass
from typing import Iterator, Literal

from numpy import concatenate, datetime64, full
from numpy.typing import NDArray


@dataclass(slots=True)
class BufferItem:
    """Buffer item.

    Attributes
    ----------
    type : Literal['v', 'm', 'mv']
        Type of item:
        v - single timestamp value,
        m - value of timestamps that should be multiplied,
        mv - multi value array of timestamps

    value : datetime64 | NDArray[datetime64]
        Target value

    multiply : int:
        multiplication factor for type 'm'
    """
    type: Literal['v', 'm', 'mv']
    value: datetime64 | NDArray[datetime64]
    multiply: int = 1


class Buffer:
    """Buffer for timestamps."""

    def __init__(self) -> None:
        self._buffer: deque[BufferItem] = deque()
        self._buffer_size = 0

    def push(self, timestamp: datetime64) -> None:
        """Push timestamp to buffer.

        Parameters
        ----------
        timestamp : datetime64
            Timestamp to push
        """
        self._buffer.append(BufferItem(type='v', value=timestamp))
        self._buffer_size += 1

    def m_push(self, timestamp: datetime64, multiply: int) -> None:
        """Push multiple timestamps of the same value to buffer.

        Parameters
        ----------
        timestamp : datetime64
            Timestamp to push

        Raises
        ------
        ValueError
            If parameter "multiply" is less than 1
        """
        if multiply < 1:
            raise ValueError(
                'Parameter "multiply" must be greater or equal to 1'
            )

        self._buffer.append(
            BufferItem(type='m', value=timestamp, multiply=multiply)
        )
        self._buffer_size += multiply

    def mv_push(self, timestamps: NDArray[datetime64]) -> None:
        """Push multi value timestamps array to buffer.

        Parameters
        ----------
        timestamps : NDArray[datetime64]
            Timestamps to push
        """
        if timestamps.size == 0:
            return

        self._buffer.append(BufferItem(type='mv', value=timestamps))
        self._buffer_size += timestamps.size

    def read(
        self,
        size: int,
        partial: bool = False
    ) -> Iterator[NDArray[datetime64]]:
        """Read timestamps from buffer by arrays of specified size.

        Parameters
        ----------
        size : int
            Size of arrays

        partial : bool, default = False
            Read until buffer is empty event if the last array is not
            complete

        Yields
        ------
        NDArray[datetime64]
            Array of timestamps

        Raises
        ------
        ValueError
            If  parameter "size" is less than 1

        Notes
        -----
        No push methods are supposed to be called until this method
        generator is exhausted
        """
        if size < 1:
            raise ValueError(
                'Parameter "size" must be greater or equal to 1'
            )

        to_concatenate: list[NDArray[datetime64]] = []
        current_size = 0

        while True:
            if len(self._buffer) == 0:
                break

            item = self._buffer[0]

            match item.type:
                case 'v':
                    self._buffer.popleft()
                    current_size += 1

                    to_concatenate.append(
                        full(
                            shape=1,
                            fill_value=item.value,
                            dtype='datetime64[us]'
                        )
                    )
                case 'm':
                    n = item.multiply or 1
                    required = size - current_size

                    if required >= n:
                        self._buffer.popleft()
                    else:
                        n = required
                        item.multiply -= n

                    current_size += n

                    to_concatenate.append(
                        full(
                            shape=n,
                            fill_value=item.value,
                            dtype='datetime64[us]'
                        )
                    )
                case 'mv':
                    n = item.value.size
                    required = size - current_size

                    arr: NDArray[datetime64] = item.value   # type: ignore

                    if required >= n:
                        self._buffer.popleft()
                    else:
                        n = required
                        item.value = arr[n:]
                        arr = arr[:n]

                    current_size += n

                    to_concatenate.append(arr)

            if current_size == size:
                yield concatenate(to_concatenate)

                self._buffer_size -= size
                current_size = 0
                to_concatenate.clear()

        if to_concatenate:
            remaining_array = concatenate(to_concatenate)
            to_concatenate.clear()

            if partial:
                yield remaining_array
                self._buffer_size -= remaining_array.size
            else:
                self._buffer.appendleft(
                    BufferItem(
                        type='mv',
                        value=remaining_array
                    )
                )

    @property
    def size(self) -> int:
        """Current number of timestamps in buffer."""
        return self._buffer_size
