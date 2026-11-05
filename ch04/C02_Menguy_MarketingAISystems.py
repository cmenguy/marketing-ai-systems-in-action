"""Parsing a source into a structured document with provenance (Listing 4.2).

Marketing content arrives as decks, docs, PDFs, and Figma exports, and the fields
that decide retrieval (campaign code, quarter, segment, approval) usually live in
a header block, not in the prose. A parser that flattens everything to text throws
those fields away. Parsing has two jobs: pull the readable text, and extract the
structured metadata into DocMeta while recording where the document came from.

The provenance pointer is what lets a reviewer, three steps downstream, trace a
claim back to a specific brief in a specific quarter with a specific approval
state. A claim whose origin you cannot name is a claim legal will not clear.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from C01_Menguy_MarketingAISystems import DocMeta, Document


@dataclass(frozen=True)
class Provenance:
    source_uri: str          # where this came from, for traceability
    source_type: str         # gdoc | pdf | deck | figma
    parsed_at: date


def parse_brief(raw: dict, prov: Provenance) -> Document:
    """Read the header into metadata; keep the body as one field."""
    header = raw["header"]                         # gating fields live here
    meta = DocMeta(
        campaign_code=header["campaign_code"],
        doc_type="brief",
        quarter=header["quarter"],
        effective_date=date.fromisoformat(header["effective"]),
        region=header.get("region", "US"),
        channel=header.get("channel"),
        segment=header.get("segment"),
        product=header.get("product"),
        approval_state=header.get("approval", "draft"),
    )
    return Document(
        doc_id=f"{meta.campaign_code}:{prov.source_uri}",
        text=raw["body"].strip(),                  # body does not carry metadata
        meta=meta,
    )


if __name__ == "__main__":
    raw = {
        "header": {
            "campaign_code": "cascade-spring-2026",
            "quarter": "2026-Q2",
            "effective": "2026-03-01",
            "region": "US",
            "channel": "email",
            "segment": "loyalty",
            "product": "cascade",
            "approval": "approved",
        },
        "body": ("Launch the Cascade shell. Lead with the spring price and its "
                 "end date. 10K/10K waterproof rating, 63% recycled face fabric."),
    }
    prov = Provenance("gdoc/bbb", "gdoc", date(2026, 2, 20))
    doc = parse_brief(raw, prov)
    print(doc.doc_id)
    print("  meta:", doc.meta.quarter, doc.meta.segment, doc.meta.approval_state)
    print("  provenance:", prov.source_uri, prov.source_type)
