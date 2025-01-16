import os
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class SSLParameters(BaseModel, extra='forbid', frozen=True):
    """SSL parameters.

    Attributes
    ----------
    enabled : bool, default=True
        Whether to enable SSL

    verify_mode : Literal['none', 'optional', 'required'], default='optional'
        Verification mode of SSL connections

    ca_cert: str | None, default=None
        Absolute path to CA certificate

    cert: str | None, default=None
        Absolute path to server certificate

    cert_key: str | None, default=None
        Absolute path to server certificate key
    """
    enabled: bool = Field(default=True, description='Whether to enable SSL')
    verify_mode: Literal['none', 'optional', 'required'] = Field(
        default='optional',
        description='Verification mode of SSL connections'
    )
    ca_cert: str | None = Field(
        default=None,
        min_length=1,
        description='Absolute path to CA certificate'
    )
    cert: str | None = Field(
        default=None,
        min_length=1,
        description='Absolute path to server certificate'
    )
    cert_key: str | None = Field(
        default=None,
        min_length=1,
        description='Absolute path to server certificate key'
    )

    @field_validator('ca_cert', 'server_cert', 'server_cert_key')
    def validate_absolute_paths(cls, v: str | None):
        if not isinstance(v, str):
            return v

        if not os.path.isabs(v):
            raise ValueError('Path must be absolute')

        return v

    @model_validator(mode='after')
    def validate_client_cert(self):
        if self.cert is None and self.cert_key is None:
            return self

        if self.cert is None or self.cert_key is None:
            raise ValueError(
                'Server certificate and key must be provided together'
            )

        return self


class APIParameters(BaseModel, extra='forbid', frozen=True):
    """API parameters.

    Attributes
    ----------
    enabled : bool, default = True
        Whether to enable REST API

    host : str, default='0.0.0.0'
        Bind address for API

    port : int, default=9474
        Bind port for API

    ssl : SSLParameters, default=SSLParameters(...)
        SSL parameters
    """
    enabled: bool = Field(
        default=True,
        description='Whether to enable REST API'
    )
    host: str = Field(
        default='0.0.0.0',
        min_length=1,
        description='Bind address for API'
    )
    port: int = Field(
        default=9474,
        ge=1,
        description='Bind port for API'
    )
    ssl: SSLParameters = Field(
        default_factory=lambda: SSLParameters(),
        description='SSL parameters'
    )
