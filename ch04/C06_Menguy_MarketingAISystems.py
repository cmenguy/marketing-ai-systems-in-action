"""The retrieval order: recall wide, sharpen, let supersession decide (Listing 4.6).

Section 4.3.1 argues that a semantic (cross-encoder) reranker must not have the
last word on order: it scores relevance and knows nothing about supersession or
the legal exemption. This listing wires the three stages in the order that keeps
that rule intact. Hybrid search (C04) recalls a wide pool fast, the cross-encoder
sharpens the top of it, and supersession-aware ranking (C05) runs last so
relevance never overrules "this quarter beats last". Swap the last two calls and
the pipeline still runs and still demos well while quietly floating a superseded
brief back to the top.

The cross-encoder is injected as a scoring function, matching the manuscript
listing. load_cross_encoder() returns a real one backed by sentence-transformers
(cross-encoder/ms-marco-MiniLM-L-6-v2); if that package or the model weights are
unavailable (offline, no install), the __main__ demo falls back to a token-overlap
stub so the composition still runs anywhere.
"""

from __future__ import annotations

import re
from datetime import date

from C01_Menguy_MarketingAISystems import sample_corpus
from C03_Menguy_MarketingAISystems import Chunk, chunk_corpus
from C04_Menguy_MarketingAISystems import bow, hybrid_search
from C05_Menguy_MarketingAISystems import rerank


def cross_encoder_rerank(query, hits, score):
    # score(query, text) is a cross-encoder: it reads the query and a
    # candidate together for one relevance number, unlike the two
    # separate embeddings hybrid search compared. Accurate, and too
    # slow to run over the whole corpus, so it sees only the pool.
    def key(c: Chunk):
        return score(query, c.text)
    return sorted(hits, key=key, reverse=True)


def retrieve(query, chunks, want, embed, score, today, k=5):
    pool = hybrid_search(query, chunks, want, embed, k=40)  # recall wide
    pool = cross_encoder_rerank(query, pool, score)
    return rerank(pool, today)[:k]


def load_cross_encoder(model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
    """Return a real score(query, text) -> float backed by a cross-encoder.

    Uses sentence-transformers. Returns None when the library or the model
    weights are unavailable (no install, offline) so callers can fall back to a
    dependency-free stub. Production would batch the pairs into one predict call;
    here the pool is small, so one predict per candidate keeps the score(query,
    text) shape identical to the listing.
    """
    try:
        from sentence_transformers import CrossEncoder
    except ImportError:
        return None
    try:
        model = CrossEncoder(model_name)
    except Exception:  # weights not cached and no network to fetch them
        return None
    return lambda query, text: float(model.predict([(query, text)])[0])


if __name__ == "__main__":
    def lexical_score(query: str, text: str) -> float:
        # Dependency-free fallback for when no cross-encoder is available.
        q = set(re.findall(r"[a-z0-9]+", query.lower()))
        t = set(re.findall(r"[a-z0-9]+", text.lower()))
        return float(len(q & t))

    score = load_cross_encoder()
    kind = "cross-encoder (sentence-transformers)" if score else "lexical stub"
    if score is None:
        score = lexical_score

    chunks = chunk_corpus(sample_corpus())
    want = {"channel": "email", "segment": "loyalty"}
    query = "Cascade spring price and waterproof rating"

    print(f"reranker: {kind}")
    print("cross-encoder order over the eligible pool (before supersession):")
    pool = hybrid_search(query, chunks, want, bow, k=40)
    for c in cross_encoder_rerank(query, pool, score):
        print(f"  {score(query, c.text):+.3f}  {c.chunk_id}  type={c.meta.doc_type}")

    hits = retrieve(query, chunks, want, bow, score, date.today())
    print(f"\n{len(hits)} hits after supersession runs last:")
    for c in hits:
        print(f"  {c.chunk_id}  quarter={c.meta.quarter} type={c.meta.doc_type}")
