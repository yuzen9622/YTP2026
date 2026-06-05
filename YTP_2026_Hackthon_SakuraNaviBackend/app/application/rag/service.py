"""RagApplicationService — orchestrates ingest & retrieval use cases."""
import asyncio
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional

from loguru import logger

from app.application.rag.commands import (
    DeleteDocumentCommand,
    IngestDocumentCommand,
)
from app.application.rag.dtos import (
    CategoryCountDTO,
    CategoryListDTO,
    ChunkSummaryDTO,
    DocumentDTO,
    DocumentListDTO,
    IngestResultDTO,
    SearchHitDTO,
    SearchResultDTO,
)
from app.application.rag.ports import EmbeddingClient, Tokenizer
from app.application.rag.queries import (
    GetDocumentQuery,
    ListDocumentsQuery,
    SearchKnowledgeBaseQuery,
)
from app.core.exceptions import ResourceNotFoundException
from app.domains.rag.entities import RagChunk, RagDocument
from app.domains.rag.exceptions import RagIngestionException
from app.domains.rag.repository import HybridHit, RagRepository
from app.domains.rag.value_objects import (
    ChunkId,
    DocumentId,
    DocumentTag,
    EmbeddingVector,
)
from app.infrastructure.rag.chunker import chunk_markdown
from app.infrastructure.rag.classifier import ClassificationResult, DocumentClassifier
from app.infrastructure.rag.parser import parse_markdown_metadata


_SNIPPET_MAX_CHARS = 300


class RagApplicationService:
    """Orchestrates RAG ingest + hybrid retrieval."""

    def __init__(
        self,
        rag_repo: RagRepository,
        embedding_client: EmbeddingClient,
        tokenizer: Tokenizer,
        classifier: DocumentClassifier,
    ) -> None:
        self._repo = rag_repo
        self._embed = embedding_client
        self._tokenizer = tokenizer
        self._classifier = classifier

    # ── Ingest ──────────────────────────────────────────────────────────────

    async def ingest_document(self, cmd: IngestDocumentCommand) -> IngestResultDTO:
        if not cmd.raw_content.strip():
            raise RagIngestionException(f"Empty content for {cmd.filename}")

        content_hash = hashlib.sha256(cmd.raw_content.encode("utf-8")).hexdigest()
        existing = await self._repo.find_by_filename(cmd.filename)

        if existing is not None and not cmd.force and existing.content_hash() == content_hash:
            logger.info("[rag] skip unchanged: filename={}", cmd.filename)
            return IngestResultDTO(
                document=self._document_to_dto(
                    existing,
                    include_chunks=False,
                    include_raw_content=False,
                ),
                was_ingested=False,
            )

        # Parse metadata + slice into chunks
        meta = parse_markdown_metadata(cmd.raw_content)
        classification = self._classifier.classify(cmd.filename, meta.extra)
        title = meta.title or cmd.filename.removesuffix(".md")
        raw_chunks = chunk_markdown(cmd.raw_content)
        if not raw_chunks:
            raise RagIngestionException(f"No chunks produced from {cmd.filename}")

        # Batch embed all chunk texts
        chunk_texts = [c.content for c in raw_chunks]
        embeddings = await self._embed.embed_documents(chunk_texts)
        if len(embeddings) != len(raw_chunks):
            raise RagIngestionException(
                f"Embedding count mismatch for {cmd.filename}: "
                f"chunks={len(raw_chunks)} embeddings={len(embeddings)}"
            )

        # Assemble aggregate
        now = datetime.now(tz=timezone.utc)
        document_id = existing.id() if existing else DocumentId(uuid.uuid4())
        domain_chunks: list[RagChunk] = []
        for idx, (raw, vec) in enumerate(zip(raw_chunks, embeddings)):
            tokens = self._tokenizer.tokenize(raw.content)
            domain_chunks.append(
                RagChunk(
                    id=ChunkId(uuid.uuid4()),
                    document_id=document_id,
                    chunk_index=idx,
                    heading=raw.heading,
                    content=raw.content,
                    token_count=raw.token_count,
                    embedding=EmbeddingVector(tuple(vec)),
                    tsv_tokens=tokens,
                )
            )

        document = RagDocument(
            id=document_id,
            filename=cmd.filename,
            title=title,
            primary_tag=classification.primary_tag,
            tags=classification.tags,
            source_url=meta.source_url,
            raw_content=cmd.raw_content,
            doc_metadata=meta.extra or None,
            content_hash=content_hash,
            chunks=tuple(domain_chunks),
            created_at=existing.created_at() if existing else now,
            updated_at=now,
        )

        await self._repo.save_document(document)
        logger.info(
            "[rag] ingested filename={} chunks={} category={}",
            cmd.filename, len(domain_chunks), classification.primary_tag.name,
        )
        return IngestResultDTO(
            document=self._document_to_dto(
                document,
                include_chunks=False,
                include_raw_content=False,
            ),
            was_ingested=True,
        )

    async def delete_document(self, cmd: DeleteDocumentCommand) -> None:
        deleted = await self._repo.delete_by_id(DocumentId.from_str(cmd.document_id))
        if not deleted:
            raise ResourceNotFoundException(
                f"RAG document '{cmd.document_id}' not found.",
                code="RAG_DOCUMENT_NOT_FOUND",
            )

    # ── Read ────────────────────────────────────────────────────────────────

    async def list_documents(self, query: ListDocumentsQuery) -> DocumentListDTO:
        category = self._parse_category(query.category)
        documents, total = await self._repo.list_documents(
            category=category, limit=query.limit, offset=query.offset
        )
        return DocumentListDTO(
            items=tuple(
                self._document_to_dto(
                    d,
                    include_chunks=False,
                    include_raw_content=False,
                )
                for d in documents
            ),
            total=total,
            limit=query.limit,
            offset=query.offset,
        )

    async def list_categories(self) -> CategoryListDTO:
        counts = await self._repo.count_documents_by_category()
        count_map = {cat: count for cat, count in counts if count > 0}
        return CategoryListDTO(
            items=tuple(
                CategoryCountDTO(category=cat, count=count_map[cat])
                for cat in count_map
            )
        )

    async def get_document(self, query: GetDocumentQuery) -> DocumentDTO:
        document = await self._repo.find_by_id(DocumentId.from_str(query.document_id))
        if document is None:
            raise ResourceNotFoundException(
                f"RAG document '{query.document_id}' not found.",
                code="RAG_DOCUMENT_NOT_FOUND",
            )
        return self._document_to_dto(
            document,
            include_chunks=query.include_chunks,
            include_raw_content=query.include_raw_content,
        )

    async def search(self, query: SearchKnowledgeBaseQuery) -> SearchResultDTO:
        if not query.query or not query.query.strip():
            return SearchResultDTO(query=query.query, hits=())
        category = self._parse_category(query.category)
        top_k = max(1, min(int(query.top_k or 5), 20))

        # Run tokenize + embed in parallel — embed is network-bound, tokenize is CPU.
        async def _tok() -> str:
            # Run jieba in a thread to avoid blocking the event loop on long queries.
            return await asyncio.to_thread(self._tokenizer.tokenize, query.query)

        tokens, vector = await asyncio.gather(
            _tok(),
            self._embed.embed_query(query.query),
        )

        hits = await self._repo.hybrid_search(
            query_vector=vector,
            query_tokens=tokens,
            top_k=top_k,
            category=category,
        )
        return SearchResultDTO(
            query=query.query,
            hits=tuple(self._hit_to_dto(h) for h in hits),
        )

    # ── Helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_category(raw: Optional[str]) -> Optional[str]:
        if raw is None or raw == "":
            return None
        return raw

    @staticmethod
    def _document_to_dto(
        document: RagDocument,
        *,
        include_chunks: bool,
        include_raw_content: bool,
    ) -> DocumentDTO:
        chunk_dtos: tuple[ChunkSummaryDTO, ...] = ()
        if include_chunks:
            chunk_dtos = tuple(
                ChunkSummaryDTO(
                    id=str(c.id().value),
                    chunk_index=c.chunk_index(),
                    heading=c.heading(),
                    content=c.content(),
                    token_count=c.token_count(),
                )
                for c in document.chunks()
            )
        return DocumentDTO(
            id=str(document.id().value),
            filename=document.filename(),
            title=document.title(),
            category=document.category(),
            tags=tuple(t.to_dict() for t in document.tags()),
            source_url=document.source_url(),
            doc_metadata=document.doc_metadata(),
            content_hash=document.content_hash(),
            chunk_count=len(document.chunks()),
            created_at=document.created_at(),
            updated_at=document.updated_at(),
            raw_content=document.raw_content() if include_raw_content else None,
            chunks=chunk_dtos,
        )

    @staticmethod
    def _hit_to_dto(hit: HybridHit) -> SearchHitDTO:
        content = hit.chunk.content()
        snippet = content if len(content) <= _SNIPPET_MAX_CHARS else content[:_SNIPPET_MAX_CHARS] + "…"
        return SearchHitDTO(
            chunk_id=str(hit.chunk.id().value),
            document_id=str(hit.chunk.document_id().value),
            filename=hit.document_filename,
            title=hit.document_title,
            category=hit.document_category.name,
            heading=hit.chunk.heading(),
            snippet=snippet,
            source_url=hit.document_source_url,
            score=hit.score,
        )
