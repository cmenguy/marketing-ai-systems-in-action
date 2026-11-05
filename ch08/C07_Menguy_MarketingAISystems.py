"""Listing 8.7 - Metering every call and rolling the ledger up by any key.

A vendor has to answer how much the system cost for this tenant, this month, and
the answer is not the total divided by the tenant count. Every call is tagged at
the moment it happens with the tenant, campaign, asset, tier, and token counts and
written to a ledger. The ledger stores the facts and derives the money with the
same `call_cost` the pricing model uses, so a rate-card change does not strand a
stored dollar figure. A cache hit is billed at zero against the fill that paid for
it. Rolling up by tenant gives the invoice, by campaign the per-campaign cost, by
asset the outlier an engineer chasing a spike needs.

Runs with no API key and nothing installed (standard library only).
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Callable

from C01_Menguy_MarketingAISystems import call_cost
from C05_Menguy_MarketingAISystems import TenantContext


@dataclass(frozen=True)
class Usage:
    tenant_id: str
    campaign_code: str
    asset_id: str
    tier: str
    n_in: int
    n_out: int
    cached: bool              # a cache hit spent no tokens


def meter(ledger: list, ctx: TenantContext, campaign_code: str,
          asset_id: str, tier: str, n_in: int, n_out: int,
          cached: bool = False) -> None:
    """Append one row per call, tagged with the tenant it was for."""
    ledger.append(Usage(ctx.tenant_id, campaign_code, asset_id,
                         tier, n_in, n_out, cached))


def cost_of(u: Usage) -> float:
    if u.cached:
        return 0.0                               # the fill already paid
    return call_cost(u.tier, u.n_in, u.n_out)


def rollup(ledger: list, key: Callable[[Usage], object]) -> dict:
    """Roll the ledger up by any key: tenant, campaign, or asset."""
    totals: dict[object, float] = defaultdict(float)
    for u in ledger:
        totals[key(u)] += cost_of(u)
    return dict(totals)


if __name__ == "__main__":
    ledger: list[Usage] = []
    north = TenantContext("northpeak", "corpus-2026Q2")
    ridge = TenantContext("ridgeline", "corpus-2026Q2")

    # Northpeak generates a hero once, then serves it from cache many times.
    meter(ledger, north, "cascade-spring", "hero-loyalty", "final", 1700, 200)
    for _ in range(3):
        meter(ledger, north, "cascade-spring", "hero-loyalty",
              "final", 0, 0, cached=True)
    meter(ledger, ridge, "trail-launch", "hero-core", "final", 1700, 200)

    print("by tenant:  ", {k: round(v, 4)
                           for k, v in rollup(ledger, lambda u: u.tenant_id).items()})
    print("by campaign:", {k: round(v, 4)
                           for k, v in rollup(ledger, lambda u: u.campaign_code).items()})
