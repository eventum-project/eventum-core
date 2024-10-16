class PluginError(Exception):
    """Base plugin error."""


class PluginRegistrationError(PluginError):
    """Plugin registration failed."""


class PluginLoadError(PluginError):
    """Error during plugin loading."""


class PluginNotFoundError(PluginLoadError):
    """Plugin is not found."""


class PluginConfigurationError(PluginError):
    """Configuration for plugin is invalid."""


class PluginRuntimeError(PluginError):
    """Error during plugin execution."""
