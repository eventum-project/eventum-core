import subprocess as subprocess
from dataclasses import dataclass
from typing import Any


@dataclass
class SubprocessResult:
    stdout: str
    stderr: str
    exit_code: int


class SubprocessRunner:
    """Runner of commands in subprocesses."""

    def run(
        self,
        command: str,
        cwd: str | None = None,
        env: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> SubprocessResult | None:
        """Run command in a subprocess.

        Parameters
        ----------
        command : str
            Shell command to execute

        cwd : str | None, default=None
            Working directory

        env: dict[str, Any] | None, default=None
            Environment variables

        timeout: float | None, default=None
            Timeout (in seconds) of command execution

        Returns
        -------
        SubprocessResult
            Command result including its stdout, stderr and exit code

        Raises
        ------
        subprocess.TimeoutExpired
            If command timed out
        """
        proc = subprocess.run(
            args=command,
            shell=True,
            capture_output=True,
            cwd=cwd,
            env=env,
            timeout=timeout,
        )

        return SubprocessResult(
            stdout=proc.stdout.decode(),
            stderr=proc.stderr.decode(),
            exit_code=proc.returncode
        )
