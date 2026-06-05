"""Admin domain exceptions."""


class AdminNotFoundException(Exception):
    """Raised when an admin record is not found."""
    pass


class AdminAlreadyExistsException(Exception):
    """Raised when trying to register an admin with an existing account."""
    pass


class InvalidAdminCredentialsException(Exception):
    """Raised when admin login credentials are invalid."""
    pass