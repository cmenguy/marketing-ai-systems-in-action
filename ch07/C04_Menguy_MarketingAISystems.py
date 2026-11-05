"""Listing 7.4 - Assembling a personalized, grounded generation request.

The per-user analogue of chapter 5's GenerationSpec. Where the spec carried a
brief, a segment, and a channel, the personalization request carries the
consent-filtered profile (listing 7.2), the item shortlist (listing 7.3), and
the grounded offer facts, each with a Citation from chapter 4's retriever, so a
personalized offer line cannot invent a discount and every claim traces to an
approved source. Selection and the prompt both read the same gated profile, and
the audit basis and the region route travel on the request, so the question
"what did we send, on what basis, and where did it run" is answered by the
object itself. Nothing raw reaches the prompt.

Runs standalone with stub retrieve/embed:
    python3 C04_Menguy_MarketingAISystems.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from C01_Menguy_MarketingAISystems import ProfileCard, render_card
from C02_Menguy_MarketingAISystems import ConsentState, assemble_for_prompt
from C03_Menguy_MarketingAISystems import Item, Embed, top_items


@dataclass(frozen=True)
class Citation:
    """Chapter 4's provenance object, stubbed here so the file runs on its own."""
    doc_id: str
    quarter: str
    approval_state: str


@dataclass(frozen=True)
class Fact:
    text: str
    citation: Citation


@dataclass(frozen=True)
class Campaign:
    code: str              # "cascade-spring-2026"
    offer_id: str          # the offer window the copy quotes
    corpus_version: str    # chapter 4's corpus version the facts came from
    picks: tuple           # editor's picks: the unpersonalized shortlist


@dataclass(frozen=True)
class PersonalRequest:
    profile: dict          # consent-filtered traits, listing 7.2
    items: tuple           # shortlist, listing 7.3
    facts: tuple           # grounded facts, each with a Citation
    channel: str
    campaign: Campaign     # code, offer id, corpus version, picks
    basis: str             # why these traits were permitted
    route: str             # region the inference has to run in


Retrieve = Callable[..., list[Fact]]


def build_request(card: ProfileCard, consent: ConsentState, catalog: list[Item],
                  retrieve: Retrieve, embed: Embed, channel: str,
                  campaign: Campaign) -> PersonalRequest:
    profile, basis, route = assemble_for_prompt(
        card, consent, "personalization")
    items = top_items(profile, catalog, embed,
                      campaign.picks, k=3)
    facts = retrieve(
        query=f"{campaign.code} offer terms and required legal",
        filters={"campaign_code": campaign.code, "channel": channel})
    return PersonalRequest(profile, tuple(items), tuple(facts),
                           channel, campaign, basis, route)


def render_prompt(req: PersonalRequest, char_ceiling: int | None = None) -> str:
    """Build the final prompt. Same work as chapter 5, with the profile and the
    shortlist added and chapter 3's channel ceiling still enforced."""
    items = ", ".join(i.title for i in req.items)
    facts = "\n".join(f"- {f.text} [{f.citation.doc_id}]" for f in req.facts)
    ceiling = f"\nHard limit: {char_ceiling} characters." if char_ceiling else ""
    return (
        f"Write {req.channel} copy for the {req.campaign.code} campaign.\n"
        f"{render_card(req.profile)}"
        f"Feature one of: {items}\n"
        f"Use only these approved facts (do not invent offers):\n{facts}"
        f"{ceiling}"
    )


def stub_retrieve(query: str, filters: dict) -> list[Fact]:
    """Stands in for chapter 4's retriever: approved facts with provenance."""
    return [
        Fact("Spring pricing runs through May 31.",
             Citation("offer-2026-q2", "2026-Q2", "approved")),
        Fact("Face fabric is 63% recycled; substantiation on file.",
             Citation("legal-recycled-2025", "2025-Q1", "approved")),
    ]


def sample_campaign(catalog: list[Item]) -> Campaign:
    return Campaign("cascade-spring-2026", "spring-2026", "corpus-2026Q2",
                    picks=(catalog[0],))


if __name__ == "__main__":
    from datetime import date
    from C01_Menguy_MarketingAISystems import build_profile, sample_events
    from C03_Menguy_MarketingAISystems import sample_catalog, stub_embed

    catalog = sample_catalog()
    campaign = sample_campaign(catalog)
    card = build_profile("cust-1041", sample_events(), date(2026, 4, 1))

    permitted = ConsentState(purposes=frozenset({"personalization"}))
    req = build_request(card, permitted, catalog, stub_retrieve, stub_embed,
                        "email", campaign)
    print(f"[basis={req.basis} route={req.route}]")
    print(render_prompt(req))

    # Same customer, personalization withheld: no traits, the editor's picks,
    # and a prompt that asks for general copy. The gate holds for both the
    # prompt and the selection.
    withheld = build_request(card, ConsentState(), catalog, stub_retrieve,
                             stub_embed, "email", campaign)
    print()
    print(f"[basis={withheld.basis} route={withheld.route}]")
    print(render_prompt(withheld))
