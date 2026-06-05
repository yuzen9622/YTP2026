"""Domain layer exceptions."""
from app.core.exceptions_base import AppException


class DomainException(AppException):
    """Base class for domain-specific exceptions."""