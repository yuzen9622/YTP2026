"""Frontend-oriented RAG read use cases."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Optional

from app.application.rag.dtos import (
    AnnouncementItemDTO,
    AnnouncementListDTO,
    DocumentDTO,
    NewsItemDTO,
    NewsListDTO,
    SearchHitDTO,
    SubsidyRecommendationItemDTO,
    SubsidyRecommendationListDTO,
)
from app.application.rag.queries import (
    GetDocumentQuery,
    ListDocumentsQuery,
    SearchKnowledgeBaseQuery,
)
from app.application.rag.service import RagApplicationService
from app.application.resume.dtos import ResumeDTO
from app.application.resume.service import ResumeApplicationService


_CATEGORY_YOUTH_SUBSIDY = "youth_subsidy"
_CATEGORY_LATEST_NEWS = "latest_news"
_CATEGORY_POLICY_NEWS = "policy_news"

_DEFAULT_LIMIT = 5
_MAX_LIMIT = 20
_LIST_POOL_LIMIT = 100
_SUMMARY_MAX_CHARS = 50
_QUERY_MAX_CHARS = 500

_CHANNEL_PREFIXES = {"最新公告", "新聞資訊", "政策新聞"}
_CONTACT_HEADING_KEYWORDS = ("聯絡", "新聞聯絡", "更多資訊", "相關附檔", "相關附件")
_AMOUNT_HEADING_KEYWORDS = (
    "貸款額度",
    "補助金額",
    "補助幅度",
    "補助內容",
    "額度上限",
)
_BAD_AMOUNT_CONTEXT_KEYWORDS = ("罰鍰", "處罰", "裁罰")

_MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_MARKDOWN_DECORATION_RE = re.compile(r"[*_`>#]")
_HEADING_RE = re.compile(r"^#{2,6}\s+(.+?)\s*$", re.MULTILINE)
_MONEY_RE = re.compile(
    r"(?:(?:最高|上限|每月|每案|基本額度|另加最高|補助|貸款)?\s*)"
    r"(?:新臺幣\s*)?[\d,]+(?:\.\d+)?\s*(?:萬)?元"
)
_TEXT_AMOUNT_RE = re.compile(r"(?:全額補助|半額補助|不予補助)")
_DEPARTMENT_STRONG_RE = re.compile(r"\*\*(臺北市政府[^*\n]{0,30}局)\*\*")
_DEPARTMENT_RE = re.compile(
    r"(臺北市政府[\u4e00-\u9fff]{1,30}局|青年局[\u4e00-\u9fff]{0,8}科?|青年局)"
)


class RagFrontendApplicationService:
    """Builds compact, deterministic RAG payloads for frontend screens."""

    def __init__(
        self,
        rag_service: RagApplicationService,
        resume_service: ResumeApplicationService,
    ) -> None:
        self._rag = rag_service
        self._resumes = resume_service

    async def recommend_subsidies(
        self,
        *,
        user_id: str,
        resume_id: Optional[str],
        query: Optional[str],
        limit: int = _DEFAULT_LIMIT,
    ) -> SubsidyRecommendationListDTO:
        safe_limit = _clamp_limit(limit)
        resume = await self._select_resume(user_id=user_id, resume_id=resume_id)
        mixed_query = _build_resume_query(resume=resume, user_query=query)
        if not mixed_query:
            return SubsidyRecommendationListDTO(items=())

        search_result = await self._rag.search(
            SearchKnowledgeBaseQuery(
                query=mixed_query,
                top_k=min(safe_limit * 3, _MAX_LIMIT),
                category=_CATEGORY_YOUTH_SUBSIDY,
            )
        )
        items: list[SubsidyRecommendationItemDTO] = []
        seen: set[str] = set()
        for hit in search_result.hits:
            if hit.document_id in seen:
                continue
            seen.add(hit.document_id)
            document = await self._get_full_document(hit.document_id)
            items.append(
                SubsidyRecommendationItemDTO(
                    document_id=document.id,
                    source_link=document.source_url,
                    title=_normalize_title(document.title),
                    amount=_extract_amount(hit.snippet, document.raw_content or ""),
                    department=_extract_department(document),
                )
            )
            if len(items) >= safe_limit:
                break
        return SubsidyRecommendationListDTO(items=tuple(items))

    async def list_announcements(
        self,
        *,
        query: Optional[str],
        limit: int = _DEFAULT_LIMIT,
    ) -> AnnouncementListDTO:
        documents = await self._load_news_documents(
            category=_CATEGORY_LATEST_NEWS,
            query=query,
            limit=limit,
        )
        return AnnouncementListDTO(
            items=tuple(
                AnnouncementItemDTO(
                    document_id=doc.id,
                    source_link=doc.source_url,
                    title=_normalize_title(doc.title),
                    summary=_extract_summary(doc.raw_content or ""),
                    published_at=_extract_date(doc),
                )
                for doc in documents
            )
        )

    async def list_news(
        self,
        *,
        query: Optional[str],
        limit: int = _DEFAULT_LIMIT,
    ) -> NewsListDTO:
        documents = await self._load_news_documents(
            category=_CATEGORY_POLICY_NEWS,
            query=query,
            limit=limit,
        )
        return NewsListDTO(
            items=tuple(
                NewsItemDTO(
                    document_id=doc.id,
                    source_link=doc.source_url,
                    date=_extract_date(doc),
                    title=_normalize_title(doc.title),
                    summary=_extract_summary(doc.raw_content or ""),
                )
                for doc in documents
            )
        )

    async def _select_resume(
        self,
        *,
        user_id: str,
        resume_id: Optional[str],
    ) -> Optional[ResumeDTO]:
        if resume_id:
            return await self._resumes.get_resume(resume_id, user_id)

        resumes = await self._resumes.get_resumes(user_id)
        if not resumes:
            return None
        for resume in resumes:
            if resume.is_primary:
                return resume
        return resumes[0]

    async def _load_news_documents(
        self,
        *,
        category: str,
        query: Optional[str],
        limit: int,
    ) -> list[DocumentDTO]:
        safe_limit = _clamp_limit(limit)
        normalized_query = _normalize_segment(query)
        if normalized_query:
            search_result = await self._rag.search(
                SearchKnowledgeBaseQuery(
                    query=normalized_query,
                    top_k=min(safe_limit * 3, _MAX_LIMIT),
                    category=category,
                )
            )
            documents: list[DocumentDTO] = []
            seen: set[str] = set()
            for hit in search_result.hits:
                if hit.document_id in seen:
                    continue
                seen.add(hit.document_id)
                documents.append(await self._get_full_document(hit.document_id))
                if len(documents) >= safe_limit:
                    break
            return documents

        listed = await self._rag.list_documents(
            ListDocumentsQuery(category=category, limit=_LIST_POOL_LIMIT, offset=0)
        )
        documents = [await self._get_full_document(doc.id) for doc in listed.items]
        documents.sort(key=_date_sort_key, reverse=True)
        return documents[:safe_limit]

    async def _get_full_document(self, document_id: str) -> DocumentDTO:
        return await self._rag.get_document(
            GetDocumentQuery(
                document_id=document_id,
                include_chunks=False,
                include_raw_content=True,
            )
        )


def _clamp_limit(limit: int) -> int:
    return max(1, min(int(limit or _DEFAULT_LIMIT), _MAX_LIMIT))


def _normalize_segment(raw: Any) -> str:
    if raw is None:
        return ""
    return " ".join(str(raw).split()).strip()


def _build_resume_query(
    *,
    resume: Optional[ResumeDTO],
    user_query: Optional[str],
) -> str:
    segments: list[str] = []

    def append(value: Any) -> None:
        normalized = _normalize_segment(value)
        if normalized:
            segments.append(normalized)

    append(user_query)
    if resume is not None:
        append(resume.title)
        append(resume.summary)
        skill_names = [
            _normalize_segment(skill.get("name"))
            for skill in resume.skills
            if isinstance(skill, dict) and _normalize_segment(skill.get("name"))
        ]
        append(" ".join(skill_names[:8]))

        positions = [
            _normalize_segment(exp.get("position"))
            for exp in resume.work_experiences
            if isinstance(exp, dict) and _normalize_segment(exp.get("position"))
        ]
        append(" ".join(positions[:5]))

        if isinstance(resume.work_time_range, dict):
            append(resume.work_time_range.get("work_time_type"))

    deduped: list[str] = []
    seen: set[str] = set()
    for segment in segments:
        key = segment.casefold()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(segment)

    mixed = " | ".join(deduped)
    if len(mixed) > _QUERY_MAX_CHARS:
        mixed = mixed[:_QUERY_MAX_CHARS].rstrip()
    return mixed


def _normalize_title(title: str) -> str:
    normalized = _normalize_segment(title)
    if "｜" not in normalized:
        return normalized
    prefix, rest = normalized.split("｜", 1)
    if prefix.strip() in _CHANNEL_PREFIXES and rest.strip():
        return rest.strip()
    return normalized


def _extract_date(document: DocumentDTO) -> Optional[str]:
    metadata = document.doc_metadata or {}
    for key in ("published_date", "發布日期", "date", "update_date", "更新日期"):
        value = _normalize_segment(metadata.get(key))
        if value:
            return value
    raw = document.raw_content or ""
    match = re.search(r"\*\*發布日期[：:]?\*\*\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", raw)
    if match:
        return match.group(1)
    return None


def _date_sort_key(document: DocumentDTO) -> datetime:
    raw_date = _extract_date(document) or ""
    try:
        return datetime.fromisoformat(raw_date)
    except ValueError:
        return datetime.min


def _extract_summary(raw_content: str) -> str:
    if not raw_content:
        return ""

    fallback_blocks: list[str] = []
    for heading, body in _iter_sections(raw_content):
        if any(keyword in heading for keyword in _CONTACT_HEADING_KEYWORDS):
            continue
        for block in re.split(r"\n\s*\n", body):
            cleaned = _clean_summary_block(block)
            if not cleaned:
                continue
            if _is_table_or_metadata_block(block):
                continue
            if block.lstrip().startswith(("-", "*", "1.")):
                fallback_blocks.append(cleaned)
                continue
            return _truncate(cleaned, _SUMMARY_MAX_CHARS)

    if fallback_blocks:
        return _truncate(fallback_blocks[0], _SUMMARY_MAX_CHARS)
    return ""


def _extract_amount(snippet: str, raw_content: str) -> Optional[str]:
    for text in (snippet, raw_content):
        for candidate in _amount_candidates(text):
            amount = _find_amount(candidate)
            if amount:
                return amount
    return None


def _amount_candidates(text: str) -> list[str]:
    if not text:
        return []
    out: list[str] = []
    cleaned = _clean_markdown(text)
    if not any(keyword in cleaned for keyword in _BAD_AMOUNT_CONTEXT_KEYWORDS):
        out.append(cleaned)

    for heading, body in _iter_sections(text):
        if not any(keyword in heading for keyword in _AMOUNT_HEADING_KEYWORDS):
            continue
        candidate = _clean_markdown(body)
        if any(keyword in candidate for keyword in _BAD_AMOUNT_CONTEXT_KEYWORDS):
            continue
        out.append(candidate)
    return out


def _find_amount(text: str) -> Optional[str]:
    text_amount = _TEXT_AMOUNT_RE.search(text)
    money_amount = _MONEY_RE.search(text)
    if text_amount and (
        money_amount is None or text_amount.start() < money_amount.start()
    ):
        return _normalize_segment(text_amount.group(0))
    if money_amount:
        return _normalize_segment(money_amount.group(0))
    return None


def _extract_department(document: DocumentDTO) -> Optional[str]:
    metadata = document.doc_metadata or {}
    for key in ("department", "發布單位", "agency", "局處"):
        value = _normalize_segment(metadata.get(key))
        if value:
            return value

    raw = document.raw_content or ""
    strong_match = _DEPARTMENT_STRONG_RE.search(raw)
    if strong_match:
        return _normalize_segment(strong_match.group(1))
    match = _DEPARTMENT_RE.search(raw)
    if match:
        return _normalize_segment(match.group(1))
    return None


def _iter_sections(raw_content: str) -> list[tuple[str, str]]:
    matches = list(_HEADING_RE.finditer(raw_content))
    sections: list[tuple[str, str]] = []
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(raw_content)
        sections.append(
            (_clean_markdown(match.group(1)), raw_content[start:end].strip())
        )
    if sections:
        return sections

    body = raw_content.split("\n\n", 1)[1] if "\n\n" in raw_content else raw_content
    return [("", body)]


def _clean_summary_block(block: str) -> str:
    lines = []
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped or stripped == "---":
            continue
        if stripped.startswith(">"):
            continue
        if stripped.startswith("#"):
            continue
        lines.append(stripped)
    return _clean_markdown(" ".join(lines))


def _is_table_or_metadata_block(block: str) -> bool:
    meaningful = [line.strip() for line in block.splitlines() if line.strip()]
    if not meaningful:
        return True
    if all(line.startswith("|") for line in meaningful):
        return True
    if all(line.startswith(">") for line in meaningful):
        return True
    return False


def _clean_markdown(text: str) -> str:
    text = _MARKDOWN_LINK_RE.sub(r"\1", text)
    text = _MARKDOWN_DECORATION_RE.sub("", text)
    text = text.replace("👉", " ")
    return _normalize_segment(text)


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars].rstrip()}..."
