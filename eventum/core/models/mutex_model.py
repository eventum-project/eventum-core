from abc import ABC
from typing import Any

from pydantic import BaseModel


class MutexModel(BaseModel, ABC, extra='forbid'):
    def _validate_mutual_exclusion(self):
        """Validate that only one field is passed and rest fields is `None`."""
        values = [
            self.__getattribute__(field) for field in self.model_fields.keys()
        ]
        print(values)

        if values.count(None) == (len(values) - 1):
            return self

        raise ValueError('Only one key can be defined at this level')

    def get_name(self) -> str:
        """Get name of used parameter."""
        return list(filter(
            lambda attr: self.__getattribute__(attr) is not None,
            self.model_fields.keys()
        )).pop()

    def get_value(self) -> Any:
        """Get value if used parameter."""
        return self.__getattribute__(self.get_name())
