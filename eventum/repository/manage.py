import os
from glob import glob

from jinja2 import Environment, FileSystemLoader

from eventum.core.models.time_pattern_config import TimePatternConfig
from eventum.utils.fs import (load_object_from_yaml, load_sample_from_csv,
                              save_object_as_yaml, validate_yaml_filename)
from pydantic import ValidationError
from yaml import YAMLError

REPOSITORY_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TIME_PATTERNS_DIR = os.path.join(REPOSITORY_BASE_DIR, 'time_patterns')
CSV_SAMPLES_DIR = os.path.join(REPOSITORY_BASE_DIR, 'samples')
EVENT_TEMPLATES_DIR = os.path.join(REPOSITORY_BASE_DIR, 'templates')


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


def load_csv_sample(filename: str, delimiter: str = ',') -> list[tuple[str]]:
    """Load specified csv sample from repository and return it as list
    of tuples. Raise `RepositoryReadError` on failure.
    """
    try:
        return load_sample_from_csv(
            filepath=os.path.join(CSV_SAMPLES_DIR, filename),
            delimiter=delimiter
        )
    except OSError as e:
        raise RepositoryReadError(str(e)) from e


def get_templates_environment() -> Environment:
    """Get basic jinja `Environment` instance with adjuster loader."""
    return Environment(
        loader=FileSystemLoader(
            searchpath=EVENT_TEMPLATES_DIR
        ),
        autoescape=False
    )
