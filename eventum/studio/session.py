import os

from dataclasses import asdict
from datetime import datetime
from typing import Callable, Optional, MutableMapping

from yaml import YAMLError

from eventum.utils.fs import save_object_as_yaml, TIME_PATTERNS_DIR, validate_yaml_filename
import eventum.studio.models as models


def initialize(session_state: MutableMapping) -> None:
    """Create initial objects in session state."""
    if 'time_pattern_id_counter' not in session_state:
        session_state['time_pattern_id_counter'] = 1

    if 'time_pattern_ids' not in session_state:
        session_state['time_pattern_ids'] = []

    if 'available_colors' not in session_state:
        session_state['available_colors'] = set(['blue', 'green', 'orange', 'red', 'violet'])


def get_widget_key(name: str, id: int) -> str:
    """Get unique key for a widget that will be used in session state.
    The parameter `id` is assumed to be a time pattern ID.
    """
    return f'{name}_{id}'


def get_pattern_widget_keys(session_state: MutableMapping, id: int) -> list[str]:
    """Get all input widget keys that are in the pattern with specified `id`."""
    widget_keys = []
    for key in session_state.keys():
        parts = key.rsplit(sep='_', maxsplit=1)
        if parts and parts[-1] == str(id):
            widget_keys.append(key)

    return widget_keys


def get_default_time_pattern_config(label: str) -> models.TimePatternConfig:
    """Get `TimePatternConfig` object with default settings for
    new time pattern created by user.
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
            standard_deviation=0,
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
    """Initialize objects for new pattern in session state and increment
    `time_pattern_id_counter`.
    """
    id_counter = session_state['time_pattern_id_counter']
    session_state['time_pattern_ids'].append(id_counter)
    session_state['time_pattern_id_counter'] += 1

    if initial_state is None:
        initial_state = get_default_time_pattern_config(f'New Pattern {id_counter}')

    session_state[get_widget_key('pattern_label', id_counter)] = initial_state.label
    session_state[get_widget_key('pattern_color', id_counter)] = session_state['available_colors'].pop()
    session_state[get_widget_key('pattern_is_saved', id_counter)] = saved

    session_state[get_widget_key('oscillator_interval', id_counter)] = initial_state.oscillator.interval
    session_state[get_widget_key('oscillator_interval_unit', id_counter)] = initial_state.oscillator.unit
    session_state[get_widget_key('oscillator_start_timestamp', id_counter)] = initial_state.oscillator.start
    session_state[get_widget_key('oscillator_end_timestamp', id_counter)] = initial_state.oscillator.end

    session_state[get_widget_key('multiplier_ratio', id_counter)] = initial_state.multiplier.ratio

    session_state[get_widget_key('randomizer_deviation', id_counter)] = initial_state.randomizer.standard_deviation
    session_state[get_widget_key('randomizer_direction', id_counter)] = initial_state.randomizer.direction

    session_state[get_widget_key('spreader_function', id_counter)] = initial_state.spreader.function


def get_pattern_config(session_state: MutableMapping, id: int) -> models.TimePatternConfig:
    """Get `TimePatternConfig` object with current settings of time pattern with specified `id."""
    return models.TimePatternConfig(
        label=session_state[get_widget_key('pattern_label', id)],
        oscillator=models.OscillatorConfig(
            interval=session_state[get_widget_key('oscillator_interval', id)],
            unit=session_state[get_widget_key('oscillator_interval_unit', id)],
            start=session_state[get_widget_key('oscillator_start_timestamp', id)],
            end=session_state[get_widget_key('oscillator_end_timestamp', id)]
        ),
        multiplier=models.MultiplierConfig(
            ratio=session_state[get_widget_key('multiplier_ratio', id)]
        ),
        randomizer=models.RandomizerConfig(
            standard_deviation=session_state[get_widget_key('randomizer_deviation', id)],
            direction=session_state[get_widget_key('randomizer_direction', id)]
        ),
        spreader=models.SpreaderConfig(
            function=session_state[get_widget_key('spreader_function', id)],
            parameters=models.DistributionParameters()
            # TODO: think how to handle parameters for different types of distrib. functions
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
        def not_notify(message): pass
        notify_callback = not_notify

    filename = session_state[get_widget_key('pattern_filename', id)]

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

    session_state[get_widget_key('pattern_is_saved', id)] = True
    notify_callback(':green[Saved in library]')


def delete_pattern(session_state: MutableMapping, id: int) -> None:
    """Delete `id` from `time_pattern_ids` and all attributes related
    with this pattern in session state.
    """
    session_state['time_pattern_ids'].remove(id)

    released_color = session_state[get_widget_key('pattern_color', id)]
    session_state['available_colors'].add(released_color)

    widget_keys = get_pattern_widget_keys(session_state, id)
    for key in widget_keys:
        del session_state[key]


def load_pattern():
    """Load pattern from existing set."""
    ...
