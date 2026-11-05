"""The generation spec: one structured, reproducible unit of work (Listing 5.1).

The demo's input was a prompt string. A production system's input is a structured
specification, because a string is not reproducible, not auditable, and not
something three teams can co-own. The spec carries everything the pipeline needs
to generate one asset, and everything the downstream stages need to check and
approve it: which brief, which segment, which channel, the approved facts
retrieval grounded it in, and the provenance for each of those facts.

`Citation` here is the same shape chapter 4 produced from grounded retrieval; it
is restated so this chapter's code runs on its own. In production the spec's
`facts` are the real citations handed over by the retrieval layer.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Citation:
    """Chapter 4's provenance record: a grounded fact and where it came from."""

    source_id: str            # the chunk the fact came from
    quarter: str
    approval_state: str
    fact: str


SEGMENTS = {
    "loyalty": "Has bought before. Lead with the product.",
    "lapsed_12mo": "No purchase in 12 months. Lead with what changed.",
}


@dataclass(frozen=True)
class GenerationSpec:
    brief: str                 # the approved campaign brief
    segment: str               # "loyalty" | "lapsed_12mo"
    channel: str               # keys chapter 3's CHANNELS registry
    campaign_code: str         # ties the asset to its campaign
    facts: list[Citation]      # chapter 4's grounded, cited facts
    prompt_fingerprint: str    # chapter 3's versioned prompt id

    def audience_note(self) -> str:
        return SEGMENTS[self.segment]


def sample_facts() -> list[Citation]:
    """The Cascade facts, grounded and cited, as retrieval would hand them over."""
    return [
        Citation("cascade-spring-2026:brief#2", "2026-Q2", "approved",
                 "10K/10K waterproof-breathable rating, taped seams"),
        Citation("cascade-spring-2026:brief#3", "2026-Q2", "approved",
                 "face fabric is 63% recycled"),
        Citation("cascade-spring-2026:brief#4", "2026-Q2", "approved",
                 "spring pricing runs through May 31"),
        Citation("legal-recycled-substantiation#0", "2024-Q1", "approved",
                 "recycled-content claims require substantiation on file"),
    ]


if __name__ == "__main__":
    spec = GenerationSpec(
        brief="Launch the Cascade waterproof shell for spring.",
        segment="lapsed_12mo",
        channel="email",
        campaign_code="cascade-spring-2026",
        facts=sample_facts(),
        prompt_fingerprint="copy.email:v3:a1b2c3d4e5f6",
    )
    print(f"segment={spec.segment}  channel={spec.channel}")
    print(f"framing: {spec.audience_note()}")
    print(f"{len(spec.facts)} grounded facts, each with provenance:")
    for c in spec.facts:
        print(f"  [{c.source_id}] {c.quarter} {c.approval_state}: {c.fact}")
    assert spec.audience_note().startswith("No purchase")
    print("OK: the spec is complete and pinned to its prompt version.")
