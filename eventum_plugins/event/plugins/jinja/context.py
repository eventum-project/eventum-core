from typing import TypedDict

from eventum_plugins.event.plugins.jinja.state import State


class EventContext(TypedDict):
    """Context for event producing.

    Attributes
    ----------
    timestamp : str
        Timestamp of event

    tags : tuple[str, ...]
        Tags from input plugin that generated timestamp

    locals : State
        Local state of template

    shared : State
        Shared state of templates

    composed : State
        Composed state of templates
    """
    timestamp: str
    tags: tuple[str, ...]
    locals: State
    shared: State
    composed: State
