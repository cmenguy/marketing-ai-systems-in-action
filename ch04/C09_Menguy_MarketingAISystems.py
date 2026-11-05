"""Generation grounded in retrieved facts, with the legal check outside the model
(Listing 4.9).

Grounding retrieves the approved facts (the 10K/10K rating, the 63% recycled
figure, the spring price) and puts them in the prompt as the ground truth the copy
must stay within. It reduces hallucination but does not eliminate it: a model
handed the right rating will occasionally round it, restate it, or attach a claim
the context never made ("warmest in its class", "guaranteed").

So grounding is necessary and insufficient, exactly like retrieving a disclaimer:
it puts the right material in front of the model, and a deterministic check
outside the model is still the guarantee. Each retrieved fact is tagged with its
chunk id, so the output can cite its source for downstream approval (chapter 5).

`generate` and `verify` are injected; in production `generate` is a model call
(read the API key from the environment) and `verify` is chapter 3's required-phrase
and claim check.
"""

from __future__ import annotations

import re

from C01_Menguy_MarketingAISystems import sample_corpus
from C03_Menguy_MarketingAISystems import Chunk, chunk_corpus
from C05_Menguy_MarketingAISystems import rerank
from datetime import date


def ground(hits: list[Chunk]) -> str:
    """Each retrieved fact is tagged with its chunk id, so output can cite it."""
    return "\n".join(f"[{c.chunk_id}] {c.text}" for c in hits)


def generate_grounded(brief, hits, generate, verify):
    context = ground(hits)
    prompt = (
        "Use only these approved brand facts. Do not add claims "
        "they do not support.\n\n" + context + "\n\nBrief: " + brief
    )
    copy = generate(prompt)                         # injected model call
    missing = verify(copy, hits)                    # deterministic, outside model
    return copy, missing


# A stand-in for chapter 3's deterministic legal check.
REQUIRED = {"waterproof rating": r"\d+K/\d+K",
            "recycled percentage": r"\d+%\s+recycled"}
UNSUBSTANTIATED = [r"\bwarmest\b", r"\bguaranteed\b", r"\bbest\b"]


def verify(copy: str, hits) -> dict:
    missing = [name for name, pat in REQUIRED.items()
               if not re.search(pat, copy)]
    claims = [m for pat in UNSUBSTANTIATED
              for m in re.findall(pat, copy, flags=re.I)]
    return {"missing_required": missing, "unsubstantiated": claims}


if __name__ == "__main__":
    chunks = rerank(chunk_corpus(sample_corpus()), today=date(2026, 3, 15))

    # A well-grounded model: uses the retrieved facts, adds no stray claim.
    def good_model(prompt):
        return ("The Cascade shell is here. A 10K/10K waterproof rating and a "
                "63% recycled face fabric.")

    # A model that decorates the grounded facts with an unsubstantiated claim.
    def drifting_model(prompt):
        return "The warmest, guaranteed waterproof shell you can buy."

    for label, model in (("grounded", good_model), ("drifting", drifting_model)):
        copy, checks = generate_grounded("Launch email, loyalty", chunks,
                                         model, verify)
        print(f"[{label}] {copy}\n   check: {checks}")
