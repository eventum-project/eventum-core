from typing import Self

from pydantic import BaseModel, Field, field_validator, model_validator
from pytz import all_timezones_set

from eventum.plugins.input.base.plugin import QueueOverflowMode


class BatchParameters(BaseModel, extra='forbid', frozen=True):
    """Batcher parameters.

    Parameters
    ----------
    size : int | None, default=10000
        Batch size for generating events

    timeout : float | None, default=1.0
        Batch timeout (in seconds) for generating events

    Notes
    -----
    At least one parameter must be provided
    """
    size: int | None = Field(
        default=10_000,
        ge=1,
        description='Batch size for generating events'
    )
    timeout: float | None = Field(
        default=1.0,
        ge=0.1,
        description='Batch timeout (in seconds) for generating events'
    )

    @model_validator(mode='after')
    def validate_batch_params(self) -> Self:
        if self.size is None and self.timeout is None:
            raise ValueError('Batch size or timeout must be provided')

        return self


class QueueParameters(BaseModel, extra='forbid', frozen=True):
    """Parameters of input plugins queue.

    Parameters
    ----------
    max_size : int, default=100000
        Maximum size of queue for generated timestamps per input plugin

    on_overflow : QueueOverflowMode, default='block'
        Whether to block or skip adding new timestamps when queue is
        overflowed
    """
    max_size: int = Field(
        default=100_000,
        ge=1,
        description=(
            'Maximum size of queue for generated timestamps per input plugin'
        )
    )
    on_overflow: QueueOverflowMode = Field(
        default='block',
        validate_default=True,
        description=(
            'Whether to block or skip adding new timestamps when '
            'queue is overflowed'
        )
    )


class GenerationParameters(BaseModel, extra='forbid', frozen=True):
    """Generation parameters that are common for all generators and can
    be overridden from generators parameters level.

    Parameters
    ----------
    timezone : str, default='UTC'
        Time zone for generating timestamps

    batch : BatchParameters, default=BatchParameters(...)
        Batch parameters

    queue : QueueParameters, default=QueueParameters(...)
        Queue parameters

    order_timestamps : bool, default=False
        Whether to keep chronological order of timestamps after
        merging them from many input plugins
    """
    timezone: str = Field(
        default='UTC',
        min_length=3,
        description='Time zone for generating timestamps'
    )
    batch: BatchParameters = Field(
        default_factory=lambda: BatchParameters(),
        description='Batch parameters'
    )
    queue: QueueParameters = Field(
        default_factory=lambda: QueueParameters(),
        description='Queue parameters'
    )
    order_timestamps: bool = Field(
        default=False,
        description=(
            'Whether to keep chronological order of timestamps after '
            'merging them from many input plugins'
        )
    )

    @field_validator('timezone')
    def validate_timezone(cls, v: str) -> str:
        if v in all_timezones_set:
            return v

        raise ValueError(f'Unknown time zone "{v}"')
