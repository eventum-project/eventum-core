
from pydantic import Field

from eventum_plugins.input.base.config import InputPluginConfig


class SampleInputPluginConfig(InputPluginConfig, frozen=True):
    """Configuration for `sample` input plugin.

    Attributes
    ----------
    count : int
        Number of events to generate
    """
    count: int = Field(..., gt=0)
