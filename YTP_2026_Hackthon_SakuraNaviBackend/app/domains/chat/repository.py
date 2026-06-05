"""Repository interface for chat conversation aggregate persistence."""
from typing import Optional, Protocol

from app.domains.chat.entities import Conversation, Message
from app.domains.chat.value_objects import ChatUserId, ConversationId, MessageId


class ChatRepository(Protocol):
    """Port for conversation & message persistence."""

    async def find_conversation_by_id(self, id: ConversationId) -> Optional[Conversation]: ...

    async def find_conversations_by_user_id(
        self, user_id: ChatUserId, limit: int = 20, offset: int = 0
    ) -> list[Conversation]: ...

    async def search_conversations_by_title(
        self, user_id: ChatUserId, q: str, limit: int = 20, offset: int = 0
    ) -> list[Conversation]: ...

    async def count_conversations_by_user_id(self, user_id: ChatUserId) -> int: ...

    async def count_conversations_by_title(self, user_id: ChatUserId, q: str) -> int: ...

    async def find_messages_by_conversation(
        self, conversation_id: ConversationId, limit: int = 50, before: Optional[MessageId] = None
    ) -> list[Message]: ...

    async def save_conversation(self, conversation: Conversation) -> None: ...

    async def save_message(self, message: Message) -> None: ...

    async def delete_conversation(self, id: ConversationId, user_id: ChatUserId) -> bool:
        """Soft-delete a conversation and all its messages (cascade).

        Returns True if deleted, False if not found or not owned by user.
        """
        ...

    async def truncate_messages_after(
        self, conversation_id: ConversationId, user_id: ChatUserId, message_id: MessageId
    ) -> int:
        """Delete all messages in the conversation dated after the given message (exclusive).

        Used for chained editing: editing message N removes all messages N+1, N+2, ...

        Returns the count of messages deleted.
        """
        ...

    async def delete_message_by_id(
        self, message_id: MessageId, conversation_id: ConversationId
    ) -> bool:
        """Delete a single message by its ID.

        Returns True if the message was found and deleted, False otherwise.
        """
        ...