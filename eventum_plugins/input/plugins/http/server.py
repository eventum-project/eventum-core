
import json
from http.server import BaseHTTPRequestHandler
from typing import Any, Callable

import structlog


class RequestHandler(BaseHTTPRequestHandler):
    _generate_callback: Callable[[int], Any] | None = None
    _stop_callback: Callable[[], Any] | None = None
    _logger = structlog.stdlib.get_logger()

    @classmethod
    def set_generate_callback(cls, callback: Callable[[int], Any]) -> None:
        """Set callback that is called for each `/generate` request.

        Parameters
        ----------
        callback : Callable[[int], Any]
            Callback to call
        """
        cls._generate_callback = callback

    @classmethod
    def set_stop_callback(cls, callback: Callable[[], Any]) -> None:
        """Set callback that is called for `/stop` request.

        Parameters
        ----------
        callback : Callable[[], Any]
            Callback to call
        """
        cls._stop_callback = callback

    @classmethod
    def set_logger(cls, logger: structlog.stdlib.BoundLogger) -> None:
        """Set logger that will be used across class instances.

        Parameters
        ----------
        logger : structlog.stdlib.BoundLogger
            Logger to use
        """
        cls._logger = logger

    def _send_response(self, status: int, message: str | None = None) -> None:
        """Send response back to client.

        Parameters
        ----------
        status : int
            HTTP response code

        message : str
            Response message
        """
        try:
            self.send_response(status)
            self.end_headers()

            if message is not None:
                self.wfile.write(message.encode())
        except OSError as e:
            RequestHandler._logger.error(
                'Failed to send response',
                reason=str(e)
            )

    def _handle_generate(self) -> None:
        """Handle request to `/generate` endpoint."""
        if self.headers.get('Content-Type') != 'application/json':
            self._send_response(400, 'Expected JSON content type')
            return

        # Read and parse JSON
        content_length = int(self.headers.get('Content-Length', 0))
        try:
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)

            count = data['count']
            if not isinstance(count, int):
                raise TypeError()

            if count < 1:
                raise ValueError
        except json.JSONDecodeError:
            self._send_response(400, 'Invalid json data')
            return
        except (TypeError, KeyError):
            self._send_response(400, 'Invalid json schema')
            return
        except ValueError:
            self._send_response(400, 'Number of events must be greater than 0')
            return
        except Exception:
            RequestHandler._logger.exception('Error during processing request')
            self._send_response(500, 'Error during processing request')
            return

        RequestHandler._logger.debug(
            'Calling "generate" callback', count=count
        )
        try:
            if RequestHandler._generate_callback is not None:
                RequestHandler._generate_callback(count)  # type: ignore
        except Exception as e:
            RequestHandler._logger.error(
                'Error occurred during handling "generate" request',
                reason=str(e)
            )
            self._send_response(500, 'Error during generation')
            return

        self._send_response(201, 'Generated')

    def _handle_stop(self) -> None:
        """Handle request to `/stop` endpoint."""
        # response now, because stop callback will shut down the server
        self._send_response(200, 'Stopping')

        RequestHandler._logger.debug('Calling "stop" callback')
        try:
            if RequestHandler._stop_callback is not None:
                RequestHandler._stop_callback()
        except Exception as e:
            RequestHandler._logger.error(
                'Error occurred during handling "stop" request',
                reason=str(e)
            )
            return

    def _handle_404(self) -> None:
        """Handle request to unknown endpoint."""
        self._send_response(404, 'Not found')

    def do_POST(self) -> None:
        match self.path:
            case '/generate':
                self._handle_generate()
            case '/stop':
                self._handle_stop()
            case _:
                self._handle_404()

    def log_message(self, format: str, *args: Any) -> None:
        RequestHandler._logger.info(
            'Request received',
            request_info=format % args,
            address=self.address_string()
        )
