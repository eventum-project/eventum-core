class PluginLoadError(Exception):
    """Exception for plugin loading errors."""


class PluginNotFoundError(PluginLoadError):
    """Exception for errors when plugin with a given name is not found."""


class PluginError(Exception):
    """Base exception for plugin errors."""


class PluginConfigurationError(PluginError):
    """Exception for plugin configuration errors."""


class PluginRuntimeError(PluginError):
    """Exception for plugin runtime errors."""
