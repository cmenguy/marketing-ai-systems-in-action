"""Composing every layer into one prompt, then running the guards (Listing 3.10).

The regression harness in C08 leaves `generate` abstract. This is where it gets
concrete, and it is where every layer this chapter built comes together: the
brand rules and examples (C02), the channel constraints (C03), the required
phrases and claim guardrails (C04, C05), the campaign window (C06), and any
fenced UGC (C07). `compose` assembles the versioned prompt; `guards` runs the
deterministic checks on the generated copy.

This is the function the harness calls and the function production calls. The
test path and the real path assemble the identical prompt, which is the only
condition under which a passing test means anything about what will ship.
Reading `compose` top to bottom is a summary of the chapter.
"""

from __future__ import annotations

from datetime import date

from C01_Menguy_MarketingAISystems import PromptLayer, PromptTemplate
from C02_Menguy_MarketingAISystems import (
    APPROVED, BRAND, examples_layer, rules_layer,
)
from C03_Menguy_MarketingAISystems import channel_layer, within_ceiling
from C04_Menguy_MarketingAISystems import (
    find_unsubstantiated, required_phrases_layer, verify_required,
)
from C06_Menguy_MarketingAISystems import check_comparative, safe_language_layer
from C07_Menguy_MarketingAISystems import Campaign, time_window_layer
from C08_Menguy_MarketingAISystems import ugc_layer


def compose(brief, channel, campaign, today, reviews=None) -> PromptTemplate:
    layers = [
        PromptLayer("system", "engineering",
                    "You write marketing copy for Northpeak."),
        rules_layer(BRAND),
        examples_layer(APPROVED),
        channel_layer(channel),
        required_phrases_layer(),
        safe_language_layer(),
        time_window_layer(campaign, today),   # gate: refuses expired
        PromptLayer("brief", "marketing", brief),
    ]
    if reviews:
        layers.append(ugc_layer(reviews))   # fenced as data, not instructions
    return PromptTemplate(f"copy.{channel}", 1, tuple(layers))


def guards(copy: str, channel: str, competitors=()) -> dict:
    return {
        "over_ceiling": not within_ceiling(copy, channel),
        "legal_missing": verify_required(copy),
        "unsubstantiated": find_unsubstantiated(copy),
        "comparative": check_comparative(copy, competitors),
    }


if __name__ == "__main__":
    spring = Campaign("cascade-spring", date(2026, 3, 1),
                      date(2026, 5, 31), "launch")
    brief = "Launch the Cascade waterproof shell for spring, loyalty segment."

    tpl = compose(brief, "email", spring, date(2026, 4, 15))
    print("layers:", [l.name for l in tpl.layers])
    print("fingerprint:", tpl.fingerprint())

    good = ("The Cascade shell has a 10K/10K waterproof rating and a 63% "
            "recycled face fabric. Spring pricing runs through May 31.")
    print("guards (clean copy):", guards(good, "email"))

    bad = "The best, most unbeatable shell ever, better than Summitline!"
    print("guards (bad copy):", guards(bad, "email", ["Summitline"]))
