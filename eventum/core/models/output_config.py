import os
from enum import StrEnum
from typing import Any, TypeAlias

from pydantic import BaseModel, Field, field_validator

from eventum.core.models.mutex_model import MutexModel


class OutputConfigModel(BaseModel, extra='forbid'):
    """Base model class for all input config models."""


def init_none_config() -> None:
    return None


NullOutputConfig = init_none_config


class OutputFormat(StrEnum):
    ORIGINAL = 'original'
    JSON_LINES = 'json-lines'


class FileOutputConfig(OutputConfigModel):
    path: str
    format: OutputFormat = OutputFormat.ORIGINAL
    flush: bool = False

    @field_validator('path')
    def validate_path(cls, v: Any):
        if os.path.isabs(v):
            return v
        raise ValueError('Path must be absolute')


class OpensearchOutputConfig(OutputConfigModel):
    hosts: list[str] = Field(..., min_length=1)
    user: str = Field(..., min_length=1)
    index: str = Field(..., min_length=1)
    verify_ssl: bool
    ca_cert_path: str | None = None


class StdOutOutputConfig(OutputConfigModel):
    format: OutputFormat = OutputFormat.ORIGINAL


OutputConfig: TypeAlias = (
    FileOutputConfig | OpensearchOutputConfig | StdOutOutputConfig
)


class OutputConfigMapping(MutexModel):
    file: FileOutputConfig | None = None
    opensearch: OpensearchOutputConfig | None = None
    stdout: StdOutOutputConfig | None = None
