"""User domain specific exceptions."""
from app.domains.domain_exceptions import DomainException


class UserDomainException(DomainException):
    """User domain specific business rule violation."""
    pass


class UserAlreadyInactiveException(UserDomainException):
    """User is already inactive."""

    def __init__(self, message: str = "User is already inactive.") -> None:
        super().__init__(message, code="USER_ALREADY_INACTIVE")


class UserAlreadyActiveException(UserDomainException):
    """User is already active."""

    def __init__(self, message: str = "User is already active.") -> None:
        super().__init__(message, code="USER_ALREADY_ACTIVE")