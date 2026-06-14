from typing import List, Optional

import torch
from sentence_transformers import CrossEncoder
from config import config


class RerankerService:
    """
    Cross-encoder reranker service using a model like BAAI/bge-reranker-base.

    Lazy-loads the CrossEncoder on first use and scores query-document pairs.
    """

    def __init__(self):
        self._model: Optional[CrossEncoder] = None
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def _load_model(self) -> None:
        if self._model is None:
            print(f"\n🔄 Loading reranker model: {config.BM25_RERANKER_MODEL_NAME}...")
            self._model = CrossEncoder(config.BM25_RERANKER_MODEL_NAME)

            if self._device.type == "cuda":
                try:
                    self._model.to(self._device)
                    print("✓ Reranker moved to CUDA device")
                except Exception as device_error:
                    print(f"⚠ CUDA setup failed for reranker, falling back to CPU: {device_error}")
                    self._device = torch.device("cpu")

            print(f"✓ Reranker loaded successfully (device: {self._device.type})")

    def score_pairs(self, pairs: List[List[str]], batch_size: int = 32) -> List[float]:
        """
        Score list of [query, document_text] pairs and return a list of float scores.

        Args:
            pairs: list of [query, doc_text]
            batch_size: batch size for prediction

        Returns:
            list of floats (higher = more relevant)
        """
        if not pairs:
            return []

        self._load_model()

        # CrossEncoder.predict expects a list of pairs
        scores = self._model.predict(pairs, convert_to_numpy=True, batch_size=batch_size)
        return [float(s) for s in scores]
