"""A campaign calendar that injects the window and refuses expired offers (Listing 3.7).

Marketing runs on a calendar with teeth. An offer is valid through a date and not
after it; a launch happens on a day; Black Friday is not a theme you can invoke
in July. A plausible, on-brand, legally clean piece of copy that advertises an
expired offer is still wrong, and it reaches the customer.

The validity window is a fact about the campaign, so it belongs in the prompt as
data and in a gate that refuses to build a prompt for an offer that is not live.
Raising at prompt-build time turns a silent content bug into a loud pipeline
failure, which is the trade you want: a pipeline failure is fixed before send.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from C01_Menguy_MarketingAISystems import PromptLayer

# Event-anchored instructions: the event changes the lead, not just a noun.
EVENT_TEMPLATES = {
    "launch": "Open on what is new. Assume the reader has not seen it.",
    "flash": "Open on the deadline. Keep the window explicit. Real urgency only.",
    "holiday": "Borrow the occasion's frame without manufacturing urgency.",
}


@dataclass(frozen=True)
class Campaign:
    code: str
    valid_from: date
    valid_through: date
    event: str            # "launch", "flash", "holiday"


def offer_is_live(camp: Campaign, today: date) -> bool:
    return camp.valid_from <= today <= camp.valid_through


def event_instruction(camp: Campaign) -> str:
    return EVENT_TEMPLATES[camp.event]


def time_window_layer(camp: Campaign, today: date) -> PromptLayer:
    """Inject the 'valid through' language, or refuse if the offer is dead."""
    if not offer_is_live(camp, today):
        raise ValueError(
            f"{camp.code} is not live on {today} "
            f"({camp.valid_from}..{camp.valid_through})"
        )
    ends = f"{camp.valid_through:%B} {camp.valid_through.day}"
    return PromptLayer(
        "time_window", "marketing",
        f"{event_instruction(camp)} "
        f"State that the offer runs through {ends}. "
        f"Do not imply it is open-ended.",
    )


if __name__ == "__main__":
    spring = Campaign("cascade-spring", date(2026, 3, 1),
                      date(2026, 5, 31), "launch")

    print(time_window_layer(spring, date(2026, 4, 15)).content)
    try:
        time_window_layer(spring, date(2026, 7, 1))
    except ValueError as e:
        print("refused:", e)
