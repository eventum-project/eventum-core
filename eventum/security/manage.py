import os
from functools import lru_cache

import keyrings.cryptfile.cryptfile as crypt  # type: ignore[import-untyped]
import structlog

DEFAULT_PASSWORD = 'eventum'
KEYRING_PASS_ENV_VAR = 'EVENTUM_KEYRING_PASSWORD'
KEYRING_SERVICE_NAME = 'eventum'


logger = structlog.stdlib.get_logger()


@lru_cache
def get_keyring_password() -> str:
    """Get password for keyring from environment variable or return
    default password.

    Returns
    -------
    str
        Password for keyring
    """
    password = os.getenv(KEYRING_PASS_ENV_VAR)

    if password is None:
        password = DEFAULT_PASSWORD
        logger.warning(
            'Environment variable with keyring password is not set, '
            'using default password for keyring'
        )

    return password


def get_secret(name: str) -> str:
    """Get secret from keyring.

    Parameters
    ----------
    name : str
        Name of the secret

    Returns
    -------
    str
        Secret

    Raises
    ------
    ValueError
        If name of secret is blank or missing in keyring

    EnvironmentError
        If any error occurs during obtaining secret from keyring
    """
    if not name:
        raise ValueError('Name of secret cannot be blank')

    keyring = crypt.CryptFileKeyring()
    keyring.keyring_key = get_keyring_password()

    try:
        secret = keyring.get_password(
            service=KEYRING_SERVICE_NAME,
            username=name
        )
    except Exception as e:
        raise EnvironmentError(str(e))

    if secret is None:
        raise ValueError('Secret is missing')

    return secret


def set_secret(name: str, value: str) -> None:
    """Set secret to keyring under specified name.

    Parameters
    ----------
    name : str
        Name of the secret

    value : str
        Value of the secret

    Raises
    ------
    ValueError
        If name or value of secret are blank

    EnvironmentError
        If any error occurs during setting secret to keyring
    """
    if not name or not value:
        raise ValueError('Name and value of secret cannot be empty')

    keyring = crypt.CryptFileKeyring()
    keyring.keyring_key = get_keyring_password()

    try:
        keyring.set_password(               # type: ignore
            system=KEYRING_SERVICE_NAME,
            username=name,
            password=value
        )
    except Exception as e:
        raise EnvironmentError(str(e))


def remove_secret(name: str) -> None:
    """Remove secret from keyring.

    Parameters
    ----------
    name : str
        Name of the secret to remove

    Raises
    ------
    ValueError
        If name of secret is blank

    EnvironmentError
        If any error occurs during removing secret from keyring
    """
    if not name:
        raise ValueError('Name of secret cannot be blank')

    keyring = crypt.CryptFileKeyring()
    keyring.keyring_key = get_keyring_password()

    try:
        keyring.delete_password(
            service=KEYRING_SERVICE_NAME,
            username=name,
        )
    except Exception as e:
        raise EnvironmentError(str(e))
