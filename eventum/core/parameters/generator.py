
from typing import Any, Literal

from pydantic import Field

from eventum.core.parameters.generation import CommonGenerationParameters


class GeneratorParameters(CommonGenerationParameters, frozen=True):
    """Parameters for single generator.

    Parameters
    ----------
    path : str
        Path to configuration

    time_mode : Literal['live', 'sample']
        Wether to use live mode and generate events at moments defined
        by timestamp values or sample mode to generate all events at a
        time

    params: dict[str, Any], default={}
        Parameters that can be used in generator configuration file
    """
    path: str = Field(
        description='Path to generator configuration file'
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
