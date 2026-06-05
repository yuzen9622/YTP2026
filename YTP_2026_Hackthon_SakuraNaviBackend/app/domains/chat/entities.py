"""Chat domain entities — aggregate root and value objects."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.domains.chat.exceptions import ConversationNotFoundException
from app.domains.chat.value_objects import (
    ChatUserId,
    ConversationId,
    ConversationTitle,
    MessageContent,
    MessageId,
    MessageRole,
    ToolName,
)


@dataclass
class Message:
    """Chat message — part of Conversation aggregate."""
    _id: MessageId
    _conversation_id: ConversationId
    _role: MessageRole
    _content: MessageContent
    _tool_name: Optional[ToolName]
    _created_at: datetime

    def __init__(
        self,
        id: MessageId,
        conversation_id: ConversationId,
        role: MessageRole,
        content: str,
        tool_name: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ) -> None:
        self._id = id
        self._conversation_id = conversation_id
        self._role = role
        self._content = MessageContent(content)
        self._tool_name = ToolName(tool_name) if tool_name else None
        self._created_at = created_at or datetime.now(tz=timezone.utc)

    def id(self) -> MessageId:
        return self._id

    def conversation_id(self) -> ConversationId:
        return self._conversation_id

    def role(self) -> MessageRole:
        return self._role

    def content(self) -> str:
        return self._content.value

    def tool_name(self) -> Optional[str]:
        return self._tool_name.value if self._tool_name else None

    def created_at(self) -> datetime:
        return self._created_at

    def update_content(self, new_content: str) -> None:
        """Update message content."""
        self._content = MessageContent(new_content)

    @classmethod
    def _restore(
        cls,
        id: MessageId,
        conversation_id: ConversationId,
        role: MessageRole,
        content: str,
        tool_name: Optional[str],
        created_at: datetime,
    ) -> "Message":
        obj = cls.__new__(cls)
        obj._id = id
        obj._conversation_id = conversation_id
        obj._role = role
        obj._content = MessageContent(content)
        obj._tool_name = ToolName(tool_name) if tool_name else None
        obj._created_at = created_at
        return obj


@dataclass
class Conversation:
    """Conversation aggregate root.

    All state changes must go through domain methods.
    """
    _id: ConversationId
    _user_id: ChatUserId
    _title: ConversationTitle
    _created_at: datetime
    _updated_at: datetime
    _deleted_at: datetime | None

    def __init__(
        self,
        id: ConversationId,
        user_id: ChatUserId,
        title: str,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        deleted_at: Optional[datetime] = None,
    ) -> None:
        self._id = id
        self._user_id = user_id
        self._title = ConversationTitle(title)
        self._created_at = created_at or datetime.now(tz=timezone.utc)
        self._updated_at = updated_at or self._created_at
        self._deleted_at = deleted_at

    def id(self) -> ConversationId:
        return self._id

    def user_id(self) -> ChatUserId:
        return self._user_id

    def title(self) -> str:
        return self._title.value

    def created_at(self) -> datetime:
        return self._created_at

    def updated_at(self) -> datetime:
        return self._updated_at

    def deleted_at(self) -> datetime | None:
        return self._deleted_at

    def is_deleted(self) -> bool:
        return self._deleted_at is not None

    def update_title(self, new_title: str, now: datetime) -> None:
        self._title = ConversationTitle(new_title)
        self._updated_at = now

    def touch(self, now: datetime) -> None:
        """Update updated_at without mutating other fields."""
        self._updated_at = now

    def soft_delete(self, now: datetime) -> None:
        """Mark the conversation as deleted."""
        self._deleted_at = now

    @classmethod
    def _restore(
        cls,
        id: ConversationId,
        user_id: ChatUserId,
        title: str,
        created_at: datetime,
        updated_at: datetime,
        deleted_at: datetime | None = None,
    ) -> "Conversation":
        obj = cls.__new__(cls)
        obj._id = id
        obj._user_id = user_id
        obj._title = ConversationTitle(title)
        obj._created_at = created_at
        obj._updated_at = updated_at
        obj._deleted_at = deleted_at
        return obj