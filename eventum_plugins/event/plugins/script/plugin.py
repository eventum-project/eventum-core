import importlib.util as util
from typing import Callable

from eventum_plugins.event.base.plugin import (EventPlugin, EventPluginParams,
                                               ProduceParams)
from eventum_plugins.event.plugins.script.config import ScriptEventPluginConfig
from eventum_plugins.exceptions import (PluginConfigurationError,
                                        PluginRuntimeError)


class ScriptEventPlugin(
    EventPlugin[ScriptEventPluginConfig, EventPluginParams]
):
    """Event plugin for producing events using script with user
    defined logic.

    Notes
    -----
    User script must include function with the following signature:
    ```
    def produce(params: ProduceParams) -> str | list[str]:
        ...
    ```
    For more information see documentation string of ProduceParams
    """

    _FUNCTION_NAME = 'produce'

    def __init__(
        self,
        config: ScriptEventPluginConfig,
        params: EventPluginParams
    ) -> None:
        super().__init__(config, params)
        self._function = self._import_function()

    def _import_function(self) -> Callable[[ProduceParams], str | list[str]]:
        """Import the function from the user defined module.

        Returns
        -------
        Callable[[ProduceParams], str | list[str]]
            Function

        Raises
        ------
        PluginConfigurationError
            If module is not found, function is not found in module or
            other error occurred during module execution
        """
        script_path = self._config.path
        spec = util.spec_from_file_location('user_module', script_path)

        if spec is None:
            raise PluginConfigurationError(
                f'Could not get spec of script "{script_path}"'
            )

        try:
            module = util.module_from_spec(spec)

            if spec.loader is not None:
                spec.loader.exec_module(module)
            else:
                raise RuntimeError(
                    'Script cannot be executed due to loader problem '
                )
        except Exception as e:
            raise PluginConfigurationError(
                f'Failed to import script as external module: {e}'
            )

        try:
            function = getattr(module, ScriptEventPlugin._FUNCTION_NAME)
        except AttributeError:
            raise PluginConfigurationError(
                f'Function "{ScriptEventPlugin._FUNCTION_NAME}" is not '
                f'found in "{script_path}"'
            )

        return function

    def produce(self, params: ProduceParams) -> list[str]:
        try:
            result = self._function(params)
        except Exception as e:
            raise PluginRuntimeError(
                f'{e.__class__.__name__} exception occurred during '
                f'"{ScriptEventPlugin._FUNCTION_NAME}" function execution: {e}'
            )

        if isinstance(result, str):
            return [result]
        elif isinstance(result, list):
            for item in result:
                if not isinstance(item, str):
                    returned_type = type(item)
                    raise PluginRuntimeError(
                        f'Function "{ScriptEventPlugin._FUNCTION_NAME}" '
                        f"returned list that contains object of type "
                        f"{returned_type}, but elements of type <class 'str'>"
                        " are expected"
                    )

            return result
        else:
            returned_type = type(result)
            raise PluginRuntimeError(
                f'Function "{ScriptEventPlugin._FUNCTION_NAME}" returned '
                f"object of type {returned_type}, but <class 'str'> or "
                "<class 'list'> are expected"
            )
