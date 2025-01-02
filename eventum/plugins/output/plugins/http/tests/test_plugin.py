import re

import pytest
from aioresponses import aioresponses
from pydantic import HttpUrl

from eventum.plugins.output.fields import Format, JsonFormatterConfig
from eventum.plugins.output.plugins.http.config import HttpOutputPluginConfig
from eventum.plugins.output.plugins.http.plugin import HttpOutputPlugin


@pytest.mark.asyncio
async def test_plugin_write():
    config = HttpOutputPluginConfig(
        url=HttpUrl('http://localhost:8000/endpoint'),   # type: ignore
        headers={'Content-Type': 'application/json'},
        formatter=JsonFormatterConfig(format=Format.JSON, indent=0)
    )
    plugin = HttpOutputPlugin(config=config, params={'id': 1})

    await plugin.open()

    with aioresponses() as m:
        m.post(
            url=re.compile(r'http://localhost:8000/.*'),
            status=201,
            body='Ok.'
        )
        written = await plugin.write(
            events=['{"@timestamp": "2024-01-01T00:00:00.000Z", "value": 1}']
        )
        await plugin.close()

        m.assert_called()

        (method, url), requests = m.requests.popitem()
        assert method == 'POST'
        assert str(url) == 'http://localhost:8000/endpoint'
        assert requests[0].kwargs['data'] == (
            '{"@timestamp": "2024-01-01T00:00:00.000Z", "value": 1}'
        )
        assert written == 1


@pytest.mark.asyncio
async def test_plugin_wrong_code():
    config = HttpOutputPluginConfig(
        url=HttpUrl('http://localhost:8000/endpoint'),   # type: ignore
        headers={'Content-Type': 'application/json'},
        formatter=JsonFormatterConfig(format=Format.JSON, indent=0)
    )
    plugin = HttpOutputPlugin(config=config, params={'id': 1})

    await plugin.open()

    with aioresponses() as m:
        m.post(
            url=re.compile(r'http://localhost:8000/.*'),
            status=200,
            body='Ok.'
        )
        written = await plugin.write(
            events=['{"@timestamp": "2024-01-01T00:00:00.000Z", "value": 1}']
        )
        await plugin.close()

        m.assert_called()

        (method, url), requests = m.requests.popitem()
        assert method == 'POST'
        assert str(url) == 'http://localhost:8000/endpoint'
        assert requests[0].kwargs['data'] == (
            '{"@timestamp": "2024-01-01T00:00:00.000Z", "value": 1}'
        )
        assert written == 0
