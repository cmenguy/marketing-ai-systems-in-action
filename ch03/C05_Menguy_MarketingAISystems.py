"""Regenerating on a failed legal check by feeding the specific failure back (Listing 3.5).

The legal gate does not just reject a draft; it says what is wrong. The checks
in Listing 3.4 return structured detail: `verify_required` gives the names of the
phrases that are missing, and `find_unsubstantiated` gives the words that fired.
That detail is enough to write the model a specific correction and try again.

Regeneration is a bounded retry. After a set number of attempts with explicit
feedback, a still-failing draft escalates to a person. The deterministic check
stays the gate; the loop only tries to satisfy it automatically, and nothing
returns until the check comes back clean.
"""

from __future__ import annotations

from typing import Callable

from C04_Menguy_MarketingAISystems import find_unsubstantiated, verify_required


class NeedsHuman(Exception):
    """Retries were spent without a draft that clears the legal check."""


def legal_correction(copy: str) -> str:
    """Turn the structured check failures into an instruction for the next call."""
    missing = verify_required(copy)
    claims = find_unsubstantiated(copy)
    notes = []
    if missing:
        notes.append("Missing required: " + ", ".join(missing)
                     + ". Include each one.")
    if claims:
        notes.append("Remove unsubstantiated claims: " + ", ".join(claims)
                     + ". State a defensible spec instead.")
    return "The previous draft was rejected. " + " ".join(notes)


def regenerate(brief: str, generate: Callable[[str], str],
               max_tries: int = 2) -> str:
    """Generate, check, and feed the specific failure back until it passes."""
    copy = ""
    for _ in range(max_tries + 1):
        copy = generate(brief)
        if not verify_required(copy) and not find_unsubstantiated(copy):
            return copy                                 # passed the legal gate
        brief = brief + "\n\n" + legal_correction(copy)
    raise NeedsHuman(copy)


if __name__ == "__main__":
    # A stub model: the first draft fails two checks, the corrected retry passes.
    drafts = iter([
        "The Cascade shell is the best jacket for the storms ahead. A 63% "
        "recycled face fabric and taped seams. Spring pricing through May 31.",
        "The Cascade shell is here. A 10K/10K waterproof-breathable rating and "
        "a 63% recycled face fabric. Spring pricing through May 31.",
    ])

    def fake_generate(brief: str) -> str:
        if "rejected" in brief:
            print("correction fed back:\n  " + brief.splitlines()[-1])
        return next(drafts)

    final = regenerate("Launch email for the Cascade shell.", fake_generate)
    print("shipped:", final)
