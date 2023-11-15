from typing import MutableMapping

from eventum.utils.loaders import load_yaml


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

    session_state['time_pattern_ids'].append(pattern_id_counter)
    session_state[get_widget_key('pattern_filepath', pattern_id_counter)] = 'unsaved'
    session_state[get_widget_key('pattern_label', pattern_id_counter)] = f'New Pattern {pattern_id_counter}'
    session_state[get_widget_key('pattern_color', pattern_id_counter)] = session_state['available_colors'].pop()
    session_state['time_pattern_id_counter'] += 1


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
