"""Pydantic schemas for chat streaming endpoint."""
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ChatStreamRequest(BaseModel):
    """POST /chat/stream request body."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "我想找一份在台北的軟體工程師工作",
                "conversation_id": None,
            }
        }
    )

    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="使用者輸入的訊息（1–4000 字元）",
    )
    conversation_id: Optional[str] = Field(
        None,
        description="對話 ID（用於多輪對話續傳；如不提供則自動產生新的 UUID）",
    )


class ChatTextEvent(BaseModel):
    """SSE text chunk event."""

    type: Literal["text"] = "text"
    content: str = Field(description="模型回覆的文字片段")


class ChatToolCallEvent(BaseModel):
    """SSE tool call event."""

    type: Literal["tool_call"] = "tool_call"
    tool: str = Field(description="工具名稱")
    arguments: str = Field(description="工具參數的 JSON 字串")


class ChatToolResultEvent(BaseModel):
    """SSE tool result event."""

    type: Literal["tool_result"] = "tool_result"
    tool: str = Field(description="工具名稱")
    result: dict = Field(
        description=(
            "工具執行結果（JSON 物件）。`search_knowledge_base` 時固定包含 "
            "`query/hits/sources/note/error/code` 六個欄位；"
            "無命中時 `hits` 與 `sources` 會是空陣列，供前端穩定渲染。"
        )
    )


class ChatDoneEvent(BaseModel):
    """SSE response done event."""

    type: Literal["done"] = "done"
    conversation_id: str = Field(description="對話 ID，用於續傳多輪對話")
    message_id: str = Field(description="助手訊息 ID，可用於刪除")


class ChatErrorEvent(BaseModel):
    """SSE error event."""

    type: Literal["error"] = "error"
    code: int = Field(description="HTTP 錯誤碼或應用錯誤碼")
    message: str = Field(description="錯誤訊息")


# ---------------------------------------------------------------------------
# Conversation list schemas
# ---------------------------------------------------------------------------


class ConversationListItemSchema(BaseModel):
    """Summary of a single conversation."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "新對話",
                "created_at": "2026-04-22T10:00:00Z",
                "updated_at": "2026-04-22T10:05:00Z",
            }
        }
    )

    id: str = Field(description="對話 ID（UUID）")
    title: str = Field(description="對話標題")
    created_at: str = Field(description="建立時間（ISO 8601）")
    updated_at: str = Field(description="最後更新時間（ISO 8601）")


class ConversationListResponse(BaseModel):
    """Paginated list of conversations."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 1,
                "limit": 20,
                "offset": 0,
            }
        }
    )

    items: list[ConversationListItemSchema] = Field(description="對話列表")
    total: int = Field(description="符合條件的總筆數")
    limit: int = Field(description="本次回傳的筆數上限")
    offset: int = Field(description="跳過的筆數（分頁偏移）")


# ---------------------------------------------------------------------------
# Message list schemas
# ---------------------------------------------------------------------------


class MessageItemSchema(BaseModel):
    """A single chat message."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "660e8400-e29b-41d4-a716-446655440001",
                "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                "role": "user",
                "content": "我想報名比賽",
                "tool_name": None,
                "created_at": "2026-04-22T10:00:00Z",
            }
        }
    )

    id: str = Field(description="訊息 ID（UUID）")
    conversation_id: str = Field(description="所屬對話 ID（UUID）")
    role: str = Field(description="角色：user / assistant / tool")
    content: str = Field(description="訊息內容")
    tool_name: str | None = Field(None, description="若 role=tool，記錄觸發的工具名稱")
    created_at: str = Field(description="時間（ISO 8601）")


class MessageListResponse(BaseModel):
    """Paginated message list for a conversation."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "returned_count": 0,
                "limit": 50,
                "has_more": False,
            }
        }
    )

    items: list[MessageItemSchema] = Field(description="訊息列表（依時間新→舊）")
    returned_count: int = Field(description="本次回傳的筆數")
    limit: int = Field(description="本次回傳的筆數上限")
    has_more: bool = Field(description="是否還有更多訊息（可用 before_message_id 參數取得更早的訊息）")


# ---------------------------------------------------------------------------
# Conversation management schemas
# ---------------------------------------------------------------------------


class UpdateConversationRequest(BaseModel):
    """PATCH /chat/conversations/{conversation_id} request body."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "更新後的對話標題",
            }
        }
    )

    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="對話新標題（1–255 字元）",
    )


class DeleteConversationResponse(BaseModel):
    """DELETE /chat/conversations/{conversation_id} response body."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "deleted": True,
            }
        }
    )

    id: str = Field(description="已刪除的對話 ID")
    deleted: bool = Field(description="刪除是否成功")


# ---------------------------------------------------------------------------
# Message management schemas
# ---------------------------------------------------------------------------


class UpdateMessageRequest(BaseModel):
    """PATCH /chat/conversations/{conversation_id}/messages/{message_id} request body."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "這是我更正後的訊息內容",
            }
        }
    )

    content: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="更新後的訊息內容（1–4000 字元）",
    )


class UpdateMessageResponse(BaseModel):
    """PATCH /chat/conversations/{conversation_id}/messages/{message_id} response body.

    Cascade truncation applied after edit: all messages after the edited
    message (exclusive) are removed. The `truncated_count` field reports
    how many subsequent messages were deleted.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                "message_id": "660e8400-e29b-41d4-a716-446655440001",
                "content": "這是我更正後的訊息內容",
                "truncated_count": 3,
            }
        }
    )

    conversation_id: str = Field(description="所屬對話 ID")
    message_id: str = Field(description="被編輯的訊息 ID")
    content: str = Field(description="編輯後的訊息內容")
    truncated_count: int = Field(description="編輯引發的連鎖刪除筆數（此訊息之後的所有訊息）")


class DeleteMessageResponse(BaseModel):
    """DELETE /chat/conversations/{conversation_id}/messages/{message_id} response body.

    Cascade truncation applied: all messages after the deleted message
    (inclusive) are removed. The `total_deleted` field reports how many
    messages were removed in total.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                "message_id": "660e8400-e29b-41d4-a716-446655440001",
                "total_deleted": 4,
            }
        }
    )

    conversation_id: str = Field(description="所屬對話 ID")
    message_id: str = Field(description="被刪除的訊息 ID")
    total_deleted: int = Field(
        description="連鎖刪除的總筆數（含目標訊息及其後所有訊息）"
    )
