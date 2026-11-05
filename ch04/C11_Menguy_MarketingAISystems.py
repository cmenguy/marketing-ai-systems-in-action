"""Canary set: monitor retrieval quality against known-correct results (Listing 4.11).

A retriever always returns something, so retrieval drifts invisibly: a superseded
brief slips back in, or a disclaimer stops coming back for a class of queries after
a chunking change. The canary set is the retrieval analogue of chapter 3's prompt
regression suite. It is a fixed list of queries, each with the documents that must
come back (a binding disclaimer) and the ones that must not (a superseded brief).
run_canaries flags any query that breaks either rule.

The __main__ runs two canaries seeded from the chapter's own failures against the
healthy sample corpus (both pass), then plants a supersession regression (the Q2
brief no longer supersedes Q1) and shows the canary catching the stale brief.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Canary:
    query: str
    must_include: tuple[str, ...] = ()   # a binding disclaimer, say
    must_exclude: tuple[str, ...] = ()   # a superseded brief


def run_canaries(canaries, retrieve_fn):
    failures = []
    for c in canaries:
        got = {h.meta.campaign_code for h in retrieve_fn(c.query)}
        missing = set(c.must_include) - got      # a dropped disclaimer
        leaked = set(c.must_exclude) & got        # a superseded brief back in
        if missing or leaked:
            failures.append((c.query, missing, leaked))
    return failures


if __name__ == "__main__":
    import re
    from datetime import date
    from dataclasses import replace

    from C01_Menguy_MarketingAISystems import sample_corpus
    from C03_Menguy_MarketingAISystems import chunk_corpus
    from C04_Menguy_MarketingAISystems import bow
    from C06_Menguy_MarketingAISystems import retrieve

    def lexical_score(query: str, text: str) -> float:
        q = set(re.findall(r"[a-z0-9]+", query.lower()))
        t = set(re.findall(r"[a-z0-9]+", text.lower()))
        return float(len(q & t))

    want = {"channel": "email", "segment": "loyalty"}
    today = date.today()

    def retriever(chunks):
        return lambda q: retrieve(q, chunks, want, bow, lexical_score, today)

    canaries = [
        Canary("recycled content substantiation on file",
               must_include=("legal-recycled",)),
        Canary("Cascade spring price and waterproof rating",
               must_exclude=("cascade-spring-2025",)),
    ]

    healthy = chunk_corpus(sample_corpus())
    print("healthy corpus:",
          run_canaries(canaries, retriever(healthy)) or "all canaries pass")

    # Plant a regression: the Q2 brief no longer supersedes Q1, so the stale
    # brief is no longer dropped and the supersession canary should catch it.
    broken_docs = [
        replace(d, meta=replace(d.meta, supersedes=()))
        if d.meta.campaign_code == "cascade-spring-2026" else d
        for d in sample_corpus()
    ]
    broken = chunk_corpus(broken_docs)
    print("after a supersession regression:")
    fails = run_canaries(canaries, retriever(broken))
    for q, missing, leaked in fails:
        print(f"  FAIL {q!r} missing={sorted(missing)} leaked={sorted(leaked)}")
    if not fails:
        print("  (no failures - unexpected)")
