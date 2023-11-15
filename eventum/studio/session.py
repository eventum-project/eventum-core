from typing import MutableMapping


def initialize(session_state: MutableMapping) -> None:
    """Create initial objects in session state."""
    if 'time_pattern_id_counter' not in session_state:
        session_state['time_pattern_id_counter'] = 1

    if 'time_pattern_ids' not in session_state:
        session_state['time_pattern_ids'] = []


def get_widget_key(name: str, id: int) -> str:
    """Get unique key for a widget that will be used in `st.session_state`.
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
    """Append current `time_pattern_id_counter` to `time_pattern_ids` list
    in session state and incremenet `time_pattern_id_counter`.
    """
    session_state['time_pattern_ids'].append(session_state['time_pattern_id_counter'])
    session_state['time_pattern_id_counter'] += 1


def delete_pattern(session_state: MutableMapping, id: int) -> None:
    """Remove id from `time_pattern_ids` list and all attributes of specified
    pattern by their id postfix in session state.
    """
    session_state['time_pattern_ids'].remove(id)
    widget_keys = get_pattern_widget_keys(session_state, id)

    for key in widget_keys:
        del session_state[key]
