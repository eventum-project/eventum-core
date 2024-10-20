
from typing import TypedDict

from eventum_plugins.event.plugins.jinja.state import State


class EventContext(TypedDict):
    """Kwargs for `check` method of  `Checkable`.

    Attributes
    ----------
    timestamp : str
        Timestamp of event

    tags : list[str]
        Tags from input plugin that generated timestamp

    locals : State
        Local state of template

    shared : State
        Shared state of templates

    composed : State
        Composed state of templates
    """
    timestamp: str
    tags: list[str]
    locals: State
    shared: State
    composed: State
