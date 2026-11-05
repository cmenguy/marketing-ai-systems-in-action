"""Listing 7.2 - A consent-aware assembler that decides what enters the prompt.

The prompt is a data flow. Putting a customer attribute into a prompt is a
processing operation, and if the model runs in another region it may be a
transfer. `assemble_for_prompt` enforces the engineering moves that hold across
GDPR, CCPA/CPRA, LGPD, and APPI even though the statutes differ: minimize to
derived traits, gate every use by its purpose against what the customer
permits, exclude identifiers and sensitive categories outright, and hand back a
region route and an audit basis. The caller names the purpose of *this* use;
the gate never infers it from the field. The trait-to-purpose mapping here is a
starting point a privacy team signs off on, not a statement of what the law
requires (chapter 10 owns the regimes).

Runs standalone:  python3 C02_Menguy_MarketingAISystems.py
"""

from __future__ import annotations

from dataclasses import dataclass

from C01_Menguy_MarketingAISystems import ProfileCard, build_profile, sample_events

# Identifiers and sensitive fields never enter a prompt, whatever consent says.
NEVER_IN_PROMPT: frozenset[str] = frozenset({
    "user_id", "email", "name", "device_id", "precise_geo",
    "health", "ethnicity", "religion",
})

# Each permissible trait lists the purposes it may serve. Exact recency and
# tenure are deliberately absent: the segment already carries recency at the
# only resolution the copy needs.
FIELD_PURPOSES: dict[str, frozenset[str]] = {
    "segment": frozenset({"personalization", "advertising"}),
    "top_categories": frozenset({"personalization", "advertising"}),
    "price_band": frozenset({"personalization"}),
}

# Where the inference should run, keyed by the customer's region.
_REGION_ROUTE = {"US": "us", "EU": "eu", "BR": "br", "JP": "jp"}


@dataclass(frozen=True)
class ConsentState:
    """The customer's permissible-use state, as the consent service reports it.
    `purposes` is whatever is currently permitted for this customer, however the
    regime they live under arrives at it (a recorded basis, or no opt-out)."""
    purposes: frozenset[str] = frozenset()
    do_not_sell_share: bool = False
    deleted: bool = False

    def permits(self, purpose: str) -> bool:
        if self.deleted:
            return False
        if purpose == "advertising" and self.do_not_sell_share:
            return False       # opted out of cross-context advertising
        return purpose in self.purposes


def _basis(consent: ConsentState, purpose: str) -> str:
    if consent.deleted:
        return f"{purpose}:deleted"
    return f"{purpose}:{'permitted' if consent.permits(purpose) else 'withheld'}"


def _region_route(locale: str) -> str:
    return _REGION_ROUTE.get(locale.split("-")[0], "us")


def assemble_for_prompt(card: ProfileCard, consent: ConsentState, purpose: str):
    """Return (permissible_fields, audit_basis, region_route) for one use."""
    fields: dict[str, object] = {}
    if consent.permits(purpose):
        for name, uses in FIELD_PURPOSES.items():
            if purpose in uses and name not in NEVER_IN_PROMPT:
                fields[name] = getattr(card, name)
    return (fields, _basis(consent, purpose),
            _region_route(card.locale))


if __name__ == "__main__":
    from datetime import date

    card = build_profile("cust-1041", sample_events(), date(2026, 4, 1))

    full = ConsentState(purposes=frozenset({"personalization", "advertising"}))
    opted_out = ConsentState(purposes=frozenset({"personalization", "advertising"}),
                             do_not_sell_share=True)
    none = ConsentState()

    cases = [
        ("full", full, "personalization"),
        ("full", full, "advertising"),
        ("do-not-sell", opted_out, "personalization"),
        ("do-not-sell", opted_out, "advertising"),
        ("no consent", none, "personalization"),
    ]
    for label, c, purpose in cases:
        fields, basis, route = assemble_for_prompt(card, c, purpose)
        print(f"{label:>12} -> route={route} basis={basis}")
        print(f"{'':>12}    fields={fields}")
