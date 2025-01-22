from abc import abstractmethod
from typing import Any, Iterator, Literal, Required, TypeAlias, TypeVar

from numpy import datetime64
from numpy.typing import NDArray
from pydantic import RootModel
from pytz import BaseTzInfo

from eventum.plugins.base.plugin import Plugin, PluginParams
from eventum.plugins.input.base.config import InputPluginConfig
from eventum.plugins.input.buffer import Buffer

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
ParamsT = TypeVar('ParamsT', bound=InputPluginParams)


class InputPlugin(Plugin[ConfigT, ParamsT], register=False):
    """Base class for all input plugins.

    Parameters
    ----------
    **kwargs : Unpack[InputPluginKwargs]
        Arguments for plugin configuration (see `InputPluginKwargs`)


    Other Parameters
    ----------------
    interactive : bool, default=False
        Whether to mark input plugin as interactive, interactive input
        plugins cannot be merged with others and are used individually
        since they are blocking generation due to unpredictable user
        interactions

    Raises
    ------
    PluginConfigurationError
        If any error occurs during initializing plugin with the
        provided parameters
    """

    def __init__(self, config: ConfigT, params: ParamsT) -> None:
        super().__init__(config, params)

        with self.required_params():
            self._timezone = params['timezone']

        self._buffer = Buffer()

    def __init_subclass__(cls, interactive: bool = False, **kwargs: Any):
        super().__init_subclass__(**kwargs)

        setattr(cls, '_interactive', interactive)

    @abstractmethod
    def generate(
        self,
        size: int,
        skip_past: bool = True
    ) -> Iterator[NDArray[datetime64]]:
        """Generate timestamps.

        Parameters
        ----------
        size : int
            Number of timestamps to generate for each iteration

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

    @property
    def is_interactive(self) -> bool:
        """Wether the plugin is interactive."""
        return getattr(self, '_interactive')
