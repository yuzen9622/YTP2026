"""Customer service domain entities."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domains.customer_service.value_objects import (
    MessageId,
    SenderType,
    TicketId,
    TicketStatus,
    TicketTitle,
)


@dataclass
class CustomerServiceMessage:
    """Customer service message entity."""
    _id: MessageId
    _ticket_id: TicketId
    _sender_type: SenderType
    _sender_id: str
    _content: str
    _created_at: datetime

    def __init__(
        self,
        id: MessageId,
        ticket_id: TicketId,
        sender_type: SenderType,
        sender_id: str,
        content: str,
        created_at: datetime,
    ) -> None:
        self._id = id
        self._ticket_id = ticket_id
        self._sender_type = sender_type
        self._sender_id = sender_id
        self._content = content
        self._created_at = created_at

    def id(self) -> MessageId:
        return self._id

    def ticket_id(self) -> TicketId:
        return self._ticket_id

    def sender_type(self) -> SenderType:
        return self._sender_type

    def sender_id(self) -> str:
        return self._sender_id

    def content(self) -> str:
        return self._content

    def created_at(self) -> datetime:
        return self._created_at

    # --- Persistence reconstruction ---
    @classmethod
    def _restore(
        cls,
        *,
        id: MessageId,
        ticket_id: TicketId,
        sender_type: str,
        sender_id: str,
        content: str,
        created_at: datetime,
    ) -> "CustomerServiceMessage":
        obj: "CustomerServiceMessage" = cls.__new__(cls)
        obj._id = id
        obj._ticket_id = ticket_id
        obj._sender_type = SenderType(sender_type)
        obj._sender_id = sender_id
        obj._content = content
        obj._created_at = created_at
        return obj


@dataclass
class CustomerServiceTicket:
    """Customer service ticket aggregate root."""
    _id: TicketId
    _user_id: str
    _assigned_admin_id: Optional[str]
    _status: TicketStatus
    _previous_ticket_id: Optional[TicketId]
    _title: TicketTitle
    _created_at: datetime
    _updated_at: datetime
    _closed_at: Optional[datetime]
    _closed_by: Optional[str]  # "user" or "admin"

    def __init__(
        self,
        id: TicketId,
        user_id: str,
        assigned_admin_id: Optional[str],
        status: TicketStatus,
        previous_ticket_id: Optional[TicketId],
        title: TicketTitle,
        created_at: datetime,
        updated_at: datetime,
        closed_at: Optional[datetime],
        closed_by: Optional[str],
    ) -> None:
        self._id = id
        self._user_id = user_id
        self._assigned_admin_id = assigned_admin_id
        self._status = status
        self._previous_ticket_id = previous_ticket_id
        self._title = title
        self._created_at = created_at
        self._updated_at = updated_at
        self._closed_at = closed_at
        self._closed_by = closed_by

    def id(self) -> TicketId:
        return self._id

    def user_id(self) -> str:
        return self._user_id

    def assigned_admin_id(self) -> Optional[str]:
        return self._assigned_admin_id

    def status(self) -> TicketStatus:
        return self._status

    def previous_ticket_id(self) -> Optional[TicketId]:
        return self._previous_ticket_id

    def title(self) -> TicketTitle:
        return self._title

    def created_at(self) -> datetime:
        return self._created_at

    def updated_at(self) -> datetime:
        return self._updated_at

    def closed_at(self) -> Optional[datetime]:
        return self._closed_at

    def closed_by(self) -> Optional[str]:
        return self._closed_by

    def is_waiting(self) -> bool:
        return self._status == TicketStatus.WAITING

    def is_active(self) -> bool:
        return self._status == TicketStatus.ACTIVE

    def is_closed(self) -> bool:
        return self._status == TicketStatus.CLOSED

    def assign(self, admin_id: str, now: datetime) -> None:
        if self._status != TicketStatus.WAITING:
            raise ValueError("Can only assign a waiting ticket")
        self._assigned_admin_id = admin_id
        self._status = TicketStatus.ACTIVE
        self._updated_at = now

    def close(self, closed_by: str, now: datetime) -> None:
        if self._status == TicketStatus.CLOSED:
            raise ValueError("Ticket is already closed")
        self._status = TicketStatus.CLOSED
        self._closed_at = now
        self._closed_by = closed_by
        self._updated_at = now

    def touch(self, now: datetime) -> None:
        self._updated_at = now

    # --- Persistence reconstruction ---
    @classmethod
    def _restore(
        cls,
        *,
        id: TicketId,
        user_id: str,
        assigned_admin_id: Optional[str],
        status: str,
        previous_ticket_id: Optional[str],
        title: str,
        created_at: datetime,
        updated_at: datetime,
        closed_at: Optional[datetime],
        closed_by: Optional[str],
    ) -> "CustomerServiceTicket":
        obj: "CustomerServiceTicket" = cls.__new__(cls)
        obj._id = id
        obj._user_id = user_id
        obj._assigned_admin_id = assigned_admin_id
        obj._status = TicketStatus(status)
        obj._previous_ticket_id = TicketId.from_str(previous_ticket_id) if previous_ticket_id else None
        obj._title = TicketTitle(title)
        obj._created_at = created_at
        obj._updated_at = updated_at
        obj._closed_at = closed_at
        obj._closed_by = closed_by
        return obj