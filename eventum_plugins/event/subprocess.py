import subprocess as subprocess


class SubprocessManager:
    """Class for running any command in subprocess."""

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
        proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)

        if block:
            stdout, _ = proc.communicate()
            return stdout.decode()

        return None
