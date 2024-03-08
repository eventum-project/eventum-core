import os
from glob import glob

from yaml import YAMLError
from pydantic import ValidationError

from eventum.core.models.time_pattern_config import TimePatternConfig
from eventum.utils.fs import (load_object_from_yaml, save_object_as_yaml,
                              validate_yaml_filename)

REPOSITORY_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TIME_PATTERNS_DIR = os.path.join(REPOSITORY_BASE_DIR, 'time_patterns')


class RepositoryError(Exception):
    """Base exception for all content repository manipulation errors."""


class RepositoryUpdateError(RepositoryError):
    """Exception for errors related with creation, changing
    or deleting content.
    """


class RepositoryReadError(RepositoryError):
    """Exception for errors related with reading content."""


def get_time_pattern_filenames() -> list[str]:
    """Get all filenames of currently existing time patterns in repository."""
    return glob(pathname='*.y*ml', root_dir=TIME_PATTERNS_DIR)


def save_time_pattern(
    pattern_config: TimePatternConfig,
    filename: str,
    overwrite: bool = False
):
    """Save time pattern in repository. Raise `RepositoryUpdateError`
    on failure.
    """
    try:
        validate_yaml_filename(filename)
    except ValueError as e:
        raise RepositoryUpdateError(str(e)) from e

    filepath = os.path.join(TIME_PATTERNS_DIR, filename)
    if overwrite is False and os.path.exists(filepath):
        raise RepositoryUpdateError(
            'Time pattern already exists in repository'
            )

    try:
        save_object_as_yaml(
            data=pattern_config.model_dump(mode='json'),
            filepath=filepath
        )
    except (OSError, YAMLError) as e:
        raise RepositoryUpdateError(str(e)) from e


def load_time_pattern(filename: str) -> TimePatternConfig:
    """Load specified time pattern from repository and return its
    model representation. Raise `RepositoryReadError` on failure.
    """
    try:
        data = load_object_from_yaml(
            os.path.join(TIME_PATTERNS_DIR, filename)
        )
    except (OSError, YAMLError) as e:
        raise RepositoryReadError(str(e)) from e

    try:
        return TimePatternConfig.model_validate(data)
    except ValidationError as e:
        raise RepositoryReadError(str(e)) from e
