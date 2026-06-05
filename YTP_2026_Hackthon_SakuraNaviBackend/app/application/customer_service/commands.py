"""Command objects for customer service operations."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CreateTicketCommand:
    """Command to create a new customer service ticket."""
    user_id: str
    title: str


@dataclass(frozen=True)
class AgentAcceptTicketCommand:
    """Command for an agent to accept a waiting ticket."""
    admin_id: str
    ticket_id: str


@dataclass(frozen=True)
class SendMessageCommand:
    """Command to send a message on a ticket."""
    sender_type: str  # user / admin / system
    sender_id: str
    ticket_id: str
    content: str


@dataclass(frozen=True)
class CloseTicketCommand:
    """Command to close a ticket."""
    ticket_id: str
    closed_by: str  # "user" or "admin"


@dataclass(frozen=True)
class ReopenTicketCommand:
    """Command to reopen a closed ticket (creates a new linked ticket)."""
    user_id: str
    previous_ticket_id: str
    title: str


@dataclass(frozen=True)
class ListTicketsQuery:
    """Query to list tickets with pagination."""
    user_id: Optional[str] = None
    is_agent: bool = False
    limit: int = 20
    offset: int = 0


@dataclass(frozen=True)
class GetMessagesQuery:
    """Query to get messages for a ticket."""
    ticket_id: str
    limit: int = 50
    before_id: Optional[str] = None