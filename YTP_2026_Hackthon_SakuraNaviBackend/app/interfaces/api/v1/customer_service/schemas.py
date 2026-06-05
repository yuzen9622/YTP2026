"""Pydantic schemas for customer service endpoints."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CreateTicketRequest(BaseModel):
    """POST /customer-service/tickets request body."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "無法登入帳戶",
            }
        }
    )

    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="客服單標題（1–255 字元）",
    )


class TicketResponse(BaseModel):
    """Customer service ticket response."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "660e8400-e29b-41d4-a716-446655440001",
                "assigned_admin_id": None,
                "status": "waiting",
                "previous_ticket_id": None,
                "title": "無法登入帳戶",
                "created_at": "2026-04-26T10:00:00Z",
                "updated_at": "2026-04-26T10:00:00Z",
                "closed_at": None,
                "closed_by": None,
            }
        }
    )

    id: str = Field(description="客服單 ID")
    user_id: str = Field(description="發起者使用者 ID")
    assigned_admin_id: Optional[str] = Field(None, description="負責客服 ID（等待中為 null）")
    status: str = Field(description="狀態：waiting / active / closed")
    previous_ticket_id: Optional[str] = Field(None, description="前一關聯客服單 ID")
    title: str = Field(description="標題")
    created_at: datetime = Field(description="建立時間")
    updated_at: datetime = Field(description="最後更新時間")
    closed_at: Optional[datetime] = Field(None, description="關閉時間")
    closed_by: Optional[str] = Field(None, description="關閉者：user / admin")


class TicketListResponse(BaseModel):
    """Paginated ticket list response."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "user_id": "660e8400-e29b-41d4-a716-446655440001",
                        "assigned_admin_id": None,
                        "status": "waiting",
                        "previous_ticket_id": None,
                        "title": "無法登入帳戶",
                        "created_at": "2026-04-26T10:00:00Z",
                        "updated_at": "2026-04-26T10:00:00Z",
                        "closed_at": None,
                        "closed_by": None,
                    }
                ],
                "total": 1,
                "limit": 20,
                "offset": 0,
            }
        }
    )

    items: List[TicketResponse] = Field(description="客服單列表")
    total: int = Field(description="總筆數")
    limit: int = Field(description="本頁上限")
    offset: int = Field(description="跳過筆數")


class SendMessageRequest(BaseModel):
    """POST /customer-service/tickets/{ticket_id}/messages request body."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "我想詢問關於訂單的問題",
            }
        }
    )

    content: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="訊息內容（1–4000 字元）",
    )


class MessageResponse(BaseModel):
    """Customer service message response."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "770e8400-e29b-41d4-a716-446655440002",
                "ticket_id": "550e8400-e29b-41d4-a716-446655440000",
                "sender_type": "user",
                "sender_id": "660e8400-e29b-41d4-a716-446655440001",
                "content": "我想詢問關於訂單的問題",
                "created_at": "2026-04-26T10:05:00Z",
            }
        }
    )

    id: str = Field(description="訊息 ID")
    ticket_id: str = Field(description="所屬客服單 ID")
    sender_type: str = Field(description="發送者類型：user / admin / system")
    sender_id: str = Field(description="發送者 ID")
    content: str = Field(description="訊息內容")
    created_at: datetime = Field(description="發送時間")


class MessageListResponse(BaseModel):
    """Paginated message list response."""
    items: List[MessageResponse] = Field(description="訊息列表")
    returned_count: int = Field(description="本頁回傳筆數")
    limit: int = Field(description="本頁上限")
    has_more: bool = Field(description="是否還有更多訊息")


class CloseTicketRequest(BaseModel):
    """POST /customer-service/tickets/{ticket_id}/close request body."""
    closed_by: Optional[str] = Field(
        default=None,
        description="關閉者：user 或 admin（由伺服器端決定，此欄位可忽略）",
    )


class ReopenTicketRequest(BaseModel):
    """POST /customer-service/tickets/{ticket_id}/reopen request body."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "問題仍未解決，需要 further 協助",
            }
        }
    )

    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="新客服單標題（1–255 字元）",
    )