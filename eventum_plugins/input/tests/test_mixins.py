import pytest
from pydantic import Field

from eventum_plugins.input.base.config import InputPluginConfig
from eventum_plugins.input.fields import VersatileDatetime
from eventum_plugins.input.mixins import DaterangeValidatorMixin


class NotValidatedConfig(InputPluginConfig, frozen=True):
    start: VersatileDatetime = Field(default=None, union_mode='left_to_right')
    end: VersatileDatetime = Field(default=None, union_mode='left_to_right')

    __test__ = False


class ValidatedConfig(DaterangeValidatorMixin, InputPluginConfig, frozen=True):
    start: VersatileDatetime = Field(default=None, union_mode='left_to_right')
    end: VersatileDatetime = Field(default=None, union_mode='left_to_right')

    __test__ = False


def test_daterange_validator_mixin():
    NotValidatedConfig(start='now', end='1969 year')

    with pytest.raises(ValueError):
        ValidatedConfig(start='now', end='1969 year')
