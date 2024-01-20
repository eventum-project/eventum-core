
from typing import MutableMapping, Optional

import streamlit as st

from eventum.studio.key_management import (ContextualSessionState,
                                           WidgetKeysContext)

from abc import ABC, abstractmethod


class BaseComponent(ABC):
    """Base class for creating session isolated components."""

    def __init__(
        self,
        session_state: MutableMapping = st.session_state,
        id: int = 1,
        widget_keys_context: Optional[WidgetKeysContext] = None
    ) -> None:
        if widget_keys_context is None:
            self._wk = WidgetKeysContext()
        else:
            self._wk = widget_keys_context

        self._wk.register_component(self.__class__.__name__, id)

        self._session_state = ContextualSessionState(session_state, self._wk)
        self._init_session_wrapper()

        self._show()

    def _init_session_wrapper(self):
        """Check whether the session is initilized and call
        intialization in case it's not.
        """
        if 'initialized' in self._session_state:
            return
        self._init_session()
        self._session_state['initialized'] = True

    @abstractmethod
    def _init_session(self) -> None:
        """Perform session initialization."""
        ...

    @abstractmethod
    def _show(self):
        """Present widgets layout."""
        ...
