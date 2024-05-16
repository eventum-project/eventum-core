from datetime import datetime
from typing import Any, Callable, Self

from numpy import datetime64, linspace, timedelta64

from eventum.core import settings
from eventum.core.models.input_config import LinspaceInputConfig
from eventum.core.plugins.input.base import InputPluginConfigurationError
from eventum.core.plugins.input.base import \
    SampleInputPlugin as BaseSampleInputPlugin


class LinspaceInputPlugin(BaseSampleInputPlugin):
    """Input plugin for generating specified count of events linearly
    spaced in time.
    """

    def __init__(
        self,
        start: datetime,
        end: datetime,
        count: int,
        endpoint: bool
    ) -> None:
        if count <= 0:
            raise InputPluginConfigurationError('Count must be greater than 0')

        if end <= start:
            raise InputPluginConfigurationError(
                'End cannot be earlier or equal to start'
            )

        self._start = start
        self._end = end
        self._count = count
        self._endpoint = endpoint

    def sample(self, on_event: Callable[[datetime64], Any]) -> None:
        start = datetime64(
            self._start.astimezone(settings.TIMEZONE).replace(tzinfo=None)
        )
        end = datetime64(
            self._end.astimezone(settings.TIMEZONE).replace(tzinfo=None)
        )

        timedelta = timedelta64(end - start)
        space = linspace(
            start=0,
            stop=1,
            num=self._count,
            endpoint=self._endpoint,
        )
        timestamps = [start + delta for delta in space * timedelta]

        for ts in timestamps:
            on_event(ts)

    @classmethod
    def create_from_config(
        cls,
        config: LinspaceInputConfig     # type: ignore[override]
    ) -> Self:
        return cls(
            start=config.start,
            end=config.end,
            count=config.count,
            endpoint=config.endpoint
        )


def load_plugin():
    """Return class of plugin from current module."""
    return LinspaceInputPlugin
