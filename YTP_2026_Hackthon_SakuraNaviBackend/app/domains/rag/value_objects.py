"""Value objects for the RAG knowledge-base domain."""
from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from typing import Literal

_EMBEDDING_DIM = 768


@dataclass(frozen=True)
class DocumentId:
    """RagDocument unique identifier."""
    value: uuid.UUID

    def __post_init__(self):
        if not isinstance(self.value, uuid.UUID):
            raise ValueError(f"Invalid DocumentId: {self.value}")

    @classmethod
    def from_str(cls, s: str) -> "DocumentId":
        return cls(uuid.UUID(s))


@dataclass(frozen=True)
class ChunkId:
    """RagChunk unique identifier."""
    value: uuid.UUID

    def __post_init__(self):
        if not isinstance(self.value, uuid.UUID):
            raise ValueError(f"Invalid ChunkId: {self.value}")

    @classmethod
    def from_str(cls, s: str) -> "ChunkId":
        return cls(uuid.UUID(s))


@dataclass(frozen=True)
class DocumentTag:
    """A tag for classifying RAG documents.

    Attributes:
        name: Internal identifier (e.g., "youth_subsidy").
        display_name: Chinese name for frontend display (e.g., "青年補助").
        namespace: Category group (e.g., "topic", "news", "target").
    """
    name: str
    display_name: str
    namespace: str

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("Tag name cannot be empty")
        if not self.display_name or not self.display_name.strip():
            raise ValueError("Tag display_name cannot be empty")
        if not self.namespace or not self.namespace.strip():
            raise ValueError("Tag namespace cannot be empty")

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "namespace": self.namespace,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DocumentTag":
        return cls(
            name=data["name"],
            display_name=data["display_name"],
            namespace=data["namespace"],
        )


@dataclass
class ClassificationRule:
    """A rule for classifying documents based on metadata or filename.

    Attributes:
        tag: The DocumentTag to assign if this rule matches.
        priority: Higher priority rules are checked first.
        source: Where to extract the classification from.
        metadata_key: Key to look up in document metadata (if source is "metadata").
        filename_pattern: Glob pattern to match against filename (if source is "filename").
    """
    tag: DocumentTag
    priority: int = 0
    source: "Literal['metadata', 'filename', 'default']" = "filename"
    metadata_key: Optional[str] = None
    filename_pattern: Optional[str] = None


@dataclass(frozen=True)
class EmbeddingVector:
    """Dense embedding vector — fixed local dimension (must match DB schema)."""
    values: tuple[float, ...]

    def __post_init__(self):
        if len(self.values) != _EMBEDDING_DIM:
            raise ValueError(
                f"EmbeddingVector must have {_EMBEDDING_DIM} dims, got {len(self.values)}"
            )

    def as_list(self) -> list[float]:
        return list(self.values)


@dataclass(frozen=True)
class ChunkContent:
    """Chunk text content."""
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Chunk content cannot be empty")
        if len(self.value) > 8000:
            raise ValueError("Chunk content cannot exceed 8000 characters")
