from pydantic import BaseModel

from eventum.core.models.event_config import JinjaEventConfig
from eventum.core.models.input_config import InputConfigMapping
from eventum.core.models.output_config import OutputConfigMapping


class ApplicationConfig(BaseModel):
    input: InputConfigMapping
    event: JinjaEventConfig
    output: list[OutputConfigMapping]
