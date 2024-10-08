from abc import ABC, abstractmethod
from copy import deepcopy
from multiprocessing.shared_memory import SharedMemory
from multiprocessing.synchronize import RLock
from typing import Any

import msgspec


class State(ABC):
    """Base key-value state."""

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
        ...

    @abstractmethod
    def cancel_update(self) -> None:
        """Release state lock acquired by `get_for_update` method."""
        ...

    @abstractmethod
    def as_dict(self) -> dict:
        """Get dictionary representation of state."""
        ...


class SingleThreadState(State):
    """Key-value state for single thread."""

    __slots__ = ('_state', )

    def __init__(self, initial: dict[str, Any] | None = None) -> None:
        self._state: dict[str, Any] = initial or dict()

    def set(self, key: str, value: Any) -> None:
        self._state[key] = value

    def get(self, key: str, default: Any | None = None) -> Any:
        try:
            return self._state[key]
        except KeyError:
            return default

    def get_for_update(self, key: str, default: Any = None) -> Any:
        return self.get(key, default)

    def cancel_update(self) -> None:
        return

    def as_dict(self) -> dict:
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
    ValueError
        If `create` is `True` but state already exists

    ValueError
        If `create` is `False` but state does not exist

    ValueError
        If `create` is `False` but `initial` is provided

    RuntimeError
        If state cannot be created due to other shared memory error
    """

    __slots__ = ('_shm', '_lock', '_encoder', '_decoder', '_state_to_update')
    _HEADER_SIZE = 8

    def __init__(
        self,
        name: str,
        create: bool,
        max_bytes: int,
        lock: RLock,
        initial: dict[str, Any] | None = None
    ) -> None:
        if initial is not None and not create:
            raise ValueError(
                'Parameter `initial` must be none when `create` is `False`'
            )
        try:
            self._shm = SharedMemory(name=name, create=create, size=max_bytes)
        except FileExistsError:
            raise ValueError(
                f'State with name "{name}" already exists'
            ) from None
        except FileNotFoundError:
            raise ValueError(
                f'State with name "{name}" does not exist'
            ) from None
        except OSError as e:
            raise RuntimeError(f'Cannot create shared state: {e}')

        self._lock = lock
        self._encoder = msgspec.msgpack.Encoder()
        self._decoder = msgspec.msgpack.Decoder()
        self._state_to_update: dict | None = None

        if create:
            self._write_state(initial or dict())

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            if self._state_to_update is None:
                state: dict = self._load_state()
            else:
                state = self._state_to_update

            state[key] = value
            self._write_state(state)

        if self._state_to_update is not None:
            self._state_to_update = None
            self._lock.release()

    def get(self, key: str, default: Any = None) -> Any:
        state: dict = self._load_state()

        if key not in state:
            return default
        else:
            return state[key]

    def get_for_update(self, key: str, default: Any = None) -> Any:
        self._lock.acquire()
        state: dict = self._load_state()
        self._state_to_update = state

        if key not in state:
            return default
        else:
            return state[key]

    def cancel_update(self) -> None:
        self._lock.release()

    def as_dict(self) -> dict:
        state: dict = self._load_state()
        return state

    def close(self) -> None:
        """Close state for caller process."""
        self._shm.close()

    def destroy(self) -> None:
        """Destroy state with releasing resources. This method should
        be called once after closing state in all related processes.
        """
        self._shm.unlink()

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

        with self._lock:
            self._shm.buf[:total_size] = data

    def _load_state(self) -> Any:
        """Load object from the shared memory.

        Returns
        -------
        Any
            Loaded object
        """
        with self._lock:
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
