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
    """
    host: str = Field(
        default='0.0.0.0',
        min_length=1,
        validate_default=True
    )
    port: int = Field(ge=1)
