# Chapter 4 — Retrieval over Brand Knowledge

Companion code for chapter 4. Marketing retrieval is RAG on a different corpus:
small, heavily structured, and deliberately contradictory. The standard
chunk-embed-rank recipe breaks on it, returning superseded briefs and dropping
append-only disclaimers. These listings rebuild the pipeline for the corpus
marketing actually has: metadata that gates retrieval before similarity,
supersession-aware ranking, graph and agentic retrieval over campaign genealogy,
and generation grounded in retrieved facts with citable provenance.

Each file is named `C{LL}_Menguy_MarketingAISystems.py`, where `LL` is the listing
number in the manuscript. Northpeak, the Cascade shell, and the loyalty /
lapsed-12mo segments are the running example carried over from chapters 1–3.

## Files

| File | Listing | What it shows |
|---|---|---|
| `C01_...py` | 4.1 | The marketing document model (`DocMeta`, `Document`): metadata is a first-class field that gates retrieval; body text is the tiebreaker. Includes the sample Northpeak corpus (Q1 vs Q2 briefs + a legal clause) the other files import. |
| `C02_...py` | 4.2 | Parsing a source (deck / doc / PDF / Figma) into a structured `Document` plus a `Provenance` pointer, extracting the header fields into `DocMeta`. |
| `C03_...py` | 4.3 | Metadata-aware chunking: every chunk carries its parent's metadata, and an atomic legal clause is never windowed. |
| `C04_...py` | 4.4 | Hybrid search (dense + sparse via reciprocal rank fusion) with a metadata + trust filter applied *before* scoring. |
| `C05_...py` | 4.5 | Supersession-aware re-ranking: drop the superseded brief, let the newer brief win, exempt legal copy from recency. |
| `C06_...py` | 4.6 | The retrieval order: hybrid recall, then a cross-encoder reranker for precision, then supersession-aware ranking last so relevance never overrules "this quarter wins". The cross-encoder is a real `sentence-transformers` model (`load_cross_encoder`), with a lexical stub fallback when it is not installed. |
| `C07_...py` | 4.7 | A campaign genealogy graph queried by walking edges (`lineage`, `campaigns_for`), and `graph_scoped_retrieve`, which uses the walk to scope the corpus and then runs `retrieve` (C06) over it unchanged. |
| `C08_...py` | 4.8 | Agentic retrieval: an injected planner decomposes a multi-hop question into vector/graph steps, and a synthesizer returns a cited answer. |
| `C09_...py` | 4.9 | Generation grounded in retrieved facts, with the deterministic legal check running on the output, outside the model. |
| `C10_...py` | 4.10 | The citation / provenance record (`Citation`, `ReviewPackage`) that grounded generation hands to chapter 5's approval routing. |
| `C11_...py` | 4.11 | The retrieval canary set: queries with must-include (a binding disclaimer) and must-exclude (a superseded brief) expectations; `run_canaries` flags any regression. `__main__` seeds two canaries, passes on the healthy corpus, then catches a planted supersession bug. |

## Setup

```bash
python3 --version   # 3.10+ for the modern type hints
```

The listings need only the standard library (`dataclasses`, `re`, `collections`,
`datetime`, `math`), with one optional exception: `C06` loads a real cross-encoder
from `sentence-transformers` (`pip install sentence-transformers`, downloads a
small model on first use) and falls back to a dependency-free lexical stub when it
is not installed, so it still runs with nothing extra. The `embed` in `C04` is a
dependency-free bag-of-words stand-in so the listing runs anywhere; production
swaps in chapter 2's real embedding model. The model calls in `C08` (planner / synthesizer) and
`C09` (`generate`) are injected, so stubs stand in and no API key is needed to run
the code. In production those become calls to a capable model (prefer Claude
Sonnet / Opus), with the API key read from the environment.

## Run

```bash
python3 C01_Menguy_MarketingAISystems.py   # the document model + sample corpus
python3 C03_Menguy_MarketingAISystems.py   # metadata-aware chunking, atomic legal
python3 C04_Menguy_MarketingAISystems.py   # hybrid search, filter-first
python3 C05_Menguy_MarketingAISystems.py   # supersession ranking (Q2 wins, legal kept)
python3 C06_Menguy_MarketingAISystems.py   # retrieval order: recall, rerank, supersede
python3 C07_Menguy_MarketingAISystems.py   # walk the campaign genealogy graph
python3 C08_Menguy_MarketingAISystems.py   # agentic multi-hop retrieval
python3 C09_Menguy_MarketingAISystems.py   # grounded generation + the outside check
python3 C10_Menguy_MarketingAISystems.py   # the citation record approval consumes
python3 C11_Menguy_MarketingAISystems.py   # retrieval canaries catch a planted regression
```

Files import each other by module name (for example
`from C01_Menguy_MarketingAISystems import Document`), so run them from inside
this directory.

## Notes

- `C01` is the backbone. `DocMeta` puts the eligibility fields (quarter, channel,
  segment, approval_state, trust, supersedes) first; every later file filters and
  ranks over them. The corpus in `sample_corpus()` is the Q1-teases /
  Q2-supersedes contradiction the chapter keeps returning to.
- `C02` keeps a `Provenance` pointer so a retrieved fact can be traced to a
  specific brief in a specific quarter with a specific approval state. Build it at
  ingestion; it is impossible to reconstruct after an asset ships.
- `C03` enforces two invariants: metadata propagates to every chunk, and atomic
  units (legal clauses) stay whole. A disclaimer split by a chunker is a
  compliance defect that looks like a working pipeline.
- `C04` filters on metadata and trust *before* scoring, so a draft or a piece of
  untrusted UGC never competes. The trust filter is the retrieval-side defense
  against the injected-review problem from chapter 3.
- `C05` models supersession as a relationship and exempts legal by `doc_type`, so
  one ranking gets both rules right: newer brief wins, binding disclaimer survives
  regardless of age. The `__main__` asserts both.
- `C06` is about order, not new scoring: hybrid recall, a cross-encoder for
  precision, then supersession last so relevance never overrules "this quarter
  wins". `load_cross_encoder()` returns a real `sentence-transformers` model when
  available and falls back to a lexical stub offline, so the demo runs either way.
  Swap the last two stages and a superseded brief floats back.
- `C07`'s dictionaries stand in for a graph database or `networkx`. Some brand
  questions are traversals; a retriever that can only embed answers them badly.
  `graph_scoped_retrieve` ties the two together: the traversal picks the eligible
  campaigns by structure, then `retrieve` (C06) runs unchanged over just those
  chunks, with legal and style copy exempt from the scoping so a disclaimer is
  never dropped.
- `C08` is the retrieval loop chapter 9's full campaign agent is built around.
  It is the most capable pattern and the one to reach for last: every step is a
  model call, so it is slower and costlier by the number of hops.
- `C09` shows the division of labor: retrieval supplies and grounds the facts, the
  prompt instructs, and the deterministic check (chapter 3) is the guarantee. The
  drifting-model run shows the check catching an invented "warmest / guaranteed"
  claim that grounding made less likely but did not prevent.
- `C11` is the retrieval analogue of chapter 3's prompt regression suite: every
  incident becomes a permanent canary, so a disclaimer that stopped surviving or a
  superseded brief that slipped back cannot regress unnoticed. The `__main__`
  plants a supersession bug and shows the canary catching it.
- The code reads cleanly rather than being production-hardened. Real embedding
  models, a real vector store and graph DB, caching, and cost controls arrive in
  later chapters (2, 8) and in the companion repository's fuller versions.
