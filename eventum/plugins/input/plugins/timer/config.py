
from pydantic import Field

from eventum.plugins.input.base.config import InputPluginConfig
from eventum.plugins.input.fields import VersatileDatetime


class TimerInputPluginConfig(InputPluginConfig, frozen=True):
    """Configuration for `timer` input plugin.

    Attributes
    ----------
    start : VersatileDatetime
        Start time of timer countdown, if not set current time is used

    seconds : float
        Number of seconds to wait before generating timestamp

    count : int
        Number of timestamps to generate

    repeat : bool
        Number of cycles to repeat, if value is not set (only for live
        mode) repeat infinitely
    """
    start: VersatileDatetime = Field(default=None, union_mode='left_to_right')
    seconds: float = Field(ge=0.1)
    count: int = Field(ge=1)
    repeat: int | None = Field(default=None, ge=1)
