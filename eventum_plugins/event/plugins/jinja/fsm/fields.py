import logging
from abc import ABC, abstractmethod
from operator import contains, eq, ge, gt, le, lt
from typing import Any, Callable, TypeAlias, Union

from pydantic import BaseModel, Field

from eventum_plugins.event.plugins.jinja.fsm.operators import (len_eq, len_ge,
                                                               len_gt, len_le,
                                                               len_lt)
from eventum_plugins.event.state import State

logger = logging.getLogger(__name__)


class Checkable(ABC):
    """Base class for models used in condition checking."""

    @abstractmethod
    def check(self, timestamp: str, tags: list[str], state: State) -> bool:
        """Check class-specific condition using current state.

        Parameters
        ----------
        timestamp : str
            Timestamp of event

        tags : list[str]
            Tags from input plugin that generated event

        state : State
            Shared state of templates

        Returns
        -------
        bool
            Result of condition check
        """
        ...


def _compare_with_state(
    operator: Callable[[Any, Any], bool],
    state: State,
    field_name: str,
    target_value: Any
) -> bool:
    """Perform comparison with value from state.

    Parameters
    ----------
    operator : Callable[[Any, Any], bool]
        Binary operator for comparing values

    state : State
        State with value for comparison

    field_name : str
        Field name of value in state that is compared with target value

    target_value : Any
        Target value for comparison

    Returns
    -------
    bool
        Result of comparison
    """
    state_value = state.get(field_name)

    if state_value is None:
        logger.warning(
            'Comparing with None: '
            f'{operator.__name__}({state_value}, {target_value}), '
            f'where {state_value} is value of "{field_name}" field from state'
        )
        return False

    try:
        return operator(state_value, target_value)
    except TypeError as e:
        logger.warning(
            'Comparing error: '
            f'{operator.__name__}({state_value}, {target_value}), '
            f'where {state_value} is value of "{field_name}" field from '
            f'state, {e}'
        )
        return False


SharedStateFieldName: TypeAlias = str


class Eq(BaseModel, Checkable, frozen=True, extra='forbid'):
    """Check if values are equal using '==' operator."""
    eq: dict[SharedStateFieldName, Any] = Field(
        ...,
        min_length=1,
        max_length=1
    )

    def check(self, timestamp: str, tags: list[str], state: State) -> bool:
        field, value = next(iter(self.eq.items()))
        return _compare_with_state(
            operator=eq,
            state=state,
            field_name=field,
            target_value=value
        )


class Gt(BaseModel, Checkable, frozen=True, extra='forbid'):
    """Check if value is greater than other value using '>' operator."""
    gt: dict[SharedStateFieldName, float | int] = Field(
        ...,
        min_length=1,
        max_length=1
    )

    def check(self, timestamp: str, tags: list[str], state: State) -> bool:
        field, value = next(iter(self.gt.items()))
        return _compare_with_state(
            operator=gt,
            state=state,
            field_name=field,
            target_value=value
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

    def check(self, timestamp: str, tags: list[str], state: State) -> bool:
        field, value = next(iter(self.ge.items()))
        return _compare_with_state(
            operator=ge,
            state=state,
            field_name=field,
            target_value=value
        )


class Lt(BaseModel, frozen=True, extra='forbid'):
    """Check if value is lower than other value using '<' operator."""
    lt: dict[SharedStateFieldName, float | int] = Field(
        ...,
        min_length=1,
        max_length=1
    )

    def check(self, timestamp: str, tags: list[str], state: State) -> bool:
        field, value = next(iter(self.lt.items()))
        return _compare_with_state(
            operator=lt,
            state=state,
            field_name=field,
            target_value=value
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

    def check(self, timestamp: str, tags: list[str], state: State) -> bool:
        field, value = next(iter(self.le.items()))
        return _compare_with_state(
            operator=le,
            state=state,
            field_name=field,
            target_value=value
        )


class LenEq(BaseModel, frozen=True, extra='forbid'):
    """Check if sequence length is equal to value."""
    len_eq: dict[SharedStateFieldName, int] = Field(
        ...,
        min_length=1,
        max_length=1
    )

    def check(self, timestamp: str, tags: list[str], state: State) -> bool:
        field, value = next(iter(self.len_eq.items()))
        return _compare_with_state(
            operator=len_eq,
            state=state,
            field_name=field,
            target_value=value
        )


class LenGt(BaseModel, frozen=True, extra='forbid'):
    """Check if sequence length is greater than value."""
    len_gt: dict[SharedStateFieldName, int] = Field(
        ...,
        min_length=1,
        max_length=1
    )

    def check(self, timestamp: str, tags: list[str], state: State) -> bool:
        field, value = next(iter(self.len_gt.items()))
        return _compare_with_state(
            operator=len_gt,
            state=state,
            field_name=field,
            target_value=value
        )


class LenGe(BaseModel, frozen=True, extra='forbid'):
    """Check if sequence length is greater or equal to value."""
    len_ge: dict[SharedStateFieldName, int] = Field(
        ...,
        min_length=1,
        max_length=1
    )

    def check(self, timestamp: str, tags: list[str], state: State) -> bool:
        field, value = next(iter(self.len_ge.items()))
        return _compare_with_state(
            operator=len_ge,
            state=state,
            field_name=field,
            target_value=value
        )


class LenLt(BaseModel, frozen=True, extra='forbid'):
    """Check if sequence length is lower than value."""
    len_lt: dict[SharedStateFieldName, int] = Field(
        ...,
        min_length=1,
        max_length=1
    )

    def check(self, timestamp: str, tags: list[str], state: State) -> bool:
        field, value = next(iter(self.len_lt.items()))
        return _compare_with_state(
            operator=len_lt,
            state=state,
            field_name=field,
            target_value=value
        )


class LenLe(BaseModel, frozen=True, extra='forbid'):
    """Check if sequence length is lower or equal to value."""
    len_le: dict[SharedStateFieldName, int] = Field(
        ...,
        min_length=1,
        max_length=1
    )

    def check(self, timestamp: str, tags: list[str], state: State) -> bool:
        field, value = next(iter(self.len_le.items()))
        return _compare_with_state(
            operator=len_le,
            state=state,
            field_name=field,
            target_value=value
        )


class In(BaseModel, frozen=True, extra='forbid'):
    """Check if value is in sequence."""
    in_: dict[SharedStateFieldName, Any] = Field(
        ...,
        min_length=1,
        max_length=1,
        alias='in'
    )

    def check(self, timestamp: str, tags: list[str], state: State) -> bool:
        field, value = next(iter(self.in_.items()))
        return _compare_with_state(
            operator=contains,
            state=state,
            field_name=field,
            target_value=value
        )


class HasTags(BaseModel, frozen=True, extra='forbid'):
    """Check if event has specific tag."""
    has_tags: str | list[str] = Field(..., min_length=1)

    def check(self, timestamp: str, tags: list[str], state: State) -> bool:
        if isinstance(self.has_tags, str):
            target_tags = [self.has_tags]
        else:
            target_tags = self.has_tags

        return set(target_tags).issubset(set(tags))


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
