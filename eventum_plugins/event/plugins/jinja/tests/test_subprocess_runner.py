from eventum_plugins.event.plugins.jinja.subprocess_runner import \
    SubprocessRunner


def test_subprocess_block():
    result = SubprocessRunner().run('echo "Hello, world!"', block=True)
    assert result == 'Hello, world!\n'


def test_subprocess_non_block():
    result = SubprocessRunner().run('echo "Hello, world!"', block=False)
    assert result is None
