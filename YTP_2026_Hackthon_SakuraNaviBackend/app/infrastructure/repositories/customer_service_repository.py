"""SQLAlchemy implementation of CustomerServiceRepository."""
import uuid
from typing import Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.customer_service.entity import CustomerServiceMessage, CustomerServiceTicket
from app.domains.customer_service.value_objects import MessageId, TicketId
from app.infrastructure.db.models.customer_service import (
    CustomerServiceMessageModel,
    CustomerServiceTicketModel,
)


class CustomerServiceRepositoryImpl:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_ticket_by_id(self, ticket_id: TicketId) -> Optional[CustomerServiceTicket]:
        result = await self._session.execute(
            select(CustomerServiceTicketModel).where(CustomerServiceTicketModel.id == ticket_id.value)
        )
        row = result.scalar_one_or_none()
        return self._reconstruct_ticket(row) if row else None

    async def find_tickets_by_user(self, user_id: str, limit: int, offset: int) -> list[CustomerServiceTicket]:
        result = await self._session.execute(
            select(CustomerServiceTicketModel)
            .where(CustomerServiceTicketModel.user_id == uuid.UUID(user_id))
            .order_by(desc(CustomerServiceTicketModel.created_at))
            .limit(limit)
            .offset(offset)
        )
        rows = result.scalars().all()
        return [self._reconstruct_ticket(r) for r in rows]

    async def find_waiting_tickets(self, limit: int, offset: int) -> list[CustomerServiceTicket]:
        result = await self._session.execute(
            select(CustomerServiceTicketModel)
            .where(CustomerServiceTicketModel.status == "waiting")
            .order_by(CustomerServiceTicketModel.created_at)
            .limit(limit)
            .offset(offset)
        )
        rows = result.scalars().all()
        return [self._reconstruct_ticket(r) for r in rows]

    async def find_active_ticket_by_user(self, user_id: str) -> Optional[CustomerServiceTicket]:
        result = await self._session.execute(
            select(CustomerServiceTicketModel)
            .where(
                CustomerServiceTicketModel.user_id == uuid.UUID(user_id),
                CustomerServiceTicketModel.status.in_(["waiting", "active"]),
            )
            .order_by(desc(CustomerServiceTicketModel.created_at))
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return self._reconstruct_ticket(row) if row else None

    async def count_waiting_tickets(self) -> int:
        result = await self._session.execute(
            select(CustomerServiceTicketModel)
            .where(CustomerServiceTicketModel.status == "waiting")
        )
        return len(result.scalars().all())

    async def count_tickets_by_user(self, user_id: str) -> int:
        result = await self._session.execute(
            select(CustomerServiceTicketModel)
            .where(CustomerServiceTicketModel.user_id == uuid.UUID(user_id))
        )
        return len(result.scalars().all())

    async def save_ticket(self, ticket: CustomerServiceTicket) -> None:
        row = CustomerServiceTicketModel(
            id=ticket.id().value,
            user_id=uuid.UUID(ticket.user_id()),
            assigned_admin_id=uuid.UUID(ticket.assigned_admin_id()) if ticket.assigned_admin_id() else None,
            status=ticket.status().value,
            previous_ticket_id=uuid.UUID(str(ticket.previous_ticket_id())) if ticket.previous_ticket_id() else None,
            title=str(ticket.title()),
            created_at=ticket.created_at(),
            updated_at=ticket.updated_at(),
            closed_at=ticket.closed_at(),
            closed_by=ticket.closed_by(),
        )
        await self._session.merge(row)

    async def find_messages(
        self, ticket_id: TicketId, limit: int, before_id: Optional[MessageId]
    ) -> list[CustomerServiceMessage]:
        query = (
            select(CustomerServiceMessageModel)
            .where(CustomerServiceMessageModel.ticket_id == ticket_id.value)
            .order_by(desc(CustomerServiceMessageModel.created_at))
            .limit(limit)
        )
        if before_id:
            result = await self._session.execute(
                select(CustomerServiceMessageModel)
                .where(
                    CustomerServiceMessageModel.ticket_id == ticket_id.value,
                    CustomerServiceMessageModel.created_at < (
                        select(CustomerServiceMessageModel.created_at)
                        .where(CustomerServiceMessageModel.id == before_id.value)
                    ),
                )
                .order_by(desc(CustomerServiceMessageModel.created_at))
                .limit(limit)
            )
        else:
            result = await self._session.execute(query)
        rows = result.scalars().all()
        return [self._reconstruct_message(r) for r in rows]

    async def save_message(self, message: CustomerServiceMessage) -> None:
        row = CustomerServiceMessageModel(
            id=message.id().value,
            ticket_id=message.ticket_id().value,
            sender_type=message.sender_type().value,
            sender_id=uuid.UUID(message.sender_id()),
            content=message.content(),
            created_at=message.created_at(),
        )
        await self._session.merge(row)

    @staticmethod
    def _reconstruct_ticket(row: CustomerServiceTicketModel) -> CustomerServiceTicket:
        return CustomerServiceTicket._restore(
            id=TicketId(row.id),
            user_id=str(row.user_id),
            assigned_admin_id=str(row.assigned_admin_id) if row.assigned_admin_id else None,
            status=row.status,
            previous_ticket_id=str(row.previous_ticket_id) if row.previous_ticket_id else None,
            title=row.title,
            created_at=row.created_at,
            updated_at=row.updated_at,
            closed_at=row.closed_at,
            closed_by=row.closed_by,
        )

    @staticmethod
    def _reconstruct_message(row: CustomerServiceMessageModel) -> CustomerServiceMessage:
        return CustomerServiceMessage._restore(
            id=MessageId(row.id),
            ticket_id=TicketId(row.ticket_id),
            sender_type=row.sender_type,
            sender_id=str(row.sender_id),
            content=row.content,
            created_at=row.created_at,
        )