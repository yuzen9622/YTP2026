"""Chat API router — streaming chat with tool calling."""
import asyncio
import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, StreamingResponse
from loguru import logger

from app.application.chat.commands import (
    ChatStreamCommand,
    DeleteConversationCommand,
    DeleteMessageCommand,
    GetMessagesQuery,
    ListConversationsQuery,
    SearchConversationsQuery,
    UpdateConversationCommand,
    UpdateMessageCommand,
)
from app.application.chat.query_service import ChatQueryService
from app.application.chat.service import ChatApplicationService
from app.interfaces.api.deps import get_chat_query_service, get_chat_service, get_current_user_id
from app.interfaces.api.v1.chat.schemas import (
    ChatStreamRequest,
    ConversationListItemSchema,
    ConversationListResponse,
    DeleteMessageResponse,
    MessageItemSchema,
    MessageListResponse,
    UpdateConversationRequest,
    UpdateMessageRequest,
    UpdateMessageResponse,
)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post(
    "/stream",
    summary="串流對話（含工具呼叫）",
    description=(
        "SSE 串流端點，需在標頭提供 `Authorization: Bearer <access_token>`。\n\n"
        "**對話鏈式架構**：每次呼叫 `/stream` 會在對話中新增一對（user + assistant）訊息。"
        "若要編輯或刪除訊息，請使用 `PATCH/DELETE /chat/conversations/{id}/messages/{msg_id}` 接口。\n\n"
        "**SSE 事件順序**：\n"
        "1. `text` — 模型回覆文字片段（可出现多次）\n"
        "2. `tool_call` — 模型觸發工具呼叫（可出现多次）\n"
        "3. `tool_result` — 工具執行結果（每個 tool_call 后紧跟一个）。"
        "其中 `search_knowledge_base` 的 `result` 固定含 `query/hits/sources/note/error/code`；"
        "`hits`/`sources` 內含 `document_id` 與 `source_url` 供前端導頁，無命中時為空陣列；"
        "履歷精靈工具包含 `start_resume_draft`、`update_resume_draft`、`finalize_resume_draft`、`set_resume_primary`。\n"
        "4. `done` — 回應結束，附帶 `conversation_id` 與 `message_id`（用於續傳多輪對話與刪除）\n"
        "5. `error` — 錯誤事件（發生錯誤時）"
    ),
    responses={
        status.HTTP_200_OK: {
            "description": "SSE 串流回應。依序發送 text / tool_call / tool_result / done / error 事件。",
            "content": {
                "text/event-stream": {
                    "schema": {
                        "oneOf": [
                            {
                                "type": "object",
                                "properties": {
                                    "type": {"const": "text"},
                                    "content": {"type": "string", "description": "模型回覆的文字片段"},
                                },
                                "required": ["type", "content"],
                                "additionalProperties": False,
                            },
                            {
                                "type": "object",
                                "properties": {
                                    "type": {"const": "tool_call"},
                                    "tool": {"type": "string", "description": "工具名稱"},
                                    "arguments": {"type": "string", "description": "工具參數的 JSON 字串"},
                                },
                                "required": ["type", "tool", "arguments"],
                                "additionalProperties": False,
                            },
                            {
                                "type": "object",
                                "properties": {
                                    "type": {"const": "tool_result"},
                                    "tool": {"type": "string", "description": "工具名稱"},
                                    "result": {
                                        "type": "object",
                                        "description": (
                                            "工具執行結果（JSON 物件）。"
                                            "`search_knowledge_base` 固定包含 "
                                            "query/hits/sources/note/error/code。"
                                        ),
                                    },
                                },
                                "required": ["type", "tool", "result"],
                                "additionalProperties": False,
                            },
                            {
                                "type": "object",
                                "properties": {
                                    "type": {"const": "done"},
                                    "conversation_id": {"type": "string", "description": "對話 ID，用於續傳多輪對話"},
                                    "message_id": {"type": "string", "description": "助手訊息 ID，可用於刪除"},
                                },
                                "required": ["type", "conversation_id", "message_id"],
                                "additionalProperties": False,
                            },
                            {
                                "type": "object",
                                "properties": {
                                    "type": {"const": "error"},
                                    "code": {"type": "integer", "description": "HTTP 錯誤碼或應用錯誤碼"},
                                    "message": {"type": "string", "description": "錯誤訊息"},
                                },
                                "required": ["type", "code", "message"],
                                "additionalProperties": False,
                            },
                        ],
                    },
                    "example": {
                        "type": "text",
                        "content": "以下是我為您整理的比賽與活動資訊...",
                    },
                },
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "JWT 缺失或無效",
            "content": {
                "application/json": {
                    "examples": {
                        "missing": {
                            "summary": "JWT 缺失",
                            "value": {"detail": "Access Token 已過期或無效", "code": "UNAUTHORIZED"},
                        },
                        "invalid": {
                            "summary": "JWT 無效或過期",
                            "value": {"detail": "Access Token 已過期或無效", "code": "UNAUTHORIZED"},
                        },
                    }
                }
            },
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "輸入驗證失敗",
            "content": {
                "application/json": {
                    "examples": {
                        "empty_message": {
                            "summary": "訊息為空",
                            "value": {"detail": [{"loc": ["body", "message"], "msg": "String should have at least 1 character", "type": "string_too_short"}]},
                        },
                        "message_too_long": {
                            "summary": "訊息超出長度限制",
                            "value": {"detail": [{"loc": ["body", "message"], "msg": "String should have at most 4000 characters", "type": "string_too_long"}]},
                        },
                    }
                }
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "伺服器內部錯誤（通常以 SSE error 事件呈現）",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "上游 LLM 服務不可用或串流逾時（通常以 SSE error 事件呈現）",
        },
    },
)
async def chat_stream(
    body: ChatStreamRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[ChatApplicationService, Depends(get_chat_service)],
) -> StreamingResponse:
    logger.info(
        "[api] /chat/stream started: user_id={} conv_id={} message_len={}",
        user_id, body.conversation_id, len(body.message),
    )
    cmd = ChatStreamCommand(
        user_id=user_id,
        message=body.message,
        conversation_id=body.conversation_id,
    )

    async def _stream_with_timeout():
        try:
            async with asyncio.timeout(120):
                async for chunk in svc.stream_chat(cmd):
                    yield chunk
        except TimeoutError:
            yield f"data: {json.dumps({'type': 'error', 'code': 503, 'message': 'Upstream LLM stream timed out.'})}\n\n"
        except Exception:
            yield f"data: {json.dumps({'type': 'error', 'code': 500, 'message': 'Unexpected streaming error.'})}\n\n"

    return StreamingResponse(
        _stream_with_timeout(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-store",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/conversations",
    summary="列出使用者的對話列表",
    description="取得目前認證使用者的所有對話區塊（分頁），依更新時間倒序排列。",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "JWT 缺失或無效",
        },
        status.HTTP_200_OK: {
            "description": "對話列表",
            "content": {
                "application/json": {
                    "examples": {
                        "default": {
                            "summary": "範例回應",
                            "value": {
                                "items": [
                                    {
                                        "id": "550e8400-e29b-41d4-a716-446655440000",
                                        "title": "新對話",
                                        "created_at": "2026-04-22T10:00:00+00:00",
                                        "updated_at": "2026-04-22T10:05:00+00:00",
                                    },
                                    {
                                        "id": "660e8400-e29b-41d4-a716-446655440001",
                                        "title": "AI 比賽查詢",
                                        "created_at": "2026-04-21T08:30:00+00:00",
                                        "updated_at": "2026-04-21T09:15:00+00:00",
                                    },
                                ],
                                "total": 2,
                                "limit": 20,
                                "offset": 0,
                            },
                        },
                    },
                    "schema": {
                        "type": "object",
                        "properties": {
                            "items": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string", "format": "uuid"},
                                        "title": {"type": "string"},
                                        "created_at": {"type": "string", "format": "date-time"},
                                        "updated_at": {"type": "string", "format": "date-time"},
                                    },
                                    "required": ["id", "title", "created_at", "updated_at"],
                                },
                            },
                            "total": {"type": "integer", "description": "符合條件的總筆數"},
                            "limit": {"type": "integer", "description": "本次回傳的筆數上限"},
                            "offset": {"type": "integer", "description": "跳過的筆數（分頁偏移）"},
                        },
                        "required": ["items", "total", "limit", "offset"],
                    },
                },
            },
        },
    },
)
async def list_conversations(
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[ChatQueryService, Depends(get_chat_query_service)],
    limit: Annotated[int, Query(ge=1, le=100, description="每頁回傳筆數上限")] = 20,
    offset: Annotated[int, Query(ge=0, description="跳過的筆數")] = 0,
) -> JSONResponse:
    query = ListConversationsQuery(user_id=user_id, limit=limit, offset=offset)
    dto = await svc.list_conversations(query)
    return JSONResponse(
        content={
            "items": [
                {
                    "id": item.id,
                    "title": item.title,
                    "created_at": item.created_at.isoformat(),
                    "updated_at": item.updated_at.isoformat(),
                }
                for item in dto.items
            ],
            "total": dto.total,
            "limit": dto.limit,
            "offset": dto.offset,
        }
    )

@router.get(
    "/conversations/search",
    summary="搜尋對話",
    description="以標題關鍵字搜尋使用者的對話（不分大小寫，支援模糊比對）。",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "JWT 缺失或無效",
        },
        status.HTTP_200_OK: {
            "description": "搜尋結果",
            "content": {
                "application/json": {
                    "examples": {
                        "default": {
                            "summary": "範例回應",
                            "value": {
                                "items": [
                                    {
                                        "id": "550e8400-e29b-41d4-a716-446655440000",
                                        "title": "2026 櫻花黑客松討論",
                                        "created_at": "2026-04-22T10:00:00+00:00",
                                        "updated_at": "2026-04-22T10:05:00+00:00",
                                    },
                                ],
                                "total": 1,
                                "limit": 20,
                                "offset": 0,
                            },
                        },
                    },
                    "schema": {
                        "type": "object",
                        "properties": {
                            "items": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string", "format": "uuid"},
                                        "title": {"type": "string"},
                                        "created_at": {"type": "string", "format": "date-time"},
                                        "updated_at": {"type": "string", "format": "date-time"},
                                    },
                                    "required": ["id", "title", "created_at", "updated_at"],
                                },
                            },
                            "total": {"type": "integer", "description": "符合條件的總筆數"},
                            "limit": {"type": "integer", "description": "本次回傳的筆數上限"},
                            "offset": {"type": "integer", "description": "跳過的筆數（分頁偏移）"},
                        },
                        "required": ["items", "total", "limit", "offset"],
                    },
                },
            },
        },
    },
)
async def search_conversations(
    q: Annotated[str, Query(min_length=1, max_length=255, description="搜尋關鍵字（不分大小寫）")],
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[ChatQueryService, Depends(get_chat_query_service)],
    limit: Annotated[int, Query(ge=1, le=100, description="每頁回傳筆數上限")] = 20,
    offset: Annotated[int, Query(ge=0, description="跳過的筆數")] = 0,
) -> JSONResponse:
    query = SearchConversationsQuery(user_id=user_id, q=q, limit=limit, offset=offset)
    dto = await svc.search_conversations(query)
    return JSONResponse(
        content={
            "items": [
                {
                    "id": item.id,
                    "title": item.title,
                    "created_at": item.created_at.isoformat(),
                    "updated_at": item.updated_at.isoformat(),
                }
                for item in dto.items
            ],
            "total": dto.total,
            "limit": dto.limit,
            "offset": dto.offset,
        }
    )


@router.patch(
    "/conversations/{conversation_id}",
    summary="更新對話標題",
    description=(
        "更新指定對話的標題。\n\n"
        "**認證方式**：`Authorization: Bearer <access_token>`"
    ),
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "JWT 缺失或無效"},
        status.HTTP_403_FORBIDDEN: {"description": "對話存在但不屬於目前使用者"},
        status.HTTP_404_NOT_FOUND: {"description": "對話不存在"},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"description": "標題格式不符"},
    },
)
async def update_conversation(
    conversation_id: str,
    body: UpdateConversationRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[ChatApplicationService, Depends(get_chat_service)],
) -> JSONResponse:
    from app.application.chat.commands import UpdateConversationCommand
    from app.core.exceptions import ForbiddenException, ResourceNotFoundException

    cmd = UpdateConversationCommand(
        user_id=user_id,
        conversation_id=conversation_id,
        title=body.title,
    )
    try:
        await svc.update_conversation(cmd)
    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except ForbiddenException as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    return JSONResponse(
        content={"id": conversation_id, "updated": True},
        status_code=status.HTTP_200_OK,
    )


@router.delete(
    "/conversations/{conversation_id}",
    summary="刪除對話",
    description=(
        "刪除指定對話及所有隸屬訊息。刪除後無法復原。\n\n"
        "**認證方式**：`Authorization: Bearer <access_token>`"
    ),
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "JWT 缺失或無效"},
        status.HTTP_403_FORBIDDEN: {"description": "對話存在但不屬於目前使用者"},
        status.HTTP_404_NOT_FOUND: {"description": "對話不存在"},
    },
)
async def delete_conversation(
    conversation_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[ChatApplicationService, Depends(get_chat_service)],
) -> JSONResponse:
    from app.application.chat.commands import DeleteConversationCommand
    from app.core.exceptions import ForbiddenException, ResourceNotFoundException

    cmd = DeleteConversationCommand(user_id=user_id, conversation_id=conversation_id)
    try:
        await svc.delete_conversation(cmd)
    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except ForbiddenException as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    return JSONResponse(content={"id": conversation_id, "deleted": True})


@router.get(
    "/conversations/{conversation_id}/messages",
    summary="取得對話的訊息列表",
    description="取得指定對話的訊息列表（分頁）。只有對話擁有者可存取。",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "JWT 缺失或無效"},
        status.HTTP_403_FORBIDDEN: {"description": "對話存在但不屬於目前使用者"},
        status.HTTP_404_NOT_FOUND: {"description": "對話不存在"},
    },
)
async def get_messages(
    conversation_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[ChatQueryService, Depends(get_chat_query_service)],
    limit: Annotated[int, Query(ge=1, le=100, description="每頁回傳筆數上限")] = 50,
    before_message_id: Annotated[str | None, Query(description="訊息 ID，取其之前的更早訊息")] = None,
) -> JSONResponse:
    from app.core.exceptions import ForbiddenException, ResourceNotFoundException

    query = GetMessagesQuery(
        user_id=user_id,
        conversation_id=conversation_id,
        limit=limit,
        before_message_id=before_message_id,
    )
    try:
        dto = await svc.get_messages(query)
    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except ForbiddenException as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    return JSONResponse(
        content={
            "items": [
                {
                    "id": item.id,
                    "conversation_id": item.conversation_id,
                    "role": item.role,
                    "content": item.content,
                    "tool_name": item.tool_name,
                    "created_at": item.created_at.isoformat(),
                }
                for item in dto.items
            ],
            "returned_count": dto.returned_count,
            "limit": dto.limit,
            "has_more": dto.has_more,
        }
    )


@router.patch(
    "/conversations/{conversation_id}/messages/{message_id}",
    summary="編輯訊息（連鎖刪除）",
    description=(
        "編輯指定訊息的內容。\n\n"
        "**連鎖刪除行為**：編輯訊息 N 後，訊息 N+1、N+2、... 等所有較新的訊息都會被刪除。"
        "這是鏈式對話架構的設計：上方編輯後，下方較新的對話紀錄會一併移除，以確保對話邏輯一致性。\n\n"
        "**認證方式**：`Authorization: Bearer <access_token>`"
    ),
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "JWT 缺失或無效"},
        status.HTTP_403_FORBIDDEN: {"description": "對話存在但不屬於目前使用者"},
        status.HTTP_404_NOT_FOUND: {"description": "對話或訊息不存在"},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"description": "內容格式不符（空白或過長）"},
    },
)
async def update_message(
    conversation_id: str,
    message_id: str,
    body: UpdateMessageRequest,
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[ChatApplicationService, Depends(get_chat_service)],
) -> UpdateMessageResponse:
    from app.application.chat.commands import UpdateMessageCommand
    from app.core.exceptions import ForbiddenException, ResourceNotFoundException

    cmd = UpdateMessageCommand(
        user_id=user_id,
        conversation_id=conversation_id,
        message_id=message_id,
        content=body.content,
    )
    try:
        truncated_count = await svc.update_message(cmd)
    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except ForbiddenException as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    return UpdateMessageResponse(
        conversation_id=conversation_id,
        message_id=message_id,
        content=body.content,
        truncated_count=truncated_count,
    )


@router.delete(
    "/conversations/{conversation_id}/messages/{message_id}",
    summary="刪除訊息（連鎖刪除）",
    description=(
        "刪除指定訊息。\n\n"
        "**連鎖刪除行為**：刪除訊息 N 後，訊息 N+1、N+2、... 等所有較新的訊息都會被刪除。"
        "這是鏈式對話架構的設計：刪除上方訊息後，下方較新的對話紀錄會一併移除，以確保對話邏輯一致性。\n\n"
        "**認證方式**：`Authorization: Bearer <access_token>`"
    ),
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "JWT 缺失或無效"},
        status.HTTP_403_FORBIDDEN: {"description": "對話存在但不屬於目前使用者"},
        status.HTTP_404_NOT_FOUND: {"description": "對話或訊息不存在"},
    },
)
async def delete_message(
    conversation_id: str,
    message_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    svc: Annotated[ChatApplicationService, Depends(get_chat_service)],
) -> DeleteMessageResponse:
    from app.application.chat.commands import DeleteMessageCommand
    from app.core.exceptions import ForbiddenException, ResourceNotFoundException

    cmd = DeleteMessageCommand(
        user_id=user_id,
        conversation_id=conversation_id,
        message_id=message_id,
    )
    try:
        total_deleted = await svc.delete_message(cmd)
    except ResourceNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except ForbiddenException as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    return DeleteMessageResponse(
        conversation_id=conversation_id,
        message_id=message_id,
        total_deleted=total_deleted,
    )
