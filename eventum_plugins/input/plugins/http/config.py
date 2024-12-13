from pydantic import Field

from eventum_plugins.input.base.config import InputPluginConfig
from eventum_plugins.input.fields import IPv4AddressStr


class HttpInputPluginConfig(
    InputPluginConfig,
    frozen=True
):
    """Configuration for `http` input plugin.

    Attributes
    ----------
    ip : str, default='0.0.0.0'
        IP to listen

    port : int
        Port to listen
    """
    ip: IPv4AddressStr = Field(default='0.0.0.0')
    port: int = Field(ge=1)
