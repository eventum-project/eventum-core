from eventum.plugins.base.metrics import PluginMetrics


class OutputPluginMetrics(PluginMetrics):
    """Output plugin metrics.

    Attributes
    ----------
    format_failed : int
        Number of unsuccessfully formatted events

    write_failed : int
        Number of unsuccessfully written events

    written : int
        Number of written events
    """
    format_failed: int
    write_failed: int
    written: int
