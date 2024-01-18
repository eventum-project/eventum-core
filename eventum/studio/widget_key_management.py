from typing import Any, Optional, MutableMapping


class WidgetKeyBuilder():
    """Helper class for creating widget keys."""

    _ACCESS_READ_ONLY = 'r'
    _ACCESS_READ_WRITE = 'rw'
    _SEPARATOR = ':'
    _NOT_REPEATABLE_ID_SIGN = '-'

    def __init__(
        self,
        context: str,
    ) -> None:
        self._context = context

    def __call__(
        self,
        base_key: str,
        id: Optional[int] = None,
        mutable: bool = True
    ) -> str:
        wk = WidgetKeyBuilder

        if not isinstance(base_key, str):
            raise TypeError("base_key must be 'str'")

        if id is not None and not isinstance(id, int):
            raise TypeError("'id' must be 'int'")

        if not isinstance(mutable, bool):
            raise TypeError("'mutable' must be 'bool'")

        key_part = f'{wk._SEPARATOR}{base_key}'

        if mutable:
            access_part = f'{wk._SEPARATOR}{wk._ACCESS_READ_WRITE}'
        else:
            access_part = f'{wk._SEPARATOR}{wk._ACCESS_READ_ONLY}'

        if id is None:
            id_part = f'{wk._SEPARATOR}{wk._NOT_REPEATABLE_ID_SIGN}'
        else:
            id_part = f'{wk._SEPARATOR}{id}'

        return f'{self._context}{key_part}{access_part}{id_part}'


class ContextualSessionState:
    """Wrapper class for streamlit session state that provides isolation
    for widget keys from different contexts.
    """
    def __init__(
        self,
        st_session_state: MutableMapping,
        widget_key_builder: WidgetKeyBuilder
    ) -> None:
        self._session_state = st_session_state
        self._wk_builder = widget_key_builder

    def __getitem__(self, __key: Any) -> Any:
        if isinstance(__key, tuple):
            return self._session_state[self._wk_builder(*__key)]
        else:
            return self._session_state[self._wk_builder(__key)]

    def __setitem__(self, __key: Any, __value: Any) -> None:
        if isinstance(__key, tuple):
            self._session_state[self._wk_builder(*__key)] = __value
        else:
            self._session_state[self._wk_builder(__key)] = __value

    def __contains__(self, __key: object) -> bool:
        if isinstance(__key, tuple):
            return self._wk_builder(*__key) in self._session_state
        else:
            return self._wk_builder(__key) in self._session_state
