from datetime import datetime
from typing import Iterator

from numpy import datetime64, full
from numpy.typing import NDArray

from eventum.plugins.input.base.plugin import InputPlugin, InputPluginParams
from eventum.plugins.input.plugins.static.config import StaticInputPluginConfig


class StaticInputPlugin(InputPlugin[StaticInputPluginConfig]):
    """Input plugin for generating specified number of timestamps with
    static value. All timestamps have a value of time when generation
    was started.
    """

    def __init__(
        self,
        config: StaticInputPluginConfig,
        params: InputPluginParams
    ) -> None:
        super().__init__(config, params)

    def generate(
        self,
        skip_past: bool = True
    ) -> Iterator[NDArray[datetime64]]:
        now = datetime.now().astimezone(self._timezone)
        self._logger.info(
            'Generating in range',
            start_timestamp=now.isoformat(),
            end_timestamp=now.isoformat()
        )
        timestamps = full(
            shape=self._config.count,
            fill_value=datetime64(now.replace(tzinfo=None)),
            dtype='datetime64[us]'
        )

        yield timestamps
