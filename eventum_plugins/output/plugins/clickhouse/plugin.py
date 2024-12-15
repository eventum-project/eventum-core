import contextlib
import re
from typing import Sequence

from clickhouse_connect import get_async_client
from clickhouse_connect.driver.asyncclient import AsyncClient
from clickhouse_connect.driver.binding import quote_identifier as quote

from eventum_plugins.exceptions import PluginRuntimeError
from eventum_plugins.output.base.plugin import OutputPlugin, OutputPluginParams
from eventum_plugins.output.formatters import Format, format_events
from eventum_plugins.output.plugins.clickhouse.config import \
    ClickhouseOutputPluginConfig


class ClickhouseOutputPlugin(
    OutputPlugin[ClickhouseOutputPluginConfig, OutputPluginParams]
):
    """Output plugin for indexing events to OpenSearch."""

    def __init__(
        self,
        config: ClickhouseOutputPluginConfig,
        params: OutputPluginParams
    ) -> None:
        super().__init__(config, params)

        self._fq_table_name = '.'.join(
            [quote(config.database), quote(config.table)]
        )

        self._fmt_error_row_pattern = re.compile(r'\(at row (?P<row>\d+)\)')

        self._client: AsyncClient

    async def _open(self) -> None:
        try:
            self._client = await get_async_client(
                host=self._config.host,
                port=self._config.port,
                interface=self._config.protocol,
                database=self._config.database,
                username=self._config.username,
                password=self._config.password,
                dsn=self._config.dsn,
                connect_timeout=self._config.connect_timeout,
                send_receive_timeout=self._config.request_timeout,
                client_name=self._config.client_name,
                verify=self._config.verify,
                ca_cert=self._config.ca_cert,
                client_cert=self._config.client_cert,
                client_cert_key=self._config.client_cert_key,
                server_host_name=self._config.server_host_name,
                tls_mode=self._config.tls_mode,
            )
        except Exception as e:
            raise PluginRuntimeError(
                'Cannot initialize ClickHouse client',
                context=dict(self.instance_info, reason=str(e))
            )

        await self._logger.ainfo('ClickHouse client is initialized')

    async def _close(self) -> None:
        self._client.close

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

        try:
            response = await self._client.raw_insert(
                table=self._fq_table_name,
                insert_block=('\n'.join(formatted_events) + '\n'),
                fmt='JSONEachRow'
            )
        except Exception as e:
            context = dict(
                self.instance_info,
                reason=str(e),
                host=self._config.host
            )

            # try to enrich exception with original (formatted) event
            pos_match = re.search(self._fmt_error_row_pattern, str(e))
            if pos_match is not None:
                row = int(pos_match.group('row'))
                with contextlib.suppress(IndexError):
                    context.update(formatted_event=formatted_events[row - 1])

            raise PluginRuntimeError(
                'Failed to insert events to ClickHouse',
                context=context
            ) from e

        return response.written_rows
