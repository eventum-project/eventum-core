from typing import Self

from pydantic import BaseModel, Field, field_validator, model_validator
from pytz import all_timezones_set


class BatchParameters(BaseModel, extra='forbid', frozen=True):
    """Batcher parameters.

    Attributes
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
    delay: float | None = Field(
        default=1.0,
        ge=0.1,
        description='Batch timeout (in seconds) for generating events'
    )

    @model_validator(mode='after')
    def validate_batch_params(self) -> Self:
        if self.size is None and self.delay is None:
            raise ValueError('Batch size or timeout must be provided')

        return self


class QueueParameters(BaseModel, extra='forbid', frozen=True):
    """Parameters of input plugins queue.

    Attributes
    ----------
    max_batches : int, default=10
        Maximum number of batches in queue
    """
    max_batches: int = Field(
        default=10,
        ge=1,
        description='Maximum number of batches in queue'
    )


class GenerationParameters(BaseModel, extra='forbid', frozen=True):
    """Generation parameters that are common for all generators and can
    be overridden from generator parameters level.

    Attributes
    ----------
    timezone : str, default='UTC'
        Time zone for generating timestamps

    batch : BatchParameters, default=BatchParameters(...)
        Batch parameters

    queue : QueueParameters, default=QueueParameters(...)
        Queue parameters

    keep_order : bool, default=False
        Whether to keep chronological order of timestamps by disabling
        output plugins concurrency

    max_concurrency : int, default=100
        Maximum number of concurrent write operations performed by
        output plugins

    skip_past : bool, default=True
        Whether to skip past timestamps when starting generation in
        live mode

    metrics_interval : float, default=5.0
        Time interval (in seconds) of metrics gauging
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
    keep_order: bool = Field(
        default=False,
        description=(
            'Whether to keep chronological order of timestamps by disabling '
            'output plugins concurrency'
        )
    )
    max_concurrency: int = Field(
        default=100,
        description=(
            'Maximum number of concurrent write operations performed '
            'by output plugins'
        )
    )
    skip_past: bool = Field(
        default=True,
        description=(
            'Whether to skip past timestamps when starting generation '
            'in live mode'
        )
    )
    metrics_interval: float = Field(
        default=5.0,
        ge=1.0,
        description='Time interval (in seconds) of metrics gauging'
    )

    @field_validator('timezone')
    def validate_timezone(cls, v: str) -> str:
        if v in all_timezones_set:
            return v

        raise ValueError(f'Unknown time zone "{v}"')
