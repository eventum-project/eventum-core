import os

from keyrings.cryptfile.cryptfile import CryptFileKeyring  # type: ignore


def get_credentials_manager() -> CryptFileKeyring:
    """Get common credentials manager."""
    manager = CryptFileKeyring()

    key = os.getenv("KEYRING_CRYPTFILE_PASSWORD")
    if key is not None:
        manager.keyring_key = key

    return manager
