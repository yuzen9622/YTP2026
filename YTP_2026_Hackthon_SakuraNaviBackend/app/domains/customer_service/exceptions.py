"""Customer service domain exceptions."""


class TicketNotFoundException(Exception):
    """Raised when a ticket is not found."""
    pass


class TicketNotWaitingException(Exception):
    """Raised when trying to accept a ticket that is not in WAITING status."""
    pass


class TicketClosedException(Exception):
    """Raised when trying to act on a closed ticket."""
    pass


class NotAssignedException(Exception):
    """Raised when an admin tries to act on a ticket not assigned to them."""
    pass


class TicketAlreadyExistsException(Exception):
    """Raised when user tries to create a second open ticket while one is already open."""
    pass


class MessageNotAllowedException(Exception):
    """Raised when a sender is not allowed to send a message on a ticket."""
    pass