
import json
import logging
from http.server import BaseHTTPRequestHandler
from typing import Any, Callable

logger = logging.getLogger(__name__)


class RequestHandler(BaseHTTPRequestHandler):
    _generate_callback: Callable[[int], Any] | None = None
    _stop_callback: Callable[[], Any] | None = None

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

    def _handle_generate(self) -> None:
        """Handle request to `/generate` endpoint."""
        if self.headers.get('Content-Type') != 'application/json':
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Expected JSON content type')
            return

        # Read and parse JSON
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        error_message = b''
        try:
            data = json.loads(post_data)

            count = data['count']
            if not isinstance(count, int):
                raise TypeError()

            if count < 1:
                raise ValueError
        except json.JSONDecodeError:
            error_message = b'Invalid json data'
        except (TypeError, KeyError):
            error_message = b'Invalid json schema'
        except ValueError:
            error_message = b'Count must be greater than 0'

        if error_message:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(error_message)
            return

        if RequestHandler._generate_callback is not None:
            RequestHandler._generate_callback(count)  # type: ignore

        self.send_response(201)
        self.end_headers()
        self.wfile.write(b'Generated')

    def _handle_stop(self) -> None:
        """Handle request to `/stop` endpoint."""
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Stopped')

        if RequestHandler._stop_callback is not None:
            RequestHandler._stop_callback()

    def _handle_404(self) -> None:
        """Handle request to unknown endpoint."""
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b'Not found')

    def do_POST(self) -> None:
        match self.path:
            case '/generate':
                self._handle_generate()
            case '/stop':
                self._handle_stop()
            case _:
                self._handle_404()

    def log_message(self, format: str, *args: Any) -> None:
        logger.info(f'{self.address_string()} - {format % args}')
