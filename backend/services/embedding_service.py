"""
Embedding Service for semantic content and vector generation.
Handles formatting game metadata into semantic_content and generating embeddings
using BAAI/bge-small-en-v1.5 model via sentence-transformers.
"""

from typing import List, Optional

import torch
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL_NAME, EMBEDDING_DIMENSION


def format_semantic_content(
    name: str,
    summary: str,
    genres: Optional[List[str]] = None,
    themes: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
) -> str:
    """
    Format game metadata into a semantic content string for embedding.

    Combines title, summary, genres, themes, and keywords into a structured text
    format that captures the game's semantic meaning for vector embeddings.

    Format:
        Title: {name}

        Summary:
        {summary}

        Genres:
        {genres_joined}

        Themes:
        {themes_joined}

        Keywords:
        {keywords_joined}

    Args:
        name: Game name
        summary: Game summary/description
        genres: List of genre strings
        themes: List of theme strings
        keywords: List of keyword strings

    Returns:
        Formatted semantic content string ready for embedding
    """
    parts = [f"Title: {name}"]

    if summary:
        parts.append(f"\nSummary:\n{summary}")

    if genres:
        genres_str = ", ".join(genres)
        parts.append(f"\nGenres:\n{genres_str}")

    if themes:
        themes_str = ", ".join(themes)
        parts.append(f"\nThemes:\n{themes_str}")

    if keywords:
        keywords_str = ", ".join(keywords)
        parts.append(f"\nKeywords:\n{keywords_str}")

    return "".join(parts)


class EmbeddingService:
    """
    Service for generating semantic embeddings using BAAI/bge-small-en-v1.5.

    Lazy-loads the model on first use to avoid unnecessary overhead.
    Reuses model instance across all documents for performance.

    Model: BAAI/bge-small-en-v1.5
    - Optimized for retrieval tasks
    - Output dimension: 384
    - Lightweight and fast (~133MB)
    """

    def __init__(self):
        """Initialize EmbeddingService with lazy model loading."""
        self._model: Optional[SentenceTransformer] = None
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def _load_model(self) -> None:
        """Load the sentence transformer model (lazy loading)."""
        if self._model is None:
            print(f"\n🔄 Loading embedding model: {EMBEDDING_MODEL_NAME}...")
            self._model = SentenceTransformer(EMBEDDING_MODEL_NAME)

            if self._device.type == "cuda":
                try:
                    self._model.to(self._device)
                    print("✓ Model moved to CUDA device")
                except Exception as device_error:
                    print(
                        f"⚠ CUDA setup failed, falling back to CPU: {device_error}"
                    )
                    self._device = torch.device("cpu")

            print(
                f"✓ Model loaded successfully (dimension: {EMBEDDING_DIMENSION}, device: {self._device.type})"
            )

    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for the given text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the 384-dimensional embedding

        Raises:
            ValueError: If text is empty or model loading fails
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        # Lazy load model on first use
        self._load_model()

        # Generate embedding (normalize=True for cosine similarity)
        embedding = self._model.encode(
            text, normalize_embeddings=True, device=self._device
        )

        # Convert to list of floats
        return embedding.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch (more efficient).

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings, one per input text

        Raises:
            ValueError: If texts list is empty or any text is empty
        """
        if not texts:
            raise ValueError("Cannot embed empty text list")

        if any(not t or not t.strip() for t in texts):
            raise ValueError("All texts must be non-empty")

        # Lazy load model on first use
        self._load_model()

        # Generate embeddings (normalize=True for cosine similarity)
        embeddings = self._model.encode(
            texts, normalize_embeddings=True, device=self._device
        )

        # Convert to list of lists
        return embeddings.tolist()
