class FormatError(Exception):
    """Exception for formatting errors.

    Parameters
    ----------
    original_event : str | None, default=NOne
        Original event
    """

    def __init__(
        self,
        *args: object,
        original_event: str | None = None
    ) -> None:
        super().__init__(*args)
        self.original_event = original_event
