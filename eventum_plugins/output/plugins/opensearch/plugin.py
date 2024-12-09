import itertools
import json
import logging
import os
import ssl
from typing import Iterable, Iterator, Sequence

import aiohttp

from eventum_plugins.exceptions import (PluginConfigurationError,
                                        PluginRuntimeError)
from eventum_plugins.output.base.plugin import OutputPlugin, OutputPluginParams
from eventum_plugins.output.formatters import Format, format_events
from eventum_plugins.output.plugins.opensearch.config import \
    OpensearchOutputPluginConfig

logger = logging.getLogger(__name__)


class OpensearchOutputPlugin(
    OutputPlugin[OpensearchOutputPluginConfig, OutputPluginParams]
):
    """Output plugin for indexing events to OpenSearch."""

    def __init__(
        self,
        config: OpensearchOutputPluginConfig,
        params: OutputPluginParams
    ) -> None:
        super().__init__(config, params)

        self._hosts = self._choose_host()
        self._ssl_context = ssl.create_default_context()

        if not config.verify_ssl:
            self._ssl_context.check_hostname = False
            self._ssl_context.verify_mode = ssl.CERT_NONE

        if config.ca_cert_path is not None:
            if not os.path.exists(config.ca_cert_path):
                raise PluginConfigurationError(
                    f'Failed to find CA certificate in "{config.ca_cert_path}"'
                )

            try:
                self._ssl_context.load_verify_locations(
                    cafile=config.ca_cert_path)
            except ssl.SSLError as e:
                raise PluginConfigurationError(
                    f'Failed to load CA certificate: {e}'
                ) from None

        self._session: aiohttp.ClientSession

    async def _open(self) -> None:
        self._session = aiohttp.ClientSession(
            auth=aiohttp.BasicAuth(self._config.user, self._config.password),
            connector=aiohttp.TCPConnector(ssl=self._ssl_context),
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        )

    async def _close(self) -> None:
        await self._session.close()

    def _choose_host(self) -> Iterator[str]:
        """Choose host from nodes list specified in config.

        Yields
        ------
        str
            Chosen host
        """
        for node in itertools.cycle(self._config.hosts):
            yield node

    def _create_bulk_data(self, events: Iterable[str]) -> str:
        """Create body for bulk request. It is expected that events
        are already formatted as single line serialized json document.

        Parameters
        ----------
        events : Iterable[str]
            Events for bulk request

        Returns
        -------
        str
            Bulk data for request body
        """
        bulk_lines = []
        operation = json.dumps({'index': {'_index': self._config.index}})

        for event in events:
            bulk_lines.append(operation)
            bulk_lines.append(event)

        return '\n'.join(bulk_lines) + '\n'

    @staticmethod
    def _get_bulk_response_errors(bulk_response: dict) -> list[str]:
        """Get list of errors in bulk response.
        Parameters
        ----------
        bulk_response : dict
            Original response of bulk request

        Return
        ------
        list[str]
            List of error messages

        Raises
        ------
        ValueError
            If bulk response has invalid structure
        """
        if 'errors' not in bulk_response or 'items' not in bulk_response:
            raise ValueError(
                'Invalid bulk response structure, '
                '"errors" and "items" fields must be presented'
            )

        has_errors = bulk_response['errors']

        if not has_errors:
            return []

        items = bulk_response['items']

        errors = []
        try:
            for item in items:
                info = item['index']
                if 'error' in info:
                    error = info['error']
                    errors.append(f'{error["type"]} - {error["reason"]}')
        except KeyError:
            raise ValueError(
                'Invalid bulk response structure, '
                '"type" and "reason" must be presented in error info'
            )

        return errors

    async def _post_bulk(self, events: Sequence[str]) -> int:
        """Index events using `_bulk` API.

        Parameters
        ----------
        events : Sequence[str]
            Events to index

        Returns
        -------
        int
            Number of successfully written events

        Raises
        ------
        PluginRuntimeError
            If events indexing fails
        """
        host = next(self._hosts)

        try:
            response = await self._session.post(
                url=f'{host}/_bulk/',
                data=self._create_bulk_data(events)
            )
            text = await response.text()
        except aiohttp.ClientError as e:
            raise PluginRuntimeError(
                f'Failed to perform bulk indexing using node "{host}": {e}'
            )

        if response.status != 200:
            raise PluginRuntimeError(
                f'Failed to perform bulk indexing using node "{host}": '
                f'HTTP {response.status} - {text}'
            )

        try:
            result = json.loads(text)
        except json.JSONDecodeError as e:
            raise PluginRuntimeError(
                f'Failed to decode response from node "{host}": {e}'
            )

        try:
            errors = self._get_bulk_response_errors(result)
        except ValueError as e:
            raise PluginRuntimeError(
                f'Failed to process bulk response from node "{host}": {e}'
            )

        if errors:
            logger.error(
                f'{len(errors)} events was not indexed due to error, '
                f'first 3 errors are shown: {errors[:3]}'
            )

        return len(events) - len(errors)

    async def _post_doc(self, event: str) -> int:
        """Index event using `_doc` API.

        Parameters
        ----------
        event : str
            Event to index

        Returns
        -------
        int
            Number of successfully written events (always 1)

        Raises
        ------
        PluginRuntimeError
            If events indexing fails
        """
        host = next(self._hosts)

        try:
            response = await self._session.post(
                url=f'{host}/{self._config.index}/_doc',
                data=event
            )
            text = await response.text()
        except aiohttp.ClientError as e:
            raise PluginRuntimeError(
                f'Failed to perform bulk indexing using node "{host}": {e}'
            )

        if response.status != 201:
            raise PluginRuntimeError(
                f'Failed to post document using node "{host}": '
                f'HTTP {response.status} - {text}'
            )

        return 1

    async def _write(self, events: Sequence[str]) -> int:
        formatted_events = await self._loop.run_in_executor(
            executor=None,
            func=lambda: format_events(
                events=events,
                format=Format.NDJSON,
                ignore_errors=True,
                error_callback=lambda e: logger.warning(
                    f'Failed to format event as json document: {e}',
                )
            )
        )

        if not formatted_events:
            return 0

        if len(formatted_events) > 1:
            return await self._post_bulk(formatted_events)
        else:
            return await self._post_doc(formatted_events[0])
