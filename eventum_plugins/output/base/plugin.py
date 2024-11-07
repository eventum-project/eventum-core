from eventum_plugins.base.plugin import Plugin


class OutputPlugin(Plugin, config_cls=object, register=False):
    """Base class for all output plugins."""
