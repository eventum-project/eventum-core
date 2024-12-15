from numpy import full

from eventum_plugins.input.base.plugin import InputPlugin, InputPluginParams
from eventum_plugins.input.plugins.static.config import StaticInputPluginConfig
from eventum_plugins.input.utils.time_utils import now64


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

    def _generate_sample(self) -> None:
        self._logger.info('Generating at current timestamp')
        timestamps = full(
            shape=self._config.count,
            fill_value=now64(timezone=self._timezone),
            dtype='datetime64[us]'
        )

        self._enqueue(timestamps)

    def _generate_live(self) -> None:
        self._generate_sample()
