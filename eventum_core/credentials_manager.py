import os

import keyrings.cryptfile.cryptfile as crypt  # type: ignore[import-untyped]


def get_credentials_manager() -> crypt.CryptFileKeyring:
    """Get common credentials manager."""
    manager = crypt.CryptFileKeyring()

    key = os.getenv("KEYRING_CRYPTFILE_PASSWORD")
    if key is not None:
        manager.keyring_key = key

    return manager
