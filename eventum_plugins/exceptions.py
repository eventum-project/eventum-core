class PluginLoadError(Exception):
    """Failed to load plugin."""


class PluginNotFoundError(PluginLoadError):
    """Failed to load plugin because it is not found."""


class PluginError(Exception):
    """Error occurred while working with plugin."""


class PluginConfigurationError(PluginError):
    """Configuration for plugin is invalid."""


class PluginRuntimeError(PluginError):
    """Error occurred during plugin execution."""
