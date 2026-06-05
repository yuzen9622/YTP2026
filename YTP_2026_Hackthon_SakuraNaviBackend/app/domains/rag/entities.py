"""RAG aggregate root and chunk entities."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.domains.rag.value_objects import DocumentTag

from app.domains.rag.value_objects import (
    ChunkContent,
    ChunkId,
    DocumentId,
    EmbeddingVector,
)


@dataclass
class RagChunk:
    """A single retrievable text fragment within a RagDocument.

    Chunks are owned by their parent document. External code MUST NOT
    construct chunks directly outside of RagDocument.replace_chunks().
    """
    _id: ChunkId
    _document_id: DocumentId
    _chunk_index: int
    _heading: Optional[str]
    _content: ChunkContent
    _token_count: int
    _embedding: EmbeddingVector
    _tsv_tokens: str  # whitespace-joined tokens, fed into PG to_tsvector

    def __init__(
        self,
        id: ChunkId,
        document_id: DocumentId,
        chunk_index: int,
        heading: Optional[str],
        content: str,
        token_count: int,
        embedding: EmbeddingVector,
        tsv_tokens: str,
    ) -> None:
        if chunk_index < 0:
            raise ValueError("chunk_index must be non-negative")
        if token_count < 0:
            raise ValueError("token_count must be non-negative")
        if heading is not None and len(heading) > 300:
            raise ValueError("heading cannot exceed 300 characters")
        self._id = id
        self._document_id = document_id
        self._chunk_index = chunk_index
        self._heading = heading
        self._content = ChunkContent(content)
        self._token_count = token_count
        self._embedding = embedding
        self._tsv_tokens = tsv_tokens or ""

    def id(self) -> ChunkId:
        return self._id

    def document_id(self) -> DocumentId:
        return self._document_id

    def chunk_index(self) -> int:
        return self._chunk_index

    def heading(self) -> Optional[str]:
        return self._heading

    def content(self) -> str:
        return self._content.value

    def token_count(self) -> int:
        return self._token_count

    def embedding(self) -> EmbeddingVector:
        return self._embedding

    def tsv_tokens(self) -> str:
        return self._tsv_tokens


@dataclass
class RagDocument:
    """RagDocument aggregate root.

    Represents one source markdown file in the knowledge base. Owns its
    chunks; chunks are replaced atomically via replace_chunks() to keep
    chunk_index contiguous and prevent orphaned vectors.
    """
    _id: DocumentId
    _filename: str
    _title: str
    _primary_tag: "DocumentTag"
    _tags: frozenset["DocumentTag"]
    _source_url: Optional[str]
    _raw_content: str
    _doc_metadata: Optional[dict]
    _content_hash: str
    _chunks: tuple[RagChunk, ...]
    _created_at: datetime
    _updated_at: datetime

    def __init__(
        self,
        id: DocumentId,
        filename: str,
        title: str,
        primary_tag: "DocumentTag",
        tags: frozenset["DocumentTag"],
        source_url: Optional[str],
        raw_content: str,
        doc_metadata: Optional[dict],
        content_hash: str,
        chunks: tuple[RagChunk, ...] = (),
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        if not filename or len(filename) > 200:
            raise ValueError("filename must be 1..200 chars")
        if not title or len(title) > 200:
            raise ValueError("title must be 1..200 chars")
        if not primary_tag:
            raise ValueError("primary_tag is required")
        if not tags:
            raise ValueError("tags cannot be empty")
        if source_url is not None and len(source_url) > 500:
            raise ValueError("source_url cannot exceed 500 characters")
        if len(content_hash) != 64:
            raise ValueError("content_hash must be a 64-char sha256 hex digest")
        now = datetime.now(tz=timezone.utc)
        self._id = id
        self._filename = filename
        self._title = title
        self._primary_tag = primary_tag
        self._tags = tags
        self._source_url = source_url
        self._raw_content = raw_content
        self._doc_metadata = doc_metadata
        self._content_hash = content_hash
        self._chunks = chunks
        self._created_at = created_at or now
        self._updated_at = updated_at or self._created_at

    def id(self) -> DocumentId:
        return self._id

    def filename(self) -> str:
        return self._filename

    def title(self) -> str:
        return self._title

    def category(self) -> str:
        """Returns primary tag name for backwards compatibility."""
        return self._primary_tag.name

    def primary_tag(self) -> "DocumentTag":
        return self._primary_tag

    def tags(self) -> frozenset["DocumentTag"]:
        return self._tags

    def source_url(self) -> Optional[str]:
        return self._source_url

    def raw_content(self) -> str:
        return self._raw_content

    def doc_metadata(self) -> Optional[dict]:
        return self._doc_metadata

    def content_hash(self) -> str:
        return self._content_hash

    def chunks(self) -> tuple[RagChunk, ...]:
        return self._chunks

    def created_at(self) -> datetime:
        return self._created_at

    def updated_at(self) -> datetime:
        return self._updated_at

    def replace_chunks(self, new_chunks: tuple[RagChunk, ...], now: datetime) -> None:
        """Replace all chunks atomically; ensures chunk_index forms 0..N-1."""
        for expected_index, chunk in enumerate(new_chunks):
            if chunk.chunk_index() != expected_index:
                raise ValueError(
                    f"chunk_index mismatch: expected {expected_index}, got {chunk.chunk_index()}"
                )
            if chunk.document_id().value != self._id.value:
                raise ValueError("Chunk does not belong to this document")
        self._chunks = new_chunks
        self._updated_at = now
