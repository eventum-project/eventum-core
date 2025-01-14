from typing import Iterable, Iterator

import numpy as np
import structlog
from numpy.typing import NDArray

from eventum.plugins.exceptions import PluginRuntimeError
from eventum.plugins.input.base.plugin import InputPlugin
from eventum.plugins.input.protocols import (
    IdentifiedTimestamps, SupportsIdentifiedTimestampsIterate)
from eventum.plugins.input.utils.array_utils import chunk_array, merge_arrays

logger = structlog.stdlib.get_logger()


class InputPluginsMerger(SupportsIdentifiedTimestampsIterate):
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
        self._plugins = {plugin.guid: plugin for plugin in plugins}

        if not self._plugins:
            raise ValueError('At least one plugin must be provided')

    def _slice(
        self,
        size: int,
        skip_past: bool
    ) -> Iterator[dict[str, NDArray[np.datetime64]]]:
        """Slice timestamps from active generators. For each active
        generator current slice starts at earliest available timestamp
        and ends at minimal latest of arrays across all generators

        Parameters
        ----------
        size : int
            Number of timestamps to read from each generator

        skip_past : bool
            Wether to skip past timestamps before starting slicing

        Yields
        ------
        dict[str, NDArray[np.datetime64]]
            Slices of generators as a map with plugin guids in keys and
            arrays in values

        Notes
        -----
        Algorithm can be described by the following illustration:
        ```txt
        gen.
        ^
        |    0          1  2 3       4  5
        |    v          v  v v       v  v
        |3   |/////////////|   |////////|
        |2        |//////////|    |/////|
        |1     |////////|  |/////////|
        --------------------------------> t
        ```
        In the above example for 3 independent generators `_slice`
        method will yield 5 times.
        """
        active_generators = {
            guid: iter(plugin.generate(size, skip_past))
            for guid, plugin in self._plugins.items()
        }

        next_arrays: dict[str, NDArray[np.datetime64]] = dict()
        next_required_guids = list(active_generators.keys())

        while True:
            # get next arrays from generators if required
            if next_required_guids:
                for guid in next_required_guids:
                    try:
                        array = next(active_generators[guid])
                        next_arrays[guid] = array
                    except StopIteration:
                        del active_generators[guid]
                    except PluginRuntimeError as e:
                        logger.error(
                            (
                                'One of the input plugins finished execution '
                                ' with error'
                            ),
                            **e.context
                        )
                        del active_generators[guid]
                    except Exception as e:
                        plugin = self._plugins[guid]
                        logger.exception(
                            (
                                'One of the input plugins finished execution '
                                ' with unexpected error'
                            ),
                            **plugin.instance_info,
                            reason=str(e),
                        )

                next_required_guids.clear()

            if not next_arrays:
                break

            # find cutoff timestamp
            cutoff_timestamp = min(
                next_arrays.values(),
                key=lambda arr: arr[-1]
            )[-1]

            # fill the slice
            slice: dict[str, NDArray[np.datetime64]] = dict()
            for guid in tuple(next_arrays.keys()):
                array = next_arrays[guid]

                if array[-1] <= cutoff_timestamp:
                    slice[guid] = array
                    del next_arrays[guid]

                    if guid in active_generators:
                        next_required_guids.append(guid)
                elif array[0] < cutoff_timestamp < array[-1]:
                    index = np.searchsorted(
                        a=array,
                        v=cutoff_timestamp,
                        side='right'
                    )
                    left_part = array[:index]
                    right_part = array[index:]

                    if left_part.size > 0:
                        slice[guid] = left_part

                    if right_part.size > 0:
                        next_arrays[guid] = right_part
                    else:
                        del next_arrays[guid]

                        if guid in active_generators:
                            next_required_guids.append(guid)

            yield slice

    def iterate(
        self,
        size: int,
        skip_past: bool = True
    ) -> Iterator[IdentifiedTimestamps]:
        if size < 1:
            raise ValueError(
                'Parameter "size" must be greater or equal to 1'
            )

        consume_size = max(10_000, size // len(self._plugins))

        current_size = 0
        merged_arrays: list[IdentifiedTimestamps] = []

        for arrays in self._slice(size=consume_size, skip_past=skip_past):
            # build arrays with id from simple arrays
            arrays_with_id: list[IdentifiedTimestamps] = []
            for guid, array in arrays.items():
                array_with_id = np.empty(
                    shape=array.size,
                    dtype=[('timestamp', 'datetime64[us]'), ('id', 'uint16')]
                )
                array_with_id['timestamp'][:] = array
                array_with_id['id'][:] = self._plugins[guid].id

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

                chunks = chunk_array(result_array, size)
                if chunks[-1].size < size:
                    merged_arrays.append(chunks.pop())

                for chunk in chunks:
                    yield chunk
                    current_size -= chunk.size

        if merged_arrays:
            result_array = np.concatenate(merged_arrays)
            yield from chunk_array(result_array, size)
