import os

from string import ascii_letters, digits
from typing import Any

import yaml


CWD = os.path.abspath('.')
PROJECT_DIR = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../'))

LIBRARY_DIR = os.path.realpath(os.path.join(PROJECT_DIR, 'library'))
TIME_PATTERNS_DIR = os.path.join(LIBRARY_DIR, 'time_patterns')


def resolve_path(path: str) -> str:
    """Transform relative path to absolute. If absolute path is given,
    then it is return unchanged. The base path for resolving relative
    paths is stored in `BASE_DIR` variable."""

    if os.path.isabs(path):
        return path

    return os.path.join(CWD, path)


def load_object_from_yaml(filepath: str) -> Any:
    """Load yaml file and return its content as object."""

    filepath = resolve_path(filepath)

    if not os.path.exists(filepath):
        raise FileNotFoundError(f'File not found in "{filepath}"')

    with open(filepath) as f:
        content = f.read()

    return yaml.load(content, yaml.Loader)


def save_object_as_yaml(data: Any, filepath) -> None:
    """Save python object as yaml file."""
    with open(filepath, 'w') as f:
        yaml.dump(data, f)


def validate_yaml_filename(filename: str) -> tuple[bool, str]:
    """Check if provided filename is in format <basename>.[yml|yaml].
    Where basename consists only of ascii letters, digits and underscores.
    """
    filename, ext = os.path.splitext(filename)

    restricted_symbols = set(filename) - set(ascii_letters + digits + '_')
    if restricted_symbols:
        return (False, 'Only **letters**, **digits** and **underscore** are allowed in file basename')

    if ext not in ['.yml', '.yaml']:
        return (False, 'Only **yml** and **yaml** extensions are allowed')

    return (True, 'ok')
