"""SQLAlchemy implementation of RagRepository — ARRAY float[] + tsvector hybrid search."""
import uuid
from typing import TYPE_CHECKING, Optional

import numpy as np
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.rag.entities import RagChunk, RagDocument
from app.domains.rag.repository import HybridHit
from app.domains.rag.value_objects import (
    ChunkId,
    DocumentId,
    DocumentTag,
    EmbeddingVector,
)
from app.infrastructure.db.models.rag import RagChunkModel, RagDocumentModel

if TYPE_CHECKING:
    from app.infrastructure.rag.config_loader import TagRegistry


_RRF_K = 60  # Reciprocal Rank Fusion constant
_POOL_MULTIPLIER = 4  # candidate pool = top_k * multiplier


# Global tag registry for reconstructing DocumentTag from stored name
_tag_registry: Optional["TagRegistry"] = None

# Mapping from old category values to new tag names for backwards compatibility
_OLD_CATEGORY_TO_TAG = {
    "創業諮詢": "entrepreneurship",
    "國際交流": "international",
    "general": "general",
}


def _get_tag_registry() -> "TagRegistry":
    global _tag_registry
    if _tag_registry is None:
        from app.infrastructure.rag.config_loader import load_config
        _tag_registry = load_config().tag_registry
    return _tag_registry


def _reconstruct_tags(tags_data: Optional[list]) -> tuple[DocumentTag, ...]:
    """Reconstruct tuple of DocumentTag from stored JSON data."""
    if not tags_data:
        return ()
    registry = _get_tag_registry()
    result = []
    for tag_dict in tags_data:
        tag = registry.get(tag_dict.get("name", ""))
        if tag:
            result.append(tag)
    return tuple(result)


class RagRepositoryImpl:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Mutations ───────────────────────────────────────────────────────────

    async def save_document(self, document: RagDocument) -> None:
        tags_data = None
        if document.tags():
            tags_data = [t.to_dict() for t in document.tags()]

        existing = (
            await self._session.execute(
                select(RagDocumentModel).where(RagDocumentModel.id == document.id().value)
            )
        ).scalar_one_or_none()

        if existing is None:
            self._session.add(
                RagDocumentModel(
                    id=document.id().value,
                    filename=document.filename(),
                    title=document.title(),
                    category=document.category(),
                    tags=tags_data,
                    source_url=document.source_url(),
                    raw_content=document.raw_content(),
                    doc_metadata=document.doc_metadata(),
                    content_hash=document.content_hash(),
                    created_at=document.created_at(),
                    updated_at=document.updated_at(),
                )
            )
        else:
            await self._session.execute(
                update(RagDocumentModel)
                .where(RagDocumentModel.id == document.id().value)
                .values(
                    filename=document.filename(),
                    title=document.title(),
                    category=document.category(),
                    tags=tags_data,
                    source_url=document.source_url(),
                    raw_content=document.raw_content(),
                    doc_metadata=document.doc_metadata(),
                    content_hash=document.content_hash(),
                    updated_at=document.updated_at(),
                )
            )
            await self._session.execute(
                delete(RagChunkModel).where(
                    RagChunkModel.document_id == document.id().value
                )
            )

        # Flush so the document row is visible to FK constraints on the chunk inserts.
        await self._session.flush()

        for chunk in document.chunks():
            self._session.add(
                RagChunkModel(
                    id=chunk.id().value,
                    document_id=document.id().value,
                    chunk_index=chunk.chunk_index(),
                    heading=chunk.heading(),
                    content=chunk.content(),
                    token_count=chunk.token_count(),
                    embedding=chunk.embedding().as_list(),
                    tsv_content=func.to_tsvector("simple", chunk.tsv_tokens()),
                )
            )

    async def delete_by_id(self, id: DocumentId) -> bool:
        result = await self._session.execute(
            delete(RagDocumentModel).where(RagDocumentModel.id == id.value)
        )
        return (result.rowcount or 0) > 0

    # ── Queries ─────────────────────────────────────────────────────────────

    async def find_by_id(self, id: DocumentId) -> Optional[RagDocument]:
        doc_row = (
            await self._session.execute(
                select(RagDocumentModel).where(RagDocumentModel.id == id.value)
            )
        ).scalar_one_or_none()
        if doc_row is None:
            return None
        chunk_rows = (
            await self._session.execute(
                select(RagChunkModel)
                .where(RagChunkModel.document_id == id.value)
                .order_by(RagChunkModel.chunk_index.asc())
            )
        ).scalars().all()
        return self._reconstruct(doc_row, chunk_rows)

    async def find_by_filename(self, filename: str) -> Optional[RagDocument]:
        doc_row = (
            await self._session.execute(
                select(RagDocumentModel).where(RagDocumentModel.filename == filename)
            )
        ).scalar_one_or_none()
        if doc_row is None:
            return None
        chunk_rows = (
            await self._session.execute(
                select(RagChunkModel)
                .where(RagChunkModel.document_id == doc_row.id)
                .order_by(RagChunkModel.chunk_index.asc())
            )
        ).scalars().all()
        return self._reconstruct(doc_row, chunk_rows)

    async def list_documents(
        self,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[RagDocument], int]:
        base = select(RagDocumentModel)
        count_stmt = select(func.count()).select_from(RagDocumentModel)
        if category is not None:
            base = base.where(RagDocumentModel.category == category)
            count_stmt = count_stmt.where(RagDocumentModel.category == category)

        total = (await self._session.execute(count_stmt)).scalar_one()
        rows = (
            await self._session.execute(
                base.order_by(RagDocumentModel.filename.asc()).limit(limit).offset(offset)
            )
        ).scalars().all()
        documents = [self._reconstruct(r, ()) for r in rows]
        return documents, int(total)

    async def count_documents_by_category(self) -> list[tuple[str, int]]:
        rows = (
            await self._session.execute(
                select(
                    RagDocumentModel.category,
                    func.count(RagDocumentModel.id),
                )
                .group_by(RagDocumentModel.category)
            )
        ).all()
        return [(str(category), int(count)) for category, count in rows]

    async def hybrid_search(
        self,
        query_vector: list[float],
        query_tokens: str,
        top_k: int,
        category: Optional[str] = None,
    ) -> list[HybridHit]:
        pool = max(top_k, top_k * _POOL_MULTIPLIER)

        cat_filter = None
        if category is not None:
            cat_filter = RagDocumentModel.category == category

        # Vector branch — load all candidates then rank with Python cosine similarity
        vec_stmt = (
            select(
                RagChunkModel,
                RagDocumentModel.id,
                RagDocumentModel.filename,
                RagDocumentModel.title,
                RagDocumentModel.category,
                RagDocumentModel.source_url,
            )
            .join(RagDocumentModel, RagChunkModel.document_id == RagDocumentModel.id)
        )
        if cat_filter is not None:
            vec_stmt = vec_stmt.where(cat_filter)
        all_rows = (await self._session.execute(vec_stmt)).all()

        q_arr = np.asarray(query_vector, dtype=np.float32)
        q_norm = float(np.linalg.norm(q_arr))

        def _cosine_sim(embedding: list[float]) -> float:
            e_arr = np.asarray(embedding, dtype=np.float32)
            denom = q_norm * float(np.linalg.norm(e_arr))
            return float(np.dot(q_arr, e_arr)) / denom if denom > 0.0 else 0.0

        vec_rows = sorted(all_rows, key=lambda row: _cosine_sim(row[0].embedding), reverse=True)[:pool]

        # Keyword branch (skip if tokens empty → degrade to pure vector)
        kw_rows = []
        if query_tokens.strip():
            ts_query = func.plainto_tsquery("simple", query_tokens)
            rank_expr = func.ts_rank(RagChunkModel.tsv_content, ts_query)
            kw_stmt = (
                select(
                    RagChunkModel,
                    RagDocumentModel.id,
                    RagDocumentModel.filename,
                    RagDocumentModel.title,
                    RagDocumentModel.category,
                    RagDocumentModel.source_url,
                )
                .join(RagDocumentModel, RagChunkModel.document_id == RagDocumentModel.id)
                .where(RagChunkModel.tsv_content.op("@@")(ts_query))
                .order_by(rank_expr.desc())
                .limit(pool)
            )
            if cat_filter is not None:
                kw_stmt = kw_stmt.where(cat_filter)
            kw_rows = (await self._session.execute(kw_stmt)).all()

        # RRF fusion
        scored: dict[uuid.UUID, dict] = {}
        for rank, row in enumerate(vec_rows, start=1):
            chunk_model, doc_id, fname, title, cat, source_url = row
            s = 1.0 / (_RRF_K + rank)
            scored[chunk_model.id] = {
                "chunk": chunk_model,
                "document_id": doc_id,
                "filename": fname,
                "title": title,
                "category": cat,
                "source_url": source_url,
                "score": s,
            }
        for rank, row in enumerate(kw_rows, start=1):
            chunk_model, doc_id, fname, title, cat, source_url = row
            s = 1.0 / (_RRF_K + rank)
            if chunk_model.id in scored:
                scored[chunk_model.id]["score"] += s
            else:
                scored[chunk_model.id] = {
                    "chunk": chunk_model,
                    "document_id": doc_id,
                    "filename": fname,
                    "title": title,
                    "category": cat,
                    "source_url": source_url,
                    "score": s,
                }

        ordered = sorted(scored.values(), key=lambda x: x["score"], reverse=True)[:top_k]
        registry = _get_tag_registry()
        return [
            HybridHit(
                chunk=self._chunk_to_entity(r["chunk"]),
                document_filename=r["filename"],
                document_title=r["title"],
                document_category=registry.get_or_raise(r["category"]),
                document_source_url=r["source_url"],
                score=r["score"],
            )
            for r in ordered
        ]

    # ── Mappers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _reconstruct(
        doc_row: RagDocumentModel,
        chunk_rows: "list[RagChunkModel] | tuple[RagChunkModel, ...]",
    ) -> RagDocument:
        chunks = tuple(RagRepositoryImpl._chunk_to_entity(c) for c in chunk_rows)
        tags_data = doc_row.tags
        registry = _get_tag_registry()

        # Handle backwards compatibility: old documents have no tags_data
        if not tags_data:
            # Try to map old category string to a tag
            old_category = doc_row.category
            tag_name = _OLD_CATEGORY_TO_TAG.get(old_category, old_category or "unknown")
            primary_tag = registry.get(tag_name)
            if primary_tag is None:
                primary_tag = DocumentTag(
                    name=tag_name,
                    display_name=tag_name,
                    namespace="topic",
                )
            tags_tuple = (primary_tag,)
        else:
            tags_tuple = _reconstruct_tags(tags_data)
            primary_tag = tags_tuple[0] if tags_tuple else registry.get(doc_row.category)
            if primary_tag is None:
                primary_tag = DocumentTag(
                    name=doc_row.category or "unknown",
                    display_name=doc_row.category or "unknown",
                    namespace="topic",
                )

        return RagDocument(
            id=DocumentId(doc_row.id),
            filename=doc_row.filename,
            title=doc_row.title,
            primary_tag=primary_tag,
            tags=frozenset(tags_tuple),
            source_url=doc_row.source_url,
            raw_content=doc_row.raw_content,
            doc_metadata=doc_row.doc_metadata,
            content_hash=doc_row.content_hash,
            chunks=chunks,
            created_at=doc_row.created_at,
            updated_at=doc_row.updated_at,
        )

    @staticmethod
    def _chunk_to_entity(row: RagChunkModel) -> RagChunk:
        emb_values = row.embedding
        # pgvector may return numpy array or list depending on driver — normalize.
        emb_tuple = tuple(float(x) for x in emb_values)
        return RagChunk(
            id=ChunkId(row.id),
            document_id=DocumentId(row.document_id),
            chunk_index=row.chunk_index,
            heading=row.heading,
            content=row.content,
            token_count=row.token_count,
            embedding=EmbeddingVector(emb_tuple),
            # tsv_tokens is a server-side TSVECTOR; we don't round-trip the raw token
            # string back to the domain layer — leave empty here since the entity
            # shape requires a string but no caller reads it after retrieval.
            tsv_tokens="",
        )
