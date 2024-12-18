import ssl
from typing import Any

import aiohttp


def create_ssl_context(
    verify: bool,
    ca_cert: str | None = None,
    client_cert: str | None = None,
    client_key: str | None = None
) -> ssl.SSLContext:
    """Create initialized SSL context.

    Parameters
    ----------
    verify : bool
    ca_cert : str | None, default=None
        Path to CA certificate

    client_cert : str | None, default=None
        Path to client certificate

    client_key : str | None, default=None
        Path to client certificate key

    Returns
    -------
    ssl.SSLContext
        Initialized SSL context

    Raises
    ------
    OSError
        If error occurs during reading certificates

    ValueError:
        If client cert is provided but client key is not or vise versa
    """
    context = ssl.create_default_context()

    if not verify:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

    if ca_cert is not None:
        try:
            context.load_verify_locations(cafile=ca_cert)
        except ssl.SSLError as e:
            raise OSError(f'Invalid CA certificate: {e}') from e
        except OSError as e:
            raise OSError(f'Failed to load CA certificate: {e}') from e

    if client_cert is not None or client_key is not None:
        if client_cert is None or client_key is None:
            raise ValueError(
                'Client certificate and key must be provided together'
            )

        try:
            context.load_cert_chain(certfile=client_cert, keyfile=client_key)
        except ssl.SSLError as e:
            raise OSError(f'Invalid client certificate or key: {e}') from e
        except OSError as e:
            raise OSError(
                f'Failed to load client certificate or key: {e}'
            ) from e

    return context


def create_session(
    ssl_context: ssl.SSLContext | None = None,
    username: str | None = None,
    password: str | None = None,
    headers: dict[str, Any] | None = None,
    connect_timeout: int = 10,
    request_timeout: int = 300

) -> aiohttp.ClientSession:
    """Create client HTTP session with initialized parameters.

    Parameters
    ----------
    ssl_context : ssl.SSLContext | None, default=None
        SSL context for session

    username : str | None, default=None
        Username used in basic auth

    password : str | None, default=None
        Password for user used in basic auth, can be `None` with
        provided `username` (in this case empty string will be used)

    headers : dict[str, Any] | None, default=None
        Headers to set in session

    connect_timeout : int, default=10
        Timeout of connection to host

    request_timeout : int, default=300
        Timeout of requests

    Returns
    -------
    aiohttp.ClientSession
        Initialized client HTTP session
    """
    ssl_context = ssl_context or ssl.create_default_context()

    if username is None:
        auth = None
    else:
        auth = aiohttp.BasicAuth(
            login=username,
            password=password or ""
        )

    if headers is None:
        headers = dict()

    return aiohttp.ClientSession(
        auth=auth,
        connector=aiohttp.TCPConnector(ssl=ssl_context),
        headers=headers,
        timeout=aiohttp.ClientTimeout(
            sock_connect=connect_timeout,
            sock_read=request_timeout
        )
    )
