from copy import deepcopy
from datetime import datetime
from typing import Sequence

from eventum.core.models.metrics import CommonMetrics, Metrics, PluginsMetrics
from eventum.core.models.parameters.generator import GeneratorParameters
from eventum.plugins.event.base.plugin import EventPlugin
from eventum.plugins.input.base.plugin import InputPlugin
from eventum.plugins.output.base.plugin import OutputPlugin


class MetricsGauge:
    """Metrics gauge.

    Parameters
    ----------
    input : Sequence[InputPlugin]
        List of input plugins

    event: EventPlugin
        Event plugin

    output: Sequence[OutputPlugin]
        List of output plugins

    params: GeneratorParameters
        Generator parameters
    """

    def __init__(
        self,
        input: Sequence[InputPlugin],
        event: EventPlugin,
        output: Sequence[OutputPlugin],
        params: GeneratorParameters
    ) -> None:
        self._input = list(input)
        self._event = event
        self._output = list(output)
        self._params = params

        self._common_metrics = self._create_common_metrics()

    def _create_common_metrics(self) -> CommonMetrics:
        """Create common metrics.

        Returns
        -------
        CommonMetrics
            Common metrics
        """
        return CommonMetrics(
            started=datetime.now().astimezone(None).isoformat(),
            parameters=self._params.model_dump()
        )

    def gauge_metrics(self) -> Metrics:
        """Get gauged metrics.

        Returns
        -------
        Metrics
            Metrics
        """
        return Metrics(
            common=deepcopy(self._common_metrics),
            plugins=PluginsMetrics(
                input=[plugin.get_metrics() for plugin in self._input],
                event=self._event.get_metrics(),
                output=[plugin.get_metrics() for plugin in self._output]
            )
        )
