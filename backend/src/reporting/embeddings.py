"""Embedding generation service for report sections."""

from __future__ import annotations

import numpy as np
from typing import List

from ..config.base_settings import settings
from ..logging_utils import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating embeddings from text."""

    def __init__(self) -> None:
        self.provider = settings.embedding_provider
        self.model_name = settings.embedding_model
        self._model = None
        self._openai_client = None

    def _get_model(self):
        """Lazy load the embedding model."""
        if self._model is not None:
            return self._model

        if self.provider == "openai":
            try:
                from openai import OpenAI

                if not settings.openai_api_key:
                    raise ValueError("OPENAI_API_KEY not set")
                self._openai_client = OpenAI(api_key=settings.openai_api_key)
                logger.info("Using OpenAI embeddings with model: %s", self.model_name)
                return self._openai_client
            except ImportError:
                logger.warning("OpenAI not available, falling back to sentence-transformers")
                self.provider = "sentence-transformers"
                self.model_name = "all-MiniLM-L6-v2"

        if self.provider == "sentence-transformers":
            try:
                from sentence_transformers import SentenceTransformer

                logger.info("Loading sentence-transformers model: %s", self.model_name)
                self._model = SentenceTransformer(self.model_name)
                return self._model
            except ImportError:
                raise ImportError(
                    "sentence-transformers not installed. Install with: pip install sentence-transformers"
                )

        raise ValueError(f"Unknown embedding provider: {self.provider}")

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text string."""
        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0] * 384  # Default dimension for all-MiniLM-L6-v2

        if self.provider == "openai":
            client = self._get_model()
            response = client.embeddings.create(
                model=self.model_name if self.model_name.startswith("text-") else "text-embedding-3-small",
                input=text,
            )
            return response.data[0].embedding

        # sentence-transformers
        model = self._get_model()
        embedding = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        return embedding.tolist()

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts (more efficient)."""
        if not texts:
            return []

        if self.provider == "openai":
            client = self._get_model()
            # Filter empty texts
            non_empty = [(i, t) for i, t in enumerate(texts) if t and t.strip()]
            if not non_empty:
                return [[0.0] * 1536 for _ in texts]  # OpenAI dimension

            indices, valid_texts = zip(*non_empty)
            response = client.embeddings.create(
                model=self.model_name if self.model_name.startswith("text-") else "text-embedding-3-small",
                input=list(valid_texts),
            )
            embeddings = {idx: resp.embedding for idx, resp in zip(indices, response.data)}
            return [embeddings.get(i, [0.0] * 1536) for i in range(len(texts))]

        # sentence-transformers
        model = self._get_model()
        embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False)
        return embeddings.tolist()

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this service."""
        if self.provider == "openai":
            return 1536  # text-embedding-3-small dimension
        # Default for sentence-transformers models
        return 384  # all-MiniLM-L6-v2 dimension

