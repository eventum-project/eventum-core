from concurrent.futures import Future, ThreadPoolExecutor
from queue import Empty, Queue
from typing import Iterator

import uvicorn
from fastapi import FastAPI, HTTPException
from numpy import datetime64
from numpy.typing import NDArray
from pydantic import BaseModel, Field

from eventum.plugins.exceptions import PluginRuntimeError
from eventum.plugins.input.base.plugin import InputPlugin, InputPluginParams
from eventum.plugins.input.plugins.http.config import HttpInputPluginConfig
from eventum.plugins.input.utils.time_utils import now64


class GenerateRequestData(BaseModel, extra='forbid', frozen=True):
    """Data for generate request.

    Attributes
    ----------
    count : int
        Number of events to generate
    """
    count: int = Field(ge=1, description='Number of events to generate')


class HttpInputPlugin(
    InputPlugin[HttpInputPluginConfig, InputPluginParams],
    interactive=True
):
    """Input plugin for generating timestamps when HTTP request is
    received.

    Notes
    -----
    For generating events a POST request is required with following
    data in body:
    ```json
    {"count": 10}
    ```
    , where 10 - is an example number of events to generate
    """

    def __init__(
        self,
        config: HttpInputPluginConfig,
        params: InputPluginParams
    ) -> None:
        super().__init__(config, params)
        self._app = FastAPI(
            docs_url=None,
            redoc_url=None,
            openapi_url=None
        )
        self._app.add_api_route(
            '/generate',
            self._handle_generate,
            methods=['POST'],
            status_code=201,
            response_description='Enqueued'
        )
        self._app.add_api_route(
            '/stop',
            self._handle_stop,
            methods=['POST'],
            status_code=200,
            response_description='Stopped'
        )
        self._server = uvicorn.Server(
            uvicorn.Config(
                self._app,
                host=self._config.host,
                port=self._config.port,
                log_config=None
            )
        )
        self._request_queue: Queue[int] = Queue(
            maxsize=config.max_pending_requests
        )
        self._is_stopping = False

    async def _handle_generate(
        self,
        data: GenerateRequestData
    ) -> None:
        """Handle incoming generate request.

        Parameters
        ----------
        data : GenerateRequest
            Request data

        Raises
        ------
        HTTPException
            429 - If requests queue is full
            403 - If server is stopping
        """
        if self._is_stopping:
            await self._logger.awarning(
                'Generate request is refused due to server is stopping',
                count=data.count
            )
            raise HTTPException(
                status_code=403,
                detail='Server is stopping'
            )

        if self._request_queue.full():
            await self._logger.awarning(
                'Generate request is skipped due to queue is full',
                count=data.count
            )
            raise HTTPException(
                status_code=429,
                detail='Too Many Requests'
            )
        else:
            await self._logger.ainfo(
                'Generate request is received',
                count=data.count
            )
            self._request_queue.put_nowait(data.count)

    async def _handle_stop(self) -> None:
        """Handle incoming stop request."""
        await self._logger.ainfo('Stop request is received')
        self._is_stopping = True
        self._server.should_exit = True

    def _watch_server(self, future: Future) -> None:
        """Watch server execution.

        Parameters
        ----------
        future : Future
            Done future
        """
        try:
            future.result()
        except Exception as e:
            self._is_stopping = True
            self._server.should_exit = True

            raise PluginRuntimeError(
                'Error during server execution',
                context=dict(self.instance_info, reason=str(e))
            )

    def generate(
        self,
        size: int,
        skip_past: bool = True
    ) -> Iterator[NDArray[datetime64]]:
        self._logger.info(
            'Starting http server',
            host=self._config.host,
            port=self._config.port
        )

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self._server.run)
            future.add_done_callback(self._watch_server)

            self._logger.info('Waiting for incoming generation requests')
            while not (self._is_stopping and self._request_queue.empty()):
                try:
                    count = self._request_queue.get(timeout=0.1)
                except Empty:
                    continue

                self._buffer.m_push(
                    timestamp=now64(self._timezone),
                    multiply=count
                )
                yield from self._buffer.read(size, partial=True)
