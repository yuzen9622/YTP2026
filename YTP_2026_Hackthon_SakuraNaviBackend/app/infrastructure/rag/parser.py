"""Markdown header / metadata parser for the rag_docs corpus."""
import re
from dataclasses import dataclass, field
from typing import Optional


_TITLE_RE = re.compile(r"^\s*#\s+(.+?)\s*$", re.MULTILINE)
# Metadata lines like:
#   > **資料來源**：https://...
#   **發布日期：** 2026-03-30
_META_RE = re.compile(
    r"^\s*>?\s*\*\*([^*：:]+?)\s*[：:]?\*\*\s*[：:]?\s*(.+?)\s*$",
    re.MULTILINE,
)
_URL_RE = re.compile(r"https?://[^\s)]+")

_SOURCE_KEYS = {"資料來源", "來源連結", "Source", "source"}
_UPDATE_DATE_KEYS = {"頁面更新日期", "更新日期", "Last Updated"}
_PUBLISHED_DATE_KEYS = {"發布日期", "公告日期", "Publish Date", "Published At"}
_FETCHED_AT_KEYS = {"擷取日期", "Fetched At"}
_DEPARTMENT_KEYS = {"發布單位", "局處", "承辦單位", "Department"}


@dataclass(frozen=True)
class ParsedMetadata:
    title: Optional[str]
    source_url: Optional[str]
    update_date: Optional[str]
    fetched_at: Optional[str]
    extra: dict = field(default_factory=dict)


def parse_markdown_metadata(text: str) -> ParsedMetadata:
    """Extract title, source URL, and date metadata from the document header.

    Stops scanning at the first H2 (`##`) since metadata always sits in the
    blockquote between H1 and the first section.
    """
    title_match = _TITLE_RE.search(text)
    title = title_match.group(1).strip() if title_match else None

    head = text.split("\n## ", 1)[0]

    source_url: Optional[str] = None
    update_date: Optional[str] = None
    fetched_at: Optional[str] = None
    extra: dict = {}

    for m in _META_RE.finditer(head):
        key = m.group(1).strip()
        value = m.group(2).strip()
        if key in _SOURCE_KEYS:
            url_match = _URL_RE.search(value)
            source_url = url_match.group(0) if url_match else value
        elif key in _UPDATE_DATE_KEYS:
            update_date = value
        elif key in _PUBLISHED_DATE_KEYS:
            extra["published_date"] = value
        elif key in _FETCHED_AT_KEYS:
            fetched_at = value
        elif key in _DEPARTMENT_KEYS:
            extra["department"] = value
        else:
            extra[key] = value

    if source_url is None:
        url_match = _URL_RE.search(head)
        if url_match:
            source_url = url_match.group(0)

    if update_date:
        extra.setdefault("update_date", update_date)
    if fetched_at:
        extra.setdefault("fetched_at", fetched_at)

    return ParsedMetadata(
        title=title,
        source_url=source_url,
        update_date=update_date,
        fetched_at=fetched_at,
        extra=extra,
    )
