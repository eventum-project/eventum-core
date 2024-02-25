from pydantic import BaseModel


class FlushSettings(BaseModel):
    flush_after_size: int
    flush_after_millis: int


class RuntimeSettings(BaseModel):
    flush_settings: FlushSettings
