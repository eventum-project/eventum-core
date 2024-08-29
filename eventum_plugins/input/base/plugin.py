import inspect
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Iterator, Literal, assert_never, final

from numpy import datetime64
from numpy.typing import NDArray
from pytz import BaseTzInfo

from eventum_plugins.enums import PluginType
from eventum_plugins.exceptions import PluginConfigurationError, PluginError
from eventum_plugins.input.base.config import InputPluginConfig
from eventum_plugins.input.batcher import TimestampsBatcher
from eventum_plugins.input.enums import TimeMode
from eventum_plugins.registry import PluginsRegistry


class InputPlugin(ABC):
    """Base class for all input plugins.

    Parameters
    ----------
    id : int
        Arbitrary number for distinction deferent instances of the same
        plugin class

    config : Any
        Configuration for a plugin which class (in implemented plugins)
        is subclass of `InputPluginConfig` model

    mode : TimeMode
            Time mode of timestamps generation.

    timezone : BaseTzInfo
        Timezone that is used for generating timestamps

    batch_size : int | None, default=100_000
        Parameter `batch_size` for underlying batcher

    batch_delay : float | None, default=0.1
        Parameter `batch_delay` for underlying batcher

    queue_max_size : int, default=100_000_000
        Parameter `queue_max_size` for underlying batcher

    on_queue_overflow : Literal['block', 'skip'], default='block'
        Block or skip adding new timestamps when batcher input
        queue is overflowed

    Raises
    ------
    PluginConfigurationError
        If any error occurred during initializing plugin with the
        provided config

    Notes
    -----
    All subclasses of this class is considered as implemented plugins
    that are automatically registered in `PluginsRegistry` via
    `__init_subclass__`. Therefore some inheritance parameters must be
    provided.

    Other Parameters
    ----------------
    Parameters that can be used in inheritance:

    config_cls : type
        Model class of config used by plugin

    register : bool, default=True
        Whether to register class as implemented plugin
    """

    def __init_subclass__(
        cls,
        config_cls: type,
        register: bool = True,
        **kwargs
    ):
        super().__init_subclass__(**kwargs)

        if not register:
            return

        class_module = inspect.getmodule(cls)
        if class_module is None:
            raise PluginError(
                'Cannot inspect module of plugin class definition'
            )

        if class_module.__name__ == '__main__':
            raise PluginError(
                'Plugin can be registered only from external package, '
                f'but trying to register in module "{cls.__module__}"'
            )

        try:
            plugin_name = class_module.__name__.split('.')[-2]
        except IndexError:
            raise PluginError(
                f'Cannot extract plugin name from "{class_module.__name__}"'
            )

        PluginsRegistry().register_plugin(
            type=PluginType.INPUT,
            name=plugin_name,
            cls=cls,
            config_cls=config_cls
        )

    def __init__(
        self,
        id: int,
        config: InputPluginConfig,
        mode: TimeMode,
        timezone: BaseTzInfo,
        batch_size: int | None = 100_000,
        batch_delay: float | None = 0.1,
        queue_max_size: int = 100_000_000,
        on_queue_overflow: Literal['block', 'skip'] = 'block'
    ) -> None:
        self._id = id
        self._config = config
        self._mode = mode
        self._timezone = timezone

        try:
            self._batcher = TimestampsBatcher(
                batch_size=batch_size,
                batch_delay=batch_delay,
                scheduling=True if mode == TimeMode.LIVE else False,
                timezone=self._timezone,
                queue_max_size=queue_max_size
            )
        except ValueError as e:
            raise PluginConfigurationError(f'Wrong batching parameters: {e}')

        self._block_on_overflow = on_queue_overflow == 'block'

    @final
    def generate(self) -> Iterator[NDArray[datetime64]]:
        """Start timestamps generation in background thread and yield
        batches of generated timestamps. In sample mode timestamps
        are yielded immediately, in live mode - respectively to real
        time.

        Yields
        -------
        NDArray[datetime64]
            Batches of generated timestamps

        Raises
        ------
        PluginRuntimeError
            If any error occurred during timestamps generation
        """
        match self._mode:
            case TimeMode.SAMPLE:
                method = self._generate_sample
            case TimeMode.LIVE:
                method = self._generate_live
            case v:
                assert_never(v)

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                method,
                lambda batch: self._batcher.add(batch, self._block_on_overflow)
            )
            future.add_done_callback(lambda _: self._batcher.close())

            yield from self._batcher.scroll()
            future.result()

    @abstractmethod
    def _generate_sample(
        self,
        on_events: Callable[[NDArray[datetime64]], Any]
    ) -> None:
        """Start timestamps generation in sample mode. `on_events`
        callback should be called once timestamps are generated.

        Parameters
        ----------
        on_events : Callable[[NDArray[datetime64]], Any]
            Callback that should be called for generated timestamps

        Raises
        ------
        PluginRuntimeError
            If any error occurred during timestamps generation
        """
        ...

    @abstractmethod
    def _generate_live(
        self,
        on_events: Callable[[NDArray[datetime64]], Any]
    ) -> None:
        """Start timestamps generation in live mode. `on_events`
        callback should be called with some delays but without
        increasing accumulation of future timestamps. Also it is
        not necessary to schedule precisely when to call `on_events`
        callback since timestamps scheduling is implemented internally.

        Parameters
        ----------
        on_events : Callable[[NDArray[datetime64]], Any]
            Callback that should be called for generated timestamps

        Raises
        ------
        PluginRuntimeError
            If any error occurred during timestamps generation
        """
        ...
