import itertools
import json
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
        self._initialize_ssl_context()

        self._session: aiohttp.ClientSession

    def _initialize_ssl_context(self) -> None:
        """Initialize SSL context for session."""
        if not self._config.verify:
            self._ssl_context.check_hostname = False
            self._ssl_context.verify_mode = ssl.CERT_NONE

        if self._config.ca_cert is not None:
            self._load_ca_cert(self._config.ca_cert)

            self._logger.info(
                'CA certificate is loaded',
                file_path=self._config.ca_cert
            )

        if (
            self._config.client_cert is not None
            and self._config.client_cert_key is not None
        ):
            self._load_client_cert(
                cert_path=self._config.client_cert,
                key_path=self._config.client_cert_key,
            )
            self._logger.info(
                'Client certificate chain is loaded',
                cert_file_path=self._config.client_cert,
                key_file_path=self._config.client_cert_key
            )

    def _load_ca_cert(self, path: str) -> None:
        """Load CA certificate from file.

        Parameters
        ----------
        path : str
            Path to CA certificate
        """
        if not os.path.exists(path):
            raise PluginConfigurationError(
                'CA certificate file does not exist',
                context=dict(
                    self.instance_info,
                    file_path=path
                )
            )

        try:
            self._ssl_context.load_verify_locations(cafile=path)
        except ssl.SSLError as e:
            raise PluginConfigurationError(
                'Failed to load CA certificate',
                context=dict(
                    self.instance_info,
                    reason=str(e),
                    file_path=path
                )
            ) from e

    def _load_client_cert(self, cert_path: str, key_path: str) -> None:
        """Load client cert and key from files.

        Parameters
        ----------
        cert_path : str
            Path to client certificate

        key_path : str
            Path to client certificate key
        """
        if not os.path.exists(cert_path):
            raise PluginConfigurationError(
                'Client certificate file does not exist',
                context=dict(
                    self.instance_info,
                    file_path=cert_path
                )
            )

        if not os.path.exists(key_path):
            raise PluginConfigurationError(
                'Client certificate key file does not exist',
                context=dict(
                    self.instance_info,
                    file_path=key_path
                )
            )

        try:
            self._ssl_context.load_cert_chain(
                certfile=cert_path,
                keyfile=key_path
            )
        except ssl.SSLError as e:
            raise PluginConfigurationError(
                'Failed to load client certificate chain',
                context=dict(
                    self.instance_info,
                    reason=str(e),
                    cert_file_path=cert_path,
                    key_file_path=key_path
                )
            ) from e

    async def _open(self) -> None:
        self._session = aiohttp.ClientSession(
            auth=aiohttp.BasicAuth(
                self._config.username,
                self._config.password
            ),
            connector=aiohttp.TCPConnector(ssl=self._ssl_context),
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            conn_timeout=self._config.connect_timeout,
            read_timeout=self._config.request_timeout
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
                url=f'{host}/_bulk',
                data=self._create_bulk_data(events)
            )
            text = await response.text()
        except aiohttp.ClientError as e:
            raise PluginRuntimeError(
                'Failed to perform bulk indexing',
                context=dict(
                    self.instance_info,
                    reason=str(e),
                    url=host
                )
            ) from e

        if response.status != 200:
            raise PluginRuntimeError(
                'Failed to perform bulk indexing',
                context=dict(
                    self.instance_info,
                    reason=text,
                    http_status=response.status,
                    url=host
                )
            )

        try:
            result = json.loads(text)
        except json.JSONDecodeError as e:
            raise PluginRuntimeError(
                'Failed to decode bulk response',
                context=dict(
                    self.instance_info,
                    reason=str(e),
                    url=host
                )
            ) from None

        try:
            errors = self._get_bulk_response_errors(result)
        except ValueError as e:
            raise PluginRuntimeError(
                'Failed to process bulk response',
                context=dict(
                    self.instance_info,
                    reason=str(e),
                    url=host
                )
            ) from None

        if errors:
            await self._logger.aerror(
                'Some events were not indexed using bulk request',
                reason=f'First 3/{len(errors)} are shown: {errors[:3]}'
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
                'Failed to post document',
                context=dict(
                    self.instance_info,
                    reason=str(e),
                    url=host
                )
            ) from e

        if response.status != 201:
            raise PluginRuntimeError(
                'Failed to post document',
                context=dict(
                    self.instance_info,
                    reason=text,
                    http_status=response.status,
                    url=host
                )
            )

        return 1

    async def _write(self, events: Sequence[str]) -> int:
        formatted_events = await self._loop.run_in_executor(
            executor=None,
            func=lambda: format_events(
                events=events,
                format=Format.NDJSON,
                ignore_errors=True,
                error_callback=lambda event, err: self._logger.error(
                    'Failed to format event as json document',
                    reason=str(err),
                    original_event=event
                )
            )
        )

        if not formatted_events:
            return 0

        if len(formatted_events) > 1:
            return await self._post_bulk(formatted_events)
        else:
            return await self._post_doc(formatted_events[0])
