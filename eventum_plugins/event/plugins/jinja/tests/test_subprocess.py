from eventum_plugins.event.plugins.jinja.subprocess import SubprocessManager


def test_subprocess_block():
    result = SubprocessManager().run('echo "Hello, world!"', block=True)
    assert result == 'Hello, world!\n'


def test_subprocess_non_block():
    result = SubprocessManager().run('echo "Hello, world!"', block=False)
    assert result is None
