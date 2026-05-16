import numpy as np

MODEL_NAME = "all-MiniLM-L6-v2"


class Embedder:
    """Lazy-loading local sentence-transformer embedder. Model downloads once on first use."""

    def __init__(self, model_name: str = MODEL_NAME) -> None:
        self._model_name = model_name
        self._model = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer  # noqa: PLC0415 — lazy import avoids slow startup
            self._model = SentenceTransformer(self._model_name)
        return self._model

    def encode(self, texts: list[str]) -> np.ndarray:
        """Return L2-normalised float32 embedding matrix (N × dim)."""
        vecs = self._load().encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return np.array(vecs, dtype=np.float32)

    def encode_one(self, text: str) -> np.ndarray:
        return self.encode([text])[0]

    @property
    def dimension(self) -> int:
        return self._load().get_sentence_embedding_dimension()
