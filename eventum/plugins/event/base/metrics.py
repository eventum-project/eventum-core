from eventum.plugins.base.metrics import PluginMetrics


class EventPluginMetrics(PluginMetrics):
    """Event plugin metrics.

    Attributes
    ----------
    produced : int
        Number of produced events

    produce_failed : int
        Number unsuccessfully produced events
    """
    produced: int
    produce_failed: int
