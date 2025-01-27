import importlib.util as util
from typing import Callable

from eventum.plugins.event.base.plugin import (EventPlugin, EventPluginParams,
                                               ProduceParams)
from eventum.plugins.event.plugins.script.config import ScriptEventPluginConfig
from eventum.plugins.exceptions import (PluginConfigurationError,
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
        self._logger.info('External function is imported successfully')

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
                'Cannot get spec of script module',
                context=dict(self.instance_info, file_path=script_path)
            )

        try:
            module = util.module_from_spec(spec)

            if spec.loader is not None:
                spec.loader.exec_module(module)
            else:
                raise PluginConfigurationError(
                    'Script cannot be executed due to loader problem',
                    context=dict(self.instance_info, file_path=script_path)
                )
        except Exception as e:
            raise PluginConfigurationError(
                'Failed to import script as external module',
                context=dict(
                    self.instance_info,
                    reason=str(e),
                    file_path=script_path
                )
            )

        try:
            function = getattr(module, ScriptEventPlugin._FUNCTION_NAME)
        except AttributeError:
            raise PluginConfigurationError(
                f'Definition of function "{ScriptEventPlugin._FUNCTION_NAME}" '
                'is missing in script',
                context=dict(self.instance_info, file_path=script_path)
            )

        return function

    def _produce(self, params: ProduceParams) -> list[str]:
        try:
            result = self._function(params)
        except Exception as e:
            raise PluginRuntimeError(
                'Exception occurred during function execution',
                context=dict(
                    self.instance_info,
                    reason=f'{e.__class__.__name__}: {e}'
                )
            )

        if isinstance(result, str):
            return [result]
        elif isinstance(result, list):
            types = set(map(lambda el: el.__class__.__name__, result))
            if (not result) or ('str' in types and len(types) == 1):
                return result
            else:
                raise PluginRuntimeError(
                    'Function returned object of invalid type, '
                    'string or list of strings are expected',
                    context=dict(
                        self.instance_info,
                        reason=(
                            'Elements of next types encountered '
                            f'in list: {types}'
                        )
                    )
                )
        else:
            raise PluginRuntimeError(
                'Function returned object of invalid type, '
                'string or list of strings are expected',
                context=dict(self.instance_info)
            )
