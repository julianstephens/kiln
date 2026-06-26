class MustBePositiveError(ValueError):
    """Raised when a value must be positive but is not."""

    def __init__(self, value: int | float) -> None:
        super().__init__(f"value must be positive, got {value}")
