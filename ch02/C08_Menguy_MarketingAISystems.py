"""Fine-tuning the weights: SFT dataset and preference pairs (Listing 2.8).

In practice you rarely full-fine-tune. A low-rank adapter (LoRA/QLoRA) is the
default: cheaper and less prone to forgetting the base model's range. The work is
mostly in the data. This builds a provider-neutral SFT dataset (with a
minimum-volume guard) and the (prompt, chosen, rejected) preference dataset that
editor corrections give you for DPO-style tuning, usually the better use of the
data than SFT alone.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

MIN_EXAMPLES = 200          # below this, prefer retrieval + prompt injection


@dataclass(frozen=True)
class ApprovedAsset:
    brief: str
    copy: str               # the human-approved final, not the draft


@dataclass(frozen=True)
class Correction:
    """An editor correction: the model's draft and the human rewrite of it."""

    brief: str
    rejected: str           # the draft the editor cut
    chosen: str             # the approved rewrite that replaced it


def to_chat_example(asset: ApprovedAsset, system: str) -> dict:
    """One supervised (SFT) training row in the common chat format."""
    return {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": asset.brief},
            {"role": "assistant", "content": asset.copy},
        ]
    }


def build_dataset(assets: list[ApprovedAsset], system: str) -> str:
    """Serialize approved assets to JSONL, or refuse if there are too few."""
    if len(assets) < MIN_EXAMPLES:
        raise ValueError(
            f"{len(assets)} examples is below the {MIN_EXAMPLES} floor; "
            "a fine-tune here will overfit. Use retrieval + prompt instead."
        )
    rows = (to_chat_example(a, system) for a in assets)
    return "\n".join(json.dumps(r) for r in rows)


def to_preference_example(correction: Correction, system: str) -> dict:
    """One (prompt, chosen, rejected) row for DPO-style tuning."""
    return {
        "system": system,
        "prompt": correction.brief,
        "chosen": correction.chosen,
        "rejected": correction.rejected,
    }


if __name__ == "__main__":
    demo = [ApprovedAsset("Launch the Cascade shell.", "The shell is here.")]
    try:
        build_dataset(demo, system="Write in Northpeak's voice.")
    except ValueError as exc:
        print("refused:", exc)

    correction = Correction(
        brief="Launch the Cascade shell to loyalty members.",
        rejected="Conquer any storm in the revolutionary all-new Cascade!",
        chosen="The shell is here. A 10K/10K rating and a 63% recycled face fabric.",
    )
    print("preference row:", to_preference_example(correction, "Northpeak voice."))
