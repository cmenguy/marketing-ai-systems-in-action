"""Listing 8.2 - Routing a batch to the cheap async tier, and costing it first.

Most campaign work has a deadline hours away rather than a customer waiting, so it
belongs on a provider's asynchronous batch tier (about half price, results in
hours). Only work with someone waiting stays on the synchronous full-price path.
Costing the batch before it runs turns a launch into a line item you approve
rather than a surprise on the invoice, and a spend ceiling stops a batch that
would blow its budget before it spends the money.

Runs with no API key and nothing installed (standard library only).
"""
from __future__ import annotations

from C01_Menguy_MarketingAISystems import price_campaign

BATCH_DISCOUNT = 0.5     # async tier: about half price, hours not seconds


def plan_batch(assets: int, urgent: bool, ceiling_usd: float,
               n: int = 4) -> dict:
    """Pick the tier, project the bill, and flag a batch over its ceiling."""
    rate = 1.0 if urgent else BATCH_DISCOUNT
    projected = price_campaign(assets, n) * rate
    return {
        "tier": "sync" if urgent else "async",
        "assets": assets,
        "projected_usd": round(projected, 2),
        "over_ceiling": projected > ceiling_usd,
    }


def split_on_ceiling(assets: int, urgent: bool, ceiling_usd: float,
                     n: int = 4) -> list[int]:
    """Split a batch into chunks that each fit under the ceiling, so a large
    refresh is admitted in pieces rather than refused outright."""
    rate = 1.0 if urgent else BATCH_DISCOUNT
    per_asset = price_campaign(1, n) * rate
    if per_asset == 0:
        return [assets]
    per_chunk = max(1, int(ceiling_usd // per_asset))
    chunks, remaining = [], assets
    while remaining > 0:
        take = min(per_chunk, remaining)
        chunks.append(take)
        remaining -= take
    return chunks


if __name__ == "__main__":
    refresh = plan_batch(40_000, urgent=False, ceiling_usd=1_000)
    print("quarterly refresh (non-urgent):", refresh)

    live = plan_batch(500, urgent=True, ceiling_usd=100)
    print("closing send window (urgent):  ", live)

    over = plan_batch(200_000, urgent=False, ceiling_usd=1_000)
    print("over ceiling:", over["over_ceiling"],
          "-> split into", split_on_ceiling(200_000, False, 1_000), "chunks")
