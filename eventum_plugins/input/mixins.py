from typing import Self

from pydantic import model_validator
from pytz import timezone

from eventum_plugins.input.normalizers import normalize_versatile_daterange


class DaterangeValidatorMixin:
    """Mixin for validation date range in plugin configuration models
    with `start` and `end` fields.
    """

    @model_validator(mode='after')
    def validate_interval(self) -> Self:
        # raises ValueError if start > end
        try:
            normalize_versatile_daterange(
                start=self.start,   # type: ignore[attr-defined]
                end=self.end,       # type: ignore[attr-defined]
                timezone=timezone('UTC'),
                none_start='min',
                none_end='max'
            )
        except OverflowError:
            raise ValueError(
                'Unable to validate date range due to datetime overflow'
            ) from None

        return self
