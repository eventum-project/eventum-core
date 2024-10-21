import subprocess as subprocess


class SubprocessRunner:
    """Class for running any command in subprocess."""

    def __init__(self) -> None:
        self._last_command: str | None = None

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
        self._last_command = command

        proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)

        if block:
            stdout, _ = proc.communicate()
            return stdout.decode()

        return None

    @property
    def last_command(self) -> str | None:
        """Last ran command that was run."""
        return self._last_command
