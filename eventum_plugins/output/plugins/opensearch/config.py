import os

from pydantic import Field, field_validator, model_validator, HttpUrl

from eventum_plugins.output.base.config import OutputPluginConfig


class OpensearchOutputPluginConfig(OutputPluginConfig, frozen=True):
    """Configuration for `opensearch` output plugin.

    Parameters
    ----------
    hosts: list[HttpUrl]
        Opensearch cluster nodes that will be used for indexing events,
        specifying more than one nodes allows for load balancing,
        nodes must be specified in format `https://<host>:<port>`

    username: str
        Username that is used to authenticate to Opensearch for indexing
        events

    password: str
        Password for user to authenticate

    index: str
        Index for writing events

    connect_timeout : int, default=10
        Connection timeout in seconds

    request_timeout : int, default=300
        Requests timeout in seconds

    verify: bool, default=True
        Whether to verify SSL certificate of the cluster nodes when
        connecting to them

    ca_cert: str | None, default=None
        Absolute path to CA certificate

    client_cert: str | None, default=None
        Absolute path to client certificate

    client_cert_key: str | None, default=None
        Absolute path to client certificate key

    proxy_url : HttpUrl
        HTTP(S) proxy address
    """
    hosts: list[HttpUrl] = Field(min_length=1)
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    index: str = Field(min_length=1)
    connect_timeout: int = Field(default=10, ge=1)
    request_timeout: int = Field(default=300, ge=1)
    verify: bool = Field(default=False)
    ca_cert: str | None = Field(default=None, min_length=1)
    client_cert: str | None = Field(default=None, min_length=1)
    client_cert_key: str | None = Field(default=None, min_length=1)
    proxy_url: HttpUrl | None = Field(default=None)

    @field_validator('ca_cert', 'client_cert', 'client_cert_key')
    def validate_absolute_paths(cls, v: str | None):
        if not isinstance(v, str):
            return v

        if not os.path.isabs(v):
            raise ValueError('Path must be absolute')

        return v

    @model_validator(mode='after')
    def validate_client_cert(self):
        if self.client_cert is None and self.client_cert_key is None:
            return self

        if self.client_cert is None or self.client_cert_key is None:
            raise ValueError(
                'Client certificate and key must be provided together'
            )

        return self
