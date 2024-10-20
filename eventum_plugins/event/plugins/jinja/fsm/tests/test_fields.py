from datetime import datetime

import pytest

from eventum_plugins.event.plugins.jinja.fsm.fields import (
    After, And, Before, Contains, Defined, Eq, Ge, Gt, HasTags, In, Le, LenEq,
    LenGe, LenGt, LenLe, LenLt, Lt, Matches, Not, Or, TimestampComponents)
from eventum_plugins.event.plugins.jinja.state import \
    SingleThreadState as State


def test_eq():
    state = State({'field': 10})
    assert Eq(eq={'locals.field': 10}).check(locals=state)
    assert not Eq(eq={'locals.field': 5}).check(locals=state)
    assert not Eq(eq={'locals.other_field': 10}).check(locals=state)


def test_gt():
    state = State({'field': 10})
    assert Gt(gt={'locals.field': 5}).check(locals=state)
    assert not Gt(gt={'locals.field': 10}).check(locals=state)
    assert not Gt(gt={'locals.field': 15}).check(locals=state)


def test_ge():
    state = State({'field': 10})
    assert Ge(ge={'locals.field': 5}).check(locals=state)
    assert Ge(ge={'locals.field': 10}).check(locals=state)
    assert not Ge(ge={'locals.field': 15}).check(locals=state)


def test_lt():
    state = State({'field': 10})
    assert Lt(lt={'locals.field': 15}).check(locals=state)
    assert not Lt(lt={'locals.field': 10}).check(locals=state)
    assert not Lt(lt={'locals.field': 5}).check(locals=state)


def test_le():
    state = State({'field': 10})
    assert Le(le={'locals.field': 15}).check(locals=state)
    assert Le(le={'locals.field': 10}).check(locals=state)
    assert not Le(le={'locals.field': 5}).check(locals=state)


def test_len_eq():
    state = State({'field': [1, 2, 3]})
    assert LenEq(len_eq={'locals.field': 3}).check(locals=state)
    assert not LenEq(len_eq={'locals.field': 2}).check(locals=state)


def test_len_gt():
    state = State({'field': [1, 2, 3]})
    assert LenGt(len_gt={'locals.field': 2}).check(locals=state)
    assert not LenGt(len_gt={'locals.field': 3}).check(locals=state)


def test_len_ge():
    state = State({'field': [1, 2, 3]})
    assert LenGe(len_ge={'locals.field': 2}).check(locals=state)
    assert LenGe(len_ge={'locals.field': 3}).check(locals=state)
    assert not LenGe(len_ge={'locals.field': 4}).check(locals=state)


def test_len_lt():
    state = State({'field': [1, 2, 3]})
    assert LenLt(len_lt={'locals.field': 4}).check(locals=state)
    assert not LenLt(len_lt={'locals.field': 3}).check(locals=state)


def test_len_le():
    state = State({'field': [1, 2, 3]})
    assert LenLe(len_le={'locals.field': 4}).check(locals=state)
    assert LenLe(len_le={'locals.field': 3}).check(locals=state)
    assert not LenLe(len_le={'locals.field': 2}).check(locals=state)


def test_contains():
    state = State({'field': [5, 10, 15]})
    assert Contains(contains={'locals.field': 10}).check(locals=state)
    assert not Contains(contains={'locals.field': 2}).check(locals=state)


def test_in():
    state = State({'field': 5})
    assert In(in_={'locals.field': [5, 10, 15]}).check(locals=state)
    assert not In(in_={'locals.field': [2, 4, 6]}).check(locals=state)


def test_has_tags():
    assert HasTags(has_tags='tag1').check(tags=['tag1', 'tag2'])
    assert HasTags(has_tags=['tag1', 'tag2']).check(
        tags=['tag1', 'tag2', 'tag3']
    )
    assert not HasTags(has_tags='tag3').check(
        tags=['tag1', 'tag2']
    )


def test_before():
    timestamp = datetime(2023, 10, 27, 10, 30, 20, 500_000).isoformat()
    assert Before(
        before=TimestampComponents(year=2024)
    ).check(timestamp=timestamp)

    assert Before(
        before=TimestampComponents(month=11)
    ).check(timestamp=timestamp)

    assert Before(
        before=TimestampComponents(day=28)
    ).check(timestamp=timestamp)

    assert Before(
        before=TimestampComponents(hour=11)
    ).check(timestamp=timestamp)

    assert Before(
        before=TimestampComponents(minute=31)
    ).check(timestamp=timestamp)

    assert Before(
        before=TimestampComponents(second=21)
    ).check(timestamp=timestamp)

    assert Before(
        before=TimestampComponents(microsecond=600_000)
    ).check(timestamp=timestamp)

    assert Before(
        before=TimestampComponents(year=2023, month=11)
    ).check(timestamp=timestamp)

    assert Before(
        before=TimestampComponents(year=2023, month=10, day=28)
    ).check(timestamp=timestamp)

    assert Before(
        before=TimestampComponents(year=2023, month=10, day=27, hour=11)
    ).check(timestamp=timestamp)

    assert not Before(
        before=TimestampComponents(year=2023)
    ).check(timestamp=timestamp)

    assert not Before(
        before=TimestampComponents(month=10)
    ).check(timestamp=timestamp)

    assert not Before(
        before=TimestampComponents(day=27)
    ).check(timestamp=timestamp)

    assert not Before(
        before=TimestampComponents(hour=10)
    ).check(timestamp=timestamp)

    assert not Before(
        before=TimestampComponents(year=2022, month=12)
    ).check(timestamp=timestamp)

    assert not Before(
        before=TimestampComponents(year=2022, month=12, day=31)
    ).check(timestamp=timestamp)


def test_after():
    timestamp = datetime(2023, 10, 27, 10, 30, 20, 500_000).isoformat()

    assert After(
        after=TimestampComponents(year=2022)
    ).check(timestamp=timestamp)

    assert After(
        after=TimestampComponents(month=9)
    ).check(timestamp=timestamp)

    assert After(
        after=TimestampComponents(day=26)
    ).check(timestamp=timestamp)

    assert After(
        after=TimestampComponents(hour=9)
    ).check(timestamp=timestamp)

    assert After(
        after=TimestampComponents(minute=29)
    ).check(timestamp=timestamp)

    assert After(
        after=TimestampComponents(second=19)
    ).check(timestamp=timestamp)

    assert After(
        after=TimestampComponents(microsecond=400_000)
    ).check(timestamp=timestamp)

    assert After(
        after=TimestampComponents(year=2023)
    ).check(timestamp=timestamp)

    assert After(
        after=TimestampComponents(month=10)
    ).check(timestamp=timestamp)

    assert After(
        after=TimestampComponents(day=27)
    ).check(timestamp=timestamp)

    assert After(
        after=TimestampComponents(hour=10)
    ).check(timestamp=timestamp)

    assert After(
        after=TimestampComponents(year=2023, month=10)
    ).check(timestamp=timestamp)

    assert After(
        after=TimestampComponents(year=2023, month=10, day=27)
    ).check(timestamp=timestamp)

    assert After(
        after=TimestampComponents(year=2023, month=10, day=27, hour=10)
    ).check(timestamp=timestamp)

    assert not After(
        after=TimestampComponents(hour=11)
    ).check(timestamp=timestamp)

    assert not After(
        after=TimestampComponents(year=2023, month=10, day=27, hour=11)
    ).check(timestamp=timestamp)


def test_matches():
    state = State({'field': 'abc'})
    assert Matches(matches={'locals.field': r'^a.*c$'}).check(locals=state)
    assert not Matches(matches={'locals.field': r'^b.*c$'}).check(locals=state)


def test_defined():
    state = State({'field': 10})
    assert Defined(defined='locals.field').check(locals=state)
    assert not Defined(defined='locals.other_field').check(locals=state)


def test_or():
    state = State({'field': 10})

    assert Or(
        or_=[
            Eq(eq={'locals.field': 5}),
            Eq(eq={'locals.field': 10})
        ]
    ).check(locals=state)

    assert not Or(
        or_=[
            Eq(eq={'locals.field': 5}),
            Eq(eq={'locals.field': 15})
        ]
    ).check(locals=state)


def test_and():
    state = State({'field': 10})

    assert And(
        and_=[
            Gt(gt={'locals.field': 5}),
            Lt(lt={'locals.field': 15})
        ]
    ).check(locals=state)

    assert not And(
        and_=[
            Gt(gt={'locals.field': 5}),
            Lt(lt={'locals.field': 7})
        ]
    ).check(locals=state)


def test_not():
    state = State({'field': 10})
    assert Not(not_=Eq(eq={'locals.field': 5})).check(locals=state)
    assert not Not(not_=Eq(eq={'locals.field': 10})).check(locals=state)


def test_complex_condition():
    state = State({'field1': 10, 'field2': 'abc'})

    condition = Or(
        or_=[
            And(
                and_=[
                    Gt(gt={'locals.field1': 5}),
                    Lt(lt={'locals.field1': 15})
                ]
            ),
            Not(
                not_=Matches(matches={'locals.field2': r'^a.*c$'})
            )
        ]
    )

    assert condition.check(locals=state)


def test_invalid_timestamp_components():
    with pytest.raises(ValueError):
        TimestampComponents()
