import json
import os
import re
from collections import defaultdict
from enum import StrEnum
from functools import lru_cache
from typing import Any, assert_never

import keyrings.cryptfile.cryptfile as crypt  # type: ignore[import-untyped]
from jinja2 import BaseLoader, Environment, TemplateError
from pwinput import pwinput  # type: ignore[import-untyped]

KEYRING_PASS_ENV_VAR = 'EVENTUM_KEYRING_PASSWORD'
KEYRING_SERVICE_NAME = 'eventum'


class TokenValueSource(StrEnum):
    PARAMS = 'params'
    SECRETS = 'secrets'


@lru_cache
def get_keyring_password() -> str:
    """Get password for keyring from environment variable or prompt it
    interactively otherwise.
    """
    return (
        os.getenv(KEYRING_PASS_ENV_VAR)
        or pwinput('Password for keyring: ')
    )


def get_secret(name: str) -> str:
    """Get secret from keyring for specified `name`. If name is not
    found in keyring or some error occurs during obtaining data from
    keyring `ValueError` is raised.
    """

    keyring = crypt.CryptFileKeyring()
    keyring.keyring_key = get_keyring_password()

    value = keyring.get_password(
        service=KEYRING_SERVICE_NAME,
        username=name
    )

    if value is None:
        raise ValueError(
            f'Name "{name}" not found for service '
            f'"{KEYRING_SERVICE_NAME}" in keyring'
        )

    return value


def substitute_tokens(content: str, params: dict[str, Any]) -> str:
    tokens = re.findall(
        pattern=r'\${\s*?(\S*?)\s*?}', string=content
    )

    if not tokens:
        return content

    available_sources = tuple(el.value for el in TokenValueSource)
    source_to_tokens_map: dict[str, dict] = defaultdict(lambda: dict())

    for token in tokens:
        parts = token.split('.')
        if len(parts) != 2:
            raise ValueError(
                f'Failed to parse token "{token}" in config: '
                'token name should be in format <source>.<name> where '
                f'source can be one of {available_sources}'
            )

        source, name = parts

        if source not in available_sources:
            raise ValueError(
                f'Failed to parse token "{token}": '
                f'source part should be one of {available_sources} '
                f'but got "{source}"'
            )

        match TokenValueSource(source):
            case TokenValueSource.PARAMS:
                if name not in params:
                    raise ValueError(
                        f'Parameter "{name}" expected for token "{token}" '
                        'in config'
                    )
                value = params[name]
            case TokenValueSource.SECRETS:
                value = get_secret(name=name)
            case val:
                assert_never(val)

        source_to_tokens_map[source][name] = value

    template = Environment(
        loader=BaseLoader(),
        variable_start_string='${',
        variable_end_string='}'
    ).from_string(
        source=content,
        globals=source_to_tokens_map
    )

    try:
        return template.render()
    except TemplateError as e:
        raise ValueError(f'Failed to render config with token values: {e}')
    except json.JSONDecodeError as e:
        raise ValueError(
            f'Failed to decode config after tokens substitution: {e}'
        )
