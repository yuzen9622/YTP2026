"""Tool definitions and executor for MiniMax function-calling."""
import json
from typing import Any
from urllib.parse import urlparse

import httpx

from app.application.chat.ports import ToolExecutor
from app.application.rag.queries import SearchKnowledgeBaseQuery
from app.application.rag.service import RagApplicationService
from app.application.resume.commands import SetPrimaryResumeCommand
from app.application.resume.service import ResumeApplicationService
from app.application.resume_draft.commands import (
    FinalizeResumeDraftCommand,
    LoadResumeForEditCommand,
    StartResumeDraftCommand,
    UpdateResumeDraftCommand,
)
from app.application.resume_draft.dtos import ResumeDraftProgressDTO
from app.application.resume_draft.service import ResumeDraftApplicationService
from app.application.user.queries import GetUserProfileQuery
from app.application.user.service import UserApplicationService
from app.core.config import settings
from loguru import logger


# MiniMax function-calling tool definitions
# NOTE: call_internal_api is intentionally excluded — it created an SSRF attack surface.
TOOL_DEFINITIONS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "get_user_profile",
            "description": "Retrieve the authenticated user's profile data including name, account, email, phone, bio, career, and tags.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_resumes",
            "description": "Retrieve one or more of the authenticated user's resumes by their IDs. Returns title, summary, skills, work experiences, and expected salary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "resume_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of resume UUIDs to retrieve. Pass empty array to get all resumes for the user.",
                    },
                },
                "required": ["resume_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "start_resume_draft",
            "description": "Start or load the active resume draft for this conversation. Returns the next guided question and missing required fields.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "load_resume_for_edit",
            "description": "將現有履歷載入草稿階段，之後可逐欄位修改。呼叫前需先確認 user 想修改哪份履歷。",
            "parameters": {
                "type": "object",
                "properties": {
                    "resume_id": {
                        "type": "string",
                        "description": "履歷 UUID",
                    },
                },
                "required": ["resume_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_resume_draft",
            "description": "Patch the active resume draft fields in this conversation. Use this after collecting one answer from the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patch": {
                        "type": "object",
                        "description": "Draft patch object. Supported keys: title, summary, skills, work_experiences, external_links, expected_salary, work_time_range.",
                    },
                },
                "required": ["patch"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finalize_resume_draft",
            "description": "Finalize the active draft into a real resume after required fields are completed.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_resume_primary",
            "description": "Set one of the user's resumes as primary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "resume_id": {
                        "type": "string",
                        "description": "Resume UUID.",
                    },
                },
                "required": ["resume_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tools",
            "description": "List all available tools that can be called. Returns the name and description of each tool so the user knows what actions can be performed.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": (
                "搜尋 SakuraNavi 內部知識庫的官方青年政策文件（青創貸款、留學貸款、實習津貼、"
                "國際發展補助、創業諮詢、國際交流等）。回傳最相關的內容片段與可點擊來源。"
                "**優先順序**：使用者問及具體政策內容、申請條件、補助金額、創業諮詢、國際交流等，"
                "請先呼叫此工具；若知識庫無命中或屬即時性問題（職缺、活動截止日、最新公告），再用 web_search。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "查詢字串，建議使用使用者原問句的關鍵詞。",
                    },
                    "category": {
                        "type": "string",
                        "enum": [
                            "general",
                            "youth_subsidy",
                            "entrepreneurship",
                            "international",
                            "latest_news",
                            "policy_news",
                        ],
                        "description": "（選填）限定 RAG 分類 tag name。",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "回傳片段數，預設 5，最多 10。",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "在網際網路上搜尋即時資訊。適用於查詢青年政策補助、活動、申請期限、資格條件、"
                "求職資訊、學生事務及任何需要最新資料的問題。"
                "搜尋結果包含標題、來源 URL 與摘要，回答時請標示來源網址。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "搜尋關鍵字，建議加上site:限定官方來源，例如 "
                            "'site:youth.gov.taipei 青年實習津貼申請資格'。"
                        ),
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "回傳結果筆數上限，預設 5，最多 10。",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
]


# Static tool metadata for list_tools response
_TOOL_METADATA: list[dict] = [
    {
        "name": "get_user_profile",
        "description": "Retrieve the authenticated user's profile data including name, account, email, phone, bio, career, and tags. No parameters.",
    },
    {
        "name": "get_user_resumes",
        "description": "Retrieve resumes for the authenticated user. Parameters: resume_ids (array of string UUIDs, required). Pass an empty array to get all resumes.",
    },
    {
        "name": "start_resume_draft",
        "description": "Start or load a conversation-scoped resume draft. No parameters.",
    },
    {
        "name": "load_resume_for_edit",
        "description": "將現有履歷載入草稿階段。Parameters: resume_id (string, required).",
    },
    {
        "name": "update_resume_draft",
        "description": "Update the active resume draft. Parameters: patch (object, required).",
    },
    {
        "name": "finalize_resume_draft",
        "description": "Finalize active draft into a resume and remove the draft. No parameters.",
    },
    {
        "name": "set_resume_primary",
        "description": "Set a resume as primary. Parameters: resume_id (string UUID, required).",
    },
    {
        "name": "list_tools",
        "description": "List all available tools that can be called. No parameters.",
    },
    {
        "name": "search_knowledge_base",
        "description": (
            "搜尋內部 RAG 知識庫的青年政策官方文件，回傳片段與可點擊來源（含 source_url/document_id）。"
            "Parameters: query (string, required), category (string, optional tag name), "
            "top_k (integer, optional, default 5)。"
            "Result payload is stable: query/hits/sources/note/error/code."
        ),
    },
    {
        "name": "web_search",
        "description": (
            "在網際網路搜尋即時資訊，回傳標題、URL 與摘要。"
            "適用於青年政策、補助、活動、求職、學生事務等查詢。"
            "Parameters: query (string, required), max_results (integer, optional, default 5)."
        ),
    },
]


class ToolExecutorImpl:
    """Executes tools on behalf of the LLM, using MiniMax function-calling protocol."""

    def __init__(
        self,
        user_app_service: UserApplicationService,
        http_client: httpx.AsyncClient,
        access_token: str,
        resume_app_service: ResumeApplicationService | None = None,
        rag_app_service: RagApplicationService | None = None,
        resume_draft_app_service: ResumeDraftApplicationService | None = None,
    ) -> None:
        self._user_svc = user_app_service
        self._http = http_client
        self._access_token = access_token
        self._resume_svc = resume_app_service
        self._rag_svc = rag_app_service
        self._resume_draft_svc = resume_draft_app_service

    async def execute(
        self,
        tool_name: str,
        arguments: str,
        user_id: str,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        """Execute a named tool with JSON arguments and return its result.

        Args:
            tool_name: Name of the tool to execute.
            arguments: JSON string of tool arguments.
            user_id: Authenticated user ID for context.
            conversation_id: Optional conversation scope for draft tools.

        Returns:
            Tool result dict (JSON-serializable).
        """
        logger.debug(
            "[tool] Executing tool={} user_id={} conv_id={} args={}",
            tool_name,
            user_id,
            conversation_id,
            arguments,
        )
        try:
            args = json.loads(arguments) if arguments else {}
        except json.JSONDecodeError as exc:
            logger.debug("[tool] Invalid JSON arguments for tool={}: {}", tool_name, exc)
            if tool_name == "search_knowledge_base":
                return self._build_search_result_payload(
                    query="",
                    hits=[],
                    sources=[],
                    note="知識庫查詢參數格式錯誤，請稍後再試。",
                    error=f"Invalid arguments JSON: {exc}",
                    code="RAG_INVALID_ARGUMENTS_JSON",
                )
            return {"error": f"Invalid arguments JSON: {exc}"}

        handler = {
            "get_user_profile": self._get_user_profile,
            "get_user_resumes": self._get_user_resumes,
            "start_resume_draft": self._start_resume_draft,
            "load_resume_for_edit": self._load_resume_for_edit,
            "update_resume_draft": self._update_resume_draft,
            "finalize_resume_draft": self._finalize_resume_draft,
            "set_resume_primary": self._set_resume_primary,
            "list_tools": self._list_tools,
            "search_knowledge_base": self._search_knowledge_base,
            "web_search": self._web_search,
        }.get(tool_name)

        if not handler:
            logger.warning("[tool] Unknown tool requested: {}", tool_name)
            return {"error": f"Unknown tool: {tool_name}"}

        try:
            result = await handler(
                user_id=user_id,
                conversation_id=conversation_id,
                **args,
            )
            logger.debug("[tool] Tool={} result_keys={}", tool_name, list(result.keys()))
            return result
        except TypeError as exc:
            logger.debug("[tool] Tool={} invalid arguments: {}", tool_name, exc)
            if tool_name == "search_knowledge_base":
                query = args.get("query", "") if isinstance(args, dict) else ""
                return self._build_search_result_payload(
                    query=str(query),
                    hits=[],
                    sources=[],
                    note="知識庫查詢參數不正確，請稍後再試。",
                    error=f"工具參數無效: {exc}",
                    code="RAG_INVALID_ARGUMENTS",
                )
            return {"error": f"工具參數無效: {exc}"}
        except ValueError as exc:
            logger.debug("[tool] Tool={} value error: {}", tool_name, exc)
            if tool_name == "search_knowledge_base":
                query = args.get("query", "") if isinstance(args, dict) else ""
                return self._build_search_result_payload(
                    query=str(query),
                    hits=[],
                    sources=[],
                    note="知識庫查詢參數不正確，請稍後再試。",
                    error=str(exc),
                    code="RAG_INVALID_VALUE",
                )
            return {"error": str(exc)}
        except httpx.TimeoutException:
            logger.error("[tool] Tool={} request timed out", tool_name)
            if tool_name == "search_knowledge_base":
                query = args.get("query", "") if isinstance(args, dict) else ""
                return self._build_search_result_payload(
                    query=str(query),
                    hits=[],
                    sources=[],
                    note="知識庫檢索逾時，請稍後再試。",
                    error="工具請求逾時",
                    code="RAG_TIMEOUT",
                )
            return {"error": "工具請求逾時"}
        except httpx.RequestError as exc:
            logger.error("[tool] Tool={} network error: {}", tool_name, exc)
            if tool_name == "search_knowledge_base":
                query = args.get("query", "") if isinstance(args, dict) else ""
                return self._build_search_result_payload(
                    query=str(query),
                    hits=[],
                    sources=[],
                    note="知識庫連線異常，請稍後再試。",
                    error=f"網路錯誤: {exc}",
                    code="RAG_NETWORK_ERROR",
                )
            return {"error": f"網路錯誤: {exc}"}
        except Exception as exc:  # noqa: BLE001
            logger.exception("[tool] Tool={} unexpected error: {}", tool_name, exc)
            if tool_name == "search_knowledge_base":
                query = args.get("query", "") if isinstance(args, dict) else ""
                return self._build_search_result_payload(
                    query=str(query),
                    hits=[],
                    sources=[],
                    note="知識庫暫時不可用，請稍後再試。",
                    error=f"Unexpected tool error: {exc}",
                    code="RAG_UNEXPECTED_ERROR",
                )
            return {"error": f"Unexpected tool error: {exc}"}

    async def close(self) -> None:
        """No-op: executor reuses shared clients managed by dependency lifecycle."""
        return None

    def get_tool_definitions(self) -> list[dict]:
        """Return the MiniMax-compatible tool definitions for this executor."""
        return TOOL_DEFINITIONS

    async def _get_user_profile(
        self,
        user_id: str,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        """Retrieve user profile via the application service."""
        dto = await self._user_svc.get_profile(GetUserProfileQuery(user_id=user_id))
        return {
            "id": dto.id,
            "name": dto.name,
            "account": dto.account,
            "email": dto.email,
            "phone": dto.phone,
            "bio": dto.bio,
            "birth_date": dto.birth_date.isoformat() if dto.birth_date else None,
            "career": dto.career,
            "tags": list(dto.tags),
            "is_active": dto.is_active,
        }

    async def _get_user_resumes(
        self,
        user_id: str,
        conversation_id: str | None = None,
        resume_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Retrieve resumes for the user by IDs, or all resumes if resume_ids is empty.

        Always returns a stable `resumes` list for robust downstream parsing.
        """
        if self._resume_svc is None:
            return {
                "resumes": [],
                "error": "Resume service is not configured on this server.",
                "code": "RESUME_UNAVAILABLE",
            }

        if resume_ids is None:
            normalized_ids: list[str] = []
        elif isinstance(resume_ids, list):
            normalized_ids = [
                rid.strip() for rid in resume_ids
                if isinstance(rid, str) and rid.strip()
            ]
        else:
            return {
                "resumes": [],
                "error": "Invalid arguments: resume_ids must be an array of UUID strings.",
                "code": "INVALID_RESUME_IDS",
            }

        try:
            if not normalized_ids:
                dtos = await self._resume_svc.get_resumes(user_id)
            else:
                dtos = []
                for rid in normalized_ids:
                    try:
                        dto = await self._resume_svc.get_resume(rid, user_id)
                    except Exception:
                        # Skip IDs that cannot be loaded; keep schema stable.
                        continue
                    if dto:
                        dtos.append(dto)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[tool] get_user_resumes failed: user_id={} err={}", user_id, exc)
            return {
                "resumes": [],
                "error": "Failed to retrieve resumes.",
                "code": "RESUME_FETCH_FAILED",
            }

        resumes_payload: list[dict[str, Any]] = []
        for dto in dtos:
            skills_payload: list[dict[str, Any]] = []
            for s in dto.skills:
                if not isinstance(s, dict):
                    continue
                skills_payload.append({
                    "name": s.get("name"),
                    "level": s.get("level"),
                })

            resumes_payload.append(
                {
                    "id": dto.id,
                    "title": dto.title,
                    "summary": dto.summary,
                    "skills": skills_payload,
                    "work_experiences": list(dto.work_experiences),
                    "external_links": list(dto.external_links),
                    "expected_salary": dto.expected_salary,
                    "work_time_range": dto.work_time_range,
                    "is_primary": dto.is_primary,
                }
            )

        return {"resumes": resumes_payload}

    async def _start_resume_draft(
        self,
        user_id: str,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        """Start or load a conversation-scoped resume draft."""
        if self._resume_draft_svc is None:
            return {
                "error": "Resume draft service is not configured on this server.",
                "code": "RESUME_DRAFT_UNAVAILABLE",
            }
        conv_id = self._require_conversation_id(conversation_id)
        progress = await self._resume_draft_svc.start_or_get_draft(
            StartResumeDraftCommand(user_id=user_id, conversation_id=conv_id)
        )
        return self._serialize_draft_progress(progress)

    async def _load_resume_for_edit(
        self,
        user_id: str,
        conversation_id: str | None = None,
        resume_id: str | None = None,
    ) -> dict[str, Any]:
        """Load an existing resume into the draft session for editing."""
        if self._resume_draft_svc is None:
            return {
                "error": "Resume draft service is not configured on this server.",
                "code": "RESUME_DRAFT_UNAVAILABLE",
            }
        if not isinstance(resume_id, str) or not resume_id.strip():
            return {
                "error": "resume_id is required.",
                "code": "INVALID_RESUME_ID",
            }
        conv_id = self._require_conversation_id(conversation_id)
        progress = await self._resume_draft_svc.load_resume_for_edit(
            LoadResumeForEditCommand(
                user_id=user_id,
                conversation_id=conv_id,
                resume_id=resume_id.strip(),
            )
        )
        return self._serialize_draft_progress(progress)

    async def _update_resume_draft(
        self,
        user_id: str,
        conversation_id: str | None = None,
        patch: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update active draft with one round's collected answer."""
        if self._resume_draft_svc is None:
            return {
                "error": "Resume draft service is not configured on this server.",
                "code": "RESUME_DRAFT_UNAVAILABLE",
            }
        conv_id = self._require_conversation_id(conversation_id)
        progress = await self._resume_draft_svc.update_draft(
            UpdateResumeDraftCommand(
                user_id=user_id,
                conversation_id=conv_id,
                patch=patch or {},
            )
        )
        return self._serialize_draft_progress(progress)

    async def _finalize_resume_draft(
        self,
        user_id: str,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        """Finalize active draft into a real resume record."""
        if self._resume_draft_svc is None:
            return {
                "error": "Resume draft service is not configured on this server.",
                "code": "RESUME_DRAFT_UNAVAILABLE",
            }
        conv_id = self._require_conversation_id(conversation_id)
        dto = await self._resume_draft_svc.finalize_draft(
            FinalizeResumeDraftCommand(user_id=user_id, conversation_id=conv_id)
        )
        return {
            "resume_id": dto.id,
            "title": dto.title,
            "is_primary": dto.is_primary,
            "message": "履歷已建立完成。接下來可詢問是否要設為主要履歷。",
        }

    async def _set_resume_primary(
        self,
        user_id: str,
        conversation_id: str | None = None,
        resume_id: str | None = None,
    ) -> dict[str, Any]:
        """Set the specified resume as primary."""
        if self._resume_svc is None:
            return {
                "error": "Resume service is not configured on this server.",
                "code": "RESUME_UNAVAILABLE",
            }
        if not isinstance(resume_id, str) or not resume_id.strip():
            return {
                "error": "resume_id is required.",
                "code": "INVALID_RESUME_ID",
            }
        dto = await self._resume_svc.set_primary(
            SetPrimaryResumeCommand(user_id=user_id, resume_id=resume_id.strip())
        )
        return {
            "resume_id": dto.id,
            "is_primary": dto.is_primary,
            "message": "已設定為主要履歷。",
        }

    async def _search_knowledge_base(
        self,
        user_id: str,
        conversation_id: str | None = None,
        query: str = "",
        category: str | None = None,
        top_k: int = 5,
    ) -> dict[str, Any]:
        """Hybrid retrieval over the internal RAG knowledge base.

        Returns hits (with snippets) plus a deduplicated `sources` list so the
        client UI can show users which documents were consulted.
        """
        normalized_query = str(query or "").strip()
        if self._rag_svc is None:
            return self._build_search_result_payload(
                query=normalized_query,
                hits=[],
                sources=[],
                note="知識庫暫時不可用，請稍後再試。",
                error="Knowledge-base search is not configured on this server.",
                code="RAG_UNAVAILABLE",
            )
        top_k = max(1, min(int(top_k or 5), 10))
        normalized_category = category if category else None

        try:
            result = await self._rag_svc.search(
                SearchKnowledgeBaseQuery(
                    query=normalized_query,
                    top_k=top_k,
                    category=normalized_category,
                )
            )
            if not result.hits and normalized_category is not None:
                logger.info(
                    "[tool] search_knowledge_base retry without category: query={!r} category={}",
                    normalized_query,
                    normalized_category,
                )
                result = await self._rag_svc.search(
                    SearchKnowledgeBaseQuery(
                        query=normalized_query,
                        top_k=top_k,
                        category=None,
                    )
                )
        except httpx.TimeoutException:
            return self._build_search_result_payload(
                query=normalized_query,
                hits=[],
                sources=[],
                note="知識庫檢索逾時，請稍後再試。",
                error="Knowledge-base search request timed out.",
                code="RAG_TIMEOUT",
            )
        except httpx.RequestError as exc:
            return self._build_search_result_payload(
                query=normalized_query,
                hits=[],
                sources=[],
                note="知識庫連線異常，請稍後再試。",
                error=f"Knowledge-base search network error: {exc}",
                code="RAG_NETWORK_ERROR",
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("[tool] search_knowledge_base unexpected error: {}", exc)
            return self._build_search_result_payload(
                query=normalized_query,
                hits=[],
                sources=[],
                note="知識庫暫時不可用，請稍後再試。",
                error=f"Knowledge-base search failed: {exc}",
                code="RAG_SEARCH_FAILED",
            )

        hits = [
            {
                "chunk_id": h.chunk_id,
                "document_id": h.document_id,
                "filename": h.filename,
                "title": h.title,
                "category": h.category,
                "heading": h.heading,
                "snippet": h.snippet,
                "source_url": h.source_url,
                "score": round(h.score, 4),
            }
            for h in result.hits
        ]
        # Deduplicate sources by document_id (fallback to filename for safety).
        seen: set[str] = set()
        sources: list[dict] = []
        for h in result.hits:
            dedupe_key = h.document_id or h.filename
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            sources.append(
                {
                    "document_id": h.document_id,
                    "filename": h.filename,
                    "title": h.title,
                    "category": h.category,
                    "source_url": h.source_url,
                }
            )
        if not hits:
            return self._build_search_result_payload(
                query=result.query,
                hits=[],
                sources=[],
                note="知識庫沒有命中相關內容。可改用 web_search 搜尋即時資訊。",
                error=None,
                code=None,
            )
        return self._build_search_result_payload(
            query=result.query,
            hits=hits,
            sources=sources,
            note=None,
            error=None,
            code=None,
        )

    async def _list_tools(
        self,
        user_id: str,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        """Return the list of all available tools with their descriptions."""
        return {
            "tools": _TOOL_METADATA,
        }

    async def _web_search(
        self,
        user_id: str,
        conversation_id: str | None = None,
        query: str = "",
        max_results: int = 5,
    ) -> dict[str, Any]:
        """Perform a web search via Tavily API and return structured results."""
        if not settings.tavily_api_key:
            logger.warning("[tool] web_search called but TAVILY_API_KEY is not configured")
            return {
                "error": "Web search is not configured on this server (missing TAVILY_API_KEY).",
                "code": "WEB_SEARCH_UNAVAILABLE",
            }
        max_results = max(1, min(int(max_results or 5), 10))
        payload = {
            "api_key": settings.tavily_api_key,
            "query": query,
            "search_depth": settings.tavily_search_depth,
            "max_results": max_results,
            "include_answer": False,
            "include_raw_content": False,
        }
        try:
            resp = await self._http.post(
                f"{settings.tavily_base_url}/search",
                json=payload,
                timeout=15.0,
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error("[tool] web_search HTTP error: {} {}", exc.response.status_code, exc.response.text[:200])
            return {"error": f"搜尋服務回傳錯誤 ({exc.response.status_code})"}
        except httpx.TimeoutException:
            logger.error("[tool] web_search request timed out")
            return {"error": "搜尋請求逾時，請稍後再試"}

        data = resp.json()
        raw_results = data.get("results", [])
        if not raw_results:
            return {
                "results": [],
                "note": "此次搜尋沒有找到相關結果，請嘗試調整查詢關鍵字。",
            }

        results = []
        for item in raw_results:
            url = item.get("url", "")
            # Validate URL is http/https to prevent unexpected schemes
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                continue
            results.append({
                "title": item.get("title", ""),
                "url": url,
                "excerpt": (item.get("content") or "")[:800],
                "score": item.get("score"),
            })

        logger.debug("[tool] web_search query={!r} found {} results", query, len(results))
        return {"results": results, "query": query}

    @staticmethod
    def _serialize_draft_progress(progress: ResumeDraftProgressDTO) -> dict[str, Any]:
        return {
            "draft_id": progress.draft_id,
            "conversation_id": progress.conversation_id,
            "current_step": progress.current_step,
            "status": progress.status,
            "missing_fields": list(progress.missing_fields),
            "collected": progress.collected,
            "next_question": progress.next_question,
            "ready_to_finalize": progress.ready_to_finalize,
            "loaded_resume_title": progress.loaded_resume_title,
        }

    @staticmethod
    def _build_search_result_payload(
        *,
        query: str,
        hits: list[dict[str, Any]],
        sources: list[dict[str, Any]],
        note: str | None,
        error: str | None,
        code: str | None,
    ) -> dict[str, Any]:
        return {
            "query": query,
            "hits": hits,
            "sources": sources,
            "note": note,
            "error": error,
            "code": code,
        }

    @staticmethod
    def _require_conversation_id(conversation_id: str | None) -> str:
        if not isinstance(conversation_id, str) or not conversation_id.strip():
            raise ValueError("This tool requires conversation_id context.")
        return conversation_id.strip()
