from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from operator import contains, eq, ge, gt, le, lt
from typing import (Annotated, Any, Callable, Generic, Literal, Self,
                    TypeAlias, TypeVar, Union)

from pydantic import (BaseModel, ConfigDict, Field, StringConstraints,
                      model_validator)

from eventum_plugins.event.plugins.jinja.context import (BaseEventContext,
                                                         EventContext,
                                                         EventStateContext,
                                                         EventTagsContext,
                                                         EventTimestampContext)
from eventum_plugins.event.plugins.jinja.fsm.operators import (len_eq, len_ge,
                                                               len_gt, len_le,
                                                               len_lt)
from eventum_plugins.event.plugins.jinja.state import State

logger = logging.getLogger(__name__)

context_T = TypeVar('context_T', bound=BaseEventContext)


class Checkable(ABC, Generic[context_T]):
    """Base class for models used in condition checking."""

    @abstractmethod
    def check(self, context: context_T) -> bool:
        """Check class-specific condition using provided context.

        Parameters
        ----------
        context : context_T
            Event context parameters for checking condition

        Returns
        -------
        bool
            Result of condition check

        Raises
        ------
        KeyError
            If required kwarg is missing
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


def _decompose_field(
    field: str
) -> tuple[Literal['locals', 'shared', 'globals'], str]:
    """Get state and field name from original field name."""
    state, field = field.split('.', maxsplit=1)

    return (state, field)   # type: ignore[return-value]


StateFieldName: TypeAlias = Annotated[
    str,
    StringConstraints(pattern=r'^(locals|shared|globals)\..+$')
]


class Eq(BaseModel, Checkable[EventStateContext], frozen=True, extra='forbid'):
    """Check if values are equal using '==' operator."""
    eq: dict[StateFieldName, Any] = Field(min_length=1, max_length=1)

    def check(self, context: EventStateContext) -> bool:
        field, value = next(iter(self.eq.items()))
        state, field = _decompose_field(field)
        return _compare_with_state(
            operator=eq,
            state=context[state],
            field_name=field,
            target_value=value
        )


class Gt(BaseModel, Checkable[EventStateContext], frozen=True, extra='forbid'):
    """Check if value is greater than other value using '>' operator."""
    gt: dict[StateFieldName, float | int] = Field(min_length=1, max_length=1)

    def check(self, context: EventStateContext) -> bool:
        field, value = next(iter(self.gt.items()))
        state, field = _decompose_field(field)
        return _compare_with_state(
            operator=gt,
            state=context[state],
            field_name=field,
            target_value=value
        )


class Ge(BaseModel, Checkable[EventStateContext], frozen=True, extra='forbid'):
    """Check if value is greater or equal to other value using '>='
    operator.
    """
    ge: dict[StateFieldName, float | int] = Field(min_length=1, max_length=1)

    def check(self, context: EventStateContext) -> bool:
        field, value = next(iter(self.ge.items()))
        state, field = _decompose_field(field)
        return _compare_with_state(
            operator=ge,
            state=context[state],
            field_name=field,
            target_value=value
        )


class Lt(BaseModel, Checkable[EventStateContext], frozen=True, extra='forbid'):
    """Check if value is lower than other value using '<' operator."""
    lt: dict[StateFieldName, float | int] = Field(min_length=1, max_length=1)

    def check(self, context: EventStateContext) -> bool:
        field, value = next(iter(self.lt.items()))
        state, field = _decompose_field(field)
        return _compare_with_state(
            operator=lt,
            state=context[state],
            field_name=field,
            target_value=value
        )


class Le(BaseModel, Checkable[EventStateContext], frozen=True, extra='forbid'):
    """Check if value is lower or equal to other value using '<='
    operator.
    """
    le: dict[StateFieldName, float | int] = Field(min_length=1, max_length=1)

    def check(self, context: EventStateContext) -> bool:
        field, value = next(iter(self.le.items()))
        state, field = _decompose_field(field)
        return _compare_with_state(
            operator=le,
            state=context[state],
            field_name=field,
            target_value=value
        )


class LenEq(
    BaseModel,
    Checkable[EventStateContext],
    frozen=True,
    extra='forbid'
):
    """Check if sequence length is equal to value."""
    len_eq: dict[StateFieldName, int] = Field(min_length=1, max_length=1)

    def check(self, context: EventStateContext) -> bool:
        field, value = next(iter(self.len_eq.items()))
        state, field = _decompose_field(field)
        return _compare_with_state(
            operator=len_eq,
            state=context[state],
            field_name=field,
            target_value=value
        )


class LenGt(
    BaseModel,
    Checkable[EventStateContext],
    frozen=True,
    extra='forbid'
):
    """Check if sequence length is greater than value."""
    len_gt: dict[StateFieldName, int] = Field(min_length=1, max_length=1)

    def check(self, context: EventStateContext) -> bool:
        field, value = next(iter(self.len_gt.items()))
        state, field = _decompose_field(field)
        return _compare_with_state(
            operator=len_gt,
            state=context[state],
            field_name=field,
            target_value=value
        )


class LenGe(
    BaseModel,
    Checkable[EventStateContext],
    frozen=True,
    extra='forbid'
):
    """Check if sequence length is greater or equal to value."""
    len_ge: dict[StateFieldName, int] = Field(min_length=1, max_length=1)

    def check(self, context: EventStateContext) -> bool:
        field, value = next(iter(self.len_ge.items()))
        state, field = _decompose_field(field)
        return _compare_with_state(
            operator=len_ge,
            state=context[state],
            field_name=field,
            target_value=value
        )


class LenLt(
    BaseModel,
    Checkable[EventStateContext],
    frozen=True,
    extra='forbid'
):
    """Check if sequence length is lower than value."""
    len_lt: dict[StateFieldName, int] = Field(min_length=1, max_length=1)

    def check(self, context: EventStateContext) -> bool:
        field, value = next(iter(self.len_lt.items()))
        state, field = _decompose_field(field)
        return _compare_with_state(
            operator=len_lt,
            state=context[state],
            field_name=field,
            target_value=value
        )


class LenLe(
    BaseModel,
    Checkable[EventStateContext],
    frozen=True,
    extra='forbid'
):
    """Check if sequence length is lower or equal to value."""
    len_le: dict[StateFieldName, int] = Field(min_length=1, max_length=1)

    def check(self, context: EventStateContext) -> bool:
        field, value = next(iter(self.len_le.items()))
        state, field = _decompose_field(field)
        return _compare_with_state(
            operator=len_le,
            state=context[state],
            field_name=field,
            target_value=value
        )


class Contains(
    BaseModel,
    Checkable[EventStateContext],
    frozen=True,
    extra='forbid'
):
    """Check if sequence value contains element."""
    contains: dict[StateFieldName, Any] = Field(min_length=1, max_length=1)

    model_config = ConfigDict(populate_by_name=True)

    def check(self, context: EventStateContext) -> bool:
        field, value = next(iter(self.contains.items()))
        state, field = _decompose_field(field)
        return _compare_with_state(
            operator=contains,
            state=context[state],
            field_name=field,
            target_value=value
        )


class In(BaseModel, Checkable[EventStateContext], frozen=True, extra='forbid'):
    """Check if value is in sequence."""
    in_: dict[StateFieldName, Any] = Field(
        min_length=1,
        max_length=1,
        alias='in'
    )

    model_config = ConfigDict(populate_by_name=True)

    def check(self, context: EventStateContext) -> bool:
        field, value = next(iter(self.in_.items()))
        state, field = _decompose_field(field)
        return _compare_with_state(
            operator=lambda a, b: contains(b, a),
            state=context[state],
            field_name=field,
            target_value=value
        )


class HasTags(
    BaseModel,
    Checkable[EventTagsContext],
    frozen=True,
    extra='forbid'
):
    """Check if event has specific tag."""
    has_tags: str | list[str] = Field(min_length=1)

    def check(self, context: EventTagsContext) -> bool:
        if isinstance(self.has_tags, str):
            target_tags = [self.has_tags]
        else:
            target_tags = self.has_tags

        return set(target_tags).issubset(set(context['tags']))


class TimestampComponents(BaseModel, frozen=True, extra='forbid'):
    """Time components of timestamp."""
    year: int | None = Field(default=None, ge=0, le=10_000)
    month: int | None = Field(default=None, ge=1, le=12)
    day: int | None = Field(default=None, ge=1, le=31)
    hour: int | None = Field(default=None, ge=0, le=24)
    minute: int | None = Field(default=None, ge=0, le=60)
    second: int | None = Field(default=None, ge=0, le=60)
    microsecond: int | None = Field(default=None, ge=0, le=1_000_000)

    @model_validator(mode='after')
    def validate_specified(self) -> Self:
        if not any(self.model_dump().values()):
            raise ValueError('At least one component must be specified')

        return self


class Before(
    BaseModel,
    Checkable[EventTimestampContext],
    frozen=True,
    extra='forbid'
):
    """Check if event timestamp is before specific time."""
    before: TimestampComponents

    def check(self, context: EventTimestampContext) -> bool:
        dt = context['timestamp']

        target = dt.replace(
            **self.before.model_dump(exclude_none=True)
        )

        return dt < target


class After(
    BaseModel,
    Checkable[EventTimestampContext],
    frozen=True,
    extra='forbid'
):
    """Check if event timestamp is after specific time."""
    after: TimestampComponents

    def check(self, context: EventTimestampContext) -> bool:
        dt = context['timestamp']

        target = dt.replace(
            **self.after.model_dump(exclude_none=True)
        )

        return dt >= target


class Matches(
    BaseModel,
    Checkable[EventStateContext],
    frozen=True,
    extra='forbid'
):
    """Check if a string matches a regular expression pattern."""
    matches: dict[StateFieldName, str] = Field(min_length=1, max_length=1)

    def check(self, context: EventStateContext) -> bool:
        field, pattern = next(iter(self.matches.items()))
        state, field = _decompose_field(field)
        state_value = context[state].get(field)

        if not isinstance(state_value, str):
            return False

        return bool(re.match(pattern, state_value))


NotDefined = object()


class Defined(
    BaseModel,
    Checkable[EventStateContext],
    frozen=True,
    extra='forbid'
):
    """Check if state has specified key."""
    defined: StateFieldName = Field(min_length=1)

    def check(self, context: EventStateContext) -> bool:
        state, field = _decompose_field(self.defined)
        return context[state].get(field, default=NotDefined) is not NotDefined


ConditionCheck: TypeAlias = (
    Eq | Gt | Ge | Lt | Le | Matches
    | LenEq | LenGt | LenGe | LenLt | LenLe
    | Contains | In
    | Before | After
    | Defined | HasTags
)
ConditionLogic: TypeAlias = Union['Or', 'And', 'Not']

Condition: TypeAlias = ConditionLogic | ConditionCheck


class Or(BaseModel, Checkable[EventContext], frozen=True, extra='forbid'):
    """Logic operator 'or' for combining checks or other logic
    operators.
    """
    or_: list[Condition] = Field(min_length=2, alias='or')

    model_config = ConfigDict(populate_by_name=True)

    def check(self, context: EventContext) -> bool:
        for clause in self.or_:
            if clause.check(context):
                return True

        return False


class And(BaseModel, Checkable[EventContext], frozen=True, extra='forbid'):
    """Logic operator 'and' for combining checks or other logic
    operators.
    """
    and_: list[Condition] = Field(min_length=2, alias='and')

    model_config = ConfigDict(populate_by_name=True)

    def check(self, context: EventContext) -> bool:
        for clause in self.and_:
            if not clause.check(context):
                return False

        return True


class Not(BaseModel, Checkable[EventContext], frozen=True, extra='forbid'):
    """Logic operator 'not' for negate checks or other logic
    operators.
    """
    not_: Condition = Field(alias='not')

    model_config = ConfigDict(populate_by_name=True)

    def check(self, context: EventContext) -> bool:
        return not self.not_.check(context)
