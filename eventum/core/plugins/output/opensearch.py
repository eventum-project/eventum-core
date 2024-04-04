import logging
import os
import random
import ssl
from typing import Iterable

import aiohttp
import eventum.logging_config
from eventum.core.models.application_config import OutputFormat
from eventum.core.plugins.output.base import (BaseOutputPlugin, FormatError,
                                              OutputPluginConfigurationError,
                                              OutputPluginRuntimeError,
                                              format_event)

eventum.logging_config.apply()
logger = logging.getLogger(__name__)


class OpensearchOutputPlugin(BaseOutputPlugin):
    """Output plugin for sending events to opensearch."""

    def __init__(
        self,
        hosts: Iterable[str],
        user: str,
        password: str,
        index: str,
        verify_ssl: bool,
        ca_cert_path: str | None = None,
    ) -> None:
        super().__init__()

        self._user = user
        self._password = password
        self._index = index

        self._hosts: list[str] = list(hosts)
        if not self._hosts:
            raise OutputPluginConfigurationError(
                'At least one host must be provided'
            )

        self._ssl_context = ssl.create_default_context()
        if not verify_ssl:
            self._ssl_context.check_hostname = False
            self._ssl_context.verify_mode = ssl.CERT_NONE

        if ca_cert_path is not None:
            if not os.path.isabs(ca_cert_path):
                raise OutputPluginConfigurationError(
                    'Path to CA certificate must be absolute'
                )

            if not os.path.exists(ca_cert_path):
                raise OutputPluginConfigurationError(
                    f'Failed to find CA certificate in "{ca_cert_path}"'
                )

            self._ssl_context.load_verify_locations(cafile=ca_cert_path)

        self._session = None

    async def _open(self) -> None:
        self._session = aiohttp.ClientSession(
            auth=aiohttp.BasicAuth(self._user, self._password),
            connector=aiohttp.TCPConnector(ssl=self._ssl_context),
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        )

    async def _close(self) -> None:
        if self._session is None:
            return

        await self._session.close()
        self._session = None

    async def _write(self, event: str) -> int:
        host = random.choice(self._hosts)
        url = f'{host}/{self._index}/_doc/'

        try:
            event = format_event(format=OutputFormat.JSON_LINES, event=event)
        except FormatError as e:
            logger.warning(
                f'Failed to format event before sending to opensearch: {e}'
                f'{os.linesep}'
                'Original unformatted event: '
                f'{os.linesep}'
                f'{event}')
            return 0

        try:
            response = await self._session.post(
                url=url,
                data=event
            )
        except aiohttp.ClientError as e:
            raise OutputPluginRuntimeError(
                f'Failed to index events to opensearch: {e}'
            )

        if response.status != 201:
            text = await response.text()
            raise OutputPluginRuntimeError(
                f'Failed to index events to opensearch: '
                f'HTTP {response.status} - {text}'
            )

        return 1

    async def _write_many(self, events: Iterable[str]) -> int:
        ...
