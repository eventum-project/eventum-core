from datetime import datetime

import pytest

from eventum_plugins.event.plugins.jinja.fsm.fields import (
    After, And, Before, Defined, Eq, Ge, Gt, HasTags, In, Le, LenEq, LenGe,
    LenGt, LenLe, LenLt, Lt, Matches, Not, Or, TimestampComponents)
from eventum_plugins.event.state import SingleThreadState as State


def test_eq():
    state = State({'field': 10})
    assert Eq(eq={'field': 10}).check('', [], state)
    assert not Eq(eq={'field': 5}).check('', [], state)
    assert not Eq(eq={'other_field': 10}).check('', [], state)


def test_gt():
    state = State({'field': 10})
    assert Gt(gt={'field': 5}).check('', [], state)
    assert not Gt(gt={'field': 10}).check('', [], state)
    assert not Gt(gt={'field': 15}).check('', [], state)


def test_ge():
    state = State({'field': 10})
    assert Ge(ge={'field': 5}).check('', [], state)
    assert Ge(ge={'field': 10}).check('', [], state)
    assert not Ge(ge={'field': 15}).check('', [], state)


def test_lt():
    state = State({'field': 10})
    assert Lt(lt={'field': 15}).check('', [], state)
    assert not Lt(lt={'field': 10}).check('', [], state)
    assert not Lt(lt={'field': 5}).check('', [], state)


def test_le():
    state = State({'field': 10})
    assert Le(le={'field': 15}).check('', [], state)
    assert Le(le={'field': 10}).check('', [], state)
    assert not Le(le={'field': 5}).check('', [], state)


def test_len_eq():
    state = State({'field': [1, 2, 3]})
    assert LenEq(len_eq={'field': 3}).check('', [], state)
    assert not LenEq(len_eq={'field': 2}).check('', [], state)


def test_len_gt():
    state = State({'field': [1, 2, 3]})
    assert LenGt(len_gt={'field': 2}).check('', [], state)
    assert not LenGt(len_gt={'field': 3}).check('', [], state)


def test_len_ge():
    state = State({'field': [1, 2, 3]})
    assert LenGe(len_ge={'field': 2}).check('', [], state)
    assert LenGe(len_ge={'field': 3}).check('', [], state)
    assert not LenGe(len_ge={'field': 4}).check('', [], state)


def test_len_lt():
    state = State({'field': [1, 2, 3]})
    assert LenLt(len_lt={'field': 4}).check('', [], state)
    assert not LenLt(len_lt={'field': 3}).check('', [], state)


def test_len_le():
    state = State({'field': [1, 2, 3]})
    assert LenLe(len_le={'field': 4}).check('', [], state)
    assert LenLe(len_le={'field': 3}).check('', [], state)
    assert not LenLe(len_le={'field': 2}).check('', [], state)


def test_in():
    state = State({'field': [5, 10, 15]})
    assert In(in_={'field': 10}).check('', [], state)
    assert not In(in_={'field': 2}).check('', [], state)


def test_has_tags():
    assert HasTags(has_tags='tag1').check('', ['tag1', 'tag2'], State())
    assert HasTags(has_tags=['tag1', 'tag2']).check(
        timestamp='',
        tags=['tag1', 'tag2', 'tag3'],
        state=State()
    )
    assert not HasTags(has_tags='tag3').check(
        timestamp='',
        tags=['tag1', 'tag2'],
        state=State()
    )


def test_before():
    timestamp = datetime(2023, 10, 27, 10, 30, 20, 500_000).isoformat()
    assert Before(
        before=TimestampComponents(year=2024)
    ).check(timestamp, [], State({}))

    assert Before(
        before=TimestampComponents(month=11)
    ).check(timestamp, [], State({}))

    assert Before(
        before=TimestampComponents(day=28)
    ).check(timestamp, [], State({}))

    assert Before(
        before=TimestampComponents(hour=11)
    ).check(timestamp, [], State({}))

    assert Before(
        before=TimestampComponents(minute=31)
    ).check(timestamp, [], State({}))

    assert Before(
        before=TimestampComponents(second=21)
    ).check(timestamp, [], State({}))

    assert Before(
        before=TimestampComponents(microsecond=600_000)
    ).check(timestamp, [], State({}))

    assert Before(
        before=TimestampComponents(year=2023, month=11)
    ).check(timestamp, [], State({}))

    assert Before(
        before=TimestampComponents(year=2023, month=10, day=28)
    ).check(timestamp, [], State({}))

    assert Before(
        before=TimestampComponents(year=2023, month=10, day=27, hour=11)
    ).check(timestamp, [], State({}))

    assert not Before(
        before=TimestampComponents(year=2023)
    ).check(timestamp, [], State({}))

    assert not Before(
        before=TimestampComponents(month=10)
    ).check(timestamp, [], State({}))

    assert not Before(
        before=TimestampComponents(day=27)
    ).check(timestamp, [], State({}))

    assert not Before(
        before=TimestampComponents(hour=10)
    ).check(timestamp, [], State({}))

    assert not Before(
        before=TimestampComponents(year=2022, month=12)
    ).check(timestamp, [], State({}))

    assert not Before(
        before=TimestampComponents(year=2022, month=12, day=31)
    ).check(timestamp, [], State({}))


def test_after():
    timestamp = datetime(2023, 10, 27, 10, 30, 20, 500_000).isoformat()

    assert After(
        after=TimestampComponents(year=2022)
    ).check(timestamp, [], State({}))

    assert After(
        after=TimestampComponents(month=9)
    ).check(timestamp, [], State({}))

    assert After(
        after=TimestampComponents(day=26)
    ).check(timestamp, [], State({}))

    assert After(
        after=TimestampComponents(hour=9)
    ).check(timestamp, [], State({}))

    assert After(
        after=TimestampComponents(minute=29)
    ).check(timestamp, [], State({}))

    assert After(
        after=TimestampComponents(second=19)
    ).check(timestamp, [], State({}))

    assert After(
        after=TimestampComponents(microsecond=400_000)
    ).check(timestamp, [], State({}))

    assert After(
        after=TimestampComponents(year=2023)
    ).check(timestamp, [], State({}))

    assert After(
        after=TimestampComponents(month=10)
    ).check(timestamp, [], State({}))

    assert After(
        after=TimestampComponents(day=27)
    ).check(timestamp, [], State({}))

    assert After(
        after=TimestampComponents(hour=10)
    ).check(timestamp, [], State({}))

    assert After(
        after=TimestampComponents(year=2023, month=10)
    ).check(timestamp, [], State({}))

    assert After(
        after=TimestampComponents(year=2023, month=10, day=27)
    ).check(timestamp, [], State({}))

    assert After(
        after=TimestampComponents(year=2023, month=10, day=27, hour=10)
    ).check(timestamp, [], State({}))

    assert not After(
        after=TimestampComponents(hour=11)
    ).check(timestamp, [], State({}))

    assert not After(
        after=TimestampComponents(year=2023, month=10, day=27, hour=11)
    ).check(timestamp, [], State({}))


def test_matches():
    state = State({'field': 'abc'})
    assert Matches(matches={'field': r'^a.*c$'}).check('', [], state)
    assert not Matches(matches={'field': r'^b.*c$'}).check('', [], state)


def test_defined():
    state = State({'field': 10})
    assert Defined(defined='field').check('', [], state)
    assert not Defined(defined='other_field').check('', [], state)


def test_or():
    state = State({'field': 10})

    assert Or(
        or_=[
            Eq(eq={'field': 5}),
            Eq(eq={'field': 10})
        ]
    ).check('', [], state)

    assert not Or(
        or_=[
            Eq(eq={'field': 5}),
            Eq(eq={'field': 15})
        ]
    ).check('', [], state)


def test_and():
    state = State({'field': 10})

    assert And(
        and_=[
            Gt(gt={'field': 5}),
            Lt(lt={'field': 15})
        ]
    ).check('', [], state)

    assert not And(
        and_=[
            Gt(gt={'field': 5}),
            Lt(lt={'field': 7})
        ]
    ).check('', [], state)


def test_not():
    state = State({'field': 10})
    assert Not(not_=Eq(eq={'field': 5})).check('', [], state)
    assert not Not(not_=Eq(eq={'field': 10})).check('', [], state)


def test_complex_condition():
    state = State({'field1': 10, 'field2': 'abc'})

    condition = Or(
        or_=[
            And(
                and_=[
                    Gt(gt={'field1': 5}),
                    Lt(lt={'field1': 15})
                ]
            ),
            Not(
                not_=Matches(matches={'field2': r'^a.*c$'})
            )
        ]
    )

    assert condition.check('', [], state)


def test_invalid_timestamp_components():
    with pytest.raises(ValueError):
        TimestampComponents()
