"""Query DTOs for RAG read-side operations."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SearchKnowledgeBaseQuery:
    query: str
    top_k: int = 5
    category: Optional[str] = None  # raw enum value, e.g. "創業諮詢"


@dataclass(frozen=True)
class ListDocumentsQuery:
    category: Optional[str] = None
    limit: int = 50
    offset: int = 0


@dataclass(frozen=True)
class GetDocumentQuery:
    document_id: str
    include_chunks: bool = True
    include_raw_content: bool = True
