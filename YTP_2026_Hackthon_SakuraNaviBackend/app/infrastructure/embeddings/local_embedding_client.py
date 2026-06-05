"""Local embedding client backed by HuggingFace Transformers."""
from __future__ import annotations

import asyncio
import re
import unicodedata
from typing import Any


_DIM = 768
_DEFAULT_MODEL = "intfloat/multilingual-e5-base"  # 768 dims


class LocalEmbeddingClient:
    """Generate embeddings locally with a HuggingFace model."""

    def __init__(
        self,
        *,
        model_name: str = _DEFAULT_MODEL,
        device: str = "auto",
        dimension: int = _DIM,
        max_length: int = 512,
        batch_size: int = 16,
        local_files_only: bool = False,
    ) -> None:
        self._dimension = int(dimension)
        self._model_name = model_name
        self._requested_device = device.strip().lower() if device else "auto"
        self._max_length = int(max_length)
        self._batch_size = int(batch_size)
        self._local_files_only = bool(local_files_only)

        if self._dimension <= 0:
            raise ValueError("dimension must be positive")
        if self._max_length <= 0:
            raise ValueError("max_length must be positive")
        if self._batch_size <= 0:
            raise ValueError("batch_size must be positive")

        self._torch, self._tokenizer, self._model, self._device = self._load_backend()

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed_query(self, text: str) -> list[float]:
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")
        vectors = await asyncio.to_thread(self._embed_many_sync, [text], True)
        return vectors[0]

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return await asyncio.to_thread(self._embed_many_sync, texts, False)

    async def close(self) -> None:
        # Local HF model has no external resources to close.
        return None

    def _embed_many_sync(self, texts: list[str], is_query: bool) -> list[list[float]]:
        all_vectors: list[list[float]] = []
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i : i + self._batch_size]
            formatted = [self._format_text(t, is_query) for t in batch]
            encoded = self._tokenizer(
                formatted,
                padding=True,
                truncation=True,
                max_length=self._max_length,
                return_tensors="pt",
            )
            encoded = {k: v.to(self._device) for k, v in encoded.items()}
            with self._torch.inference_mode():
                outputs = self._model(**encoded)
                pooled = self._mean_pooling(
                    outputs.last_hidden_state,
                    encoded["attention_mask"],
                )
                normalized = self._torch.nn.functional.normalize(pooled, p=2, dim=1)
            if int(normalized.shape[1]) != self._dimension:
                raise RuntimeError(
                    "HuggingFace embedding dimension mismatch: "
                    f"expected={self._dimension}, got={int(normalized.shape[1])}. "
                    "Current RAG schema is fixed to 768 dimensions."
                )
            all_vectors.extend(normalized.detach().cpu().float().tolist())
        return all_vectors

    def _load_backend(self) -> tuple[Any, Any, Any, Any]:
        try:
            import torch
            from transformers import AutoModel, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "HuggingFace local embedding requires 'torch' and 'transformers'. "
                "Install with: pip install torch transformers"
            ) from exc

        if self._requested_device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            device = self._requested_device

        tokenizer = AutoTokenizer.from_pretrained(
            self._model_name,
            local_files_only=self._local_files_only,
        )
        model = AutoModel.from_pretrained(
            self._model_name,
            local_files_only=self._local_files_only,
        )
        model.to(device)
        model.eval()
        return torch, tokenizer, model, device

    @staticmethod
    def _normalize_text(text: str) -> str:
        normalized = unicodedata.normalize("NFKC", text).strip()
        return re.sub(r"\s+", " ", normalized)

    def _format_text(self, text: str, is_query: bool) -> str:
        normalized = self._normalize_text(text)
        if not normalized:
            raise ValueError("Cannot embed empty text")
        # E5-style prefixing improves retrieval behavior for query/document pairs.
        prefix = "query: " if is_query else "passage: "
        return prefix + normalized

    def _mean_pooling(self, token_embeddings: Any, attention_mask: Any) -> Any:
        mask = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        summed = (token_embeddings * mask).sum(dim=1)
        counts = mask.sum(dim=1).clamp(min=1e-9)
        return summed / counts
