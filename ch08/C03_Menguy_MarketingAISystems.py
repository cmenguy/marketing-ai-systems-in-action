"""Listing 8.3 - A router that picks a model tier by stage and risk.

Routing sends each call to the cheapest model that can do that call's job.
Drafting goes to a small model because selection cleans up after it; the critique
and the judge stay on a strong one because nothing cleans up after them. Risk and
channel promote a draft to the strong tier where a weak first attempt would cost a
retry or a lost placement, and the audience sets N, the draft count.

Tiers are names the runtime resolves to whatever model you have chosen, so no
provider's model id is wired through the pipeline. Runs with no API key.
"""
from __future__ import annotations

from dataclasses import dataclass

MODEL_TIERS = {           # tier -> the handle your runtime resolves
    "draft": "small-fast",
    "final": "large-strong",
    "judge": "large-strong",
}
AUDITED_CHANNELS = frozenset({"display"})   # reviewed before it can serve


@dataclass(frozen=True)
class GenerationSpec:
    """The unit of work the pipeline generates; only the fields the router reads
    are shown here. In the full system this is the shared spec."""
    channel: str
    segment: str
    campaign_code: str = ""
    prompt_fingerprint: str = ""


def route(stage: str, spec: GenerationSpec, risk: str) -> str:
    """Return the model tier for this stage, promoting a draft to the strong
    tier when the asset's risk or channel warrants paying for a better start."""
    if stage != "draft":
        return MODEL_TIERS["final"]                 # critique and judge
    if risk == "high" or spec.channel in AUDITED_CHANNELS:
        return MODEL_TIERS["final"]                 # draft on the strong tier
    return MODEL_TIERS["draft"]                      # the common case


def draft_count(spec: GenerationSpec) -> int:
    """N is the other cost knob: a harder segment samples more drafts."""
    return 8 if spec.segment == "lapsed_12mo" else 4


if __name__ == "__main__":
    cases = [
        ("draft", GenerationSpec("email", "loyalty"), "low"),
        ("draft", GenerationSpec("display", "loyalty"), "low"),
        ("draft", GenerationSpec("sms", "lapsed_12mo"), "high"),
        ("critique", GenerationSpec("email", "loyalty"), "low"),
    ]
    for stage, spec, risk in cases:
        tier = route(stage, spec, risk)
        n = draft_count(spec) if stage == "draft" else 1
        print(f"{stage:9} {spec.channel:8} {spec.segment:11} "
              f"risk={risk:4} -> {tier:12} N={n}")
