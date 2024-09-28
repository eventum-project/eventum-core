from typing import Any, TypeAlias, Union

from pydantic import BaseModel, Field


class In(BaseModel, frozen=True, extra='forbid'):
    """Check if value is in sequence."""
    in_: dict[str, Any] = Field(..., min_length=1, max_length=1, alias='in')


class Eq(BaseModel, frozen=True, extra='forbid'):
    """Check if values are equal using '==' operator."""
    eq: dict[str, Any] = Field(..., min_length=1, max_length=1)


class Gt(BaseModel, frozen=True, extra='forbid'):
    """Check if value is greater than other value using '>' operator."""
    gt: dict[str, float | int] = Field(..., min_length=1, max_length=1)


class Gte(BaseModel, frozen=True, extra='forbid'):
    """Check if value is greater or equal to other value using '>='
    operator.
    """
    gte: dict[str, float | int] = Field(..., min_length=1, max_length=1)


class Lt(BaseModel, frozen=True, extra='forbid'):
    """Check if value is lower than other value using '<' operator."""
    lt: dict[str, float | int] = Field(..., min_length=1, max_length=1)


class Lte(BaseModel, frozen=True, extra='forbid'):
    """Check if value is lower or equal to other value using '<='
    operator.
    """
    lte: dict[str, float | int] = Field(..., min_length=1, max_length=1)


ConditionCheck: TypeAlias = In | Eq | Gt | Gte | Lt | Lte

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
