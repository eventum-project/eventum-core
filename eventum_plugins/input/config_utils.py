from datetime import datetime
from typing import Protocol

import dateparser
from pytz import BaseTzInfo

from eventum_plugins.input.fields import HumanDatetimeString


class SupportsDaterange(Protocol):
    """An ABC with attributes `start` and `end` of datetime-like types."""
    @property
    def start(self) -> datetime | HumanDatetimeString | None:
        pass

    @property
    def end(self) -> datetime | HumanDatetimeString | None:
        pass


def retrieve_daterange(
    config: SupportsDaterange,
    timezone: BaseTzInfo
) -> tuple[datetime, datetime]:
    """Retrieve daterange from the specified config instance. Field
    values can be of type `datetime`, `str` or `None`. In case of
    value is `None` in start field - current time is used, in end field
    - "never" (maximum datetime value) is used. In case of value is of
    type `str`, it should represent human readable date (or relative
    date) that `dateparser` can parse. Furthermore start datetime is
    used as `RELATIVE_BASE` for end field expression parsing. In case
    of value is of type `datetime`, it is only converted to the
    specified timezone. Types of start and end fields can be different
    within one config instance.

    Parameters
    ----------
    config : SupportsDaterange
        Plugin config instance that contains start and end fields

    timezone : BaseTzInfo
        Timezone that is used for datetime objects of daterange

    Returns
    -------
    tuple[datetime, datetime]
        Start and end of the daterange as a tuple
    """
    match config.start:
        case datetime():
            start_time = config.start.astimezone(timezone)
        case str():
            start_time = dateparser.parse(
                config.start,
                settings={                          # type: ignore[arg-type]
                    'TIMEZONE': timezone.zone,
                    'RETURN_AS_TIMEZONE_AWARE': True
                }
            )
            assert isinstance(start_time, datetime)
        case _:
            start_time = datetime.now(tz=timezone)

    match config.end:
        case datetime():
            end_time = config.end.astimezone(timezone)
        case str():
            end_time = dateparser.parse(
                config.end,
                settings={                          # type: ignore[arg-type]
                    'RELATIVE_BASE': start_time,
                    'TIMEZONE': timezone.zone,
                    'RETURN_AS_TIMEZONE_AWARE': True

                }
            )
            assert isinstance(end_time, datetime)
        case _:
            end_time = datetime.max.replace(tzinfo=timezone)

    return (start_time, end_time)
