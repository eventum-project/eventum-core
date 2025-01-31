from pydantic import Field, field_validator

from eventum.plugins.input.base.config import InputPluginConfig
from eventum.plugins.input.fields import TimeKeyword, VersatileDatetimeStrict
from eventum.plugins.input.mixins import DaterangeValidatorMixin


class LinspaceInputPluginConfig(
    DaterangeValidatorMixin,
    InputPluginConfig,
    frozen=True
):
    """Configuration for `linspace` input plugin.

    Attributes
    ----------
    start : VersatileDatetimeStrict
        Start of the generating date range

    end : VersatileDatetimeStrict
        End of the generating date range

    count : int
        Number of events within date range

    endpoint : bool
        Whether to include end point of date range
    """
    start: VersatileDatetimeStrict = Field(union_mode='left_to_right')
    end: VersatileDatetimeStrict = Field(union_mode='left_to_right')
    count: int = Field(ge=1)
    endpoint: bool = True

    @field_validator('end')
    def validate_start(
        cls,
        v: VersatileDatetimeStrict
    ) -> VersatileDatetimeStrict:
        if isinstance(v, str) and v == TimeKeyword.NEVER.value:
            raise ValueError(
                f'Value "{TimeKeyword.NEVER.value}" is not allowed here'
            )

        return v
