"""Embedding-based brand-voice scoring: distance to a brand centroid (2.5).

Embed the approved copy, take the mean as a brand centroid, and score new copy by
its cosine to that centroid. This prototype uses an off-the-shelf encoder to show
what the score is for; C06 fine-tunes the encoder so on-brand and off-brand
separate more sharply. The known failure (rewarding topic over voice) is visible
in the sample scores and discussed in section 2.5.
"""

from __future__ import annotations

import numpy as np

from C02_Menguy_MarketingAISystems import APPROVED_COPY, OFF_BRAND_COPY
from C03_Menguy_MarketingAISystems import embed


def brand_centroid(approved: list[str]) -> np.ndarray:
    """The mean embedding of approved copy: a prototype of the voice."""
    vecs = embed(approved)
    centroid = vecs.mean(axis=0)
    return centroid / np.linalg.norm(centroid)


def brand_score(copy: str, centroid: np.ndarray) -> float:
    """Cosine of a candidate to the brand centroid, mapped to 0..1."""
    vec = embed([copy])[0]
    return float((vec @ centroid + 1) / 2)


if __name__ == "__main__":
    centroid = brand_centroid(APPROVED_COPY)
    for label, corpus in [("on-brand", APPROVED_COPY),
                          ("off-brand", OFF_BRAND_COPY)]:
        print(label)
        for text in corpus:
            print(f"  {brand_score(text, centroid):.3f}  {text[:48]}")
