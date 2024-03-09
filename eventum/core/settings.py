# ========== Input parameters section ==========

# Minimal time for input plugin to go sleep waiting for next event.
# The higher the value, the more values from the future (equal to the
# parameter value) will be published in advance.
# Сan be considered as batch size. E.g setting parameter to 10 seconds
# will cause to publishing events every 10 seconds from the next 10
# seconds interval. This parameter does not affect the timestamps
# passed to callback at all.
# Parameter is only actual in live mode for timestamps and patterns
# input plugins.
AHEAD_PUBLICATION_SECONDS = 0.01

# Ratio to multiply required EPS to run TimePatternInputPlugin in live
# mode. This parameter serves as compensation for the error of value of
# the actual EPS obtained as a result of performance test.
REQUIRED_EPS_RESERVE_RATIO = 1.15


# ========== Output parameters section ==========

# Minimal size of output queue with rendered events to perform flush.
FLUSH_AFTER_SIZE = 100

# Timeout after which output queue with rendered events is flushed.
FLUSH_AFTER_SECONDS = 1.0
