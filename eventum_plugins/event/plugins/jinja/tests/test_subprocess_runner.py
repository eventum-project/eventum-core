import os
import platform
from pathlib import Path

from eventum_plugins.event.plugins.jinja.subprocess_runner import \
    SubprocessRunner


def test_subprocess():
    result = SubprocessRunner().run('echo Hello, world!')

    assert result.stdout == 'Hello, world!' + os.linesep
    assert result.stderr == ''
    assert result.exit_code == 0


def test_subprocess_stderr():
    result = SubprocessRunner().run(
        command='>&2 echo error',
    )

    assert result.stdout == ''
    assert result.stderr == 'error' + os.linesep
    assert result.exit_code == 0


def test_subprocess_cwd():
    home_dir = str(Path.home())

    result = SubprocessRunner().run(
        command='pwd',
        cwd=home_dir
    )
    assert result.stdout == home_dir + os.linesep


def test_subprocess_env():
    if platform.system() == 'Windows':
        result = SubprocessRunner().run(
            command='echo %MY_VAR%',
            env={'MY_VAR': 'VALUE'}
        )
    else:
        result = SubprocessRunner().run(
            command='echo $MY_VAR',
            env={'MY_VAR': 'VALUE'}
        )

    assert result.stdout == 'VALUE' + os.linesep


def test_subprocess_timed_out():
    result = SubprocessRunner().run(
        command='sleep 10 && echo "Hello, world!"',
        timeout=0.1,
    )
    assert result is None
