"""Data Transfer Objects for customer service operations."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class TicketDTO:
    """DTO for a customer service ticket."""
    id: str
    user_id: str
    assigned_admin_id: Optional[str]
    status: str
    previous_ticket_id: Optional[str]
    title: str
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime]
    closed_by: Optional[str]


@dataclass(frozen=True)
class TicketListDTO:
    """Paginated ticket list."""
    items: list[TicketDTO]
    total: int
    limit: int
    offset: int


@dataclass(frozen=True)
class MessageDTO:
    """DTO for a customer service message."""
    id: str
    ticket_id: str
    sender_type: str
    sender_id: str
    content: str
    created_at: datetime


@dataclass(frozen=True)
class MessageListDTO:
    """Paginated message list."""
    items: list[MessageDTO]
    returned_count: int
    limit: int
    has_more: bool