"""Metadata-aware chunking that never splits an atomic clause (Listing 4.3).

Standard fixed-size chunking severs two things a marketing corpus needs kept
together: the body text from the metadata that scopes it, and an atomic legal
clause from itself. The fix is two invariants:

1. Every chunk carries its parent document's full metadata, so eligibility
   filters (segment, approval, trust) still apply after chunking.
2. Atomic units (a legal clause) become exactly one chunk, never windowed.

The body window (size=500 here) is a placeholder for whatever splitter you
prefer; the two invariants around it are not negotiable.
"""

from __future__ import annotations

from dataclasses import dataclass

from C01_Menguy_MarketingAISystems import DocMeta, Document, sample_corpus


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    text: str
    meta: DocMeta            # every chunk carries its parent's metadata
    atomic: bool = False


def chunk_document(doc: Document, size: int = 500) -> list[Chunk]:
    if doc.meta.doc_type == "legal":
        # A legal clause is one indivisible chunk; never windowed.
        return [Chunk(f"{doc.doc_id}#0", doc.text, doc.meta, atomic=True)]
    chunks: list[Chunk] = []
    start, n = 0, 0
    while start < len(doc.text):
        piece = doc.text[start:start + size]
        chunks.append(Chunk(f"{doc.doc_id}#{n}", piece, doc.meta))
        start += size
        n += 1
    return chunks


def chunk_corpus(docs: list[Document], size: int = 500) -> list[Chunk]:
    out: list[Chunk] = []
    for doc in docs:
        out.extend(chunk_document(doc, size))
    return out


if __name__ == "__main__":
    chunks = chunk_corpus(sample_corpus(), size=60)
    for c in chunks:
        tag = "ATOMIC" if c.atomic else "window"
        print(f"{c.chunk_id}  [{tag}] type={c.meta.doc_type} "
              f"segment={c.meta.segment}\n    {c.text!r}")
