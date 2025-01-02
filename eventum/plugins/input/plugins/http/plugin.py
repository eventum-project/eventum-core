from concurrent.futures import ThreadPoolExecutor
from http.server import HTTPServer
from threading import Event

from numpy import full

from eventum.plugins.exceptions import (PluginConfigurationError,
                                        PluginRuntimeError)
from eventum.plugins.input.base.plugin import InputPlugin, InputPluginParams
from eventum.plugins.input.plugins.http.config import HttpInputPluginConfig
from eventum.plugins.input.plugins.http.server import RequestHandler
from eventum.plugins.input.utils.time_utils import now64


class HttpInputPlugin(InputPlugin[HttpInputPluginConfig]):
    """Input plugin for generating timestamps when HTTP request is
    received.

    Notes
    -----
    For generating events a POST request is required with following
    data in body:
    ```json
    {
        "count": x
    }
    ```
    , where `x` - is a number of events to generate
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

        try:
            self._server = HTTPServer(
                server_address=(
                    str(self._config.ip),
                    self._config.port
                ),
                RequestHandlerClass=self._request_handler_cls
            )
        except OSError as e:
            raise PluginConfigurationError(
                'Failed to initialize http server',
                context=dict(self.instance_info, reason=str(e))
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

    def _generate_sample(self) -> None:
        self._request_handler_cls.set_logger(self._logger)
        self._request_handler_cls.set_generate_callback(
            callback=lambda count:
            self._enqueue(
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
            ip=str(self._config.ip),
            port=self._config.port
        )
        with ThreadPoolExecutor(max_workers=2) as executor:
            stop_future = executor.submit(self._handle_stop)
            serve_future = executor.submit(self._server.serve_forever)

            self._logger.info('Waiting for incoming generation requests')
            try:
                serve_future.result()
                self._stop_event.set()
                stop_future.result()
            except Exception as e:
                self._server.server_close()
                raise PluginRuntimeError(
                    'HTTP server was stopped due to error',
                    context=dict(self.instance_info, reason=str(e))
                )

    def _generate_live(self) -> None:
        self._generate_sample()
