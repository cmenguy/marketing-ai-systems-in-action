"""Competitor and public copy as negatives: score by margin (Listing 2.12).

When positives are thin, negatives are cheap. Build a centroid from the copy you
want to sound nothing like, and score a candidate by the margin between its
similarity to the brand centroid and its similarity to the negative centroid.
Use negatives to set a boundary, not to imitate (Chapter 10 covers the rights
question).
"""

from __future__ import annotations

import numpy as np

from C02_Menguy_MarketingAISystems import APPROVED_COPY, OFF_BRAND_COPY
from C03_Menguy_MarketingAISystems import embed
from C05_Menguy_MarketingAISystems import brand_centroid


def negative_centroid(negatives: list[str]) -> np.ndarray:
    """The mean embedding of copy you want to sound nothing like."""
    vecs = embed(negatives)
    centroid = vecs.mean(axis=0)
    return centroid / np.linalg.norm(centroid)


def margin_score(copy: str, brand_c: np.ndarray, neg_c: np.ndarray) -> float:
    """How much closer is the copy to the brand than to the negatives?"""
    vec = embed([copy])[0]
    return float(vec @ brand_c - vec @ neg_c)


if __name__ == "__main__":
    brand_c = brand_centroid(APPROVED_COPY)
    neg_c = negative_centroid(OFF_BRAND_COPY)
    samples = [
        ("approved", APPROVED_COPY[0]),
        ("off-brand", OFF_BRAND_COPY[0]),
        ("terse but empty", "Jacket. Blue. Cheap. Get one."),
    ]
    for label, text in samples:
        print(f"{label:16s} margin={margin_score(text, brand_c, neg_c):+.3f}")
