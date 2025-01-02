import itertools
import json
from typing import Iterable, Iterator, Sequence

import aiohttp
from yarl import URL

from eventum.plugins.exceptions import (PluginConfigurationError,
                                        PluginRuntimeError)
from eventum.plugins.output.base.plugin import OutputPlugin, OutputPluginParams
from eventum.plugins.output.http_session import (create_session,
                                                 create_ssl_context)
from eventum.plugins.output.plugins.opensearch.config import \
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

        try:
            self._ssl_context = create_ssl_context(
                verify=config.verify,
                ca_cert=config.ca_cert,
                client_cert=config.client_cert,
                client_key=config.client_cert_key
            )
        except OSError as e:
            raise PluginConfigurationError(
                'Failed to create SSL context',
                context=dict(self.instance_info, reason=str(e))
            )

        self._session: aiohttp.ClientSession

    async def _open(self) -> None:
        self._session = create_session(
            ssl_context=self._ssl_context,
            username=self._config.username,
            password=self._config.password,
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            connect_timeout=self._config.connect_timeout,
            request_timeout=self._config.request_timeout
        )

    async def _close(self) -> None:
        await self._session.close()

    def _choose_host(self) -> Iterator[URL]:
        """Choose host from hosts list specified in config.

        Yields
        ------
        yarl.URL
            Chosen host URL
        """
        host_urls = [URL(str(host)) for host in self._config.hosts]

        for host in itertools.cycle(host_urls):
            yield host

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
                url=host.with_path('_bulk'),
                data=self._create_bulk_data(events),
                proxy=(
                    str(self._config.proxy_url)
                    if self._config.proxy_url else None
                )
            )
            text = await response.text()
        except aiohttp.ClientError as e:
            raise PluginRuntimeError(
                'Failed to perform bulk indexing',
                context=dict(
                    self.instance_info,
                    reason=str(e),
                    url=host.host
                )
            ) from e

        if response.status != 200:
            raise PluginRuntimeError(
                'Failed to perform bulk indexing',
                context=dict(
                    self.instance_info,
                    reason=text,
                    http_status=response.status,
                    url=host.host
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
                    url=host.host
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
                    url=host.host
                )
            ) from None

        if errors:
            await self._logger.aerror(
                'Some events were not indexed using bulk request',
                reason=f'First 3/{len(errors)} errors are shown: {errors[:3]}'
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
                url=host.with_path(f'{self._config.index}/_doc'),
                data=event,
                proxy=(
                    str(self._config.proxy_url)
                    if self._config.proxy_url else None
                )
            )
            text = await response.text()
        except aiohttp.ClientError as e:
            raise PluginRuntimeError(
                'Failed to post document',
                context=dict(
                    self.instance_info,
                    reason=str(e),
                    url=host.host
                )
            ) from e

        if response.status != 201:
            raise PluginRuntimeError(
                'Failed to post document',
                context=dict(
                    self.instance_info,
                    reason=text,
                    http_status=response.status,
                    url=host.host
                )
            )

        return 1

    async def _write(self, events: Sequence[str]) -> int:
        if len(events) > 1:
            return await self._post_bulk(events)
        else:
            return await self._post_doc(events[0])
