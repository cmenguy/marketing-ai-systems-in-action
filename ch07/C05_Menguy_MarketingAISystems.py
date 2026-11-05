"""Listing 7.5 - A deadline-aware dispatcher that picks a strategy from the budget.

The channel sets the latency budget, and the budget picks the strategy. A single
generation call is commonly a few hundred milliseconds to several seconds, so the
model does not fit inside the tightest budgets (RTB display, on-site). Those are
served from precomputed content the cache holds; live generation belongs to the
generous surfaces (email, push). `dispatch` encodes exactly that: try the cache,
allow a live call only when the budget covers the model's p99 latency, run the
checks on what comes back before it is cached or shown, and otherwise fall back
to a safe template.

Runs standalone with stub generate/checks/template:
    python3 C05_Menguy_MarketingAISystems.py
"""

from __future__ import annotations

from typing import Callable

# Budgets in milliseconds, by surface.
BUDGET_MS = {"rtb_display": 100, "onsite": 300,
             "email": 60_000, "push": 30_000}


def dispatch(surface: str, request, cache, generate: Callable,
             passes: Callable, template: Callable, gen_p99_ms: int = 1500):
    """Return (asset, strategy) where strategy is 'cache' | 'live' | 'template'."""
    budget = BUDGET_MS[surface]
    hit = cache.get(request)
    if hit is not None:
        return hit, "cache"
    if budget >= gen_p99_ms:
        asset = generate(request)
        if passes(asset, request):
            cache.put(request, asset)
            return asset, "live"
    return template(request), "template"


if __name__ == "__main__":
    from datetime import date
    from C01_Menguy_MarketingAISystems import build_profile, sample_events
    from C02_Menguy_MarketingAISystems import ConsentState
    from C03_Menguy_MarketingAISystems import sample_catalog, stub_embed
    from C04_Menguy_MarketingAISystems import (
        build_request, sample_campaign, stub_retrieve)
    from C06_Menguy_MarketingAISystems import (
        VariantCache, stub_generate, stub_passes, warm)

    catalog = sample_catalog()
    campaign = sample_campaign(catalog)
    card = build_profile("cust-1041", sample_events(), date(2026, 4, 1))
    consent = ConsentState(purposes=frozenset({"personalization"}))

    def request_for(channel):
        return build_request(card, consent, catalog, stub_retrieve, stub_embed,
                             channel, campaign)

    def template(request):
        return "[safe template: the Cascade shell is here]"

    def hallucinating(request):
        return "Cascade shell: 40% off, today only."

    cache = VariantCache()
    warm([request_for("onsite")], cache, stub_generate, stub_passes)

    runs = [
        ("rtb_display", "display", stub_generate),   # too tight -> template
        ("onsite", "onsite", stub_generate),         # warmed -> cache
        ("email", "email", stub_generate),           # generous -> live, cached
        ("email", "email", stub_generate),           # second send -> cache
        ("push", "push", hallucinating),             # fails the checks
    ]
    for surface, channel, gen in runs:
        asset, how = dispatch(surface, request_for(channel), cache, gen,
                              stub_passes, template)
        print(f"{surface:>12} -> {how:>8}: {asset}")
    print("cache entries:", len(cache), "(the failed variant was never stored)")
