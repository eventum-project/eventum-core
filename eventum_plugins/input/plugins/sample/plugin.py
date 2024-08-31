from typing import Any, Callable

from numpy import datetime64, full
from numpy.typing import NDArray

from eventum_plugins.input.base.plugin import InputPlugin
from eventum_plugins.input.plugins.sample.config import SampleInputPluginConfig
from eventum_plugins.input.utils.time_utils import now64


class SampleInputPlugin(InputPlugin, config_cls=SampleInputPluginConfig):
    """Input plugin for generating specified count of timestamps. All
    timestamps are the same and have a value of time when generation
    was started.
    """

    def __init__(self, *, config: SampleInputPluginConfig, **kwargs) -> None:
        super().__init__(config=config, **kwargs)

        self._config: SampleInputPluginConfig

    def _generate_sample(
        self,
        on_events: Callable[[NDArray[datetime64]], Any]
    ) -> None:
        on_events(
            full(
                shape=self._config.count,
                fill_value=now64(timezone=self._timezone),
                dtype='datetime64[us]'
            )
        )

    def _generate_live(
        self,
        on_events: Callable[[NDArray[datetime64]], Any]
    ) -> None:
        on_events(
            full(
                shape=self._config.count,
                fill_value=now64(timezone=self._timezone),
                dtype='datetime64[us]'
            )
        )
