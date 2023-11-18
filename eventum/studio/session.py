import datetime
import os

from typing import Callable, Optional, MutableMapping

from yaml import YAMLError

from eventum.utils.fs import save_object_as_yaml, TIME_PATTERNS_DIR, validate_yaml_filename


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


def add_pattern(session_state: MutableMapping) -> None:
    """Initialize new pattern objects in session state and increment
    `time_pattern_id_counter`.
    """
    pattern_id_counter = session_state['time_pattern_id_counter']
    timestamp = datetime.datetime.now().replace(microsecond=0).isoformat()

    session_state['time_pattern_ids'].append(pattern_id_counter)

    session_state[get_widget_key('pattern_is_saved', pattern_id_counter)] = False
    session_state[get_widget_key('pattern_label', pattern_id_counter)] = f'New Pattern {pattern_id_counter}'
    session_state[get_widget_key('pattern_color', pattern_id_counter)] = session_state['available_colors'].pop()

    session_state[get_widget_key('oscillator_start_timestamp', pattern_id_counter)] = timestamp
    session_state[get_widget_key('oscillator_end_timestamp', pattern_id_counter)] = timestamp

    session_state['time_pattern_id_counter'] += 1


def get_pattern_data(session_state: MutableMapping, id: int) -> dict:
    """Get object with settings of pattern with specified `id."""
    return {
        'label': session_state[get_widget_key('pattern_label', id)],
        'oscillator': {
            'interval':
                str(session_state[get_widget_key('oscillator_interval', id)])
                + session_state[get_widget_key('oscillator_interval_unit', id)],
            'start': session_state[get_widget_key('oscillator_start_timestamp', id)],
            'end': session_state[get_widget_key('oscillator_end_timestamp', id)]
        },
        'multiplier': {
            'ratio': session_state[get_widget_key('multiplier_ratio', id)]
        },
        'randomizer': {
            'mean': session_state[get_widget_key('randomizer_mean', id)],
            'standard_deviation': session_state[get_widget_key('randomizer_deviation', id)],
            'direction': session_state[get_widget_key('randomizer_direction', id)]
        },
        'spreader': {
            'function': session_state[get_widget_key('spreader_function', id)],
            'parameters': {}
        }
    }


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
            data=get_pattern_data(session_state, id),
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
