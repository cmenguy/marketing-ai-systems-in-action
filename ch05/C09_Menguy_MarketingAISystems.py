"""Capturing an editor correction as a preference pair and a test case (Listing 5.9).

When a reviewer rewrites a draft instead of rejecting it outright, they hand you
the cleanest training data the system produces: a rejected draft and the approved
rewrite that replaced it, a preference pair labeled by the human who owns the
judgment. Capture it structured, at the moment it happens, with enough context to
be useful three ways.

The same record feeds chapter 2's preference tuning (DPO), chapter 3's regression
suite (a permanent test case), and chapter 11's calibration (a human-labeled
signal). The `failure_tag` is what makes the stream analyzable rather than a heap.
"""

from __future__ import annotations

from dataclasses import dataclass

from C01_Menguy_MarketingAISystems import GenerationSpec, sample_facts


@dataclass(frozen=True)
class EditorCorrection:
    spec: GenerationSpec
    rejected: str            # the draft the editor cut
    chosen: str              # the approved rewrite
    failure_tag: str         # "off_voice" | "weak_hook" | "claim_fix"
    reviewer: str            # which flow: brand | creative | legal


def to_preference_pair(c):
    return {"prompt": c.spec.brief, "chosen": c.chosen, "rejected": c.rejected}


def to_regression_case(c):
    return {"brief": c.spec.brief, "channel": c.spec.channel,
            "must_not_repeat": c.rejected, "failure": c.failure_tag}


if __name__ == "__main__":
    spec = GenerationSpec(
        brief="Win back the lapsed segment on the Cascade launch.",
        segment="lapsed_12mo", channel="email",
        campaign_code="cascade-spring-2026", facts=sample_facts(),
        prompt_fingerprint="copy.email:v3")

    correction = EditorCorrection(
        spec=spec,
        rejected="Don't miss your last chance at the season's best shell!",
        chosen=("It has been a while. The Cascade shell is new this spring: a "
                "10K/10K waterproof-breathable rating and a 63% recycled face "
                "fabric. Spring pricing runs through May 31."),
        failure_tag="off_voice",
        reviewer="brand")

    pair = to_preference_pair(correction)
    case = to_regression_case(correction)
    print("preference pair ->", {k: pair[k][:40] for k in pair})
    print("regression case ->", case["failure"], "|", case["channel"])

    assert pair["chosen"] != pair["rejected"], "a pair has a better and a worse side"
    assert case["failure"] == "off_voice", "the tag makes the stream analyzable"
    print("OK: one correction becomes a preference pair and a regression case.")
