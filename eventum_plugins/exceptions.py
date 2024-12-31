from typing import Any


class PluginError(Exception):
    """Base plugin error.

    Parameters
    ----------
    context : dict[str, Any]
        Context information about plugin (e.g. plugin id, name etc.)
    """

    def __init__(
        self,
        *args: Any,
        context: dict[str, Any]
    ) -> None:
        super().__init__(*args)
        self.context = context


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
