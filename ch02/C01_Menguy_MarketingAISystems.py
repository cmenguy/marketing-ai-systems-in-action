"""On-brand as an engineering target: a checkable brand voice spec (Listing 2.1).

"On-brand" is a judgment made by people. A system cannot act on a judgment; it
needs the judgment broken into properties it can push on and check. This models
Northpeak's voice as such a spec. The example corpus the other listings reuse is
in C02. Chapter 3 turns this spec into production prompt components; Chapter 5
scores generated copy against it on the output side.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BrandVoiceSpec:
    """Northpeak's voice, decomposed into dimensions a system can target."""

    brand: str
    stance: str                      # the rhetorical posture, in one line
    preferred_terms: list[str]       # diction to reach for
    banned_terms: list[str]          # diction that reads as off-brand
    max_sentence_words: int          # a register target, not a hard rule
    allow_exclamations: bool         # Northpeak: no invented urgency


def northpeak_spec() -> BrandVoiceSpec:
    """The running example's voice, as an engineering target."""
    return BrandVoiceSpec(
        brand="Northpeak",
        stance=(
            "Plainspoken and technical. Talk to people who spend time "
            "outdoors and know the difference between a spec and a slogan. "
            "No hype, no invented urgency."
        ),
        preferred_terms=["shell", "face fabric", "rating", "seams", "spec"],
        banned_terms=[
            "revolutionary", "game-changing", "unleash",
            "supercharge", "conquer", "ultimate",
        ],
        max_sentence_words=22,
        allow_exclamations=False,
    )


if __name__ == "__main__":
    spec = northpeak_spec()
    print(f"{spec.brand}: {spec.stance}")
