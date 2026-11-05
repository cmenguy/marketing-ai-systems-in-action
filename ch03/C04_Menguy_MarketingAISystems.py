"""Required phrases go in the prompt and are verified after generation (Listing 3.4).

Legal correctness in copy has two shapes. Some things must be present (a
disclaimer, a substantiated rating, an opt-out); others must be absent (an
unsubstantiated superlative, a regulated word). Both belong partly in the prompt
and partly in a check that does not trust the prompt.

Telling the model to include the rating works most of the time, and most of the
time is not the bar for a legal requirement. The verifier is the guarantee; the
prompt instruction only raises the rate at which copy passes it on the first try.
This is the deterministic legal check chapter 1 names as present-or-not.
"""

from __future__ import annotations

import re

from C01_Menguy_MarketingAISystems import PromptLayer

REQUIRED = {
    "waterproof rating": r"\d+K/\d+K",
    "recycled percentage": r"\d+%\s+recycled",
    "promo end date": r"through\s+\w+\s+\d",
}

UNSUBSTANTIATED = [
    r"\bbest\b", r"\b#\s?1\b", r"\bguaranteed\b",
    r"\bproven\b", r"\bunbeatable\b",
]


def required_phrases_layer() -> PromptLayer:
    """Instruct the model to include each required phrase (legal-owned)."""
    reqs = "\n".join(f"- include a {name}" for name in REQUIRED)
    return PromptLayer(
        "legal_required", "legal",
        "Every claim must be substantiated. This copy must:\n" + reqs,
    )


def verify_required(copy: str) -> list[str]:
    """The names of required phrases the model was told to include but did not."""
    return [name for name, pat in REQUIRED.items()
            if not re.search(pat, copy)]


def find_unsubstantiated(copy: str) -> list[str]:
    """Superlatives that need substantiation the copy is not carrying."""
    hits: list[str] = []
    for pat in UNSUBSTANTIATED:
        hits += re.findall(pat, copy, flags=re.I)
    return hits


if __name__ == "__main__":
    good = ("The Cascade shell has a 10K/10K waterproof rating and a face "
            "fabric that is 63% recycled. Spring pricing runs through May 31.")
    bad = "The best waterproof shell you can buy. Guaranteed to keep you dry."

    for label, copy in (("good", good), ("bad", bad)):
        print(f"{label}: missing={verify_required(copy)} "
              f"claims={find_unsubstantiated(copy)}")
