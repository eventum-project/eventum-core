from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator
from pytz import all_timezones_set


class TimeMode(StrEnum):
    SAMPLE = 'sample'
    LIVE = 'live'


class Settings(BaseModel, extra='forbid', frozen=True):
    # Time zone used in input plugins to generate timestamps.
    timezone: str = 'UTC'

    # The name of variable in template with timezone value (e.g. "+0300").
    timezone_field_name: str = 'tz'

    # The name of variable in template with original event timestamp.
    timestamp_field_name: str = Field('timestamp', min_length=1)

    # Batch size / timeout (in seconds) for input-to-event plugins
    # communication.
    events_batch_size: int = Field(1_000_000, ge=1)
    events_batch_timeout: float = Field(1.0, ge=0)

    # Batch size / timeout (in seconds) for output plugins.
    output_batch_size: int = Field(10_000, ge=1)
    output_batch_timeout: float = Field(1.0, ge=0)

    # Service name for keyring credentials storage
    keyring_service_name: str = Field('eventum', min_length=1)

    @field_validator('timezone')
    def validate_timezone(cls, v: Any):
        if v in all_timezones_set:
            return v

        raise ValueError(f'Unknown time zone "{v}"')


DEFAULT_SETTINGS = Settings()   # type: ignore[call-arg]
