"""Application service for customer service ticket operations."""
import uuid
from datetime import datetime, timezone

from app.application.customer_service.commands import (
    AgentAcceptTicketCommand,
    CloseTicketCommand,
    CreateTicketCommand,
    GetMessagesQuery,
    ListTicketsQuery,
    ReopenTicketCommand,
    SendMessageCommand,
)
from app.application.customer_service.dtos import (
    MessageDTO,
    MessageListDTO,
    TicketDTO,
    TicketListDTO,
)
from app.domains.admin.value_objects import AdminRole
from app.domains.customer_service.entity import CustomerServiceMessage, CustomerServiceTicket
from app.domains.customer_service.exceptions import (
    MessageNotAllowedException,
    NotAssignedException,
    TicketAlreadyExistsException,
    TicketClosedException,
    TicketNotFoundException,
    TicketNotWaitingException,
)
from app.domains.customer_service.repository import CustomerServiceRepository
from app.domains.customer_service.value_objects import (
    MessageId,
    SenderType,
    TicketId,
    TicketStatus,
    TicketTitle,
)


class CustomerServiceApplicationService:
    def __init__(self, repo: CustomerServiceRepository) -> None:
        self._repo = repo

    async def create_ticket(self, cmd: CreateTicketCommand) -> TicketDTO:
        """Create a new ticket. Fails if user already has an open ticket."""
        # Check if user has an open ticket (waiting or active)
        existing = await self._repo.find_active_ticket_by_user(cmd.user_id)
        if existing is not None:
            raise TicketAlreadyExistsException(
                "User already has an open ticket. Please close it before creating a new one."
            )

        now = datetime.now(tz=timezone.utc)
        ticket = CustomerServiceTicket(
            id=TicketId(uuid.uuid4()),
            user_id=cmd.user_id,
            assigned_admin_id=None,
            status=TicketStatus.WAITING,
            previous_ticket_id=None,
            title=TicketTitle(cmd.title),
            created_at=now,
            updated_at=now,
            closed_at=None,
            closed_by=None,
        )
        await self._repo.save_ticket(ticket)
        return self._to_ticket_dto(ticket)

    async def agent_accept(self, cmd: AgentAcceptTicketCommand) -> TicketDTO:
        """Accept a waiting ticket and assign it to the agent."""
        ticket = await self._repo.find_ticket_by_id(TicketId(uuid.UUID(cmd.ticket_id)))
        if ticket is None:
            raise TicketNotFoundException(f"Ticket not found: {cmd.ticket_id}")
        if not ticket.is_waiting():
            raise TicketNotWaitingException(
                f"Ticket is not waiting (status={ticket.status().value})."
            )

        now = datetime.now(tz=timezone.utc)
        ticket.assign(cmd.admin_id, now)
        await self._repo.save_ticket(ticket)

        # Auto-generate system message
        system_msg = CustomerServiceMessage(
            id=MessageId(uuid.uuid4()),
            ticket_id=ticket.id(),
            sender_type=SenderType.SYSTEM,
            sender_id="system",
            content=f"客服人員已接手處理",
            created_at=now,
        )
        await self._repo.save_message(system_msg)

        return self._to_ticket_dto(ticket)

    async def send_message(self, cmd: SendMessageCommand) -> MessageDTO:
        """Send a message on a ticket. Validates sender permissions."""
        ticket = await self._repo.find_ticket_by_id(TicketId(uuid.UUID(cmd.ticket_id)))
        if ticket is None:
            raise TicketNotFoundException(f"Ticket not found: {cmd.ticket_id}")

        # Permission check based on sender type
        if cmd.sender_type == SenderType.USER.value:
            if ticket.user_id() != cmd.sender_id:
                raise MessageNotAllowedException("You do not own this ticket.")
            if not ticket.is_waiting() and not ticket.is_active():
                raise TicketClosedException("Cannot send message on a closed ticket.")
        elif cmd.sender_type == SenderType.ADMIN.value:
            if ticket.assigned_admin_id() != cmd.sender_id:
                # Allow superadmin to message any ticket
                pass  # additional superadmin check done at router level
            if not ticket.is_active():
                raise TicketClosedException("Cannot send message on a closed ticket.")

        now = datetime.now(tz=timezone.utc)
        message = CustomerServiceMessage(
            id=MessageId(uuid.uuid4()),
            ticket_id=TicketId(uuid.UUID(cmd.ticket_id)),
            sender_type=SenderType(cmd.sender_type),
            sender_id=cmd.sender_id,
            content=cmd.content,
            created_at=now,
        )
        await self._repo.save_message(message)

        # Update ticket's updated_at
        ticket.touch(now)
        await self._repo.save_ticket(ticket)

        return self._to_message_dto(message)

    async def close_ticket(self, cmd: CloseTicketCommand) -> TicketDTO:
        """Close a ticket. Can be initiated by user or admin."""
        ticket = await self._repo.find_ticket_by_id(TicketId(uuid.UUID(cmd.ticket_id)))
        if ticket is None:
            raise TicketNotFoundException(f"Ticket not found: {cmd.ticket_id}")
        if ticket.is_closed():
            raise TicketClosedException("Ticket is already closed.")

        now = datetime.now(tz=timezone.utc)
        ticket.close(cmd.closed_by, now)
        await self._repo.save_ticket(ticket)

        # Auto-generate system message
        closed_by_text = "使用者" if cmd.closed_by == "user" else "客服人員"
        system_msg = CustomerServiceMessage(
            id=MessageId(uuid.uuid4()),
            ticket_id=ticket.id(),
            sender_type=SenderType.SYSTEM,
            sender_id="system",
            content=f"{closed_by_text}已關閉此客服單",
            created_at=now,
        )
        await self._repo.save_message(system_msg)

        return self._to_ticket_dto(ticket)

    async def reopen_ticket(self, cmd: ReopenTicketCommand) -> TicketDTO:
        """Reopen a closed ticket by creating a new linked ticket."""
        previous = await self._repo.find_ticket_by_id(TicketId(uuid.UUID(cmd.previous_ticket_id)))
        if previous is None:
            raise TicketNotFoundException(f"Previous ticket not found: {cmd.previous_ticket_id}")

        # Check user doesn't have an open ticket
        existing = await self._repo.find_active_ticket_by_user(cmd.user_id)
        if existing is not None:
            raise TicketAlreadyExistsException(
                "User already has an open ticket. Please close it before creating a new one."
            )

        now = datetime.now(tz=timezone.utc)
        ticket = CustomerServiceTicket(
            id=TicketId(uuid.uuid4()),
            user_id=cmd.user_id,
            assigned_admin_id=None,
            status=TicketStatus.WAITING,
            previous_ticket_id=previous.id(),
            title=TicketTitle(cmd.title),
            created_at=now,
            updated_at=now,
            closed_at=None,
            closed_by=None,
        )
        await self._repo.save_ticket(ticket)

        # Auto-generate system message in new ticket
        system_msg = CustomerServiceMessage(
            id=MessageId(uuid.uuid4()),
            ticket_id=ticket.id(),
            sender_type=SenderType.SYSTEM,
            sender_id="system",
            content=f"使用者已重新開啟客服單，關聯至前一單 #{str(previous.id())}",
            created_at=now,
        )
        await self._repo.save_message(system_msg)

        return self._to_ticket_dto(ticket)

    async def get_ticket(self, ticket_id: str) -> TicketDTO:
        ticket = await self._repo.find_ticket_by_id(TicketId(uuid.UUID(ticket_id)))
        if ticket is None:
            raise TicketNotFoundException(f"Ticket not found: {ticket_id}")
        return self._to_ticket_dto(ticket)

    async def list_waiting_tickets(self, limit: int, offset: int) -> TicketListDTO:
        tickets = await self._repo.find_waiting_tickets(limit, offset)
        total = await self._repo.count_waiting_tickets()
        return TicketListDTO(
            items=[self._to_ticket_dto(t) for t in tickets],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def list_user_tickets(self, user_id: str, limit: int, offset: int) -> TicketListDTO:
        tickets = await self._repo.find_tickets_by_user(user_id, limit, offset)
        total = await self._repo.count_tickets_by_user(user_id)
        return TicketListDTO(
            items=[self._to_ticket_dto(t) for t in tickets],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_messages(self, query: GetMessagesQuery) -> MessageListDTO:
        before = MessageId.from_str(query.before_id) if query.before_id else None
        messages = await self._repo.find_messages(
            TicketId(uuid.UUID(query.ticket_id)), query.limit, before
        )
        has_more = len(messages) == query.limit
        return MessageListDTO(
            items=[self._to_message_dto(m) for m in messages],
            returned_count=len(messages),
            limit=query.limit,
            has_more=has_more,
        )

    @staticmethod
    def _to_ticket_dto(ticket: CustomerServiceTicket) -> TicketDTO:
        return TicketDTO(
            id=str(ticket.id()),
            user_id=ticket.user_id(),
            assigned_admin_id=ticket.assigned_admin_id(),
            status=ticket.status().value,
            previous_ticket_id=str(ticket.previous_ticket_id()) if ticket.previous_ticket_id() else None,
            title=str(ticket.title()),
            created_at=ticket.created_at(),
            updated_at=ticket.updated_at(),
            closed_at=ticket.closed_at(),
            closed_by=ticket.closed_by(),
        )

    @staticmethod
    def _to_message_dto(message: CustomerServiceMessage) -> MessageDTO:
        return MessageDTO(
            id=str(message.id()),
            ticket_id=str(message.ticket_id()),
            sender_type=message.sender_type().value,
            sender_id=message.sender_id(),
            content=message.content(),
            created_at=message.created_at(),
        )