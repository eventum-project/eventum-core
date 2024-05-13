from pydantic import BaseModel, Field, model_validator

from eventum.core.models.event_config import JinjaEventConfig
from eventum.core.models.input_config import InputConfigMapping
from eventum.core.models.output_config import (NullOutputConfig,
                                               OutputConfigMapping)


class ApplicationConfig(BaseModel):
    input: InputConfigMapping = Field(..., min_length=1, max_length=1)
    event: JinjaEventConfig
    output: list[OutputConfigMapping] | None

    @model_validator(mode='after')
    def handle_null_output(self):
        if not self.output:
            self.output = {'null': NullOutputConfig}
        return self
