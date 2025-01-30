import os
from typing import Any, Literal

from pydantic import Field, field_validator

from eventum.core.models.parameters.generation import GenerationParameters


class GeneratorParameters(GenerationParameters, frozen=True):
    """Parameters for single generator.

    Attributes
    ----------
    id : str
        Generator unique identified

    path : str
        Absolute path to configuration

    time_mode : Literal['live', 'sample'], default='live'
        Wether to use live mode and generate events at moments defined
        by timestamp values or sample mode to generate all events at a
        time

    params: dict[str, Any], default={}
        Parameters that can be used in generator configuration file
    """
    id: str = Field(min_length=1)
    path: str = Field(min_length=1)
    time_mode: Literal['live', 'sample'] = 'live'
    params: dict[str, Any] = Field(default_factory=dict)

    @field_validator('path')
    def validate_path(cls, v: str):
        if os.path.isabs(v):
            return v
        raise ValueError('Path must be absolute')
