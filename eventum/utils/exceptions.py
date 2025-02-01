from typing import Any


class ContextualException(Exception):
    """Exception with context."""

    def __init__(self, *args: object, context: dict[str, Any]) -> None:
        super().__init__(*args)

        self.context = context
