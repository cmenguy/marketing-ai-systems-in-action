"""Listing 8.1 - A cost model: price an asset and a campaign from a rate card.

Generation cost is one of the few things you can compute exactly in advance:
count the calls, count the tokens, multiply by the rate card. The prices here are
representative placeholders; replace them with your provider's current rate card.
The structure is the point, not the digits.

Runs with no API key and nothing installed (standard library only).
"""
from __future__ import annotations

# USD per 1,000,000 tokens, as (input_price, output_price).
# Tiers are names, not providers: "draft" is a small fast model, "final" a strong
# one. Which model sits behind each tier is a decision you remake as prices move.
RATE_CARD = {
    "draft": (0.40, 1.60),
    "final": (3.00, 15.00),
    "judge": (3.00, 15.00),
    "embed": (0.0, 0.0),      # a small encoder you host; near-free per call
}

# Tokens a single call of each stage spends: (tier, input_tokens, output_tokens).
STAGE_TOKENS = {
    "draft":    ("draft", 1500, 200),
    "critique": ("final", 1700, 200),
    "judge":    ("judge", 1800, 150),
}


def call_cost(tier: str, n_in: int, n_out: int) -> float:
    """Cost of one model call at a tier, from the rate card."""
    price_in, price_out = RATE_CARD[tier]
    return (n_in * price_in + n_out * price_out) / 1_000_000


def price_asset(n: int = 4, judge_rate: float = 0.15) -> float:
    """Cost of one generated asset: N cheap drafts, one critique, and a judge
    on the fraction of assets that land near the gate's threshold."""
    plan = [("draft", n), ("critique", 1), ("judge", judge_rate)]
    total = 0.0
    for stage, count in plan:
        tier, n_in, n_out = STAGE_TOKENS[stage]
        total += count * call_cost(tier, n_in, n_out)
    return total


def price_campaign(assets: int, n: int = 4, judge_rate: float = 0.15) -> float:
    """The campaign bill is the per-asset cost times the asset count."""
    return assets * price_asset(n, judge_rate)


def price_asset_all_final(n: int = 4) -> float:
    """The naive pipeline: every call on the strong model, no routing.
    Shown only to size the saving routing buys."""
    draft = n * call_cost("final", *STAGE_TOKENS["draft"][1:])
    critique = call_cost("final", *STAGE_TOKENS["critique"][1:])
    return draft + critique


if __name__ == "__main__":
    routed = price_asset()
    naive = price_asset_all_final()
    routed_gen = routed - 0.15 * call_cost("judge", 1800, 150)  # drafts+critique
    print(f"per asset, routed:          ${routed:.4f}")
    print(f"per asset, all-final naive: ${naive:.4f}")
    print(f"campaign of 40,000, routed: ${price_campaign(40_000):,.0f}")
    print(f"campaign of 40,000, naive:  ${40_000 * naive:,.0f}")
    cut = 1 - routed_gen / naive
    print(f"routing cuts the generation bill by ~{cut:.0%}")
