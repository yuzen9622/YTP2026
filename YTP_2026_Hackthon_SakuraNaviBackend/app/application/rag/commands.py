"""Command DTOs for RAG mutations."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class IngestDocumentCommand:
    """Ingest one markdown file into the knowledge base.

    Either pass `raw_content` directly (already-loaded text) or `file_path`
    (caller responsible for read access). `force=True` re-ingests even when
    content_hash is unchanged.
    """
    filename: str
    raw_content: str
    force: bool = False


@dataclass(frozen=True)
class DeleteDocumentCommand:
    document_id: str


@dataclass(frozen=True)
class IngestDirectoryCommand:
    directory: str
    force: bool = False
