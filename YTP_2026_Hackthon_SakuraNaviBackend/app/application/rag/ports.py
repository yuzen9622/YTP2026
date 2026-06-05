"""Ports (Protocols) for RAG: embedding & tokenization adapters."""
from typing import Protocol


class EmbeddingClient(Protocol):
    """Generates dense embedding vectors for text."""

    @property
    def dimension(self) -> int:
        ...

    async def embed_query(self, text: str) -> list[float]:
        """Embed a single query string."""
        ...

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed many document chunks. Implementation MAY batch internally."""
        ...

    async def close(self) -> None:
        ...


class Tokenizer(Protocol):
    """Splits Chinese (and mixed) text into whitespace-joined tokens for tsvector."""

    def tokenize(self, text: str) -> str:
        """Return whitespace-separated tokens. May return empty string."""
        ...
