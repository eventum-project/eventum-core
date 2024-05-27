import asyncio
import json
import logging
import os
import random
import ssl
from typing import Iterable

import aiohttp
from pydantic import Field, field_validator

from eventum_plugins.output.base import (BaseOutputPlugin, OutputFormat,
                                         OutputPluginBaseConfig,
                                         OutputPluginRuntimeError)

logger = logging.getLogger(__name__)


class OpensearchOutputConfig(OutputPluginBaseConfig, frozen=True):
    hosts: tuple[str, ...] = Field(..., min_length=1)
    user: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    index: str = Field(..., min_length=1)
    verify_ssl: bool
    ca_cert_path: str | None = None

    @field_validator('ca_cert_path')
    def validate_ca_cert_path(cls, v: str | None):
        if not isinstance(v, str):
            return v

        if not os.path.isabs(v):
            raise ValueError('Path must be absolute')

        if not os.path.exists(v):
            raise ValueError(
                f'Failed to find CA certificate in "{v}"'
            )


class OpensearchOutputPlugin(BaseOutputPlugin):
    """Output plugin for sending events to opensearch."""

    def __init__(self, config: OpensearchOutputConfig) -> None:
        # Format is JSON_LINES here because we need to validate that
        # string is a valid json document that OpenSearch can index
        super().__init__(config)
        self._set_formatter(format=OutputFormat.JSON_LINES)

        self._hosts = config.hosts
        self._user = config.user
        self._password = config.password
        self._index = config.index

        self._ssl_context = ssl.create_default_context()

        if not config.verify_ssl:
            self._ssl_context.check_hostname = False
            self._ssl_context.verify_mode = ssl.CERT_NONE

        if config.ca_cert_path is not None:
            self._ssl_context.load_verify_locations(cafile=config.ca_cert_path)

        self._session: aiohttp.ClientSession

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
        await self._session.close()

    async def _write(self, event: str) -> None:
        host = random.choice(self._hosts)
        url = f'{host}/{self._index}/_doc/'

        try:
            response = await self._session.post(
                url=url,
                data=event
            )
            text = await response.text()
        except aiohttp.ClientError as e:
            raise OutputPluginRuntimeError(
                f'Failed to index event to opensearch ({host}): {e}'
            )

        if response.status != 201:
            raise OutputPluginRuntimeError(
                f'Failed to index event to opensearch ({host}): '
                f'HTTP {response.status} - {text}'
            )

    async def _perform_bulk(self, host: str, bulk_data: str) -> None:
        """Index bulk data to specified host."""
        try:
            response = await self._session.post(
                url=f'{host}/_bulk/',
                data=bulk_data
            )
            text = await response.text()
        except aiohttp.ClientError as e:
            raise OutputPluginRuntimeError(
                f'Failed to perform bulk indexing to opensearch ({host}): {e}'
            )

        if response.status != 200:
            raise OutputPluginRuntimeError(
                f'Failed to perform bulk indexing to opensearch ({host}): '
                f'HTTP {response.status} - {text}'
            )

    async def _write_many(self, events: Iterable[str]) -> None:
        bulks_count = len(self._hosts)
        bulks = [""] * bulks_count

        for i, event in enumerate(events):
            bulk_item = json.dumps({"index": {"_index": self._index}}) + '\n'
            bulk_item += event + '\n'

            bulks[i % bulks_count] += bulk_item

        results = await asyncio.gather(
            *[
                self._perform_bulk(host=host, bulk_data=bulk_data)
                for host, bulk_data in zip(self._hosts, bulks)
            ],
            return_exceptions=True
        )

        successful_count = 0
        for result in results:
            if isinstance(result, OutputPluginRuntimeError):
                logger.error(str(result))
            else:
                successful_count += 1

        if successful_count < len(results):
            raise OutputPluginRuntimeError(
                'Bulk indexing did not complete with success: only'
                f'{successful_count}/{len(results)} nodes indexed events'
            )


PLUGIN_CLASS = OpensearchOutputPlugin
CONFIG_CLASS = OpensearchOutputConfig
