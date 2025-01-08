from abc import abstractmethod
from typing import Iterator, Literal, Required, TypeAlias, TypeVar

from numpy import datetime64
from numpy.typing import NDArray
from pydantic import RootModel
from pytz import BaseTzInfo

from eventum.plugins.base.plugin import Plugin, PluginParams
from eventum.plugins.input.base.config import InputPluginConfig

QueueOverflowMode: TypeAlias = Literal['block', 'skip']


class InputPluginParams(PluginParams):
    """Parameters for input plugin.

    Attributes
    ----------
    timezone : BaseTzInfo
        Timezone that is used for generated timestamps
    """
    timezone: Required[BaseTzInfo]


ConfigT = TypeVar(
    'ConfigT',
    bound=(InputPluginConfig | RootModel[InputPluginConfig])
)


class InputPlugin(Plugin[ConfigT, InputPluginParams], register=False):
    """Base class for all input plugins.

    Parameters
    ----------
    **kwargs : Unpack[InputPluginKwargs]
        Arguments for plugin configuration (see `InputPluginKwargs`)

    Raises
    ------
    PluginConfigurationError
        If any error occurs during initializing plugin with the
        provided parameters
    """

    def __init__(self, config: ConfigT, params: InputPluginParams) -> None:
        super().__init__(config, params)

        with self.required_params():
            self._timezone = params['timezone']

    @abstractmethod
    def generate(
        self,
        skip_past: bool = True
    ) -> Iterator[NDArray[datetime64]]:
        """Start timestamps generation with yielding timestamp batches.
        Size of batches mostly depends on configuration parameters.
        Generation is not blocked for future timestamps.

        Parameters
        ----------
        skip_past : bool, default=True
            Wether to skip past timestamps before starting generation

        Yields
        -------
        NDArray[datetime64]
            Array of generated timestamps

        Raises
        ------
        PluginRuntimeError
            If any error occurs during timestamps generation
        """
        ...
