"""SQLAlchemy implementation of ChatRepository."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.chat.entities import Conversation, Message
from app.domains.chat.repository import ChatRepository
from app.domains.chat.value_objects import (
    ChatUserId,
    ConversationId,
    ConversationTitle,
    MessageId,
    MessageRole,
)
from app.infrastructure.db.models.chat import ChatConversationModel, ChatMessageModel


class ChatRepositoryImpl(ChatRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_conversation_by_id(self, id: ConversationId) -> Optional[Conversation]:
        result = await self._session.execute(
            select(ChatConversationModel).where(
                ChatConversationModel.id == id.value,
                ChatConversationModel.deleted_at.is_(None),
            )
        )
        row = result.scalar_one_or_none()
        return self._reconstruct_conversation(row) if row else None

    async def find_conversations_by_user_id(
        self, user_id: ChatUserId, limit: int = 20, offset: int = 0
    ) -> list[Conversation]:
        result = await self._session.execute(
            select(ChatConversationModel)
            .where(
                ChatConversationModel.user_id == user_id.value,
                ChatConversationModel.deleted_at.is_(None),
            )
            .order_by(ChatConversationModel.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = result.scalars().all()
        return [self._reconstruct_conversation(row) for row in rows]

    async def delete_message_by_id(
        self, message_id: MessageId, conversation_id: ConversationId
    ) -> bool:
        result = await self._session.execute(
            delete(ChatMessageModel).where(
                ChatMessageModel.id == message_id.value,
                ChatMessageModel.conversation_id == conversation_id.value,
            )
        )
        return (result.rowcount or 0) > 0

    @staticmethod
    def _like_pattern(q: str) -> str:
        """Escape user-supplied LIKE wildcards to prevent expensive full-scan queries."""
        return "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"

    async def search_conversations_by_title(
        self, user_id: ChatUserId, q: str, limit: int = 20, offset: int = 0
    ) -> list[Conversation]:
        pattern = self._like_pattern(q)
        result = await self._session.execute(
            select(ChatConversationModel)
            .where(
                ChatConversationModel.user_id == user_id.value,
                ChatConversationModel.deleted_at.is_(None),
                ChatConversationModel.title.ilike(pattern),
            )
            .order_by(ChatConversationModel.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = result.scalars().all()
        return [self._reconstruct_conversation(row) for row in rows]

    async def count_conversations_by_user_id(self, user_id: ChatUserId) -> int:
        result = await self._session.execute(
            select(func.count(ChatConversationModel.id)).where(
                ChatConversationModel.user_id == user_id.value,
                ChatConversationModel.deleted_at.is_(None),
            )
        )
        return result.scalar() or 0

    async def count_conversations_by_title(self, user_id: ChatUserId, q: str) -> int:
        pattern = self._like_pattern(q)
        result = await self._session.execute(
            select(func.count(ChatConversationModel.id))
            .where(
                ChatConversationModel.user_id == user_id.value,
                ChatConversationModel.deleted_at.is_(None),
                ChatConversationModel.title.ilike(pattern),
            )
        )
        return result.scalar() or 0

    async def find_messages_by_conversation(
        self, conversation_id: ConversationId, limit: int = 50, before: Optional[MessageId] = None
    ) -> list[Message]:
        query = (
            select(ChatMessageModel)
            .where(ChatMessageModel.conversation_id == conversation_id.value)
            .order_by(ChatMessageModel.created_at.desc())
            .limit(limit)
        )
        if before:
            query = query.where(ChatMessageModel.id < before.value)
        result = await self._session.execute(query)
        rows = result.scalars().all()
        return [self._reconstruct_message(row) for row in rows]

    async def save_conversation(self, conversation: Conversation) -> None:
        row = ChatConversationModel(
            id=conversation.id().value,
            user_id=conversation.user_id().value,
            title=conversation.title(),
            created_at=conversation.created_at(),
            updated_at=conversation.updated_at(),
            deleted_at=conversation.deleted_at(),
        )
        await self._session.merge(row)

    async def save_message(self, message: Message) -> None:
        row = ChatMessageModel(
            id=message.id().value,
            conversation_id=message.conversation_id().value,
            role=message.role().value,
            content=message.content(),
            tool_name=message.tool_name(),
            created_at=message.created_at(),
        )
        await self._session.merge(row)

    async def delete_conversation(self, id: ConversationId, user_id: ChatUserId) -> bool:
        result = await self._session.execute(
            select(ChatConversationModel).where(
                ChatConversationModel.id == id.value,
                ChatConversationModel.user_id == user_id.value,
                ChatConversationModel.deleted_at.is_(None),
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            return False
        row.deleted_at = datetime.now(tz=timezone.utc)
        await self._session.merge(row)
        return True

    async def truncate_messages_after(
        self, conversation_id: ConversationId, user_id: ChatUserId, message_id: MessageId
    ) -> int:
        # First verify ownership (and conversation not deleted)
        conv = await self._session.execute(
            select(ChatConversationModel).where(
                ChatConversationModel.id == conversation_id.value,
                ChatConversationModel.user_id == user_id.value,
                ChatConversationModel.deleted_at.is_(None),
            )
        )
        if conv.scalar_one_or_none() is None:
            return 0

        # Find the cutoff timestamp
        cutoff_row = await self._session.execute(
            select(ChatMessageModel.created_at).where(
                ChatMessageModel.id == message_id.value,
                ChatMessageModel.conversation_id == conversation_id.value,
            )
        )
        cutoff_result = cutoff_row.scalar_one_or_none()
        if cutoff_result is None:
            return 0

        # Delete all messages in this conversation newer than the cutoff (exclusive)
        deleted = await self._session.execute(
            delete(ChatMessageModel).where(
                ChatMessageModel.conversation_id == conversation_id.value,
                ChatMessageModel.created_at > cutoff_result,
            )
        )
        count = deleted.rowcount
        if count < 0:
            # Driver doesn't support rowcount — perform a count query as fallback
            count_result = await self._session.execute(
                select(func.count()).select_from(ChatMessageModel).where(
                    ChatMessageModel.conversation_id == conversation_id.value,
                    ChatMessageModel.created_at > cutoff_result,
                )
            )
            count = count_result.scalar_one()
        return count

    @staticmethod
    def _reconstruct_conversation(row: ChatConversationModel) -> Conversation:
        return Conversation._restore(
            id=ConversationId(row.id),
            user_id=ChatUserId(row.user_id),
            title=row.title,
            created_at=row.created_at,
            updated_at=row.updated_at,
            deleted_at=row.deleted_at,
        )

    @staticmethod
    def _reconstruct_message(row: ChatMessageModel) -> Message:
        return Message._restore(
            id=MessageId(row.id),
            conversation_id=ConversationId(row.conversation_id),
            role=MessageRole(row.role),
            content=row.content,
            tool_name=row.tool_name,
            created_at=row.created_at,
        )