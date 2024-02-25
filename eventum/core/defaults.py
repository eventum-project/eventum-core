from eventum.core.models.runtime_settings import RuntimeSettings, FlushSettings


FLUSH_AFTER_SIZE = 100
FLUSH_AFTER_MILLIS = 1000


def get_default_settings() -> RuntimeSettings:
    return RuntimeSettings(
        flush_settings=FlushSettings(
            flush_after_size=FLUSH_AFTER_SIZE,
            flush_after_millis=FLUSH_AFTER_MILLIS
        )
    )
