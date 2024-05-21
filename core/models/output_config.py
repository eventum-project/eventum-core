import os
from enum import StrEnum
from typing import Any, TypeAlias

from pydantic import BaseModel, Field, field_validator, model_validator

from core.credentials_manager import get_credentials_manager
from core.models.mutex_model import MutexModel
from core.settings import KEYRING_SERVICE_NAME


class OutputConfigModel(BaseModel, extra='forbid'):
    """Base model class for all input config models."""


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
    password: str = Field(..., min_length=1)
    index: str = Field(..., min_length=1)
    verify_ssl: bool
    ca_cert_path: str | None = None

    @model_validator(mode='after')
    def set_password(self):
        if self.password.startswith('${') and self.password.endswith('}'):
            token = self.password[2:-1]

            try:
                credentials_manager = get_credentials_manager()
                password = credentials_manager.get_password(
                    service=KEYRING_SERVICE_NAME,
                    username=token
                )
            except ValueError as e:
                raise ValueError(
                    f'Failed to load password from keyring: {e}'
                ) from e

            if password is None:
                raise ValueError(
                    f'Token "{token}" for opensearch password '
                    'not found in keyring'
                )

            self.password = password

        return self


class StdOutOutputConfig(OutputConfigModel):
    format: OutputFormat = OutputFormat.ORIGINAL


OutputConfig: TypeAlias = (
    FileOutputConfig | OpensearchOutputConfig | StdOutOutputConfig
)


class OutputConfigMapping(MutexModel):
    file: FileOutputConfig | None = None
    opensearch: OpensearchOutputConfig | None = None
    stdout: StdOutOutputConfig | None = None
