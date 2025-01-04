from ipaddress import IPv4Address

from pydantic import Field, IPvAnyAddress

from eventum.plugins.input.base.config import InputPluginConfig


class HttpInputPluginConfig(
    InputPluginConfig,
    frozen=True
):
    """Configuration for `http` input plugin.

    Attributes
    ----------
    ip : IPvAnyAddress, default='0.0.0.0'
        Bind IP address

    port : int
        Bind port
    """
    ip: IPvAnyAddress = Field(
        default=IPv4Address('0.0.0.0'),
        validate_default=True
    )
    port: int = Field(ge=1)
