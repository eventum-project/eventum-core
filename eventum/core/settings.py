# ========== Input parameters section ==========

# Minimal time for input plugin to go sleep waiting for next event.
# The higher the value, the more values from the future (equal to the
# parameter value) will be generated in advance.
# The influence of the parameter appears with an intense flow of events
# (thousands or millions per second).
SLEEP_MIN_SECONDS = 0.1


# ========== Output parameters section ==========

# Minimal size of output queue with rendered events to perform flush.
FLUSH_AFTER_SIZE = 100

# Timeout after which output queue with rendered events is flushed.
FLUSH_AFTER_SECONDS = 1.0
