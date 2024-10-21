import subprocess as subprocess
from datetime import datetime
from typing import Any, Callable


class SubprocessRunner:
    """Class for running any command in subprocess."""

    def __init__(self) -> None:
        self._run_callback: Callable[[datetime, str, bool], Any] | None = None

    def run(self, command: str, block: bool = False) -> str | None:
        """Start command in a subprocess.

        Parameters
        ----------
        command : str
            Shell command to execute

        block : bool, default=False
            Whether to wait for the subprocess to complete and return
            its stdout

        Returns
        -------
        str | None
            Stdout of command in case of `block` is `True`, otherwise
            `None`
        """
        if self._run_callback is not None:
            self._run_callback(datetime.now().astimezone(), command, block)

        proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)

        if block:
            stdout, _ = proc.communicate()
            return stdout.decode()

        return None

    def set_run_callback(
        self,
        callback: Callable[[datetime, str, bool], Any] | None
    ) -> None:
        """Set callback for `run` method.

        Parameters
        ----------
        callback : Callable[[datetime, str, bool], Any] | None
            Callable or `None` (to unset callback). Callback parameters:
            1. timestamp of `run` call
            2. parameter `command` of `run` method
            3. parameter `block` of `run` method

        """
        self._run_callback = callback
