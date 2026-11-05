"""Listing 7.9 - Scoring served variants in layers, against the holdout, per segment.

Click-through is the metric everyone reaches for and the one most likely to
mislead: a model optimizing for clicks learns to write bait, and bait clicks.
Measure in layers instead: engagement (immediate, gameable), brand-voice quality
on a sample of what shipped (chapters 2 and 5), slow outcome metrics, and a
guardrail that must not get worse (unsubscribe, complaint, drift).

The outcome and the guardrail are measured as lift: the personalized arm's rate
minus the same segment's rate in the permanent holdout (listing 7.8). An
absolute unsubscribe rate says nothing until you know what that segment does
when it is left alone. A segment whose guardrail lift breaches its cap is the
input to the shutoff: flip that segment to the reviewed baseline without a
deploy (the same fallback listing 7.7 uses). A segment with too few customers in
either arm gets numbers and no verdict; chapter 11 builds the statistics that
replace the `min_n` floor.

Runs standalone with a stub voice scorer:
    python3 C09_Menguy_MarketingAISystems.py
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Callable


@dataclass(frozen=True)
class Served:
    user_id: str
    segment: str
    text: str


def _rate(sample: list[Served], outcomes: dict, event: str) -> float:
    if not sample:
        return 0.0
    hits = sum(1 for s in sample if event in outcomes.get(s.user_id, ()))
    return hits / len(sample)


def _lift(treat: list[Served], base: list[Served], outcomes: dict,
          event: str) -> float:
    """Personalized rate minus the same segment's holdout rate."""
    return (_rate(treat, outcomes, event)
            - _rate(base, outcomes, event))


def _subsample(sample: list[Served], every: int = 5) -> list[Served]:
    """Voice scoring runs on a sample, not every asset: it is the one check no
    human is doing on a per-user stream."""
    return sample[::every] or sample


def evaluate(served: list[Served], holdout: list[Served], outcomes: dict,
             voice_score: Callable[[str], float], caps: dict,
             min_n: int = 1000):
    """Return (per_segment_metrics, breached_segments)."""
    rows, breaches = {}, []
    for seg in sorted({s.segment for s in served}):
        treat = [s for s in served if s.segment == seg]
        base = [h for h in holdout if h.segment == seg]
        voice = mean(voice_score(s.text)
                     for s in _subsample(treat))
        m = rows[seg] = {
            "n": min(len(treat), len(base)),
            "ctr": _rate(treat, outcomes, "click"),
            "voice": voice,
            "conv_lift": _lift(treat, base, outcomes, "convert"),
            "unsub_lift": _lift(treat, base, outcomes,
                                "unsubscribe"),
        }
        if m["n"] < min_n:             # too few customers for a verdict
            continue
        if (m["unsub_lift"] > caps["unsub_lift"]
                or m["voice"] < caps["voice"]):
            breaches.append(seg)
    return rows, breaches


if __name__ == "__main__":
    # Loyalty does well. The lapsed segment clicks more, converts less than its
    # own holdout, and unsubscribes more: personalization reads as intrusive,
    # and only the comparison against the holdout shows it.
    def cohort(prefix, segment, text, n):
        return [Served(f"{prefix}{i}", segment, text) for i in range(n)]

    served = (
        cohort("LT", "loyalty", "A 10K/10K shell for the days the forecast is wrong.", 2000)
        + cohort("XT", "lapsed_12mo", "Still thinking about the shell you looked at?", 2000)
        + cohort("PT", "prospect", "The Cascade shell is here.", 40)
    )
    holdout = (
        cohort("LH", "loyalty", "[reviewed loyalty hero]", 1000)
        + cohort("XH", "lapsed_12mo", "[reviewed lapsed hero]", 1000)
        + cohort("PH", "prospect", "[house asset]", 20)
    )

    # (click %, convert %, unsubscribe per mille) by cohort prefix.
    rates = {"LT": (30, 8, 2), "LH": (24, 6, 2),
             "XT": (40, 2, 12), "XH": (22, 3, 4),
             "PT": (20, 1, 0), "PH": (20, 1, 0)}
    outcomes = {}
    for s in served + holdout:
        click, convert, unsub = rates[s.user_id[:2]]
        i = int(s.user_id[2:])
        events = []
        if i % 100 < click:
            events.append("click")
        if i % 100 < convert:
            events.append("convert")
        if i % 1000 < unsub:
            events.append("unsubscribe")
        outcomes[s.user_id] = tuple(events)

    def stub_voice(text: str) -> float:
        # Chapter 2's margin_score in production; here a cheap proxy: hype words
        # that are off the Northpeak voice pull the score down.
        hype = sum(w in text.lower() for w in ("today only", "% off", "!"))
        return max(0.0, 0.9 - 0.25 * hype)

    caps = {"unsub_lift": 0.005, "voice": 0.55}
    rows, breaches = evaluate(served, holdout, outcomes, stub_voice, caps)
    for seg, m in rows.items():
        verdict = "" if m["n"] >= 1000 else "  (n too small: no verdict)"
        print(f"{seg:>12}: n={m['n']:<5} ctr={m['ctr']:.2f} voice={m['voice']:.2f} "
              f"conv_lift={m['conv_lift']:+.3f} "
              f"unsub_lift={m['unsub_lift']:+.3f}{verdict}")
    print("breached (shut off, drop to reviewed baseline):", breaches)
