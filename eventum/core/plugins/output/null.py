from typing import Iterable, Self

from eventum.core.models.output_config import NullOutputConfig
from eventum.core.plugins.output.base import BaseOutputPlugin


class NullOutputPlugin(BaseOutputPlugin):
    """Output plugin for writing events to nowhere."""

    async def _write(self, event: str) -> int:
        return 1

    async def _write_many(self, events: Iterable[str]) -> int:
        return len(list(events))

    @classmethod
    def create_from_config(
        cls,
        config: NullOutputConfig    # type: ignore
    ) -> Self:
        return NullOutputPlugin()


def load_plugin():
    """Return class of plugin from current module."""
    return NullOutputPlugin
