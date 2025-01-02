import json
import re
from collections import defaultdict
from enum import StrEnum
from typing import Any, assert_never

from jinja2 import BaseLoader, Environment, TemplateError

from eventum_cli.keyring import get_secret


class TokenValueSource(StrEnum):
    PARAMS = 'params'
    SECRETS = 'secrets'


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
                'token name should be in format <source>.<key> where '
                f'source can be one of {available_sources}'
            )

        source, key = parts

        if source not in available_sources:
            raise ValueError(
                f'Failed to parse token "{token}": '
                f'source part should be one of {available_sources} '
                f'but got "{source}"'
            )

        match TokenValueSource(source):
            case TokenValueSource.PARAMS:
                if key not in params:
                    raise ValueError(
                        f'Parameter "{key}" expected for token "{token}" '
                        'in config'
                    )
                value = params[key]
            case TokenValueSource.SECRETS:
                value = get_secret(key=key)
                if value is None:
                    raise ValueError(
                        f'Key "{key}" not found in keyring'
                    )
            case val:
                assert_never(val)

        source_to_tokens_map[source][key] = value

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
