
import os

from pydantic import Field, field_validator

from eventum_plugins.output.base.config import OutputPluginConfig


class OpensearchOutputPluginConfig(OutputPluginConfig, frozen=True):
    """Configuration for `opensearch` output plugin.

    Parameters
    ----------
    hosts: list[str]
        Opensearch cluster nodes that will be used for indexing events,
        specifying more than one nodes allows for load balancing,
        nodes must be specified in format `https://<host>:<port>`

    username: str
        Username that is used to authenticate to opensearch for indexing
        events

    password: str
        Password for user to authenticate

    index: str
        Index for writing events

    verify_ssl: bool, default=True
        Whether to verify SSL certificate of the cluster nodes when
        connecting to them

    ca_cert_path: str
        Path to additional CA certificate for SSL verification
    """

    hosts: list[str] = Field(min_length=1)
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    index: str = Field(min_length=1)
    verify_ssl: bool = True
    ca_cert_path: str | None = None

    @field_validator('ca_cert_path')
    def validate_ca_cert_path(cls, v: str | None):
        if not isinstance(v, str):
            return v

        if not os.path.isabs(v):
            raise ValueError('Path must be absolute')
