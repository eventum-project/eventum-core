from typing import Any, MutableMapping
from uuid import uuid4

EPHEMERAL_PREFIX = '~'


class WidgetKeysContext():
    """Helper class for creating widget keys."""

    _SEPARATOR = ':'
    _ID_PREFIX = '-'

    def __init__(
        self,
    ) -> None:
        self._component_stack: list[str] = []

    def __call__(
        self,
        widget_key: str
    ) -> str:
        return self._SEPARATOR.join(self._component_stack + [widget_key])

    def __contains__(self, __key: str) -> bool:
        """Check if widget key belongs to context."""
        *_, id = __key.rsplit(self._SEPARATOR, maxsplit=1)

        if not id:
            return False

        return self.__call__(id) == __key

    def register_component(self, component_name: str, component_id: int):
        """Add component to context stack."""
        self._component_stack.append(
            f'{component_name}{self._ID_PREFIX}{component_id}'
        )

    @staticmethod
    def get_ephemeral() -> str:
        """Get globally unique ephemeral key. Used for immutable
        widgets such as button."""
        return EPHEMERAL_PREFIX + str(uuid4())


class ContextualSessionState:
    """Wrapper class for streamlit session state that provides isolation
    for widget keys from different contexts.
    """
    def __init__(
        self,
        st_session_state: MutableMapping,
        widget_keys_context: WidgetKeysContext
    ) -> None:
        self._session_state = st_session_state
        self._wk = widget_keys_context

    def __getitem__(self, __key: Any) -> Any:
        return self._session_state[self._wk(__key)]

    def __setitem__(self, __key: Any, __value: Any) -> None:
        self._session_state[self._wk(__key)] = __value

    def __delitem__(self, __key: Any) -> None:
        del self._session_state[self._wk(__key)]

    def __contains__(self, __key: str) -> bool:
        return self._wk(__key) in self._session_state

    def delete_context_elements(self) -> None:
        for key in self._session_state.keys():
            if key in self._wk:
                del self._session_state[key]
