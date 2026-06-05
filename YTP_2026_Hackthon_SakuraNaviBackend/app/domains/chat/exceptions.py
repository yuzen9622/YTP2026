"""Domain exceptions for chat aggregate."""
from app.domains.domain_exceptions import DomainException


class ConversationNotFoundException(DomainException):
    """Raised when a conversation cannot be found."""
    def __init__(self, conversation_id: str) -> None:
        super().__init__(
            f"Conversation '{conversation_id}' not found.",
            code="CONVERSATION_NOT_FOUND",
        )


class MessageNotFoundException(DomainException):
    """Raised when a message cannot be found."""
    def __init__(self, message_id: str) -> None:
        super().__init__(
            f"Message '{message_id}' not found.",
            code="MESSAGE_NOT_FOUND",
        )