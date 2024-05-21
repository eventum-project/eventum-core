from datetime import datetime
from typing import Annotated, Any, TypeAlias

from croniter import croniter
from pydantic import (BaseModel, BeforeValidator, Field, field_validator,
                      model_validator)

from core.models.mutex_model import MutexModel


class InputConfigModel(BaseModel, extra='forbid'):
    """Base model class for all input config models."""


class CronInputConfig(InputConfigModel):
    expression: str
    count: int = Field(..., gt=0)

    @field_validator('expression')
    def validate_expression(cls, v: Any):
        if croniter.is_valid(v):
            return v
        raise ValueError('Invalid cron expression')


class LinspaceInputConfig(InputConfigModel):
    start: datetime
    end: datetime
    count: int = Field(..., ge=1)
    endpoint: bool = True

    @model_validator(mode='after')
    def validate_interval(self):
        if self.start < self.end:
            return self
        raise ValueError('Start time must be earlier than end time')


class SampleInputConfig(InputConfigModel):
    count: int = Field(..., gt=0)


class TimerInputConfig(InputConfigModel):
    seconds: int = Field(..., ge=1)
    count: int = Field(..., ge=1)
    repeat: bool


TimePatternsInputConfig = list[str]


def try_parse_datetime(obj: Any) -> Any | list[datetime]:
    if isinstance(obj, list):
        casted_list = []
        for el in obj:
            try:
                casted_list.append(datetime.fromisoformat(el))
            except (ValueError, TypeError):
                return obj

        return casted_list

    return obj


TimestampsInputConfig = Annotated[
    list[datetime], BeforeValidator(try_parse_datetime)
]


InputConfig: TypeAlias = (
    CronInputConfig | LinspaceInputConfig | SampleInputConfig
    | TimerInputConfig | TimePatternsInputConfig | TimestampsInputConfig
)


class InputConfigMapping(MutexModel):
    cron: CronInputConfig | None = None
    linspace: LinspaceInputConfig | None = None
    sample: SampleInputConfig | None = None
    timer: TimerInputConfig | None = None
    time_patterns: TimePatternsInputConfig | None = None
    timestamps: TimestampsInputConfig | None = None
