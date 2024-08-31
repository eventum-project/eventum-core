from typing import Any, Callable

from numpy import datetime64, linspace, timedelta64
from numpy.typing import NDArray

from eventum_plugins.input.base.plugin import InputPlugin
from eventum_plugins.input.plugins.linspace.config import \
    LinspaceInputPluginConfig
from eventum_plugins.input.tools import normalize_daterange
from eventum_plugins.input.utils.time_utils import localize


class LinspaceInputPlugin(InputPlugin, config_cls=LinspaceInputPluginConfig):
    """Input plugin for generating specified count of events linearly
    spaced in specified date range.
    """

    def __init__(self, *, config: LinspaceInputPluginConfig, **kwargs) -> None:
        super().__init__(config=config, **kwargs)

        self._config: LinspaceInputPluginConfig

        self._start, self._end = normalize_daterange(
            start=self._config.start,
            end=self._config.end,
            timezone=self._timezone,
            none_start='now'
        )

    def _generate(
        self,
        on_events: Callable[[NDArray[datetime64]], Any]
    ) -> None:
        space = linspace(
            start=0,
            stop=1,
            num=self._config.count,
            endpoint=self._config.endpoint,
        )

        start = datetime64(localize(self._start, self._timezone), 'us')
        timedelta = timedelta64(
            value=(self._end - self._start),
            format='us'
        )

        timestamps = start + (timedelta * space)
        on_events(timestamps)

    def _generate_sample(
        self,
        on_events: Callable[[NDArray[datetime64]], Any]
    ) -> None:
        self._generate(on_events)

    def _generate_live(
        self,
        on_events: Callable[[NDArray[datetime64]], Any]
    ) -> None:
        self._generate(on_events)
