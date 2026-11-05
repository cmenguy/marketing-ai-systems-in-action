"""Listing 7.7 - A fallback ladder with a circuit breaker on the live path.

A live model call will sometimes miss its deadline or fail. The right answer is a
fallback ladder: try the bucket cache, then a live generation inside the budget,
then the precomputed segment default (the reviewed asset chapter 5 approved),
then a brand-safe house asset that always works. A live result has to clear the
checks before it is cached or shown, and one that does not falls down the ladder
like a timeout would. The circuit breaker keeps a slow model from becoming an
outage: after enough consecutive failures it opens and sends traffic straight to
the reviewed fallback, then lets exactly one probe through after a cool-off
before it closes again.

Runs standalone:  python3 C07_Menguy_MarketingAISystems.py
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable


class Timeout(Exception):
    pass


class ModelError(Exception):
    pass


@dataclass
class CircuitBreaker:
    threshold: int = 3           # consecutive failures before opening
    cool_off_s: float = 30.0
    _failures: int = 0
    _opened_at: float | None = None
    _probing: bool = False

    def allow(self) -> bool:
        if self._opened_at is None:
            return True                      # closed: traffic flows
        if self._probing:
            return False                     # a probe is already out
        if time.monotonic() - self._opened_at >= self.cool_off_s:
            self._probing = True             # half-open: exactly one probe
            return True
        return False

    def record_success(self) -> None:
        self._failures = 0
        self._opened_at = None
        self._probing = False

    def record_failure(self) -> None:
        self._failures += 1
        if self._probing or self._failures >= self.threshold:
            self._opened_at = time.monotonic()   # open, or re-open after a probe
            self._probing = False


def serve(request, deadline_ms: int, cache, generate: Callable,
          passes: Callable, segment_default: dict, house_asset: str,
          breaker: CircuitBreaker, gen_p99_ms: int = 1500):
    """Return (asset, source) where source is 'cache' | 'live' | 'fallback'."""
    hit = cache.get(request)
    if hit is not None:
        return hit, "cache"
    if deadline_ms >= gen_p99_ms and breaker.allow():
        try:
            asset = generate(request, timeout_ms=deadline_ms)
            breaker.record_success()
            if passes(asset, request):
                cache.put(request, asset)
                return asset, "live"
        except (Timeout, ModelError):
            breaker.record_failure()
    segment = request.profile.get("segment")
    default = segment_default.get(segment)
    return (default or house_asset), "fallback"


if __name__ == "__main__":
    from datetime import date
    from C01_Menguy_MarketingAISystems import build_profile, sample_events
    from C02_Menguy_MarketingAISystems import ConsentState
    from C03_Menguy_MarketingAISystems import sample_catalog, stub_embed
    from C04_Menguy_MarketingAISystems import (
        build_request, sample_campaign, stub_retrieve)
    from C06_Menguy_MarketingAISystems import (
        VariantCache, stub_generate, stub_passes)

    catalog = sample_catalog()
    campaign = sample_campaign(catalog)
    card = build_profile("cust-1041", sample_events(), date(2026, 4, 1))
    ok = ConsentState(purposes=frozenset({"personalization"}))

    def request_for(channel, consent=ok):
        return build_request(card, consent, catalog, stub_retrieve, stub_embed,
                             channel, campaign)

    def too_slow(request, timeout_ms):
        raise Timeout("model too slow under launch load")

    def hallucinating(request, timeout_ms):
        return "Cascade shell: 40% off, today only."

    defaults = {"loyalty": "[reviewed loyalty hero]",
                "lapsed_12mo": "[reviewed lapsed hero]"}
    house = "[house asset]"
    cache = VariantCache()
    breaker = CircuitBreaker(threshold=2, cool_off_s=0.05)

    def show(label, request, deadline_ms, generate):
        asset, src = serve(request, deadline_ms, cache, generate, stub_passes,
                           defaults, house, breaker)
        print(f"{label:<34} -> {src:>8}: {asset}")

    email = request_for("email")
    show("timeout 1", email, 5000, too_slow)
    show("timeout 2 (breaker opens)", email, 5000, too_slow)
    show("breaker open, model not called", email, 5000, stub_generate)
    time.sleep(0.06)
    show("cool-off over, one probe succeeds", email, 5000, stub_generate)
    show("same request again", email, 5000, stub_generate)
    show("tight budget, cold key", request_for("onsite"), 300, stub_generate)
    show("live result fails the checks", request_for("push"), 5000, hallucinating)
    show("consent withheld, model down", request_for("email", ConsentState()),
         5000, too_slow)
    print("cache entries:", len(cache))
