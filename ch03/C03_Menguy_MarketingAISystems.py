"""A channel registry that specializes one prompt into per-channel variants (Listing 3.3).

One approved brief becomes a long email, a 160-character SMS, a templated
WhatsApp message, a corporate LinkedIn post, an Instagram caption, and a set
of display slots. The channel is not a length suffix on
a generic prompt: the register changes too, and copy that lands on Instagram
reads as unserious on LinkedIn. So the channel is its own engineering-owned
layer carrying the ceiling, the register, and the format.

The character ceiling in the prompt is an instruction, not a guarantee. The
deterministic length check after generation (below) is what actually enforces
it, the same belt-and-suspenders pattern the legal checks use in C04.
"""

from __future__ import annotations

from dataclasses import dataclass

from C01_Menguy_MarketingAISystems import PromptLayer, PromptTemplate
from C02_Menguy_MarketingAISystems import (
    APPROVED, BRAND, examples_layer, rules_layer,
)


@dataclass(frozen=True)
class ChannelSpec:
    name: str
    char_ceiling: int
    register: str
    format_note: str


# Limits are current instances, not constants; platforms move them.
CHANNELS = {
    "email": ChannelSpec(
        "email", 900, "brand voice, room to explain",
        "Subject line, preview text, then a scannable body."),
    "sms": ChannelSpec(
        "sms", 160, "terse; one offer and an opt-out",
        "One message. End with an opt-out."),
    "whatsapp": ChannelSpec(
        "whatsapp", 1024, "conversational; one offer",
        "Fill the approved template. Opted-in recipients only."),
    "linkedin": ChannelSpec(
        "linkedin", 3000, "corporate, measured",
        "Feed truncates near the first line; keep the hook early."),
    "instagram": ChannelSpec(
        "instagram", 2200, "casual, visual-first",
        "The image carries the message; the caption adds detail."),
    "display": ChannelSpec(
        "display", 90, "compressed, benefit-first",
        "Text supports the visual. Headline under 30, body under 90."),
}


def channel_layer(channel: str) -> PromptLayer:
    """The engineering-owned layer that varies per channel."""
    spec = CHANNELS[channel]
    body = (
        f"Channel: {spec.name}. Register: {spec.register}. "
        f"Hard limit: {spec.char_ceiling} characters. "
        f"Format: {spec.format_note}"
    )
    return PromptLayer("channel", "engineering", body)


def build_channel_prompt(brief: str, channel: str) -> PromptTemplate:
    """Shared brand layers stay fixed; the channel layer specializes."""
    return PromptTemplate(
        template_id=f"copy.{channel}",
        version=1,
        layers=(
            rules_layer(BRAND),
            examples_layer(APPROVED),
            channel_layer(channel),
            PromptLayer("brief", "marketing", brief),
        ),
    )


def within_ceiling(copy: str, channel: str) -> bool:
    """Enforce the ceiling outside the model, where it is a guarantee."""
    return len(copy) <= CHANNELS[channel].char_ceiling


if __name__ == "__main__":
    brief = "Launch the Cascade waterproof shell for spring, loyalty segment."
    for ch in CHANNELS:
        tpl = build_channel_prompt(brief, ch)
        print(f"=== {ch} (ceiling {CHANNELS[ch].char_ceiling}) ===")
        print(tpl.render())
        print()
