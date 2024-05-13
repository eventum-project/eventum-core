import os
from enum import StrEnum
from typing import Any, Literal, TypeAlias

from pydantic import BaseModel, Field, field_validator


def init_none_config() -> None:
    return None


NullOutputConfig = init_none_config


class OutputFormat(StrEnum):
    ORIGINAL = 'original'
    JSON_LINES = 'json-lines'


class FileOutputConfig(BaseModel):
    path: str
    format: OutputFormat = OutputFormat.ORIGINAL
    flush: bool = False

    @field_validator('path')
    def validate_path(cls, v: Any):
        if os.path.isabs(v):
            return v
        raise ValueError('Path must be absolute')


class OpensearchOutputConfig(BaseModel):
    hosts: list[str] = Field(..., min_length=1)
    user: str = Field(..., min_length=1)
    index: str = Field(..., min_length=1)
    verify_ssl: bool
    ca_cert_path: str | None = None


class StdOutOutputConfig(BaseModel):
    format: OutputFormat = OutputFormat.ORIGINAL


FileOutputConfigMapping: TypeAlias = dict[
    Literal['file'], FileOutputConfig
]
OpensearchOutputConfigMapping: TypeAlias = dict[
    Literal['opensearch'], OpensearchOutputConfig
]
StdOutOutputConfigMapping: TypeAlias = dict[
    Literal['stdout'], StdOutOutputConfig
]

OutputConfig: TypeAlias = (
    FileOutputConfig | OpensearchOutputConfig | StdOutOutputConfig | None
)
OutputConfigMapping: TypeAlias = (
    FileOutputConfigMapping | OpensearchOutputConfigMapping
    | StdOutOutputConfigMapping
)
