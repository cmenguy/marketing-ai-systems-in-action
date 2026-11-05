"""Listing 8.8 - A per-tenant monthly statement built from the ledger.

The ledger is for the vendor. The client sees a statement: the handful of numbers a
brand's marketing lead and procurement actually read. How many assets the system
produced, how many model calls that took, what share was served from cache, and
what it cost, broken out by campaign. The cache-hit rate belongs on the statement
because it explains why the bill is lower than the asset count suggests, and it is
the lever the client can pull, by reusing briefs and running campaigns that share
context, to lower it further.

Runs with no API key and nothing installed (standard library only).
"""
from __future__ import annotations

from C05_Menguy_MarketingAISystems import TenantContext
from C07_Menguy_MarketingAISystems import Usage, meter, rollup


def tenant_statement(ledger: list, tenant_id: str) -> dict:
    rows = [u for u in ledger if u.tenant_id == tenant_id]
    calls = [u for u in rows if not u.cached]
    hits = [u for u in rows if u.cached]
    by_campaign = rollup(calls, lambda u: u.campaign_code)
    served = len(rows)
    return {
        "tenant_id": tenant_id,
        "assets_served": served,
        "model_calls": len(calls),
        "cache_hit_rate": round(len(hits) / served, 3) if served else 0.0,
        "cost_usd": round(sum(by_campaign.values()), 2),
        "by_campaign": {c: round(v, 2) for c, v in by_campaign.items()},
    }


if __name__ == "__main__":
    ledger: list[Usage] = []
    north = TenantContext("northpeak", "corpus-2026Q2")

    # One launch: 96 segment-level heroes generated, then served 50,000 times.
    for i in range(96):
        meter(ledger, north, "cascade-spring", f"hero-{i}", "final", 1700, 200)
    for i in range(50_000):
        meter(ledger, north, "cascade-spring", f"hero-{i % 96}",
              "final", 0, 0, cached=True)
    # A second, smaller campaign.
    for i in range(40):
        meter(ledger, north, "weekly-restock", f"note-{i}", "draft", 1500, 200)

    stmt = tenant_statement(ledger, "northpeak")
    for key, value in stmt.items():
        print(f"{key}: {value}")
