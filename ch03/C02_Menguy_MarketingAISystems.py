"""Two creative-owned layers: rules for the floor, examples for the stance (Listing 3.2).

Brand context enters the prompt two ways, and they fail in opposite directions.
Rules are explicit and auditable but cannot convey the stance. Examples carry
the stance but cannot be audited, and a bad example teaches the wrong voice.
Running both covers each other's failure: even when retrieval hands the model an
off-brand example, the banned-word and register rules still hold the floor.

This builds on chapter 2, which compiled a `BrandVoiceSpec` into a style block
(the rules) and retrieved the nearest approved copy (the examples). Here they
become owned layers of the versioned prompt from C01.
"""

from __future__ import annotations

from C01_Menguy_MarketingAISystems import PromptLayer

# Northpeak's voice, carried over from chapter 2's BrandVoiceSpec.
BRAND = {
    "stance": (
        "Plainspoken and technical. Talk to people who spend time outdoors "
        "and know the difference between a spec and a slogan. No hype."
    ),
    "preferred_terms": ["shell", "face fabric", "rating", "seams", "spec"],
    "banned_terms": [
        "revolutionary", "game-changing", "unleash", "conquer", "ultimate",
    ],
    "max_words": 22,
}

# A few lines that cleared review, the retrieval corpus in miniature.
APPROVED = [
    "The shell is here. A 10K/10K waterproof-breathable rating, taped seams, "
    "and a face fabric that is 63% recycled.",
    "Built for the days the forecast is wrong. The Cascade packs to the size "
    "of a water bottle and weighs under 12 ounces.",
]


def rules_layer(brand: dict) -> PromptLayer:
    """The checkable floor: diction, register, and the stance in one line."""
    lines = [
        f"Voice: {brand['stance']}",
        f"Prefer: {', '.join(brand['preferred_terms'])}.",
        f"Never use: {', '.join(brand['banned_terms'])}.",
        f"Keep sentences under about {brand['max_words']} words.",
    ]
    return PromptLayer("brand_voice", "creative", "\n".join(lines))


def examples_layer(approved: list[str]) -> PromptLayer:
    """The stance the rules cannot spell out, carried by imitation."""
    shown = "\n\n".join(f"Approved:\n{a}" for a in approved)
    body = (
        "Match the voice of these approved examples. Do not copy their "
        "wording:\n\n" + shown
    )
    return PromptLayer("brand_examples", "creative", body)


if __name__ == "__main__":
    print(rules_layer(BRAND).content)
    print("\n---\n")
    # A few varied examples beat many near-duplicates; three or four is plenty.
    print(examples_layer(APPROVED[:3]).content)
