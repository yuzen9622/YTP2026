"""RagRepository protocol — interface for RAG document & chunk persistence."""
from dataclasses import dataclass
from typing import Optional, Protocol

from app.domains.rag.entities import RagChunk, RagDocument
from app.domains.rag.value_objects import DocumentId, DocumentTag


@dataclass(frozen=True)
class HybridHit:
    """A hybrid-search result row, returned from the repository."""
    chunk: RagChunk
    document_filename: str
    document_title: str
    document_category: DocumentTag
    document_source_url: Optional[str]
    score: float


class RagRepository(Protocol):
    """Persistence contract for the RAG knowledge base."""

    async def save_document(self, document: RagDocument) -> None:
        """Upsert a document and atomically replace its chunks."""
        ...

    async def find_by_id(self, id: DocumentId) -> Optional[RagDocument]:
        ...

    async def find_by_filename(self, filename: str) -> Optional[RagDocument]:
        ...

    async def list_documents(
        self,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[RagDocument], int]:
        """Return (documents, total_count). Documents do NOT include chunks."""
        ...

    async def count_documents_by_category(self) -> list[tuple[str, int]]:
        """Return document counts grouped by category tag name."""
        ...

    async def delete_by_id(self, id: DocumentId) -> bool:
        """Delete a document and its chunks. Returns True if a row was deleted."""
        ...

    async def hybrid_search(
        self,
        query_vector: list[float],
        query_tokens: str,
        top_k: int,
        category: Optional[str] = None,
    ) -> list[HybridHit]:
        """Hybrid retrieval (vector + keyword) fused with RRF.

        If query_tokens is empty, falls back to pure vector retrieval.
        """
        ...
