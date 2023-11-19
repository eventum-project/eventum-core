import os
from dataclasses import asdict
from datetime import datetime
from typing import Callable, MutableMapping, Optional

from yaml import YAMLError

import eventum.studio.models as models
from eventum.utils.fs import (TIME_PATTERNS_DIR, save_object_as_yaml,
                              validate_yaml_filename)


def initialize(session_state: MutableMapping) -> None:
    """Create initial objects in session state."""
    if 'initialized' in session_state:
        return

    if 'time_pattern_id_counter' not in session_state:
        session_state['time_pattern_id_counter'] = 1

    if 'time_pattern_ids' not in session_state:
        session_state['time_pattern_ids'] = []

    if 'available_colors' not in session_state:
        session_state['available_colors'] = set(
            ['blue', 'green', 'orange', 'red', 'violet']
        )

    session_state['initialized'] = True


def get_pattern_widget_key(base_key: str, pattern_id: int) -> str:
    """Get unique key for a widget that will be used in session state."""
    return f'{base_key}_{pattern_id}'


_pwk = get_pattern_widget_key


def get_all_pattern_keys(
    session_state: MutableMapping,
    id: int
) -> list[str]:
    """Get all widget keys that are in the pattern with specified `id`."""
    widget_keys = []
    for key in session_state.keys():
        parts = key.rsplit(sep='_', maxsplit=1)
        if parts and parts[-1] == str(id):
            widget_keys.append(key)

    return widget_keys


def get_default_time_pattern_config(label: str) -> models.TimePatternConfig:
    """Get `TimePatternConfig` object with default settings for new
    time pattern created by user.
    """
    return models.TimePatternConfig(
        label=label,
        oscillator=models.OscillatorConfig(
            interval=1,
            unit=models.TimeUnit.SECONDS.value,
            start=datetime.now().replace(microsecond=0).isoformat(),
            end=datetime.now().replace(microsecond=0).isoformat()
        ),
        multiplier=models.MultiplierConfig(ratio=1),
        randomizer=models.RandomizerConfig(
            deviation=0,
            direction=models.RandomizerDirection.MIXED.value
        ),
        spreader=models.SpreaderConfig(
            function=models.DistributionFunction.LINEAR.value,
            parameters=models.DistributionParameters()
        )
    )


def add_pattern(
    session_state: MutableMapping,
    initial_state: Optional[models.TimePatternConfig] = None,
    saved: bool = False
) -> None:
    """Initialize objects for new pattern in session state and
    increment `time_pattern_id_counter`.
    """
    ss = session_state

    id_cnt = ss['time_pattern_id_counter']
    ss['time_pattern_ids'].append(id_cnt)
    ss['time_pattern_id_counter'] += 1

    if initial_state is None:
        initial_state = get_default_time_pattern_config(
            f'New Pattern {id_cnt}'
        )
    init = initial_state

    ss[_pwk('pattern_label', id_cnt)] = init.label
    ss[_pwk('pattern_color', id_cnt)] = ss['available_colors'].pop()
    ss[_pwk('pattern_is_saved', id_cnt)] = saved

    ss[_pwk('oscillator_interval', id_cnt)] = init.oscillator.interval
    ss[_pwk('oscillator_interval_unit', id_cnt)] = init.oscillator.unit
    ss[_pwk('oscillator_start_timestamp', id_cnt)] = init.oscillator.start
    ss[_pwk('oscillator_end_timestamp', id_cnt)] = init.oscillator.end

    ss[_pwk('multiplier_ratio', id_cnt)] = init.multiplier.ratio

    ss[_pwk('randomizer_deviation', id_cnt)] = init.randomizer.deviation
    ss[_pwk('randomizer_direction', id_cnt)] = init.randomizer.direction

    ss[_pwk('spreader_function', id_cnt)] = init.spreader.function


def get_pattern_config(
    session_state: MutableMapping,
    id: int
) -> models.TimePatternConfig:
    """Get `TimePatternConfig` object with current settings of time
    pattern with specified `id.
    """
    ss = session_state

    return models.TimePatternConfig(
        label=ss[_pwk('pattern_label', id)],
        oscillator=models.OscillatorConfig(
            interval=ss[_pwk('oscillator_interval', id)],
            unit=ss[_pwk('oscillator_interval_unit', id)],
            start=ss[_pwk('oscillator_start_timestamp', id)],
            end=ss[_pwk('oscillator_end_timestamp', id)]
        ),
        multiplier=models.MultiplierConfig(
            ratio=ss[_pwk('multiplier_ratio', id)]
        ),
        randomizer=models.RandomizerConfig(
            deviation=ss[_pwk('randomizer_deviation', id)],
            direction=ss[_pwk('randomizer_direction', id)]
        ),
        spreader=models.SpreaderConfig(
            function=ss[_pwk('spreader_function', id)],
            parameters=models.DistributionParameters()
            # TODO: think how to handle parameters for different distributions
        )
    )


def save_pattern(
    session_state: MutableMapping,
    id: int,
    overwrite: bool = False,
    notify_callback: Optional[Callable] = None
) -> None:
    """Save current state of pattern to library directory as yaml
    configuration file.
    """
    if notify_callback is None:
        def not_notify(_): pass
        notify_callback = not_notify

    filename = session_state[_pwk('pattern_filename', id)]
    ok, message = validate_yaml_filename(filename)
    if not ok:
        notify_callback(f':red[{message}]')
        return

    filepath = os.path.join(TIME_PATTERNS_DIR, filename)
    if overwrite is False and os.path.exists(filepath):
        notify_callback(':red[File already exists in library]')
        return

    try:
        save_object_as_yaml(
            data=asdict(get_pattern_config(session_state, id)),
            filepath=filepath
        )
    except (OSError, YAMLError) as e:
        notify_callback(f':red[{e.strerror}]')
        return

    session_state[_pwk('pattern_is_saved', id)] = True
    notify_callback(':green[Saved in library]')


def delete_pattern(session_state: MutableMapping, id: int) -> None:
    """Delete `id` from `time_pattern_ids` and all attributes related
    with this pattern in session state.
    """
    session_state['time_pattern_ids'].remove(id)

    released_color = session_state[_pwk('pattern_color', id)]
    session_state['available_colors'].add(released_color)

    widget_keys = get_all_pattern_keys(session_state, id)
    for key in widget_keys:
        del session_state[key]


def load_pattern():
    """Load pattern from existing set."""
    ...
