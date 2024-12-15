import json
import re

import pytest
from aioresponses import aioresponses

from eventum_plugins.output.plugins.opensearch.config import \
    OpensearchOutputPluginConfig
from eventum_plugins.output.plugins.opensearch.plugin import \
    OpensearchOutputPlugin

pytest_plugins = ('pytest_asyncio',)


@pytest.fixture
def config():
    return OpensearchOutputPluginConfig(
        hosts=['https://localhost:9200'],
        username='admin',
        password='pass',
        index='test_index',
        verify_ssl=False
    )


@pytest.fixture
def write_response():
    return json.dumps({
        '_index': 'test_index',
        '_id': 'pIQetY8B-vfSDQ_FAHhq',
        '_version': 1,
        'result': 'created',
        '_shards': {
            'total': 1,
            'successful': 1,
            'failed': 0
        },
        '_seq_no': 0,
        '_primary_term': 1
    })


@pytest.fixture
def write_many_response():
    return json.dumps({
        'took': 53,
        'errors': False,
        'items': [
            {
                'index': {
                    '_index': 'test_index',
                    '_id': 'QYQmtY8B-vfSDQ_Fw4u9',
                    '_version': 1,
                    'result': 'created',
                    '_shards': {
                        'total': 1,
                        'successful': 1,
                        'failed': 0
                    },
                    '_seq_no': 0,
                    '_primary_term': 17,
                    'status': 201
                }
            }
        ]
    })


@pytest.mark.asyncio
async def test_opensearch_write(config, write_response):
    plugin = OpensearchOutputPlugin(config=config, params={'id': 1})
    await plugin.open()

    with aioresponses() as m:
        m.post(
            url=re.compile(r'https://localhost:9200/.*'),
            status=201,
            body=write_response
        )
        written = await plugin.write(
            events=['{"@timestamp": "2024-01-01T00:00:00.000Z", "value": 1}']
        )
        await plugin.close()

        m.assert_called()

        (method, url), requests = m.requests.popitem()
        assert method == 'POST'
        assert str(url) == 'https://localhost:9200/test_index/_doc'
        assert requests[0].kwargs['data'] == (
            '{"@timestamp": "2024-01-01T00:00:00.000Z", "value": 1}'
        )
        assert written == 1


@pytest.mark.asyncio
async def test_opensearch_write_many(config, write_many_response):
    plugin = OpensearchOutputPlugin(config=config, params={'id': 1})
    await plugin.open()

    with aioresponses() as m:
        m.post(
            url=re.compile(r'https://localhost:9200/.*'),
            status=200,
            body=write_many_response
        )
        written = await plugin.write(
            [
                '{"@timestamp": "2024-01-01T00:00:00.000Z", "value": 1}',
                '{"@timestamp": "2024-01-01T00:00:01.000Z", "value": 2}'
            ]
        )
        await plugin.close()

        m.assert_called()

        (method, url), requests = m.requests.popitem()
        assert method == 'POST'
        assert str(url) == 'https://localhost:9200/_bulk'
        assert requests[0].kwargs['data'] == (
            '{"index": {"_index": "test_index"}}\n'
            '{"@timestamp": "2024-01-01T00:00:00.000Z", "value": 1}\n'
            '{"index": {"_index": "test_index"}}\n'
            '{"@timestamp": "2024-01-01T00:00:01.000Z", "value": 2}\n'
        )
        assert written == 2


@pytest.mark.asyncio
async def test_opensearch_invalid_data(config, write_response):
    plugin = OpensearchOutputPlugin(config=config, params={'id': 1})
    await plugin.open()

    with aioresponses() as m:
        m.post(
            url=re.compile(r'https://localhost:9200/.*'),
            status=201,
            body=write_response
        )

        written = await plugin.write(
            ['{"@timestamp": "2024-01-01T00:00:00.000Z", "val CORRUPTED...']
        )

        await plugin.close()

        m.assert_not_called()

        assert written == 0


@pytest.mark.asyncio
async def test_opensearch_write_many_partially_corrupted(
    config,
    write_response
):
    plugin = OpensearchOutputPlugin(config=config, params={'id': 1})
    await plugin.open()

    with aioresponses() as m:
        m.post(
            url=re.compile(r'https://localhost:9200/.*'),
            status=201,
            body=write_response
        )
        written = await plugin.write(
            [
                '{"@timestamp": "2024-01-01T00:00:00.000Z", "value": 1}',
                '{"@timestamp": "2024-01-01T00:00:00.000Z", "val CORRUPTED...'
            ]
        )
        await plugin.close()

        m.assert_called()

        (method, url), requests = m.requests.popitem()
        assert method == 'POST'
        assert str(url) == 'https://localhost:9200/test_index/_doc'
        assert requests[0].kwargs['data'] == (
            '{"@timestamp": "2024-01-01T00:00:00.000Z", "value": 1}'
        )
        assert written == 1
