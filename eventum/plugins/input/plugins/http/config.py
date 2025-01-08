from pydantic import Field

from eventum.plugins.input.base.config import InputPluginConfig


class HttpInputPluginConfig(
    InputPluginConfig,
    frozen=True
):
    """Configuration for `http` input plugin.

    Attributes
    ----------
    host : str, default='0.0.0.0'
        Bind address

    port : int
        Bind port

    max_pending_requests : int, default=100
        Maximum number of incoming requests to store in queue before
        they are processed, if a request arrives and the queue is full
        a 429 response will be returned immediately
    """
    host: str = Field(
        default='0.0.0.0',
        min_length=1,
        validate_default=True
    )
    port: int = Field(ge=1)
    max_pending_requests: int = Field(default=100, ge=1)
