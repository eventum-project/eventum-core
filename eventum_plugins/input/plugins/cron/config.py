
from croniter import croniter
from pydantic import Field, field_validator

from eventum_plugins.input.base.config import InputPluginConfig
from eventum_plugins.input.fields import VersatileDatetime


class CronInputPluginConfig(InputPluginConfig, frozen=True):
    """Configuration for `cron` input plugin.

    Attributes
    ----------
    start : VersatileDatetime, default = None
        Start of the generating date range

    end : VersatileDatetime, default = None
        End of the generating date range

    expression : str
        Cron expression (supports specifying seconds, years, random
        values and keywords, see more here:
        https://pypi.org/project/croniter/#about-second-repeats)

    count : int
        Number of events to generate for every interval
    """
    start: VersatileDatetime = Field(None, union_mode='left_to_right')
    end: VersatileDatetime = Field(None, union_mode='left_to_right')
    expression: str
    count: int = Field(..., gt=0)

    @field_validator('expression')
    def validate_expression(cls, v: str):
        if croniter.is_valid(v):
            return v

        raise ValueError('Invalid cron expression')
