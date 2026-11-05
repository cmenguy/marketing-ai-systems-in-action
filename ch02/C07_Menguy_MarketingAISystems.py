"""Prompt-time style-guide injection: compile the spec into a block (Listing 2.7).

The cheapest approach and the only one that works cold, with no corpus and no
training. Turn the structured voice spec (C01) into an explicit instruction block
the model reads on every call. Chapter 3 is the full treatment of prompts as
versioned, channel-aware components.
"""

from __future__ import annotations

from C01_Menguy_MarketingAISystems import BrandVoiceSpec, northpeak_spec


def compile_style_block(spec: BrandVoiceSpec) -> str:
    """Render the voice spec as an instruction block for a system prompt."""
    lines = [
        f"You are writing for {spec.brand}.",
        f"Voice: {spec.stance}",
        f"Prefer these terms: {', '.join(spec.preferred_terms)}.",
        f"Never use these words: {', '.join(spec.banned_terms)}.",
        f"Keep sentences under about {spec.max_sentence_words} words.",
    ]
    if not spec.allow_exclamations:
        lines.append("Do not use exclamation points.")
    return "\n".join(lines)


if __name__ == "__main__":
    print(compile_style_block(northpeak_spec()))
