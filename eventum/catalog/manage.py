import os
from dataclasses import asdict
from glob import glob
from dacite import DaciteError, from_dict

from yaml import YAMLError
from eventum.studio import models

from eventum.studio.models import TimePatternConfig
from eventum.utils.fs import (load_object_from_yaml, save_object_as_yaml,
                              validate_yaml_filename)

LIBRARY_DIR = os.path.dirname(os.path.abspath(__file__))
TIME_PATTERNS_DIR = os.path.join(LIBRARY_DIR, 'time_patterns')


class CatalogError(Exception):
    """Base exception for all catalog manipulation errors."""


class CatalogUpdateError(CatalogError):
    """Exception for errors related with creation, changing
    or deleting content.
    """


class CatalogReadError(CatalogError):
    """Exception for errors related with reading content."""


def get_timepattern_filenames() -> list[str]:
    """Get all filenames of currently existing timepatterns in catalog."""
    return glob(pathname='*.y*ml', root_dir=TIME_PATTERNS_DIR)


def save_timepattern(
    pattern_config: TimePatternConfig,
    filename: str,
    overwrite: bool = False
):
    """Save timepattern in catalog. Raise `CatalogUpdateError` on failure."""
    try:
        validate_yaml_filename(filename)
    except ValueError as e:
        raise CatalogUpdateError(str(e)) from e

    filepath = os.path.join(TIME_PATTERNS_DIR, filename)
    if overwrite is False and os.path.exists(filepath):
        raise CatalogUpdateError('Time patter already exists in catalog')

    try:
        save_object_as_yaml(
            data=asdict(pattern_config),
            filepath=filepath
        )
    except (OSError, YAMLError) as e:
        raise CatalogUpdateError(str(e)) from e


def load_timepattern(filename: str) -> TimePatternConfig:
    """Load specified time pattern from catalog and return its
    dataclass representation. Raise `CatalogReadError` on failure.
    """
    try:
        data = load_object_from_yaml(
            os.path.join(TIME_PATTERNS_DIR, filename)
        )
    except (OSError, YAMLError) as e:
        raise CatalogReadError(str(e)) from e

    try:
        return from_dict(
            data_class=models.TimePatternConfig,
            data=data
        )
    except DaciteError as e:
        raise CatalogReadError(str(e)) from e
