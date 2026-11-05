"""Comparative-claim detection and a safe-language layer (Listing 3.6).

Comparative advertising is its own legal surface, and the one marketers most want
to walk up to the edge of. Claiming your product beats a named rival or is number
one is only defensible with substantiation the brand may not have. At
prompt-engineering time the job is narrow: keep the unsubstantiated comparative
out of the copy, and give the model a safe way to say the true thing instead.

The safe-language list is not censorship. It is the list of claims the brand can
actually stand behind, which is shorter and more useful than the list it is
allowed to make. Chapter 10 covers the FTC / ASA regulatory frame in full.
"""

from __future__ import annotations

import re

from C01_Menguy_MarketingAISystems import PromptLayer

COMPARATIVE = [
    r"\bbetter than\b", r"\bbeats\b",
    r"\bbest[- ]in[- ]class\b", r"\bno one else\b",
]


def check_comparative(copy: str, competitors: list[str]) -> list[str]:
    """Comparative constructions and any named competitor are claim risks."""
    hits = [m for pat in COMPARATIVE
            for m in re.findall(pat, copy, flags=re.I)]
    for name in competitors:
        if re.search(rf"\b{re.escape(name)}\b", copy, flags=re.I):
            hits.append(name)
    return hits


def safe_language_layer() -> PromptLayer:
    """Tell the model the rule up front, and what to say instead."""
    body = (
        "Do not compare to competitors by name or claim to be best or "
        "number one. State defensible facts instead: a temperature rating, "
        "a measured weight, a materials spec."
    )
    return PromptLayer("claim_guardrails", "legal", body)


if __name__ == "__main__":
    competitors = ["Summitline", "Ridgeway"]
    risky = "The Cascade beats Summitline and is the best-in-class shell."
    safe = "The Cascade shell is rated 10K/10K and weighs under 12 ounces."

    for label, copy in (("risky", risky), ("safe", safe)):
        print(f"{label}: {check_comparative(copy, competitors)}")
