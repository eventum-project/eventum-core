from pydantic import Field
from pydantic.networks import IPvAnyAddress

from eventum_plugins.input.base.config import InputPluginConfig


class HttpInputPluginConfig(
    InputPluginConfig,
    frozen=True
):
    """Configuration for `http` input plugin.

    Attributes
    ----------
    ip : IPvAnyAddress, default='0.0.0.0'
        IP to listen

    port : int
        Port to listen
    """
    ip: IPvAnyAddress = Field(default='0.0.0.0')
    port: int = Field(ge=1)
