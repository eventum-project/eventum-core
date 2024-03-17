# ========== Input parameters ==========

# Precision (in seconds) of publishing events in time.
# This parameter does not affect the timestamps value but affect how
# often they are passed further - to event plugin.
# Parameter is only actual in live mode for timestamps and patterns
# input plugins.
TIME_PRECISION = 0.01


# ========== Event parameters ==========

# The name of variable in template with original event timestamp.
TIMESTAMP_FIELD_NAME = 'timestamp'

# Extensions that will be loaded to Jinja Environment
JINJA_ENABLED_EXTENSIONS = [
    'jinja2.ext.do'
]


# ========== Queues batching ==========

# Batch size / timeout (in seconds) for events rendering.
RENDER_AFTER_SIZE = 1000
RENDER_AFTER_TIMEOUT = 1.0

# Batch size / timeout (in seconds) for output events.
OUTPUT_AFTER_SIZE = 1000
OUTPUT_AFTER_TIMEOUT = 1.0
