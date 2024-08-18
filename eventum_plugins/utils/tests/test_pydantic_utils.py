from datetime import datetime

import pytest
from pydantic import BaseModel, Field, ValidationError

from eventum_plugins.utils.pydantic_utils import HumanDatetimeString


def test_validate_human_datetime():
    class MyModel(BaseModel):
        start: datetime | HumanDatetimeString | None = Field(
            None,
            union_mode='left_to_right'
        )
        end: datetime | HumanDatetimeString | None = Field(
            None,
            union_mode='left_to_right'
        )

    obj = MyModel.model_validate(
        {
            'start': '2024-01-01T00:00:00.000Z',
            'end': 'after 24 hours'
        }
    )

    assert obj.start == datetime.fromisoformat('2024-01-01T00:00:00.000Z')
    assert obj.end == 'after 24 hours'


def test_parsable_datetime_string_with_invalid_value():
    class MyModel(BaseModel):
        start: datetime | HumanDatetimeString | None = Field(
            None,
            union_mode='left_to_right'
        )
        end: datetime | HumanDatetimeString | None = Field(
            None,
            union_mode='left_to_right'
        )

    with pytest.raises(ValidationError):
        MyModel.model_validate({'start': '00:00', 'end': 'you know when'})
