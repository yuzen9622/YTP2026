"""Command and query objects for chat use cases."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class ChatStreamCommand:
    """Immutable command to initiate a streaming chat session."""

    user_id: str
    message: str
    conversation_id: Optional[str] = field(default=None)


@dataclass(frozen=True)
class ListConversationsQuery:
    """Query to list a user's chat conversations with pagination."""

    user_id: str
    limit: int = 20
    offset: int = 0


@dataclass(frozen=True)
class GetMessagesQuery:
    """Query to retrieve messages in a conversation."""

    user_id: str
    conversation_id: str
    limit: int = 50
    before_message_id: Optional[str] = field(default=None)


@dataclass(frozen=True)
class SearchConversationsQuery:
    """Query to search a user's chat conversations by title keyword."""

    user_id: str
    q: str
    limit: int = 20
    offset: int = 0


@dataclass(frozen=True)
class UpdateConversationCommand:
    """Command to update a conversation's title."""

    user_id: str
    conversation_id: str
    title: str


@dataclass(frozen=True)
class DeleteConversationCommand:
    """Command to delete a conversation and all its messages."""

    user_id: str
    conversation_id: str


@dataclass(frozen=True)
class UpdateMessageCommand:
    """Command to edit a message content.

    Editing a message triggers cascade truncation: all messages
    after the edited message in the conversation are deleted.
    """

    user_id: str
    conversation_id: str
    message_id: str
    content: str


@dataclass(frozen=True)
class DeleteMessageCommand:
    """Command to delete a specific message.

    Deleting a message triggers cascade truncation: all messages
    after the deleted message in the conversation are deleted.
    """

    user_id: str
    conversation_id: str
    message_id: str
