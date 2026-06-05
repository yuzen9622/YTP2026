"""DTOs returned from the RAG application service."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class ChunkSummaryDTO:
    id: str
    chunk_index: int
    heading: Optional[str]
    content: str
    token_count: int


@dataclass(frozen=True)
class DocumentDTO:
    id: str
    filename: str
    title: str
    category: str
    tags: tuple[dict, ...] = field(default_factory=tuple)
    source_url: Optional[str] = None
    doc_metadata: Optional[dict] = None
    content_hash: str = ""
    chunk_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    raw_content: Optional[str] = None
    chunks: tuple[ChunkSummaryDTO, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class DocumentListDTO:
    items: tuple[DocumentDTO, ...]
    total: int
    limit: int
    offset: int


@dataclass(frozen=True)
class CategoryCountDTO:
    category: str
    count: int


@dataclass(frozen=True)
class CategoryListDTO:
    items: tuple[CategoryCountDTO, ...]


@dataclass(frozen=True)
class SearchHitDTO:
    chunk_id: str
    document_id: str
    filename: str
    title: str
    category: str
    heading: Optional[str]
    snippet: str
    source_url: Optional[str]
    score: float


@dataclass(frozen=True)
class SearchResultDTO:
    query: str
    hits: tuple[SearchHitDTO, ...]


@dataclass(frozen=True)
class IngestResultDTO:
    document: DocumentDTO
    was_ingested: bool  # False = unchanged, skipped


@dataclass(frozen=True)
class SubsidyRecommendationItemDTO:
    document_id: str
    source_link: Optional[str]
    title: str
    amount: Optional[str]
    department: Optional[str]


@dataclass(frozen=True)
class SubsidyRecommendationListDTO:
    items: tuple[SubsidyRecommendationItemDTO, ...]


@dataclass(frozen=True)
class AnnouncementItemDTO:
    document_id: str
    source_link: Optional[str]
    title: str
    summary: str
    published_at: Optional[str]


@dataclass(frozen=True)
class AnnouncementListDTO:
    items: tuple[AnnouncementItemDTO, ...]


@dataclass(frozen=True)
class NewsItemDTO:
    document_id: str
    source_link: Optional[str]
    date: Optional[str]
    title: str
    summary: str


@dataclass(frozen=True)
class NewsListDTO:
    items: tuple[NewsItemDTO, ...]
