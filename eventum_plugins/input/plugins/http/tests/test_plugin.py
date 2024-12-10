import socket
from concurrent.futures import ThreadPoolExecutor

import pytest
import requests as rq  # type: ignore[import-untyped]
from pytz import timezone

from eventum_plugins.exceptions import PluginConfigurationError
from eventum_plugins.input.plugins.http.config import HttpInputPluginConfig
from eventum_plugins.input.plugins.http.plugin import HttpInputPlugin


def test_plugin():
    with ThreadPoolExecutor(max_workers=1) as executor:
        plugin = HttpInputPlugin(
            config=HttpInputPluginConfig(
                port=8080
            ),
            params={
                'id': 1,
                'batch_size': 1,
                'timezone': timezone('UTC'),
                'live_mode': True,
            }

        )

        events = []
        future = executor.submit(lambda: events.extend(plugin.generate()))

        for _ in range(5):
            res = rq.post('http://localhost:8080/generate', json={'count': 2})
            assert res.status_code == 201

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        assert sock.connect_ex(('127.0.0.1', 8080)) == 0
        sock.close()

        res = rq.post('http://localhost:8080/stop')

        assert res.status_code == 200

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        assert sock.connect_ex(('127.0.0.1', 8080)) == 0
        sock.close()

        future.result()

        assert len(events) == 10


def test_plugin_bad_address():
    with pytest.raises(PluginConfigurationError):
        HttpInputPlugin(
            config=HttpInputPluginConfig(
                address='google.com',   # why not
                port=443
            ),
            params={
                'id': 1,
                'batch_size': 1,
                'timezone': timezone('UTC'),
                'live_mode': True,
            }

        )
