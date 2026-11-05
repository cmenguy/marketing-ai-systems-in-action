"""Listing 7.1 - Deriving a model-legible profile card from a raw event stream.

Personalization starts from a mess of events (clicks, views, orders, opens) that
a language model cannot and should not read directly. `build_profile` projects
that log into a small, human-readable card of derived traits: the traits that
change how you would write to this customer. Recency derives the same
`"loyalty"` / `"lapsed_12mo"` segments chapter 5 used, so a stale label in a
table cannot disagree with the events. A customer who has never bought is a
`"prospect"`, never "lapsed", and a customer with fewer than `MIN_EVENTS`
events has no category lean yet: that is the cold-start case, and an empty lean
is what tells the selection step (listing 7.3) to fall back to a default.

Categories in `SENSITIVE_CATEGORIES` never count toward the lean. A lean toward
maternity wear is an inference about someone's health, and dropping it here,
upstream of the consent gate, means the inference never exists: it is not on the
card, so it cannot reach the prompt, the item shortlist, or the cache key. The
list is the privacy team's to maintain.

Runs standalone with the standard library only:  python3 C01_Menguy_MarketingAISystems.py
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date

MIN_EVENTS = 3               # below this there is no lean worth trusting
# Buying here implies a protected trait: never counted toward a lean
SENSITIVE_CATEGORIES = frozenset({"maternity", "adaptive"})


@dataclass(frozen=True)
class Event:
    ts: date
    kind: str                # "view" | "cart" | "purchase" | "open"
    category: str | None = None
    amount: float | None = None


@dataclass(frozen=True)
class ProfileCard:
    user_id: str
    tenure_days: int
    recency_days: int | None   # None: has never purchased
    orders: int
    top_categories: tuple[str, ...]
    price_band: str | None     # "value" | "mid" | "premium"
    segment: str               # "loyalty" | "lapsed_12mo" | "prospect"
    locale: str                # "US-CA", "EU-DE", "BR", "JP"


def _band(orders: list[Event]) -> str | None:
    """A coarse price band from average order value. Bands, not raw amounts,
    are what enters a prompt: enough signal to personalize, nothing precise.
    No orders means no band; the card does not invent one."""
    amounts = [e.amount for e in orders if e.amount is not None]
    if not amounts:
        return None
    avg = sum(amounts) / len(amounts)
    if avg < 80:
        return "value"
    if avg < 200:
        return "mid"
    return "premium"


def _segment(recency: int | None) -> str:
    if recency is None:
        return "prospect"      # never bought is not the same as lapsed
    return "loyalty" if recency <= 365 else "lapsed_12mo"


def _locale_of(user_id: str) -> str:
    """Stand-in for a CDP lookup. In production the locale comes from the
    customer record; here it is derived so the file runs on its own."""
    return {"0": "US-CA", "1": "EU-DE", "2": "BR", "3": "JP"}.get(
        user_id[-1] if user_id else "0", "US-CA"
    )


def build_profile(user_id: str, events: list[Event], today: date) -> ProfileCard:
    orders = [e for e in events if e.kind == "purchase"]
    last = max((e.ts for e in orders), default=None)
    first = min((e.ts for e in events), default=today)
    recency = (today - last).days if last else None
    cats = Counter(
        e.category for e in events
        if e.category and e.category not in SENSITIVE_CATEGORIES)
    lean = cats.most_common(3) if len(events) >= MIN_EVENTS else []
    return ProfileCard(
        user_id=user_id,
        tenure_days=(today - first).days,
        recency_days=recency,
        orders=len(orders),
        top_categories=tuple(c for c, _ in lean),
        price_band=_band(orders),
        segment=_segment(recency),
        locale=_locale_of(user_id),
    )


_FRAMING = {
    "loyalty": "lead with the product",
    "lapsed_12mo": "lead with what changed",
}


def render_card(fields: dict) -> str:
    """What enters the prompt: a short note a colleague could read. It renders
    only the fields the consent gate in listing 7.2 let through, so an empty
    dict renders as an instruction to write for a general reader. The segment
    framing rule from chapter 5 carries through on the segment line."""
    if not fields:
        return "Customer profile\n- no personal context: write for a general reader\n"
    lines = ["Customer profile"]
    seg = fields.get("segment")
    if seg:
        lines.append(f"- segment: {seg} ({_FRAMING.get(seg, 'introduce the brand')})")
    if fields.get("top_categories"):
        lines.append(f"- leans toward: {', '.join(fields['top_categories'])}")
    if fields.get("price_band"):
        lines.append(f"- price band: {fields['price_band']}")
    return "\n".join(lines) + "\n"


def sample_events() -> list[Event]:
    """A small event stream the other listings reuse for their demos."""
    return [
        Event(date(2024, 3, 2), "purchase", "insulation", 180.0),
        Event(date(2025, 11, 10), "purchase", "shells", 240.0),
        Event(date(2026, 3, 20), "view", "shells"),
        Event(date(2026, 3, 21), "cart", "shells"),
    ]


if __name__ == "__main__":
    today = date(2026, 4, 1)
    card = build_profile("cust-1041", sample_events(), today)
    print(card)
    print()
    # The full card stays inside your systems. The prompt sees only the traits
    # the gate allows; here, the three a personalization purpose would permit.
    print(render_card({"segment": card.segment,
                       "top_categories": card.top_categories,
                       "price_band": card.price_band}))

    # A browse-only visitor has never bought: a prospect, with no lean yet.
    visitor = build_profile(
        "cust-9000", [Event(date(2026, 3, 30), "view", "shells")], today)
    print("browse-only :", visitor.segment, visitor.top_categories)

    # No events at all is an empty card, not an error.
    stranger = build_profile("cust-9001", [], today)
    print("no events   :", stranger.segment, stranger.top_categories)

    # Purchases in a flagged category still count as orders, so the segment and
    # the price band are intact, but they never become a lean.
    expecting = build_profile("cust-9002", [
        Event(date(2026, 1, 12), "purchase", "maternity", 150.0),
        Event(date(2026, 2, 3), "purchase", "maternity", 130.0),
        Event(date(2026, 3, 18), "view", "shells"),
    ], today)
    print("flagged cat :", expecting.segment, expecting.price_band,
          expecting.top_categories)

    # Only flagged purchases: no lean at all, so selection falls back to the
    # editor's picks, the same branch as cold start.
    only_flagged = build_profile("cust-9003", [
        Event(date(2026, 1, 12), "purchase", "maternity", 150.0),
        Event(date(2026, 2, 3), "view", "maternity"),
        Event(date(2026, 3, 18), "view", "adaptive"),
    ], today)
    print("only flagged:", only_flagged.segment, only_flagged.top_categories)
