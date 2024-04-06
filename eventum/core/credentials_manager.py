import os
from keyrings.cryptfile.cryptfile import CryptFileKeyring


class CredentialsManagerError(Exception):
    """Exception for all credentials management errors."""


def get_credentials_manager() -> CryptFileKeyring:
    """Get common credentials manager."""
    manager = CryptFileKeyring()

    key = os.getenv("KEYRING_CRYPTFILE_PASSWORD")
    if key is None:
        raise CredentialsManagerError(
            'Environment variable "KEYRING_CRYPTFILE_PASSWORD" is not set'
        )

    manager.keyring_key = key

    return manager
