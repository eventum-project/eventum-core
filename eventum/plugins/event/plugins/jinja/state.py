from abc import ABC, abstractmethod
from copy import deepcopy
from multiprocessing.shared_memory import SharedMemory
from typing import Any

import msgspec

from eventum.plugins.event.plugins.jinja.file_lock import FileLock


class State(ABC):
    """Base key-value state."""

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from state.

        Parameters
        ----------
        key : str
            Key of the value to get

        default : Any, default=None
            Default value to return if there is no value in state with
            specified key

        Returns
        -------
        Any
            Value from the state, or default value if there is no value
            in state with specified key
        """
        ...

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set value to state.

        Parameters
        ----------
        key : str
            Key of the value to set

        value : Any
            Value to set
        """
        ...

    @abstractmethod
    def update(self, m: dict[str, Any], /) -> None:
        """Update state with new values.

        Parameters
        ----------
        key : str
            Key of the value to set

        value : Any
            Value to set
        """

    @abstractmethod
    def clear(self) -> None:
        """Clear state."""
        ...

    @abstractmethod
    def as_dict(self) -> dict[str, Any]:
        """Get dictionary representation of state."""
        ...


class SingleThreadState(State):
    """Key-value state for single thread."""

    __slots__ = ('_state', )

    def __init__(self, initial: dict[str, Any] | None = None) -> None:
        self._state: dict[str, Any] = initial or dict()

    def get(self, key: str, default: Any | None = None) -> Any:
        try:
            return self._state[key]
        except KeyError:
            return default

    def set(self, key: str, value: Any) -> None:
        self._state[key] = value

    def update(self, m: dict[str, Any], /) -> None:
        self._state.update(m)

    def clear(self) -> None:
        self._state.clear()

    def as_dict(self) -> dict[str, Any]:
        return deepcopy(self._state)


class MultiProcessState(State):
    """Key-value state for multiple processes.

    Parameters
    ----------
    name : str
        Name that enables one process to create a state shared across
        processes so that a different processes can attach to that same
        shared state using that same name

    create : bool
        Whether to create new state or connect to existing state

    max_bytes : int
        Maximum size of state in bytes

    lock : RLock
        Lock for synchronization across processes

    Raises
    ------
    RuntimeError
        If state cannot be created or connected due to some error
    """

    _HEADER_SIZE = 8
    _BUFFER_SIZE = 1 * 1024 * 1024
    _SHM_NAME = 'eventum-jinja-globals'

    def __init__(self, initial: dict[str, Any] | None = None) -> None:
        try:
            try:
                self._shm = SharedMemory(
                    name=MultiProcessState._SHM_NAME,
                    create=True,
                    size=MultiProcessState._BUFFER_SIZE
                )
                self._creator = True
            except FileExistsError:
                self._shm = SharedMemory(
                    name=MultiProcessState._SHM_NAME,
                    create=False,
                    size=MultiProcessState._BUFFER_SIZE
                )
                self._creator = False
        except OSError as e:
            raise RuntimeError(
                f'Cannot create or connect to shared state: {e}'
            )

        self._lock = FileLock(name=MultiProcessState._SHM_NAME)

        self._encoder = msgspec.msgpack.Encoder()
        self._decoder = msgspec.msgpack.Decoder()
        self._state_to_update: dict[str, Any] = dict()

        if self._creator:
            with self._lock:
                self._write_state(dict())

        if initial is not None:
            with self._lock:
                self._write_state(initial)

    def get(self, key: str, default: Any = None) -> Any:
        if self._lock.acquired:
            return self._state_to_update

        with self._lock:
            state: dict[str, Any] = self._load_state()

        if key not in state:
            return default
        else:
            return state[key]

    def set(self, key: str, value: Any) -> None:
        if self._lock.acquired:
            try:
                self._state_to_update[key] = value
                self._write_state(self._state_to_update)
            finally:
                self._lock.release()
        else:
            with self._lock:
                state: dict[str, Any] = self._load_state()
                state[key] = value
                self._write_state(state)

    def update(self, m: dict[str, Any], /) -> None:
        if self._lock.acquired:
            try:
                self._state_to_update.update(m)
                self._write_state(self._state_to_update)
            finally:
                self._lock.release()
        else:
            with self._lock:
                state: dict[str, Any] = self._load_state()
                state.update(m)
                self._write_state(state)

    def clear(self) -> None:
        if self._lock.acquired:
            try:
                self._write_state(dict())
            finally:
                self._lock.release()
        else:
            with self._lock:
                self._write_state(dict())

    def get_for_update(self, key: str, default: Any = None) -> Any:
        """Get value from state for next update with acquiring state lock
        until next set.

        Parameters
        ----------
        key : str
            Key of the value to get

        default : Any, default=None
            Default value to return if there is no value in state with
            specified key

        Returns
        -------
        Any
            Value from the state, or default value if there is no value
            in state with specified key
        """
        if self._lock.acquired:
            return self._state_to_update

        self._lock.acquire()
        try:
            self._state_to_update = self._load_state()

            if key not in self._state_to_update:
                return default
            else:
                return self._state_to_update[key]
        except Exception:
            self._lock.release()

    def cancel_update(self) -> None:
        """Release state lock acquired by `get_for_update` method."""
        if self._lock.acquired:
            self._lock.release()

    def as_dict(self) -> dict[str, Any]:
        if self._lock.acquired:
            return self._state_to_update
        else:
            with self._lock:
                return self._load_state()

    def _write_state(self, object: Any) -> None:
        """Write object to shared memory.

        Parameters
        ----------
        object : Any
            Object to write

        Raises
        ------
        ValueError
            If object is too large
        """
        encoded_obj = self._encoder.encode(object)
        header = len(encoded_obj).to_bytes(self._HEADER_SIZE)

        data = header + encoded_obj
        total_size = len(data)

        if total_size > self._shm.size:
            raise ValueError('State size limit exceeded')

        self._shm.buf[:total_size] = data

    def _load_state(self) -> Any:
        """Load object from shared memory.

        Returns
        -------
        Any
            Loaded object
        """
        size = int.from_bytes(self._shm.buf[:self._HEADER_SIZE])

        try:
            object = self._decoder.decode(
                self._shm.buf[self._HEADER_SIZE:self._HEADER_SIZE + size]
            )
            return object
        except msgspec.DecodeError as e:
            raise RuntimeError(
                f'Cannot decode data from shared memory: {e}'
            ) from None

    def cleanup(self) -> None:
        """Cleanup inter-process resources."""
        self._shm.close()

        if self._creator:
            self._shm.unlink()
