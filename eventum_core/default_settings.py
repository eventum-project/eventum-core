from pytz import timezone

# ========== Input parameters ==========

# Time zone used in input plugins to generate timestamps.
TIMEZONE = timezone('UTC')


# ========== Event parameters ==========

# The name of variable in template with original event timestamp.
TIMESTAMP_FIELD_NAME = 'timestamp'


# ========== Queues batching parameters ==========

# Batch size / timeout (in seconds) for input-to-event plugins
# communication.
EVENTS_BATCH_SIZE = 1000000
EVENTS_BATCH_TIMEOUT = 1.0

# Batch size / timeout (in seconds) for output plugins.
OUTPUT_BATCH_SIZE = 10000
OUTPUT_BATCH_TIMEOUT = 1.0


# ========== Security parameters ==========

# Service name for keyring credentials storage
KEYRING_SERVICE_NAME = 'eventum'
