"""The composite gate: block on legal, route on voice, decide (Listing 5.6).

Quality controls come in two kinds the gate treats differently. Deterministic
format and legal checks are guarantees that hard-block a failing asset; the
brand-voice score is a calibrated proxy that routes rather than blocks. Confusing
the two either buries reviewers in false positives (block on the fuzzy score) or
ships the liability (treat the legal check as advisory).

The gate runs every check, then decides among three outcomes: ship to approval,
regenerate with the specific failure attached (while retries remain), or hold for
a human. `legal_checks` restates chapter 3's `verify_required`,
`find_unsubstantiated`, and `check_comparative` as CheckResults.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from C04_Menguy_MarketingAISystems import CheckResult, voice_check
from C05_Menguy_MarketingAISystems import format_checks

REQUIRED = {"waterproof rating": r"\d+K/\d+K",
            "promo end date": r"through\s+\w+\s+\d"}
UNSUBSTANTIATED = [r"\bbest\b", r"\bunbeatable\b", r"\bguaranteed\b"]
COMPARATIVE = [r"\bbetter than\b", r"\bbeats\b"]


def legal_checks(copy, competitors):
    """Chapter 3's deterministic legal checks, as CheckResults."""
    missing = [n for n, pat in REQUIRED.items() if not re.search(pat, copy)]
    claims = [m for pat in UNSUBSTANTIATED for m in re.findall(pat, copy, re.I)]
    comp = [m for pat in COMPARATIVE for m in re.findall(pat, copy, re.I)]
    comp += [c for c in competitors if re.search(rf"\b{re.escape(c)}\b", copy, re.I)]
    return [
        CheckResult("required_phrases", not missing, None,
                    "present" if not missing else f"missing: {missing}"),
        CheckResult("unsubstantiated", not claims, None,
                    "clean" if not claims else f"claims: {claims}"),
        CheckResult("comparative_claim", not comp, None,
                    "clean" if not comp else f"comparisons: {comp}"),
    ]


@dataclass(frozen=True)
class Ctx:
    threshold: float = 0.30
    competitors: tuple = ("Summitline",)
    tries_left: int = 1
    brand_c=None
    neg_c=None


@dataclass(frozen=True)
class QualityReport:
    results: list
    decision: str             # "ship" | "regenerate" | "hold"

    @property
    def ok(self):
        return self.decision == "ship"

    def correction(self):
        fails = [r.detail for r in self.results if not r.passed]
        return "\n\nThe previous draft failed: " + "; ".join(fails)


def gate(copy, spec, ctx):
    results = format_checks(copy, spec)
    results.append(voice_check(copy, ctx.brand_c, ctx.neg_c, ctx.threshold))
    results += legal_checks(copy, ctx.competitors)
    hard_fail = any(not r.passed and r.name != "brand_voice" for r in results)
    voice_fail = not next(r.passed for r in results if r.name == "brand_voice")
    if hard_fail:
        decision = "regenerate" if ctx.tries_left else "hold"
    elif voice_fail:
        decision = "hold"
    else:
        decision = "ship"
    return QualityReport(results, decision)


if __name__ == "__main__":
    from C01_Menguy_MarketingAISystems import GenerationSpec, sample_facts

    spec = GenerationSpec("brief", "loyalty", "email",
                          "cascade-spring-2026", sample_facts(), "v3")

    bad = "The best shell for spring. A 63% recycled face fabric."
    clean = ("The shell is here. A 10K/10K waterproof-breathable rating, taped "
             "seams, and a 63% recycled face fabric. Spring pricing runs "
             "through May 31.")

    print("bad draft ->", gate(bad, spec, Ctx()).decision)      # regenerate
    print("clean draft ->", gate(clean, spec, Ctx()).decision)  # ship
    print("clean, no retries ->",
          gate(bad, spec, Ctx(tries_left=0)).decision)          # hold

    assert gate(bad, spec, Ctx()).decision == "regenerate"
    assert gate(clean, spec, Ctx()).decision == "ship"
    assert gate(bad, spec, Ctx(tries_left=0)).decision == "hold"
    print("OK: legal hard-blocks, the clean draft ships, out-of-retries holds.")
