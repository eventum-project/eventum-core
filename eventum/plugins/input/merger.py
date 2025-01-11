from datetime import datetime
from typing import Annotated, Iterable, Iterator, Literal, TypeAlias, overload

import numpy as np
import structlog
from numpy.typing import NDArray

from eventum.plugins.exceptions import PluginRuntimeError
from eventum.plugins.input.base.plugin import InputPlugin
from eventum.plugins.input.utils.array_utils import merge_arrays

logger = structlog.stdlib.get_logger()

TimestampArray: TypeAlias = NDArray[np.datetime64]
TimestampIdArray: TypeAlias = Annotated[
    NDArray,
    np.dtype([('timestamp', 'datetime64[us]'), ('id', 'uint16')])
]


class InputPluginsMerger:
    """Merger of timestamp generating by multiple input plugins.

    Parameters
    ----------
    plugins : Iterable[InputPlugin]
        Input plugins to merge

    Raises
    ------
    ValueError
        If no plugins provided in sequence
    """

    def __init__(self, plugins: Iterable[InputPlugin]) -> None:
        self._plugins = list(plugins)

        if not self._plugins:
            raise ValueError('At least one plugin must be provided')

    def _find_cutoff_timestamp(
        self,
        arrays: Iterable[NDArray[np.datetime64]],
        aligned: bool
    ) -> tuple[np.datetime64, bool]:
        """Find cutoff timestamp for timestamp arrays.

        Parameters
        ----------
        arrays : Iterable[NDArray[np.datetime64]]
            Arrays to find timestamp for

        aligned : bool
            Wether the arrays are aligned at start

        Returns
        -------
        datetime64, bool
            Cutoff timestamp and aligning status

        Raises
        ------
        ValueError
            If no arrays in iterable provided

        Notes
        -----
        See description of cutoff timestamp in `_slice` method
        """
        arrays = tuple(arrays)

        if len(arrays) == 0:
            raise ValueError('At least one array is expected')
        elif len(arrays) == 1:
            return (arrays[0][-1], False)

        first_min_ts = np.datetime64(datetime.max.isoformat(), 'us')
        second_min_ts = first_min_ts

        cutoff_timestamp = first_min_ts

        next_align = False

        for array in arrays:
            if array[0] < first_min_ts:
                second_min_ts = first_min_ts
                first_min_ts = array[0]
                cutoff_timestamp = array[-1]
                next_align = False
            elif array[0] < second_min_ts:
                second_min_ts = array[0]

            if second_min_ts < cutoff_timestamp and not aligned:
                cutoff_timestamp = second_min_ts
                next_align = True

        return (cutoff_timestamp, next_align)

    def _slice(
        self,
        size: int,
        skip_past: bool
    ) -> Iterator[dict[int, NDArray[np.datetime64]]]:
        """Slice timestamps from active generators. For each active
        generator current slice starts at earliest timestamp across all
        generators current arrays and ends at latest timestamps of this
        array with earliest timestamp.

        Parameters
        ----------
        size : int
            Number of timestamps to read from each generator

        skip_past : bool
            Parameter "skip_past" of generate method of input plugins

        Yields
        ------
        dict[int, NDArray[np.datetime64]]
            Slices of generators as a map with plugin id in keys and
            arrays in values

        Notes
        -----
        Algorithm can be described by the following illustration:
        ```
        gen.
        ^
        |    0 1  2     3  4 5 6  7  8  9
        |    v v  v     v  v v v  v  v  v
        |3   |/////////////|   |////////|
        |2        |//////////|    |/////|
        |1     |////////|  |/////////|
        --------------------------------> t
        ```
        In the above example for 3 independent generators `_slice`
        method will yield 9 times (on each point of overlapping of
        arrays returned by generators)
        """
        active_generators = {
            plugin.id: iter(plugin.generate(size, skip_past))
            for plugin in self._plugins
        }

        next_arrays: dict[int, NDArray[np.datetime64]] = dict()
        next_required_ids = list(active_generators.keys())

        aligned = False

        while active_generators or next_arrays:
            # get next arrays from generators if required
            if next_required_ids:
                for id in next_required_ids:
                    try:
                        array = next(active_generators[id])
                        next_arrays[id] = array
                    except StopIteration:
                        del active_generators[id]
                    except PluginRuntimeError as e:
                        logger.error(
                            (
                                'One of the input plugins finished execution '
                                ' with error'
                            ),
                            **e.context
                        )
                        del active_generators[id]
                    except Exception as e:
                        plugin = next(
                            filter(
                                lambda plugin: plugin.id == plugin_id,
                                self._plugins
                            )
                        )
                        logger.exception(
                            (
                                'One of the input plugins finished execution '
                                ' with unexpected error'
                            ),
                            **plugin.instance_info,
                            reason=str(e),
                        )

                next_required_ids.clear()

            # find cutoff timestamp
            cutoff_timestamp, aligned = self._find_cutoff_timestamp(
                arrays=next_arrays.values(),
                aligned=aligned
            )

            # fill the slice
            slice: dict[int, NDArray[np.datetime64]] = dict()
            for plugin_id in tuple(next_arrays.keys()):
                array = next_arrays[plugin_id]

                if array[-1] <= cutoff_timestamp:
                    slice[plugin_id] = array
                    del next_arrays[plugin_id]

                    if plugin_id in active_generators:
                        next_required_ids.append(plugin_id)
                elif array[0] < cutoff_timestamp < array[-1]:
                    index = np.searchsorted(
                        a=array,
                        v=cutoff_timestamp,
                        side='right'
                    )
                    left_part = array[:index]
                    right_part = array[index:]

                    if left_part.size > 0:
                        slice[plugin_id] = left_part

                    if right_part.size > 0:
                        next_arrays[plugin_id] = right_part
                    else:
                        del next_arrays[plugin_id]

                        if plugin_id in active_generators:
                            next_required_ids.append(plugin_id)

            yield slice

    @overload
    def generate(
        self,
        size: int,
        skip_past: bool,
        include_id: Literal[False]
    ) -> Iterator[TimestampArray]:
        ...

    @overload
    def generate(
        self,
        size: int,
        skip_past: bool,
        include_id: Literal[True]
    ) -> Iterator[TimestampIdArray]:
        ...

    def generate(
        self,
        size: int,
        skip_past: bool,
        include_id: bool = False,
    ) -> Iterator[TimestampArray | TimestampIdArray]:
        """Start timestamps generation of input plugins.

        Parameters
        ----------
        size : int
            Number of timestamps to generate

        skip_past : bool
            Parameter "skip_past" of generate method of input plugins

        include_id : bool, default=False
            Wether to include id of plugins in batches

        Yields
        ------
        TimestampArray | TimestampIdArray
            Timestamps array or timestamps with plugin id array if
            parameter `include_id` is `True`
        """
        if size < 1:
            raise ValueError(
                'Parameter "size" must be greater or equal to 1'
            )

        consume_size = max(10_000, size // len(self._plugins))

        current_size = 0
        merged_arrays: list[TimestampIdArray] = []

        for arrays in self._slice(size=consume_size, skip_past=skip_past):
            # build arrays with id from simple arrays
            arrays_with_id: list[TimestampIdArray] = []
            for plugin_id, array in arrays.items():
                array_with_id = np.empty(
                    shape=array.size,
                    dtype=[('timestamp', 'datetime64[us]'), ('id', 'uint16')]
                )
                array_with_id['timestamp'][:] = array
                array_with_id['id'][:] = plugin_id

                arrays_with_id.append(array_with_id)

            if len(arrays_with_id) > 1:
                merged_array = merge_arrays(arrays_with_id)
            else:
                merged_array = arrays_with_id[0]

            merged_arrays.append(merged_array)

            current_size += merged_array.size

            if current_size >= size:
                result_array = np.concatenate(merged_arrays)
                merged_arrays.clear()

                if result_array.size > size:
                    merged_arrays.append(result_array[size:])
                    result_array = result_array[:size]

                if include_id:
                    yield result_array
                else:
                    yield result_array['timestamp']

                current_size -= result_array.size

        if merged_arrays:
            result_array = np.concatenate(merged_arrays)

            if include_id:
                yield result_array
            else:
                yield result_array['timestamp']
