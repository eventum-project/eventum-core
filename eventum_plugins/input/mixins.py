from typing import Self

from pydantic import model_validator
from pytz import timezone

from eventum_plugins.input.fields import VersatileDatetime
from eventum_plugins.input.tools import normalize_daterange


class DaterangeValidatorMixin:
    """Mixin for validation date range in plugin configuration models
    with `start` and `end` fields.
    """

    @model_validator(mode='after')
    def validate_interval(self) -> Self:
        self.start: VersatileDatetime
        self.end: VersatileDatetime

        normalize_daterange(self.start, self.end, timezone('UTC'))

        return self
