"""Pydantic schemas for RAG knowledge-base endpoints."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ChunkSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    chunk_index: int
    heading: Optional[str] = None
    content: str
    token_count: int


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    title: str
    category: str
    source_url: Optional[str] = None
    doc_metadata: Optional[dict] = None
    content_hash: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime
    raw_content: Optional[str] = None
    chunks: list[ChunkSummary] = Field(default_factory=list)


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    limit: int
    offset: int


class CategoryCountItem(BaseModel):
    category: str
    count: int = Field(..., ge=1)


class CategoryListResponse(BaseModel):
    items: list[CategoryCountItem]


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="檢索字串")
    top_k: int = Field(5, ge=1, le=20, description="回傳片段數，1–20")
    category: Optional[str] = Field(
        None,
        description=(
            "可選分類過濾：general / youth_subsidy / entrepreneurship / "
            "international / latest_news / policy_news"
        ),
    )


class SearchHit(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    title: str
    category: str
    heading: Optional[str] = None
    snippet: str
    source_url: Optional[str] = None
    score: float


class SearchResponse(BaseModel):
    query: str
    hits: list[SearchHit]


class SubsidyRecommendationsRequest(BaseModel):
    resume_id: Optional[str] = Field(None, description="指定履歷 ID；未提供時使用主要履歷")
    query: Optional[str] = Field(None, max_length=500, description="前端額外檢索字串")
    limit: int = Field(5, ge=1, le=20, description="回傳筆數，1–20")


class SubsidyRecommendationItem(BaseModel):
    document_id: str
    source_link: Optional[str] = None
    title: str
    amount: Optional[str] = None
    department: Optional[str] = None


class SubsidyRecommendationsResponse(BaseModel):
    items: list[SubsidyRecommendationItem]


class AnnouncementItem(BaseModel):
    document_id: str
    source_link: Optional[str] = None
    title: str
    summary: str
    published_at: Optional[str] = None


class AnnouncementsResponse(BaseModel):
    items: list[AnnouncementItem]


class NewsItem(BaseModel):
    document_id: str
    source_link: Optional[str] = None
    date: Optional[str] = None
    title: str
    summary: str


class NewsResponse(BaseModel):
    items: list[NewsItem]


class IngestResponse(BaseModel):
    ingested: int
    skipped: int
    failed: list[str]


class DeleteResponse(BaseModel):
    id: str
    deleted: bool
