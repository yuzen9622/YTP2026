"""Value objects for chat aggregate."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


@dataclass(frozen=True)
class ConversationId:
    value: uuid.UUID

    @classmethod
    def from_str(cls, s: str) -> "ConversationId":
        return cls(uuid.UUID(s))

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class MessageId:
    value: uuid.UUID

    @classmethod
    def from_str(cls, s: str) -> "MessageId":
        return cls(uuid.UUID(s))

    def __str__(self) -> str:
        return str(self.value)


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass(frozen=True)
class ConversationTitle:
    value: str

    def __init__(self, title: str) -> None:
        object.__setattr__(self, "value", title[:255] if len(title) > 255 else title)


@dataclass(frozen=True)
class MessageContent:
    value: str

    def __init__(self, content: str) -> None:
        object.__setattr__(self, "value", content)


@dataclass(frozen=True)
class ToolName:
    value: str

    def __init__(self, name: str) -> None:
        object.__setattr__(self, "value", name[:64] if len(name) > 64 else name)


@dataclass(frozen=True)
class ChatUserId:
    value: uuid.UUID

    @classmethod
    def from_str(cls, s: str) -> "ChatUserId":
        return cls(uuid.UUID(s))


@dataclass(frozen=True)
class CreatedAt:
    value: datetime

    def __init__(self, dt: datetime) -> None:
        object.__setattr__(self, "value", dt)