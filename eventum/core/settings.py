# ========== Input parameters section ==========

# Precision (in seconds) of publishing events in time.
# This parameter does not affect the timestamps value but affect how
# often they are passed further - to event plugin.
# Parameter is only actual in live mode for timestamps and patterns
# input plugins.
TIME_PRECISION = 0.01


# ========== Event parameters section ==========

# The name of variable in template with original event timestamp.
TIMESTAMP_FIELD_NAME = 'timestamp'

# Extensions that will be loaded to Jinja Environment
JINJA_ENABLED_EXTENSIONS = [
    'jinja2.ext.do'
]


# ========== Output parameters section ==========

# Minimal size of output queue with rendered events to perform flush.
FLUSH_AFTER_SIZE = 1000

# Timeout after which output queue with rendered events is flushed.
FLUSH_AFTER_SECONDS = 1.0
