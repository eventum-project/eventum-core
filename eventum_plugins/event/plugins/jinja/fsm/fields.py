from abc import ABC, abstractmethod
from typing import Any, TypeAlias, Union

from pydantic import BaseModel, Field

from eventum_plugins.event.state import State


class Checkable(ABC):
    @abstractmethod
    def check(self, timestamp: str, tags: list[str], state: State) -> bool:
        ...


SharedStateFieldName: TypeAlias = str


class Eq(BaseModel, frozen=True, extra='forbid'):
    """Check if values are equal using '==' operator."""
    eq: dict[SharedStateFieldName, Any] = Field(
        ...,
        min_length=1,
        max_length=1
    )


class Gt(BaseModel, frozen=True, extra='forbid'):
    """Check if value is greater than other value using '>' operator."""
    gt: dict[SharedStateFieldName, float | int] = Field(
        ...,
        min_length=1,
        max_length=1
    )


class Ge(BaseModel, frozen=True, extra='forbid'):
    """Check if value is greater or equal to other value using '>='
    operator.
    """
    ge: dict[SharedStateFieldName, float | int] = Field(
        ...,
        min_length=1,
        max_length=1
    )


class Lt(BaseModel, frozen=True, extra='forbid'):
    """Check if value is lower than other value using '<' operator."""
    lt: dict[SharedStateFieldName, float | int] = Field(
        ...,
        min_length=1,
        max_length=1
    )


class Le(BaseModel, frozen=True, extra='forbid'):
    """Check if value is lower or equal to other value using '<='
    operator.
    """
    le: dict[SharedStateFieldName, float | int] = Field(
        ...,
        min_length=1,
        max_length=1
    )


class LenEq(BaseModel, frozen=True, extra='forbid'):
    """Check if sequence length is equal to value."""
    len_eq: dict[SharedStateFieldName, int] = Field(
        ...,
        min_length=1,
        max_length=1
    )


class LenGt(BaseModel, frozen=True, extra='forbid'):
    """Check if sequence length is greater than value."""
    len_gt: dict[SharedStateFieldName, int] = Field(
        ...,
        min_length=1,
        max_length=1
    )


class LenGe(BaseModel, frozen=True, extra='forbid'):
    """Check if sequence length is greater or equal to value."""
    len_ge: dict[SharedStateFieldName, int] = Field(
        ...,
        min_length=1,
        max_length=1
    )


class LenLt(BaseModel, frozen=True, extra='forbid'):
    """Check if sequence length is lower than value."""
    len_lt: dict[SharedStateFieldName, int] = Field(
        ...,
        min_length=1,
        max_length=1
    )


class LenLe(BaseModel, frozen=True, extra='forbid'):
    """Check if sequence length is lower or equal to value."""
    len_le: dict[SharedStateFieldName, int] = Field(
        ...,
        min_length=1,
        max_length=1
    )


class In(BaseModel, frozen=True, extra='forbid'):
    """Check if value is in sequence."""
    in_: dict[SharedStateFieldName, Any] = Field(
        ...,
        min_length=1,
        max_length=1,
        alias='in'
    )


class HasTags(BaseModel, frozen=True, extra='forbid'):
    """Check if event has specific tag."""
    has_tags: str | list[str] = Field(..., min_length=1)


ConditionCheck: TypeAlias = (
    Eq | Gt | Ge | Lt | Le
    | LenEq | LenGt | LenGe | LenLt | LenLe
    | In | HasTags
)

ConditionLogic: TypeAlias = Union['Or', 'And', 'Not']


class Or(BaseModel, frozen=True, extra='forbid'):
    """Logic operator 'or' for combining checks or other logic
    operators.
    """
    or_: list[ConditionLogic | ConditionCheck] = Field(
        ...,
        min_length=2,
        alias='or'
    )


class And(BaseModel, frozen=True, extra='forbid'):
    """Logic operator 'and' for combining checks or other logic
    operators.
    """
    and_: list[ConditionLogic | ConditionCheck] = Field(
        ...,
        min_length=2,
        alias='and'
    )


class Not(BaseModel, frozen=True, extra='forbid'):
    """Logic operator 'not' for negate checks or other logic
    operators.
    """
    not_: ConditionLogic | ConditionCheck = Field(..., alias='not')


Condition: TypeAlias = ConditionLogic | ConditionCheck
