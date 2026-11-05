"""The marketing document model, where metadata is a first-class field (Listing 4.1).

A campaign brief is a structured record with a body attached, not a blob of prose
you embed and forget. The metadata (quarter, channel, segment, approval state,
trust) is the primary key of relevance and decides whether a document is eligible
for retrieval before its text is ever scored for similarity. The body is the
tiebreaker.

This module is the backbone the rest of chapter 4 imports: DocMeta and Document
are the shapes ingestion produces (C02), chunking derives from (C03), and every
retrieval pattern (C04-C08) filters and ranks over.

Northpeak, the Cascade shell, and the loyalty / lapsed-12mo segments are the
running example carried over from chapters 1-3.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class DocMeta:
    """The fields that gate retrieval. Text is a separate concern."""
    campaign_code: str            # "cascade-spring-2026"
    doc_type: str                 # brief | style_guide | legal | asset
    quarter: str                  # "2026-Q2"
    effective_date: date
    region: str = "US"            # US | EMEA | APAC
    channel: str | None = None    # email | sms | None = all channels
    segment: str | None = None    # loyalty | lapsed_12mo | None = all
    product: str | None = None    # "cascade"
    approval_state: str = "draft"  # draft | in_review | approved
    trust: str = "brand"          # brand | ugc
    supersedes: tuple[str, ...] = ()  # campaign codes this one replaces


@dataclass(frozen=True)
class Document:
    doc_id: str
    text: str
    meta: DocMeta


# A small Northpeak corpus used across the chapter's listings. Q1 teased the
# jacket with no pricing; Q2 supersedes it and leads with the spring price. The
# legal clause is append-only and exempt from recency.
def sample_corpus() -> list[Document]:
    q1 = Document(
        doc_id="cascade-spring-2025:gdoc/aaa",
        text=("Tease the Cascade shell for spring. Build anticipation. "
              "Hold pricing back until launch."),
        meta=DocMeta(
            campaign_code="cascade-spring-2025", doc_type="brief",
            quarter="2025-Q1", effective_date=date(2025, 1, 15),
            channel="email", segment="loyalty", product="cascade",
            approval_state="approved"),
    )
    q2 = Document(
        doc_id="cascade-spring-2026:gdoc/bbb",
        text=("Launch the Cascade shell. Lead with the spring price and its "
              "end date. 10K/10K waterproof rating, 63% recycled face fabric."),
        meta=DocMeta(
            campaign_code="cascade-spring-2026", doc_type="brief",
            quarter="2026-Q2", effective_date=date(2026, 3, 1),
            channel="email", segment="loyalty", product="cascade",
            approval_state="approved",
            supersedes=("cascade-spring-2025",)),
    )
    legal = Document(
        doc_id="legal/recycled-substantiation-2024",
        text=("Recycled-content claims must state the measured percentage and "
              "reference the substantiation on file."),
        meta=DocMeta(
            campaign_code="legal-recycled", doc_type="legal",
            quarter="2024-Q1", effective_date=date(2024, 2, 1),
            product="cascade", approval_state="approved"),
    )
    return [q1, q2, legal]


if __name__ == "__main__":
    for doc in sample_corpus():
        m = doc.meta
        print(f"{doc.doc_id}\n  type={m.doc_type} quarter={m.quarter} "
              f"approval={m.approval_state} supersedes={m.supersedes}")
