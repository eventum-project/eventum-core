from concurrent.futures import ThreadPoolExecutor
from http.server import HTTPServer
from threading import Event
from typing import Any, Callable

from numpy import datetime64, full
from numpy.typing import NDArray

from eventum_plugins.exceptions import (PluginConfigurationError,
                                        PluginRuntimeError)
from eventum_plugins.input.base.plugin import InputPlugin, InputPluginParams
from eventum_plugins.input.plugins.http.config import HttpInputPluginConfig
from eventum_plugins.input.plugins.http.server import RequestHandler
from eventum_plugins.input.utils.time_utils import now64


class HttpInputPlugin(InputPlugin[HttpInputPluginConfig]):
    """Input plugin for generating timestamps when HTTP request is
    received.
    """

    def __init__(
        self,
        config: HttpInputPluginConfig,
        params: InputPluginParams
    ) -> None:
        super().__init__(config, params)
        self._request_handler_cls = RequestHandler
        self._stop_event = Event()
        self._stop_event.clear()

        self._logger.debug('Initializing http server')
        try:
            self._server = HTTPServer(
                server_address=(self._config.address, self._config.port),
                RequestHandlerClass=self._request_handler_cls
            )
        except OSError as e:
            raise PluginConfigurationError(
                f'Failed to initialize http server: {e}'
            )

    def _handle_stop(self) -> None:
        """Shut down the server once handler thread notifies via
        condition.
        """
        self._stop_event.wait()
        self._logger.info(
            'Stop request is received, shutting down the http server'
        )
        self._server.shutdown()

    def _generate_sample(
        self,
        on_events: Callable[[NDArray[datetime64]], Any]
    ) -> None:
        self._request_handler_cls.set_logger(self._logger)
        self._request_handler_cls.set_generate_callback(
            callback=lambda count:
            on_events(
                full(
                    shape=count,
                    fill_value=now64(self._timezone),
                    dtype='datetime64[us]'
                )
            )
        )
        self._request_handler_cls.set_stop_callback(
            callback=self._stop_event.set
        )

        self._logger.info(
            'Starting http server',
            address=self._config.address,
            port=self._config.port
        )
        with ThreadPoolExecutor(max_workers=2) as executor:
            stop_future = executor.submit(self._handle_stop)
            serve_future = executor.submit(self._server.serve_forever)

            try:
                serve_future.result()
                self._stop_event.set()
                stop_future.result()
            except Exception as e:
                self._server.server_close()
                raise PluginRuntimeError(
                    f'HTTP server was stopped due to error: {e}'
                )

    def _generate_live(
        self,
        on_events: Callable[[NDArray[datetime64]], Any]
    ) -> None:
        self._generate_sample(on_events)
