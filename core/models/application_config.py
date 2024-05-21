from pydantic import BaseModel

from core.models.event_config import JinjaEventConfig
from core.models.input_config import InputConfigMapping
from core.models.output_config import OutputConfigMapping


class ApplicationConfig(BaseModel):
    input: InputConfigMapping
    event: JinjaEventConfig
    output: list[OutputConfigMapping]
