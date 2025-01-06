import os
from typing import Any, Literal

from pydantic import Field, field_validator

from eventum.core.parameters.generation import CommonGenerationParameters


class GeneratorParameters(CommonGenerationParameters, frozen=True):
    """Parameters for single generator.

    Parameters
    ----------
    id : str
        Generator unique identified

    path : str
        Absolute path to configuration

    time_mode : Literal['live', 'sample']
        Wether to use live mode and generate events at moments defined
        by timestamp values or sample mode to generate all events at a
        time

    params: dict[str, Any], default={}
        Parameters that can be used in generator configuration file
    """
    id: str = Field(
        min_length=1,
        description='Generator unique identified'
    )
    path: str = Field(
        min_length=1,
        description='Absolute path to generator configuration file'
    )
    time_mode: Literal['live', 'sample'] = Field(
        description=(
            'Wether to use live mode and generate events at moments '
            'defined by timestamp values or sample mode to generate '
            'all events at a time'
        )
    )
    params: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            'Parameters that can be used in generator configuration file'
        )
    )

    @field_validator('path')
    def validate_path(cls, v: str):
        if os.path.isabs(v):
            return v
        raise ValueError('Path must be absolute')
