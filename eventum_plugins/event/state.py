from abc import ABC, abstractmethod
from copy import deepcopy
from multiprocessing.synchronize import RLock
from multiprocessing.shared_memory import SharedMemory
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
    def as_dict(self) -> dict:
        """Get dictionary representation of state."""
        ...


class SingleProcessState(State):
    """Key-value state for single process."""

    __slots__ = ('_state', )

    def __init__(self) -> None:
        self._state: dict[str, Any] = dict()

    def set(self, key: str, value: Any) -> None:
        self._state[key] = value

    def get(self, key: str, default: Any | None = None) -> Any:
        try:
            return self._state[key]
        except KeyError:
            return default

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

    lock : LockLike
        Lock for synchronization across processes

    Raises
    ------
    ValueError
        If `create` is `True` but state already exists

    ValueError
        If `create` is `False` but state does not exist

    RuntimeError
        If state cannot be created due to other shared memory error
    """

    __slots__ = ('_shm', '_lock', '_encoder', '_decoder')
    _HEADER_SIZE = 8

    def __init__(
        self,
        name: str,
        create: bool,
        max_bytes: int,
        lock: RLock
    ) -> None:
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

        if create:
            self._write_state(dict())

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            state: dict = self._load_state()
            state[key] = value
            self._write_state(state)

    def get(self, key: str, default: Any = None) -> Any:
        state: dict = self._load_state()

        if key not in state:
            return default
        else:
            return state[key]

    def as_dict(self) -> dict:
        state: dict = self._load_state()
        return state

    def close(self) -> None:
        """Close state for caller process."""
        self._shm.close()

    def destroy(self) -> None:
        """Destroy state with releasing resources. This method should
        be called after closing state in all related process.
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
            size = int.from_bytes(
                self._shm.buf[:self._HEADER_SIZE]
            )

            object = self._decoder.decode(
                self._shm.buf[self._HEADER_SIZE:self._HEADER_SIZE + size]
            )
            return object
