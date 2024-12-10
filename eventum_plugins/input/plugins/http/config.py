
from pydantic import Field

from eventum_plugins.input.base.config import InputPluginConfig


class HttpInputPluginConfig(
    InputPluginConfig,
    frozen=True
):
    """Configuration for `http` input plugin.

    Attributes
    ----------
    address : str, default='0.0.0.0'
        Address to listen

    port : int
        Port to listen
    """
    address: str = '0.0.0.0'
    port: int = Field(ge=1)
