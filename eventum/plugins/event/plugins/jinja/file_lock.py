import fcntl
import os
import tempfile
from io import TextIOWrapper
from types import TracebackType


class FileLock:
    """File based lock.

    Parameters
    ----------
    name : str
        Lock name
    """
    _LOCKS_DIR = os.path.join(
        tempfile.gettempdir(),
        '.eventum_locks'
    )

    def __init__(self, name: str) -> None:
        self._name = name + '.lock'
        self._path = os.path.join(FileLock._LOCKS_DIR, self._name)
        self._file: TextIOWrapper | None = None

    def _open(self) -> TextIOWrapper:
        """Open file with handling parent directories creation and
        return it.

        Returns
        -------
        TextIOWrapper
            Opened file
        """
        if not os.path.exists(FileLock._LOCKS_DIR):
            os.mkdir(FileLock._LOCKS_DIR)

        return open(self._path, mode='w')

    def acquire(self) -> None:
        """Acquire lock."""
        if self._file is not None:
            return

        self._file = self._open()
        fcntl.lockf(self._file, fcntl.LOCK_EX)

    def release(self) -> None:
        """Release lock."""
        if self._file is None:
            return

        fcntl.flock(self._file, fcntl.LOCK_UN)
        self._file.close()
        self._file = None

    def __enter__(self) -> None:
        self.acquire()

    def __exit__(
        self,
        exctype: type[BaseException] | None,
        excinst: BaseException | None,
        exctb: TracebackType | None
    ) -> None:
        self.release()

    @property
    def acquired(self) -> bool:
        """Whether the lock is acquired."""
        return self._file is not None
