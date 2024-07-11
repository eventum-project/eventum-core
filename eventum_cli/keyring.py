import os
from functools import lru_cache

import keyrings.cryptfile.cryptfile as crypt  # type: ignore[import-untyped]
from pwinput import pwinput  # type: ignore[import-untyped]

KEYRING_PASS_ENV_VAR = 'EVENTUM_KEYRING_PASSWORD'
KEYRING_SERVICE_NAME = 'eventum'


@lru_cache
def get_keyring_password() -> str:
    """Get password for keyring from environment variable or prompt it
    interactively otherwise.
    """
    return (
        os.getenv(KEYRING_PASS_ENV_VAR)
        or pwinput('Password for keyring: ')
    )


def get_secret(key: str) -> str:
    """Get secret from keyring for specified `key`. If key is not
    found in keyring or some error occurs during obtaining data from
    keyring `ValueError` is raised.
    """

    keyring = crypt.CryptFileKeyring()
    keyring.keyring_key = get_keyring_password()

    return keyring.get_password(
        service=KEYRING_SERVICE_NAME,
        username=key
    )


def set_secret(key: str, value: str) -> None:
    """Set secret `value` to keyring under specified `key`. If key is
    already found in keyring, then it will be overwritten.
    """

    keyring = crypt.CryptFileKeyring()
    keyring.keyring_key = get_keyring_password()

    keyring.set_password(
        service=KEYRING_SERVICE_NAME,
        username=key,
        password=value
    )


def remove_secret(key: str) -> None:
    """Remove secret with specified `key` from keyring."""

    keyring = crypt.CryptFileKeyring()
    keyring.keyring_key = get_keyring_password()

    keyring.delete_password(
        service=KEYRING_SERVICE_NAME,
        username=key,
    )
