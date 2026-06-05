"""Customer Service API router."""
from typing import Annotated, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.customer_service.commands import (
    AgentAcceptTicketCommand,
    CloseTicketCommand,
    CreateTicketCommand,
    GetMessagesQuery,
    ReopenTicketCommand,
    SendMessageCommand,
)
from app.application.customer_service.service import CustomerServiceApplicationService
from app.domains.admin.value_objects import AdminRole
from app.domains.customer_service.exceptions import (
    MessageNotAllowedException,
    TicketAlreadyExistsException,
    TicketClosedException,
    TicketNotFoundException,
    TicketNotWaitingException,
)
from app.interfaces.api.deps import get_current_admin, get_current_admin_optional, get_current_user_id, get_db_session
from app.infrastructure.repositories.customer_service_repository import CustomerServiceRepositoryImpl
from app.interfaces.api.v1.customer_service.schemas import (
    CloseTicketRequest,
    CreateTicketRequest,
    MessageListResponse,
    MessageResponse,
    ReopenTicketRequest,
    SendMessageRequest,
    TicketListResponse,
    TicketResponse,
)

router = APIRouter(prefix="/customer-service", tags=["customer-service"])


def _require_cs_role(role: str) -> None:
    if role not in (AdminRole.CUSTOMER_SERVICE.value, AdminRole.SUPERADMIN.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer service access required.",
        )


async def get_cs_service(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> CustomerServiceApplicationService:
    return CustomerServiceApplicationService(
        CustomerServiceRepositoryImpl(session)
    )


# ── User Endpoints ────────────────────────────────────────────────────────────


@router.post(
    "/tickets",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="發起客服單（使用者）",
    responses={
        status.HTTP_409_CONFLICT: {"description": "已有開啟中的客服單"},
    },
)
async def create_ticket(
    body: CreateTicketRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[CustomerServiceApplicationService, Depends(get_cs_service)],
) -> TicketResponse:
    try:
        dto = await svc.create_ticket(CreateTicketCommand(user_id=user_id, title=body.title))
    except TicketAlreadyExistsException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return TicketResponse(**dto.__dict__)


@router.get(
    "/tickets",
    response_model=TicketListResponse,
    summary="列出我的客服單（使用者）",
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "未提供或無效的 Bearer Token"}},
)
async def list_my_tickets(
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[CustomerServiceApplicationService, Depends(get_cs_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TicketListResponse:
    result = await svc.list_user_tickets(user_id, limit, offset)
    return TicketListResponse(
        items=[TicketResponse(**t.__dict__) for t in result.items],
        total=result.total,
        limit=result.limit,
        offset=result.offset,
    )


# NOTE: /tickets/waiting must be registered before /tickets/{ticket_id} to avoid
# the literal "waiting" being captured as a ticket_id path parameter.
@router.get(
    "/tickets/waiting",
    response_model=TicketListResponse,
    summary="列出等待中的客服單（客服）",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "未提供或無效的 Bearer Token"},
        status.HTTP_403_FORBIDDEN: {"description": "非客服人員"},
    },
)
async def list_waiting_tickets(
    admin_info: Annotated[Tuple[str, str], Depends(get_current_admin)],
    svc: Annotated[CustomerServiceApplicationService, Depends(get_cs_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TicketListResponse:
    _, role = admin_info
    _require_cs_role(role)
    result = await svc.list_waiting_tickets(limit, offset)
    return TicketListResponse(
        items=[TicketResponse(**t.__dict__) for t in result.items],
        total=result.total,
        limit=result.limit,
        offset=result.offset,
    )


@router.get(
    "/tickets/{ticket_id}",
    response_model=TicketResponse,
    summary="取得客服單詳情（使用者）",
    responses={status.HTTP_404_NOT_FOUND: {"description": "客服單不存在"}},
)
async def get_ticket(
    ticket_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[CustomerServiceApplicationService, Depends(get_cs_service)],
) -> TicketResponse:
    try:
        dto = await svc.get_ticket(ticket_id)
    except TicketNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if dto.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your ticket.")
    return TicketResponse(**dto.__dict__)


@router.post(
    "/tickets/{ticket_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="發送訊息（使用者）",
    responses={
        status.HTTP_403_FORBIDDEN: {"description": "不是你的客服單或已關閉"},
        status.HTTP_404_NOT_FOUND: {"description": "客服單不存在"},
    },
)
async def send_user_message(
    ticket_id: str,
    body: SendMessageRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[CustomerServiceApplicationService, Depends(get_cs_service)],
) -> MessageResponse:
    try:
        dto = await svc.send_message(
            SendMessageCommand(
                sender_type="user",
                sender_id=user_id,
                ticket_id=ticket_id,
                content=body.content,
            )
        )
    except TicketNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except (MessageNotAllowedException, TicketClosedException) as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return MessageResponse(**dto.__dict__)


@router.post(
    "/tickets/{ticket_id}/close",
    response_model=TicketResponse,
    summary="關閉客服單（使用者）",
    responses={
        status.HTTP_403_FORBIDDEN: {"description": "不是你的客服單"},
        status.HTTP_404_NOT_FOUND: {"description": "客服單不存在"},
        status.HTTP_409_CONFLICT: {"description": "客服單已關閉"},
    },
)
async def close_ticket_by_user(
    ticket_id: str,
    _: CloseTicketRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[CustomerServiceApplicationService, Depends(get_cs_service)],
) -> TicketResponse:
    # Verify ownership
    try:
        ticket_dto = await svc.get_ticket(ticket_id)
    except TicketNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if ticket_dto.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your ticket.")

    try:
        dto = await svc.close_ticket(CloseTicketCommand(ticket_id=ticket_id, closed_by="user"))
    except TicketClosedException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return TicketResponse(**dto.__dict__)


@router.post(
    "/tickets/{ticket_id}/reopen",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="重新開啟客服單（使用者）",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "未提供或無效的 Bearer Token"},
        status.HTTP_403_FORBIDDEN: {"description": "不是你的客服單"},
        status.HTTP_404_NOT_FOUND: {"description": "前一客服單不存在"},
        status.HTTP_409_CONFLICT: {"description": "已有開啟中的客服單"},
    },
)
async def reopen_ticket(
    ticket_id: str,
    body: ReopenTicketRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[CustomerServiceApplicationService, Depends(get_cs_service)],
) -> TicketResponse:
    # Verify the previous ticket belongs to this user
    try:
        prev_dto = await svc.get_ticket(ticket_id)
    except TicketNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if prev_dto.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your ticket.")

    try:
        dto = await svc.reopen_ticket(
            ReopenTicketCommand(
                user_id=user_id,
                previous_ticket_id=ticket_id,
                title=body.title,
            )
        )
    except TicketAlreadyExistsException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return TicketResponse(**dto.__dict__)


@router.get(
    "/tickets/{ticket_id}/messages",
    response_model=MessageListResponse,
    summary="取得客服單訊息歷史",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "未提供或無效的 Bearer Token"},
        status.HTTP_403_FORBIDDEN: {"description": "非擁有者且非負責客服"},
        status.HTTP_404_NOT_FOUND: {"description": "客服單不存在"},
    },
)
async def get_ticket_messages(
    ticket_id: str,
    svc: Annotated[CustomerServiceApplicationService, Depends(get_cs_service)],
    admin_info: Annotated[Tuple[str, str] | None, Depends(get_current_admin_optional)] = None,
    user_id: Annotated[str | None, Depends(get_current_user_id)] = None,
    limit: int = Query(default=50, ge=1, le=100),
    before_id: str | None = Query(default=None, description="取得此 ID 之前的訊息"),
) -> MessageListResponse:
    # Get ticket to check authorization
    try:
        ticket_dto = await svc.get_ticket(ticket_id)
    except TicketNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    # Authorization: user owns ticket OR admin is assigned OR admin is superadmin
    is_authorized = False
    if user_id and ticket_dto.user_id == user_id:
        is_authorized = True
    if admin_info:
        admin_id, role = admin_info
        if role == AdminRole.SUPERADMIN.value:
            is_authorized = True
        elif ticket_dto.assigned_admin_id == admin_id:
            is_authorized = True

    if not is_authorized:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized.")

    result = await svc.get_messages(
        GetMessagesQuery(ticket_id=ticket_id, limit=limit, before_id=before_id)
    )
    return MessageListResponse(
        items=[MessageResponse(**m.__dict__) for m in result.items],
        returned_count=result.returned_count,
        limit=result.limit,
        has_more=result.has_more,
    )


# ── Agent Endpoints ──────────────────────────────────────────────────────────


@router.post(
    "/tickets/{ticket_id}/accept",
    response_model=TicketResponse,
    summary="接手客服單（客服）",
    responses={
        status.HTTP_403_FORBIDDEN: {"description": "非客服人員"},
        status.HTTP_404_NOT_FOUND: {"description": "客服單不存在"},
        status.HTTP_409_CONFLICT: {"description": "客服單非等待中狀態"},
    },
)
async def agent_accept_ticket(
    ticket_id: str,
    admin_info: Annotated[Tuple[str, str], Depends(get_current_admin)],
    svc: Annotated[CustomerServiceApplicationService, Depends(get_cs_service)],
) -> TicketResponse:
    _, role = admin_info
    _require_cs_role(role)
    admin_id, _ = admin_info

    try:
        dto = await svc.agent_accept(
            AgentAcceptTicketCommand(admin_id=admin_id, ticket_id=ticket_id)
        )
    except TicketNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except TicketNotWaitingException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return TicketResponse(**dto.__dict__)


@router.post(
    "/tickets/{ticket_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="回覆客服單（客服）",
    responses={
        status.HTTP_403_FORBIDDEN: {"description": "非負責客服或已關閉"},
        status.HTTP_404_NOT_FOUND: {"description": "客服單不存在"},
    },
)
async def agent_send_message(
    ticket_id: str,
    body: SendMessageRequest,
    admin_info: Annotated[Tuple[str, str], Depends(get_current_admin)],
    svc: Annotated[CustomerServiceApplicationService, Depends(get_cs_service)],
) -> MessageResponse:
    _, role = admin_info
    _require_cs_role(role)
    admin_id, _ = admin_info

    # Verify admin is assigned (superadmin bypasses this)
    if role != AdminRole.SUPERADMIN.value:
        try:
            ticket_dto = await svc.get_ticket(ticket_id)
        except TicketNotFoundException as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
        if ticket_dto.assigned_admin_id != admin_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to this ticket.",
            )

    try:
        dto = await svc.send_message(
            SendMessageCommand(
                sender_type="admin",
                sender_id=admin_id,
                ticket_id=ticket_id,
                content=body.content,
            )
        )
    except (MessageNotAllowedException, TicketClosedException) as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return MessageResponse(**dto.__dict__)


@router.post(
    "/tickets/{ticket_id}/close",
    response_model=TicketResponse,
    summary="關閉客服單（客服）",
    responses={
        status.HTTP_403_FORBIDDEN: {"description": "非負責客服或已關閉"},
        status.HTTP_404_NOT_FOUND: {"description": "客服單不存在"},
        status.HTTP_409_CONFLICT: {"description": "客服單已關閉"},
    },
)
async def agent_close_ticket(
    ticket_id: str,
    admin_info: Annotated[Tuple[str, str], Depends(get_current_admin)],
    svc: Annotated[CustomerServiceApplicationService, Depends(get_cs_service)],
) -> TicketResponse:
    _, role = admin_info
    _require_cs_role(role)
    admin_id, _ = admin_info

    # Verify admin is assigned (superadmin bypasses this)
    if role != AdminRole.SUPERADMIN.value:
        try:
            ticket_dto = await svc.get_ticket(ticket_id)
        except TicketNotFoundException as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
        if ticket_dto.assigned_admin_id != admin_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to this ticket.",
            )

    try:
        dto = await svc.close_ticket(
            CloseTicketCommand(ticket_id=ticket_id, closed_by="admin")
        )
    except TicketClosedException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return TicketResponse(**dto.__dict__)