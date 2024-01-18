
from typing import MutableMapping

from eventum.studio.widget_key_management import (ContextualSessionState,
                                                  WidgetKeyBuilder)


class BaseComponent:
    def __init__(self, session_state: MutableMapping) -> None:
        self._wk = WidgetKeyBuilder(self.__class__.__name__)
        self._session_state = ContextualSessionState(session_state, self._wk)
