import os

import pytest

from eventum.core.credentials_manager import get_credentials_manager


def test_non_interactive_password():
    os.environ['KEYRING_CRYPTFILE_PASSWORD'] = 'incorrect pass'

    with pytest.raises(ValueError):
        get_credentials_manager()
