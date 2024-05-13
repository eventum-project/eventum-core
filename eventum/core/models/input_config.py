import os
from datetime import datetime
from typing import Annotated, Any, Literal, TypeAlias

from croniter import croniter
from pydantic import (BaseModel, BeforeValidator, Field, field_validator,
                      model_validator)

from eventum.utils.fs import validate_yaml_filename


class CronInputConfig(BaseModel):
    expression: str
    count: int = Field(..., gt=0)

    @field_validator('expression')
    def validate_expression(cls, v: Any):
        if croniter.is_valid(v):
            return v
        raise ValueError('Invalid cron expression')


class LinspaceInputConfig(BaseModel):
    start: datetime
    end: datetime
    count: int = Field(..., ge=1)
    endpoint: bool = True

    @model_validator(mode='after')
    def validate_interval(self):
        if self.start < self.end:
            return self
        raise ValueError('Start time must be earlier than end time')


class SampleInputConfig(BaseModel):
    count: int = Field(..., gt=0)


class TimerInputConfig(BaseModel):
    seconds: int = Field(..., ge=1)
    count: int = Field(..., ge=1)
    repeat: bool


def validate_filenames(obj: Any) -> Any:
    if isinstance(obj, list):
        for el in obj:
            if not isinstance(el, str):
                return obj

            validate_yaml_filename(os.path.basename(el))

    return obj


TimePatternsInputConfig = Annotated[
    list[str], BeforeValidator(validate_filenames)
]


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


CronInputConfigMapping: TypeAlias = dict[
    Literal['cron'], CronInputConfig
]
LinspaceInputConfigMapping: TypeAlias = dict[
    Literal['linspace'], LinspaceInputConfig
]
SampleInputConfigMapping: TypeAlias = dict[
    Literal['sample'], SampleInputConfig
]
TimerInputConfigMapping: TypeAlias = dict[
    Literal['timer'], TimerInputConfig
]
TimePatternsInputConfigMapping: TypeAlias = dict[
    Literal['time_patterns'], TimePatternsInputConfig
]
TimestampsInputConfigMapping: TypeAlias = dict[
    Literal['timestamps'], TimestampsInputConfig
]

InputConfig: TypeAlias = (
    CronInputConfig | LinspaceInputConfig | SampleInputConfig
    | TimerInputConfig | TimePatternsInputConfig | TimestampsInputConfig
)
InputConfigMapping: TypeAlias = (
    CronInputConfigMapping | LinspaceInputConfigMapping
    | SampleInputConfigMapping | TimerInputConfigMapping
    | TimePatternsInputConfigMapping | TimestampsInputConfigMapping
)
