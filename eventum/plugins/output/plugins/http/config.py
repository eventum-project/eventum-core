import os
from typing import Any, Literal

from pydantic import Field, HttpUrl, field_validator, model_validator

from eventum.plugins.output.base.config import OutputPluginConfig
from eventum.plugins.output.fields import (Format, FormatterConfigT,
                                           JsonFormatterConfig)


class HttpOutputPluginConfig(OutputPluginConfig, frozen=True):
    """Configuration for `http` output plugin.

    Parameters
    ----------
    url : HttpUrl
        URL to use for requests

    method : Literal[\
        'GET', 'HEAD', 'OPTIONS', 'POST', 'PUT', 'PATCH', 'DELETE'\
    ], default='POST'
        HTTP method to use for requests

    success_code : int,default=201
        Expected HTTP response code, if server returns other code, then
        it is considered as an error

    headers: dict[str, Any], default={}
        Request headers

    username: str | None, default=None
        Username that is used to authenticate

    password: str | None, default=None
        Password for user to authenticate

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

    Notes
    -----
    By default one line JSON batch formatter is used for events
    """
    url: HttpUrl
    method: Literal[
        'GET', 'HEAD', 'OPTIONS', 'POST', 'PUT', 'PATCH', 'DELETE'
    ] = Field(default='POST')
    success_code: int = Field(default=201, ge=100)
    headers: dict[str, Any] = Field(default_factory=dict)
    username: str | None = Field(default=None, min_length=1)
    password: str | None = Field(default=None, min_length=1)
    connect_timeout: int = Field(default=10, ge=1)
    request_timeout: int = Field(default=300, ge=1)
    verify: bool = Field(default=False)
    ca_cert: str | None = Field(default=None, min_length=1)
    client_cert: str | None = Field(default=None, min_length=1)
    client_cert_key: str | None = Field(default=None, min_length=1)
    proxy_url: HttpUrl | None = Field(default=None)
    formatter: FormatterConfigT = Field(
        default_factory=lambda: JsonFormatterConfig(
            format=Format.JSON_BATCH,
            indent=0
        ),
        validate_default=True,
        discriminator='format'
    )

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
