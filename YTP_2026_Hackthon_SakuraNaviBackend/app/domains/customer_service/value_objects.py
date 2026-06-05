"""Customer service domain value objects."""
import enum
import uuid
from dataclasses import dataclass


class TicketStatus(str, enum.Enum):
    """Ticket status enum."""
    WAITING = "waiting"
    ACTIVE = "active"
    CLOSED = "closed"


class SenderType(str, enum.Enum):
    """Message sender type enum."""
    USER = "user"
    ADMIN = "admin"
    SYSTEM = "system"


@dataclass(frozen=True)
class TicketId:
    """Ticket unique identifier."""
    value: uuid.UUID

    def __post_init__(self):
        if not isinstance(self.value, uuid.UUID):
            raise ValueError(f"Invalid TicketId: {self.value}")

    @classmethod
    def from_str(cls, s: str) -> "TicketId":
        return cls(uuid.UUID(s))

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class MessageId:
    """Message unique identifier."""
    value: uuid.UUID

    def __post_init__(self):
        if not isinstance(self.value, uuid.UUID):
            raise ValueError(f"Invalid MessageId: {self.value}")

    @classmethod
    def from_str(cls, s: str) -> "MessageId":
        return cls(uuid.UUID(s))

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class TicketTitle:
    """Ticket title value object."""
    value: str

    def __post_init__(self):
        if not self.value or len(self.value.strip()) == 0:
            raise ValueError("Ticket title cannot be empty")
        if len(self.value) > 255:
            object.__setattr__(self, "value", self.value[:255])

    def __str__(self) -> str:
        return self.value