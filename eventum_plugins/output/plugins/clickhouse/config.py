import os
from typing import Literal

from pydantic import ClickHouseDsn, Field, field_validator, model_validator

from eventum_plugins.output.base.config import OutputPluginConfig


class ClickhouseOutputPluginConfig(OutputPluginConfig, frozen=True):
    """Configuration for `clickhouse` output plugin.

    Parameters
    ----------
    host : str
        The hostname or IP address of the ClickHouse server

    port : int, default=8123
        The ClickHouse HTTP or HTTPS port

    protocol : Literal['http', 'https'], default='http'
        Protocol to use to connect to ClickHouse

    database : str, default='default'
        Database name for inserting events

    table : str
        Table name for inserting events

    username : str, default='default'
        Username that is used to authenticate to ClickHouse

    password : str, default=''
        Password for user to authenticate

    dsn : ClickHouseDsn | None, default=None
        A string in standard DSN (Data Source Name) format, other
        connection values (such as host or username) will be extracted
        from this string if not set otherwise

    connect_timeout : int, default=10
        Connection timeout in seconds

    request_timeout : int, default=300
        Requests timeout in seconds

    client_name : str | None, default=None
        Client name that is prepended to the HTTP User Agent header,
        set this to track client queries in the ClickHouse query log

    verify : bool, default=False
        Whether to verify SSL certificate of ClickHouse server

    ca_cert : str | None, default=None
        Absolute path to CA certificate

    client_cert : str | None, default=None
        Absolute path to client certificate

    client_cert_key : str | None, default=None
        Absolute path to client certificate key

    server_host_name : str | None, default=None
        The ClickHouse server hostname as identified by the CN or SNI
        of its TLS certificate, set this to avoid SSL errors when
        connecting through a proxy or tunnel with a different hostname

    tls_mode : Literal['proxy', 'strict', 'mutual'] | None, default=None
        Mode of TLS behavior, `proxy` and `strict` do not invoke
        ClickHouse mutual TLS connection, but do send client cert and
        key, `mutual` assumes ClickHouse mutual TLS auth with a client
        certificate, default behavior is `mutual`

    Notes
    -----
    To see full documentation:
    https://clickhouse.com/docs/en/integrations/python#connection-arguments
    """
    host: str = Field(min_length=1)
    port: int = Field(default=8123, ge=1)
    protocol: Literal['http', 'https'] = Field(default='http')
    database: str = Field(default='default', min_length=1)
    table: str = Field(min_length=1)
    username: str = Field(default='default', min_length=1)
    password: str = Field(default='')
    dsn: ClickHouseDsn | None = Field(default=None, min_length=1)
    connect_timeout: int = Field(default=10, ge=1)
    request_timeout: int = Field(default=300, ge=1)
    client_name: str | None = Field(default=None, min_length=1)
    verify: bool = Field(default=True)
    ca_cert: str | None = Field(default=None, min_length=1)
    client_cert: str | None = Field(default=None, min_length=1)
    client_cert_key: str | None = Field(default=None, min_length=1)
    server_host_name: str | None = Field(default=None, min_length=1)
    tls_mode: Literal['proxy', 'strict', 'mutual'] | None = Field(default=None)

    @field_validator('ca_cert', 'client_cert', 'client_cert_key')
    def validate_ca_cert(cls, v: str | None):
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
