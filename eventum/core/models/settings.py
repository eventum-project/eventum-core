from pydantic import BaseModel

from eventum.core.models.parameters.api import APIParameters
from eventum.core.models.parameters.generation import GenerationParameters
from eventum.core.models.parameters.log import LogParameters
from eventum.core.models.parameters.path import PathParameters


class Settings(BaseModel, extra='forbid', frozen=True):
    """Main settings of application.

    Attributes
    ----------
    api: APIParameters
        API parameters

    generation: GenerationParameters
        Generation parameters

    log : LogParameters
        Log parameters

    path : PathParameters
        Path parameters
    """
    api: APIParameters
    generation: GenerationParameters
    log: LogParameters
    path: PathParameters
