from datetime import UTC

# ========== Input parameters ==========

# Precision (in seconds) of publishing events in time.
# This parameter does not affect the timestamps value but affect how
# often they are published by input plugin.
# Parameter is only actual in live mode for timestamps and patterns
# input plugins.
TIME_PRECISION = 0.1

# Time zone used in input plugins to generate timestamps.
TIMEZONE = UTC


# ========== Event parameters ==========

# The name of variable in template with original event timestamp.
TIMESTAMP_FIELD_NAME = 'timestamp'

# Extensions that will be loaded to Jinja Environment
JINJA_ENABLED_EXTENSIONS = [
    'jinja2.ext.do'
]


# ========== Queues batching parameters ==========

# Batch size / timeout (in seconds) for input-to-event plugins
# communication.
EVENTS_BATCH_SIZE = 1000000
EVENTS_BATCH_TIMEOUT = 1.0

# Batch size / timeout (in seconds) for output plugins.
OUTPUT_BATCH_SIZE = 10000
OUTPUT_BATCH_TIMEOUT = 1.0
