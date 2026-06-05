"""Chat query service — read operations for conversations and messages."""

from app.application.chat.commands import GetMessagesQuery, ListConversationsQuery, SearchConversationsQuery
from app.application.chat.dtos import (
    ConversationListDTO,
    ConversationListItemDTO,
    MessageItemDTO,
    MessageListDTO,
)
from app.domains.chat.repository import ChatRepository
from app.domains.chat.value_objects import ChatUserId, ConversationId, MessageId
from app.core.exceptions import ForbiddenException, ResourceNotFoundException


class ChatQueryService:
    """Handles read-only queries for chat conversations and messages."""

    def __init__(self, chat_repo: ChatRepository) -> None:
        self._repo = chat_repo

    async def list_conversations(self, query: ListConversationsQuery) -> ConversationListDTO:
        """Return a paginated list of conversations for the given user.

        Args:
            query: Contains user_id, limit, offset.

        Returns:
            ConversationListDTO with items, total, limit, and offset.
        """
        user_id = ChatUserId.from_str(query.user_id)
        # Run sequentially — concurrent session operations are not permitted by SQLAlchemy async.
        total = await self._repo.count_conversations_by_user_id(user_id)
        conversations = await self._repo.find_conversations_by_user_id(
            user_id,
            limit=query.limit,
            offset=query.offset,
        )
        items = [
            ConversationListItemDTO(
                id=str(c.id().value),
                title=c.title(),
                created_at=c.created_at(),
                updated_at=c.updated_at(),
            )
            for c in conversations
        ]
        return ConversationListDTO(
            items=items,
            total=total,
            limit=query.limit,
            offset=query.offset,
        )

    async def get_messages(self, query: GetMessagesQuery) -> MessageListDTO:
        """Return messages for a conversation, newest first (paginated).

        Args:
            query: Contains user_id, conversation_id, limit, before_message_id.

        Returns:
            MessageListDTO with items, total (estimated), limit, and has_more flag.

        Raises:
            ResourceNotFoundException: If the conversation does not exist.
            ForbiddenException: If the conversation exists but belongs to another user.
        """
        conv_id = ConversationId.from_str(query.conversation_id)
        user_id = ChatUserId.from_str(query.user_id)

        conversation = await self._repo.find_conversation_by_id(conv_id)
        if conversation is None:
            raise ResourceNotFoundException(
                f"Conversation '{query.conversation_id}' not found.",
                code="CONVERSATION_NOT_FOUND",
            )
        if str(conversation.user_id().value) != str(user_id.value):
            raise ForbiddenException(
                "You are not allowed to access this conversation.",
                code="CONVERSATION_FORBIDDEN",
            )

        before_msg_id = MessageId.from_str(query.before_message_id) if query.before_message_id else None
        messages = await self._repo.find_messages_by_conversation(
            conv_id, limit=query.limit, before=before_msg_id
        )

        items = [
            MessageItemDTO(
                id=str(m.id().value),
                conversation_id=str(m.conversation_id().value),
                role=m.role().value,
                content=m.content(),
                tool_name=m.tool_name(),
                created_at=m.created_at(),
            )
            for m in messages
        ]
        has_more = len(items) == query.limit
        return MessageListDTO(
            items=items,
            returned_count=len(items),
            limit=query.limit,
            has_more=has_more,
        )

    async def search_conversations(
        self, query: SearchConversationsQuery
    ) -> ConversationListDTO:
        """Search a user's conversations by title keyword.

        Args:
            query: Contains user_id, q (keyword), limit, offset.

        Returns:
            ConversationListDTO with matching conversations.
        """
        user_id = ChatUserId.from_str(query.user_id)
        total = await self._repo.count_conversations_by_title(user_id, q=query.q)
        conversations = await self._repo.search_conversations_by_title(
            user_id, q=query.q, limit=query.limit, offset=query.offset
        )
        items = [
            ConversationListItemDTO(
                id=str(c.id().value),
                title=c.title(),
                created_at=c.created_at(),
                updated_at=c.updated_at(),
            )
            for c in conversations
        ]
        return ConversationListDTO(
            items=items,
            total=total,
            limit=query.limit,
            offset=query.offset,
        )