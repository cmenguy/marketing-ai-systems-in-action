"""A regression harness with the brand-voice scorer as the oracle (Listing 3.9).

You cannot test a marketing prompt against a golden string: a thousand outputs
are all correct and the model produces a new one every time. What you can assert
is that the output scores on-brand against an oracle, the brand-voice scorer from
chapter 2 (an embedding centroid, or a trained classifier), plus the
deterministic legal check. That is the test assertion.

The scenario this catches: your prompt did not change, the model under it did,
and the same instructions now drift off the voice. Run this harness as a gate on
every model change, keep a baseline, and block a rollout when a score drops past
a tolerance, the way a failing test blocks a deploy.

The `generate` function is injected, so a stub stands in for the model in CI and
the real model runs in the pre-deploy check. `brand_score` here is a deterministic
stand-in for the chapter-2 embedding scorer so the harness runs with no model or
API key; the threshold is calibrated against human ratings in chapter 11.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from C02_Menguy_MarketingAISystems import BRAND
from C04_Menguy_MarketingAISystems import find_unsubstantiated, verify_required
from C06_Menguy_MarketingAISystems import check_comparative


@dataclass(frozen=True)
class PromptTest:
    brief: str
    channel: str
    min_score: float          # the on-brand floor for a pass


@dataclass(frozen=True)
class RegressionResult:
    brief: str
    channel: str
    score: float
    legal_missing: list[str]
    claims: list[str]
    passed: bool


def brand_score(copy: str) -> float:
    """Stand-in for chapter 2's embedding scorer: reward on-brand, penalize off."""
    score = 0.8
    lower = copy.lower()
    for term in BRAND["banned_terms"]:
        if term in lower:
            score -= 0.25
    if "!" in copy:
        score -= 0.1
    if any(term in lower for term in BRAND["preferred_terms"]):
        score += 0.1
    return max(0.0, min(1.0, score))


def run_regression(template, tests, generate: Callable, scorer=brand_score,
                   competitors=()):
    """Score each test brief against the oracle and the legal checks."""
    results = []
    for t in tests:
        copy = generate(template, t.brief, t.channel)
        score = scorer(copy)
        legal_missing = verify_required(copy)
        claims = (find_unsubstantiated(copy)
                  + check_comparative(copy, competitors))
        passed = (score >= t.min_score
                  and not legal_missing and not claims)
        results.append(RegressionResult(
            brief=t.brief, channel=t.channel, score=score,
            legal_missing=legal_missing, claims=claims,
            passed=passed))
    return results


def regressions(baseline, candidate, tolerance: float = 0.05) -> list[str]:
    """Which tests dropped past the tolerance from baseline to candidate."""
    by_brief = {r.brief: r.score for r in baseline}
    return [c.brief for c in candidate
            if by_brief.get(c.brief, 0.0) - c.score > tolerance]


if __name__ == "__main__":
    # Two "model versions" as stubbed generators: v2 drifts off-brand.
    def model_v1(template, brief, channel):
        return ("The Cascade shell has a 10K/10K waterproof rating and a "
                "63% recycled face fabric. Spring pricing through May 31.")

    def model_v2(template, brief, channel):
        return "The ultimate waterproof shell. Conquer any storm!"

    # One sample test, run through the harness (mirrors Listing 3.9).
    one = [PromptTest("Launch the Cascade shell, loyalty segment.", "email", 0.7)]
    result = run_regression(None, one, model_v1)[0]
    print("single test:", result.passed, round(result.score, 2))

    # A suite across two model versions: the drift shows up as a regression.
    tests = [
        PromptTest("Launch the Cascade shell, loyalty segment.", "email", 0.7),
        PromptTest("Announce spring pricing, lapsed segment.", "sms", 0.7),
    ]
    base = run_regression(None, tests, model_v1)
    cand = run_regression(None, tests, model_v2)
    print("baseline pass:", [r.passed for r in base])
    print("candidate pass:", [r.passed for r in cand])
    print("regressions:", regressions(base, cand))
