from typing import Self

from pydantic import model_validator
from pytz import timezone

from eventum_plugins.input.fields import VersatileDatetime
from eventum_plugins.input.normalizers import normalize_versatile_daterange


class DaterangeValidatorMixin:
    """Mixin for validation date range in plugin configuration models
    with `start` and `end` fields.
    """

    @model_validator(mode='after')
    def validate_interval(self) -> Self:
        self.start: VersatileDatetime
        self.end: VersatileDatetime

        # raises ValueError if start > end
        try:
            normalize_versatile_daterange(
                start=self.start,
                end=self.end,
                timezone=timezone('UTC')
            )
        except OverflowError:
            raise ValueError(
                'Unable to validate date range due to datetime overflow '
                'for UTC timezone'
            ) from None

        return self
