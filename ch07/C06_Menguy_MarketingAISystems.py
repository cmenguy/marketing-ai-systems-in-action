"""Listing 7.6 - A bucket-level cache whose key encodes offer window and corpus version.

Cache on the customer and the hit rate collapses: every customer is unique, so
the key is unique, so nothing is reused. Cache at the granularity of the thing
that repeats, the bucket (segment, price band, leading category), and thousands
of customers share a key. The key also carries what makes a variant valid: the
items it features, the channel, the offer window, and the corpus version
(chapter 4). When the corpus refreshes or the offer expires the old key is never
requested again, so correctness needs no invalidation step; `reclaim` only frees
the memory.

The bucket is computed from the consent-filtered profile, so the key holds no
identifier and a customer who withheld personalization lands in the same
"default" bucket as everyone else who did. `warm` is the one fill path: it runs
before a launch for every populated bucket and on an event for a single one, and
nothing it generates is stored unless it passes the gate.

Runs standalone:  python3 C06_Menguy_MarketingAISystems.py
"""

from __future__ import annotations

import re
from typing import Callable, Iterable


def bucket_of(profile: dict) -> str:
    """The cacheable granularity: a bucket, never the individual customer."""
    lead = (profile.get("top_categories") or ("none",))[0]
    return ":".join([profile.get("segment") or "default",
                     profile.get("price_band") or "any", lead])


def cache_key(request) -> str:
    c = request.campaign
    items = "+".join(i.code for i in request.items)
    return "|".join([bucket_of(request.profile), items,
                     request.channel, c.offer_id, c.corpus_version])


class VariantCache:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    def get(self, request):
        return self._store.get(cache_key(request))

    def put(self, request, asset: str) -> None:
        self._store[cache_key(request)] = asset

    def reclaim(self, live_version: str) -> int:
        """Free variants grounded in a corpus version that is no longer live.
        They were already unreachable; this is housekeeping, and a TTL set to
        the offer's end date does the same job in a real cache."""
        stale = [k for k in self._store if not k.endswith(live_version)]
        for k in stale:
            del self._store[k]
        return len(stale)

    def __len__(self) -> int:
        return len(self._store)


def warm(requests: Iterable, cache: VariantCache, generate: Callable,
         passes: Callable) -> int:
    """Fill the cache ahead of the request path. Returns how many were stored."""
    stored = 0
    for request in requests:
        if cache.get(request) is None:
            asset = generate(request)
            if passes(asset, request):     # the gate sits before every write
                cache.put(request, asset)
                stored += 1
    return stored


def stub_generate(request, timeout_ms: int | None = None) -> str:
    """Stands in for the model: a line built from the bucket and the facts."""
    item = request.items[0].title if request.items else "Northpeak"
    facts = " ".join(f.text for f in request.facts)
    return f"[{bucket_of(request.profile)}] {item}. {facts}"


def stub_passes(asset: str, request) -> bool:
    """Stands in for chapter 5's gate without the judge: the deterministic
    format and legal checks plus the embedding voice score. Here: no percentage
    that is not in an approved fact, and a length ceiling."""
    approved = " ".join(f.text for f in request.facts)
    return (all(c in approved for c in re.findall(r"\d+%", asset))
            and len(asset) <= 600)


if __name__ == "__main__":
    from datetime import date
    from C01_Menguy_MarketingAISystems import Event, build_profile, sample_events
    from C02_Menguy_MarketingAISystems import ConsentState
    from C03_Menguy_MarketingAISystems import sample_catalog, stub_embed
    from C04_Menguy_MarketingAISystems import (
        build_request, sample_campaign, stub_retrieve)

    today = date(2026, 4, 1)
    catalog = sample_catalog()
    campaign = sample_campaign(catalog)
    ok = ConsentState(purposes=frozenset({"personalization"}))

    def request_for(user_id, events, consent=ok, channel="onsite"):
        card = build_profile(user_id, events, today)
        return build_request(card, consent, catalog, stub_retrieve, stub_embed,
                             channel, campaign)

    a = request_for("cust-1041", sample_events())
    b = request_for("cust-2277", [
        Event(date(2025, 6, 9), "purchase", "shells", 260.0),
        Event(date(2026, 1, 15), "purchase", "insulation", 210.0),
        Event(date(2026, 3, 28), "view", "shells"),
        Event(date(2026, 3, 29), "view", "shells"),
    ])
    print("a key:", cache_key(a))
    print("b key:", cache_key(b))

    cache = VariantCache()
    print("warmed:", warm([a], cache, stub_generate, stub_passes))
    print("b, a different customer in the same bucket, hits:",
          cache.get(b) is not None)

    # Withheld consent and no history land in one identifier-free bucket.
    c = request_for("cust-3300", sample_events(), consent=ConsentState())
    d = request_for("cust-9000", [Event(date(2026, 3, 30), "view", "shells")])
    print("no-consent key:", cache_key(c))
    print("cold-start key:", cache_key(d))

    # A variant that invents a discount never reaches the cache.
    def hallucinating(request, timeout_ms=None):
        return "Cascade shell: 40% off, today only."
    print("bad variant stored:",
          warm([c], cache, hallucinating, stub_passes), "| entries:", len(cache))

    print("reclaimed after a corpus refresh:", cache.reclaim("corpus-2026Q3"))
