from pydantic import BaseModel, Field
from pytz import timezone
from pytz.tzinfo import DstTzInfo


class Settings(BaseModel, extra='forbid', frozen=True):
    # Time zone used in input plugins to generate timestamps.
    timezone: DstTzInfo = timezone('UTC')

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


DEFAULT_SETTINGS = Settings()
