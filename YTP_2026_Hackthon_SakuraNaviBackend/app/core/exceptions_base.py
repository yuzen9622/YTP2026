"""All custom exceptions base class."""


class AppException(Exception):
    """Base class for all custom exceptions."""

    def __init__(self, message: str, code: str | None = None):
        self.message = message
        self.code = code
        super().__init__(message)