import os

from typing import Any

import yaml


BASE_DIR = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../'))
CONTENT_DIR = os.path.realpath(os.path.join(BASE_DIR, '/content'))


def resolve_path(path: str) -> str:
    """Transform relative path to absolute. If absolute path is given,
    then it is return unchanged. The base path for resolving relative
    paths is stored in `BASE_DIR` variable."""

    if os.path.isabs(path):
        return path

    return os.path.join(BASE_DIR, path)


def load_yaml(filepath: str) -> Any:
    """Try to load yaml file and return its content."""

    filepath = resolve_path(filepath)

    if not os.path.exists(filepath):
        raise FileNotFoundError(f'File not found in "{filepath}"')

    with open(filepath) as f:
        content = f.read()

    return yaml.load(content, yaml.Loader)
