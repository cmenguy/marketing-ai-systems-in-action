"""Hybrid retrieval with a metadata filter applied before scoring (Listing 4.4).

Pure vector similarity fails two ways on a marketing corpus. It blurs exact
tokens (a campaign code, a SKU, a 10K/10K rating), and it has no idea that a draft
brief is ineligible or that the query is scoped to one segment. Hybrid search
covers the first by fusing a dense retriever with a sparse (lexical) one. The
metadata filter covers the second by narrowing the candidate pool to eligible
chunks BEFORE any scoring. Filter first, then search, then fuse.

The trust field is also an eligibility field: admitting only brand-trust chunks
into a customer-facing generation keeps injected UGC (chapter 3) out of context.

The embed here is a dependency-free bag-of-words stand-in so the listing runs
anywhere; production swaps in chapter 2's real embedding model.
"""

from __future__ import annotations

import re
from collections import Counter
from math import sqrt

from C01_Menguy_MarketingAISystems import sample_corpus
from C03_Menguy_MarketingAISystems import Chunk, chunk_corpus


def bow(text: str) -> Counter:
    """A trivial 'embedding': a term-frequency vector. Swap for a real encoder."""
    return Counter(re.findall(r"[a-z0-9]+", text.lower()))


def cosine(a: Counter, b: Counter) -> float:
    shared = set(a) & set(b)
    num = sum(a[t] * b[t] for t in shared)
    denom = sqrt(sum(v * v for v in a.values())) * sqrt(sum(v * v for v in b.values()))
    return num / denom if denom else 0.0


def eligible(chunk: Chunk, want: dict) -> bool:
    m = chunk.meta
    if m.approval_state != "approved":             # a draft never competes
        return False
    if m.trust != "brand":                         # untrusted UGC stays out
        return False
    if want.get("channel") and m.channel not in (want["channel"], None):
        return False
    if want.get("segment") and m.segment not in (want["segment"], None):
        return False
    return True


def rank_by_cosine(query: str, pool: list[Chunk], embed) -> list[Chunk]:
    qv = embed(query)
    return sorted(pool, key=lambda c: cosine(qv, embed(c.text)), reverse=True)


def rank_by_lexical(query: str, pool: list[Chunk]) -> list[Chunk]:
    q = set(re.findall(r"[a-z0-9]+", query.lower()))
    def overlap(c: Chunk) -> int:
        return len(q & set(re.findall(r"[a-z0-9]+", c.text.lower())))
    return sorted(pool, key=overlap, reverse=True)


def reciprocal_rank_fusion(*rankings: list[Chunk], k: int = 60) -> list[Chunk]:
    scores: dict[str, float] = {}
    by_id: dict[str, Chunk] = {}
    for ranking in rankings:
        for rank, chunk in enumerate(ranking):
            scores[chunk.chunk_id] = scores.get(chunk.chunk_id, 0.0) + 1.0 / (k + rank)
            by_id[chunk.chunk_id] = chunk
    order = sorted(scores, key=scores.get, reverse=True)
    return [by_id[cid] for cid in order]


def hybrid_search(query, chunks, want, embed=bow, k=5) -> list[Chunk]:
    pool = [c for c in chunks if eligible(c, want)]   # filter first
    dense = rank_by_cosine(query, pool, embed)
    sparse = rank_by_lexical(query, pool)             # exact tokens
    return reciprocal_rank_fusion(dense, sparse)[:k]


if __name__ == "__main__":
    chunks = chunk_corpus(sample_corpus())
    want = {"channel": "email", "segment": "loyalty"}
    hits = hybrid_search("Cascade spring price and waterproof rating", chunks, want)
    print(f"{len(hits)} eligible hits (drafts and UGC filtered out):")
    for c in hits:
        print(f"  {c.chunk_id}  quarter={c.meta.quarter} type={c.meta.doc_type}")
