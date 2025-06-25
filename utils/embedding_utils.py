import os
from typing import List


class _SBERTEmbedder:
    """Lightweight wrapper providing the same interface as LangChain embeddings.

    • Uses `sentence-transformers` under the hood (already in requirements).
    • Exposes `.embed_documents()` and `.embed_query()` so existing code can
      stay unchanged.
    • Internally normalises embeddings to unit-length to make cosine similarity
      equivalent to dot-product.
    """

    def __init__(self, model_name: str, device: str | None = None):
        from sentence_transformers import SentenceTransformer  # local import to avoid hard dep at import time

        self.model = SentenceTransformer(model_name, device=device or "cpu")

    # --------------------------------------------------------------------- #
    def _encode(self, texts):
        vecs = self.model.encode(
            texts,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,  # ← ensures cosine = dot product
        )
        return vecs.tolist()  # convert to Py primitives for JSON safety

    # ------------------------------------------------------------------ #
    def embed_documents(self, texts: List[str]) -> List[List[float]]:  # noqa: D401
        """Return a list of embeddings for *texts*."""
        return self._encode(texts)

    def embed_query(self, query: str) -> List[float]:  # noqa: D401
        """Return the embedding vector for a single query string."""
        return self._encode([query])[0]


# ----------------------------------------------------------------------- #
# Public helper
# ----------------------------------------------------------------------- #

def get_embeddings():
    """Singleton factory for the default multilingual embedding model."""
    model_name = os.getenv("EMBEDDING_MODEL_NAME", "intfloat/multilingual-e5-large")

    if not hasattr(get_embeddings, "_INSTANCE"):
        device = os.getenv("EMBEDDING_DEVICE", "cpu")
        get_embeddings._INSTANCE = _SBERTEmbedder(model_name=model_name, device=device)

    return get_embeddings._INSTANCE 