import os
from string import ascii_letters, digits
from typing import Any

import yaml

CWD = os.path.abspath('.')
PROJECT_DIR = os.path.realpath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '../../'
    )
)
LIBRARY_DIR = os.path.realpath(os.path.join(PROJECT_DIR, 'library'))
TIME_PATTERNS_DIR = os.path.join(LIBRARY_DIR, 'time_patterns')


def resolve_path(path: str) -> str:
    """Transform relative path to absolute. If absolute path is given,
    then it is returned unchanged.
    """
    if os.path.isabs(path):
        return path

    return os.path.join(CWD, path)


def load_object_from_yaml(filepath: str) -> Any:
    """Load yaml file and return its content as object."""
    with open(resolve_path(filepath)) as f:
        content = f.read()

    return yaml.load(content, yaml.Loader)


def save_object_as_yaml(data: Any, filepath) -> None:
    """Save python object as yaml file."""
    with open(filepath, 'w') as f:
        yaml.dump(data, f)


def validate_yaml_filename(filename: str) -> tuple[bool, str]:
    """Check if provided filename is in format <basename>.[yml|yaml]
    where basename consists only of ascii letters, digits and
    underscores. Raise `ValueError` on validation failure.
    """
    filename, ext = os.path.splitext(filename)

    restricted_symbols = set(filename) - set(ascii_letters + digits + '_')
    if restricted_symbols:
        raise ValueError(
            'Only letters, digits and underscore are allowed in file basename'
        )

    if ext not in ['.yml', '.yaml']:
        raise ValueError('Only yml and yaml extensions are allowed')
