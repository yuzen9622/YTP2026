"""Application and Infrastructure layer exceptions."""
from app.core.exceptions_base import AppException


class ApplicationException(AppException):
    """Application layer workflow errors."""
    pass


class ResourceNotFoundException(ApplicationException):
    """Resource not found."""
    pass


class DuplicateResourceException(ApplicationException):
    """Resource already exists (uniqueness conflict)."""
    pass


class UnauthorizedException(ApplicationException):
    """Unauthorized operation."""
    pass


class ForbiddenException(ApplicationException):
    """Authenticated but not authorized."""
    pass