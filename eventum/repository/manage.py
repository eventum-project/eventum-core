import os
from glob import glob

from jinja2 import Environment, FileSystemLoader
from pydantic import ValidationError
from yaml import YAMLError

from eventum.core.models.application_config import ApplicationConfig
from eventum.core.models.time_pattern_config import TimePatternConfig
from eventum.utils.fs import (load_object_from_yaml, load_sample_from_csv,
                              save_object_as_yaml, validate_jinja_filename,
                              validate_yaml_filename)

REPOSITORY_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TIME_PATTERNS_DIR = os.path.join(REPOSITORY_BASE_DIR, 'time_patterns')
CSV_SAMPLES_DIR = os.path.join(REPOSITORY_BASE_DIR, 'samples')
EVENT_TEMPLATES_DIR = os.path.join(REPOSITORY_BASE_DIR, 'templates')
APPLICATION_CONFIGS_DIR = os.path.join(REPOSITORY_BASE_DIR, 'configs')


class ContentManagementError(Exception):
    """Base exception for all content manipulation errors."""


class ContentUpdateError(ContentManagementError):
    """Exception for errors related with creation, changing
    or deleting content.
    """


class ContentReadError(ContentManagementError):
    """Exception for errors related with reading content."""


def get_time_pattern_filenames() -> list[str]:
    """Get all relative paths of currently existing time patterns in
    repository. Paths are relative to time patterns directory in
    repository.
    """
    return glob(
        pathname='**/*.y*ml',
        root_dir=TIME_PATTERNS_DIR,
        recursive=True
    )


def get_template_filenames() -> list[str]:
    """Get all relative paths of currently existing templates in
    repository. Paths are relative to templates directory in
    repository.
    """
    return glob(
        pathname='**/*.jinja',
        root_dir=EVENT_TEMPLATES_DIR,
        recursive=True
    )


def get_csv_sample_filenames() -> list[str]:
    """Get all relative paths of currently existing samples in
    repository. Paths are relative to templates directory in
    repository.
    """
    return glob(
        pathname='**/*.csv',
        root_dir=CSV_SAMPLES_DIR,
        recursive=True
    )


def save_time_pattern(
    pattern_config: TimePatternConfig,
    path: str,
    overwrite: bool = False
) -> None:
    """Save time pattern in specified path. If path is relative then it
    is saved in repository. Raise `ContentUpdateError` on failure.
    """
    if not os.path.isabs(path):
        path = os.path.join(TIME_PATTERNS_DIR, path)

    _, filename = os.path.split(path)

    try:
        validate_yaml_filename(filename)
    except ValueError as e:
        raise ContentUpdateError(str(e)) from e

    if overwrite is False and os.path.exists(path):
        raise ContentUpdateError(
            'Time pattern already exists in specified location'
        )

    try:
        save_object_as_yaml(
            data=pattern_config.model_dump(mode='json'),
            filepath=path
        )
    except (OSError, YAMLError) as e:
        raise ContentUpdateError(str(e)) from e


def save_template(
    content: str,
    path: str,
    overwrite: bool = False
) -> None:
    """Save template in specified path. If path is relative then it
    is saved in repository. Raise `ContentUpdateError` on failure.
    """
    if not os.path.isabs(path):
        path = os.path.join(EVENT_TEMPLATES_DIR, path)

    _, filename = os.path.split(path)

    try:
        validate_jinja_filename(filename)
    except ValueError as e:
        raise ContentUpdateError(str(e)) from e

    if overwrite is False and os.path.exists(path):
        raise ContentUpdateError(
            'Template already exists in specified location'
        )

    try:
        with open(path, 'w') as f:
            f.write(content)
    except OSError as e:
        raise ContentUpdateError(str(e)) from e


def load_time_pattern(path: str) -> TimePatternConfig:
    """Load specified time pattern and return its model representation.
    If path is relative then it is loaded from repository. Raise
    `ContentReadError` on failure.
    """
    if not os.path.isabs(path):
        path = os.path.join(TIME_PATTERNS_DIR, path)

    try:
        data = load_object_from_yaml(path)
    except (OSError, YAMLError) as e:
        raise ContentReadError(str(e)) from e

    try:
        return TimePatternConfig.model_validate(data)
    except ValidationError as e:
        raise ContentReadError(str(e)) from e


def load_template(path: str) -> str:
    """Load specified template and return its raw content.
    If path is relative then it is loaded from repository. Raise
    `ContentReadError` on failure.
    """
    if not os.path.isabs(path):
        path = os.path.join(EVENT_TEMPLATES_DIR, path)

    try:
        with open(path) as f:
            data = f.read()
    except OSError as e:
        raise ContentReadError(str(e)) from e

    return data


def load_csv_sample(path: str, delimiter: str = ',') -> list[tuple[str, ...]]:
    """Load specified csv sample and return it as list of tuples. If
    path is relative then it is loaded from repository. Raise
    `ContentReadError` on failure.
    """
    if not os.path.isabs(path):
        path = os.path.join(CSV_SAMPLES_DIR, path)

    try:
        return load_sample_from_csv(
            filepath=path,
            delimiter=delimiter
        )
    except OSError as e:
        raise ContentReadError(str(e)) from e


def load_app_config(path: str) -> ApplicationConfig:
    """Load specified application config and return its model
    representation. If path is relative then it is loaded from
    repository. Raise `ContentReadError` on failure.
    """
    if not os.path.isabs(path):
        path = os.path.join(APPLICATION_CONFIGS_DIR, path)

    try:
        data = load_object_from_yaml(path)
    except (OSError, YAMLError) as e:
        raise ContentReadError(str(e)) from e

    try:
        return ApplicationConfig.model_validate(data)
    except ValidationError as e:
        raise ContentReadError(str(e)) from e


def get_templates_environment() -> Environment:
    """Get basic jinja `Environment` instance with adjusted loader."""
    return Environment(
        loader=FileSystemLoader(
            searchpath=EVENT_TEMPLATES_DIR
        ),
        autoescape=False
    )
