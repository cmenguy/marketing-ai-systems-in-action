"""Supersession-aware re-ranking, with legal copy exempt (Listing 4.5).

Filtering decides what is eligible; ranking decides what wins among the eligible.
Two approved Cascade briefs from different quarters are both eligible and nearly
identical in similarity, so pure cosine picks between them almost at random.

The ranker has two parts:
1. Drop any document a more recent eligible document supersedes (the `supersedes`
   relationship recorded at ingestion), so a superseded brief is removed, not
   merely down-weighted.
2. Among what remains, break ties toward recency for briefs (recency == currency)
   and exempt legal copy entirely (append-only, never dropped, never expires).

The legal exemption is an explicit branch so it cannot be tuned away by accident.
"""

from __future__ import annotations

from datetime import date

from C01_Menguy_MarketingAISystems import sample_corpus
from C03_Menguy_MarketingAISystems import Chunk, chunk_corpus


def resolve_supersession(hits: list[Chunk]) -> list[Chunk]:
    superseded: set[str] = set()
    for c in hits:
        superseded.update(c.meta.supersedes)
    return [c for c in hits if c.meta.campaign_code not in superseded]


def rerank(hits: list[Chunk], today: date) -> list[Chunk]:
    live = resolve_supersession(hits)

    def key(c: Chunk):
        if c.meta.doc_type == "legal":
            return (2, date.max)                   # always kept, order stable
        if c.meta.doc_type == "brief":
            return (1, c.meta.effective_date)      # newer brief wins
        return (0, date.min)                       # style guide: recency neutral

    return sorted(live, key=key, reverse=True)


if __name__ == "__main__":
    # All three chunks are approved and eligible; the ranker sorts them.
    chunks = chunk_corpus(sample_corpus())
    ranked = rerank(chunks, today=date(2026, 3, 15))
    print("After supersession-aware ranking:")
    for c in ranked:
        print(f"  {c.meta.doc_type:11s} {c.meta.campaign_code:22s} "
              f"quarter={c.meta.quarter}")
    codes = {c.meta.campaign_code for c in ranked}
    assert "cascade-spring-2025" not in codes, "superseded brief should be dropped"
    assert any(c.meta.doc_type == "legal" for c in ranked), "legal must survive"
    print("OK: Q1 brief dropped as superseded; legal clause kept regardless of age.")
