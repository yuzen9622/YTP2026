"""DTOs for chat use cases."""
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ConversationListItemDTO:
    """Summary DTO for a conversation in a list response."""

    id: str
    title: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ConversationListDTO:
    """Paginated list of conversations."""

    items: list[ConversationListItemDTO]
    total: int
    limit: int
    offset: int


@dataclass(frozen=True)
class MessageItemDTO:
    """DTO for a single chat message."""

    id: str
    conversation_id: str
    role: str
    content: str
    tool_name: str | None
    created_at: datetime


@dataclass(frozen=True)
class MessageListDTO:
    """Paginated list of messages in a conversation."""

    items: list[MessageItemDTO]
    returned_count: int
    limit: int
    has_more: bool