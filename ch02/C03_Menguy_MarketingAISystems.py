"""The shared embedding helper (Listing 2.3).

Everything downstream turns text into vectors, so C04 (retrieval), C05 (scoring),
and C12 (negatives) share this one helper. Any embedding model works: a hosted
API (Voyage, Cohere, OpenAI) or an open model run locally, as here. The principle
(text to unit-normalized vectors) outlives the specific encoder.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=1)  # load the model on first call, then reuse it
def _model() -> SentenceTransformer:
    # A small open embedding model, so the listings run without an API key.
    return SentenceTransformer("all-MiniLM-L6-v2")


def embed(texts: list[str]) -> np.ndarray:
    """Embed texts into unit-normalized vectors."""
    vecs = _model().encode(texts, normalize_embeddings=True)
    return np.asarray(vecs, dtype=np.float32)


if __name__ == "__main__":
    v = embed(["The shell is here.", "Conquer any storm!"])
    print("shape:", v.shape)
