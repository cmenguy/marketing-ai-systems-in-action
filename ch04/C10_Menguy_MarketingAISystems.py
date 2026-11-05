"""The citation record that grounded generation hands to approval (Listing 4.10).

An approved fact in the output is only half of what approval needs; the other
half is knowing where it came from. Because each retrieved fact went into the
prompt tagged with its chunk id (C08), and that id traces back through the
provenance record (C02) to a document in a specific quarter with a specific
approval state, the finished copy can carry a citation for every claim it makes.

That record is what chapter 5's approval routing consumes: the reviewer verifies a
chain (this rating came from an approved Q2 brief, this disclaimer from the
binding clause) rather than re-litigating every claim from a blank page. In a
well-built pipeline a claim with no source should not exist, because the grounding
step only offered the model facts that had sources.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from C01_Menguy_MarketingAISystems import sample_corpus
from C03_Menguy_MarketingAISystems import Chunk, chunk_corpus
from C05_Menguy_MarketingAISystems import rerank


@dataclass(frozen=True)
class Citation:
    source_id: str           # the chunk the fact came from
    quarter: str
    approval_state: str
    fact: str


@dataclass(frozen=True)
class ReviewPackage:
    copy: str
    citations: list[Citation]


def build_review_package(copy: str, hits: list[Chunk]) -> ReviewPackage:
    cites = [Citation(c.chunk_id, c.meta.quarter,
                      c.meta.approval_state, c.text)
             for c in hits]
    return ReviewPackage(copy, cites)


if __name__ == "__main__":
    hits = rerank(chunk_corpus(sample_corpus()), today=date(2026, 3, 15))
    copy = ("The Cascade shell is here. A 10K/10K waterproof rating and a "
            "63% recycled face fabric. Recycled-content substantiation on file.")
    pkg = build_review_package(copy, hits)
    print("Copy for review:\n ", pkg.copy, "\n")
    print("Citations the reviewer verifies:")
    for c in pkg.citations:
        print(f"  [{c.source_id}] quarter={c.quarter} "
              f"approval={c.approval_state}\n     {c.fact}")
