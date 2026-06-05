"""Factory for creating the local embedding client."""
from app.application.rag.ports import EmbeddingClient
from app.core.config import settings
from app.infrastructure.embeddings.local_embedding_client import LocalEmbeddingClient


def build_embedding_client() -> EmbeddingClient:
    return LocalEmbeddingClient(
        model_name=settings.rag_local_embedding_model,
        device=settings.rag_local_embedding_device,
        dimension=settings.rag_local_embedding_dimension,
        max_length=settings.rag_local_embedding_max_length,
        batch_size=settings.rag_local_embedding_batch_size,
        local_files_only=settings.rag_local_embedding_local_files_only,
    )
