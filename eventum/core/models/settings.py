from pydantic import BaseModel

from eventum.core.models.parameters.api import APIParameters
from eventum.core.models.parameters.generation import GenerationParameters
from eventum.core.models.parameters.startup import StartupParameters


class Settings(BaseModel, extra='forbid', frozen=True):
    """Main settings of application.

    Attributes
    ----------
    api: APIParameters
        API parameters

    generation: GenerationParameters
        Generation parameters

    startup: StartupParameters
        Startup parameters
    """
    api: APIParameters
    generation: GenerationParameters
    startup: StartupParameters
