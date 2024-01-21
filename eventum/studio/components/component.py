
from abc import ABC, abstractmethod
from typing import MutableMapping, Optional

import streamlit as st

from eventum.studio.key_management import (ContextualSessionState,
                                           WidgetKeysContext)


class BaseComponent(ABC):
    """Base class for creating session isolated components."""

    def __init__(
        self,
        session_state: MutableMapping = st.session_state,
        id: int = 1,
        widget_keys_context: Optional[WidgetKeysContext] = None,
        props: Optional[dict] = None
    ) -> None:
        if widget_keys_context is None:
            self._wk = WidgetKeysContext()
        else:
            self._wk = widget_keys_context

        if props is None:
            self._props = dict()
        else:
            self._props = props

        self._wk.register_component(self.__class__.__name__, id)
        self._session_state = ContextualSessionState(session_state, self._wk)

        self.__init_state_wrapper()
        self._show()

    def __init_state_wrapper(self):
        """Check whether the session is initilized and call
        intialization in case it's not.
        """
        if 'initialized' in self._session_state:
            return
        self._init_state()
        self._session_state['initialized'] = True

    def _init_state(self) -> None:
        """Perform state initialization."""
        ...

    def _release_state(self) -> None:
        """Delete items from session state added on initialization."""
        del self._session_state['initialized']

    @abstractmethod
    def _show(self):
        """Present component structure."""
        ...
