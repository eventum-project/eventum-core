class PluginError(Exception):
    """Base exception for all plugin errors."""


class PluginConfigurationError(PluginError):
    """Exception for plugin configuration errors."""


class PluginRuntimeError(PluginError):
    """Exception for plugin runtime errors."""
