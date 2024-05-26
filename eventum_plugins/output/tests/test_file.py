import os
import tempfile
from uuid import uuid4

import pytest

from eventum_plugins.output.file import FileOutputConfig, FileOutputPlugin

pytest_plugins = ('pytest_asyncio', )


@pytest.mark.asyncio
async def test_file_write():
    path = os.path.join(tempfile.gettempdir(), str(uuid4()))
    plugin = FileOutputPlugin(config=FileOutputConfig(path=path))

    await plugin.open()
    await plugin.write('Test event')
    await plugin.close()

    with open(path) as f:
        content = f.read()

    os.remove(path)
    assert content == ('Test event' + os.linesep)


@pytest.mark.asyncio
async def test_file_write_many():
    path = os.path.join(tempfile.gettempdir(), str(uuid4()))
    plugin = FileOutputPlugin(config=FileOutputConfig(path=path))
    events = ['Test event', 'Test event 2', 'Test event 3']

    await plugin.open()
    await plugin.write_many(events)
    await plugin.close()

    with open(path) as f:
        content = f.read()

    os.remove(path)
    assert content == (os.linesep.join(events) + os.linesep)
