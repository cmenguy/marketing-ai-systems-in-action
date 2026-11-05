"""The decision framework as code: recommend a combination of approaches (2.13).

Given a brand's maturity (approved assets), how fast its voice moves, its monthly
generation volume, and its latency budget, recommend which approaches to combine.
Not a model; the chapter's judgment written down, so a team can argue with it in
a design review instead of reaching for fine-tuning by reflex.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BrandProfile:
    approved_assets: int         # corpus thickness
    voice_changes_per_year: int  # 1 = annual refresh, 4+ = every quarter
    monthly_volume: int          # assets generated per month
    latency_budget_ms: int       # per-generation budget


def recommend(profile: BrandProfile) -> list[str]:
    """Return the approaches to combine, most load-bearing first."""
    plan = ["prompt-time style-guide injection"]   # always the floor

    if profile.approved_assets >= 50:
        plan.append("retrieval over approved copy")
    if profile.approved_assets >= 500:
        plan.append("embedding scorer for brand-voice drift")

    stable = profile.voice_changes_per_year <= 1
    high_volume = profile.monthly_volume >= 100_000
    if profile.approved_assets >= 2_000 and stable and high_volume:
        plan.append("full fine-tuning (voice only; keep retrieval for facts)")

    tight_latency = profile.latency_budget_ms < 300
    if tight_latency and "retrieval over approved copy" in plan:
        plan.append("precompute or cache retrieval to fit the latency budget")

    return plan


if __name__ == "__main__":
    profiles = {
        "new DTC brand": BrandProfile(20, 2, 5_000, 2_000),
        "established, quarterly voice": BrandProfile(3_000, 4, 200_000, 1_500),
        "established, stable voice": BrandProfile(5_000, 1, 500_000, 1_000),
    }
    for name, profile in profiles.items():
        print(name)
        for step in recommend(profile):
            print("  -", step)
