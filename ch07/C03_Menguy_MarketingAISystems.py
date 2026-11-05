"""Listing 7.3 - Co-embedding customers and items for cheap candidate selection.

Chapter 2 put brand text in a shared embedding space and built a brand centroid.
The same space solves selection: place customers and items in one space, and
picking what to feature becomes a nearest-neighbor lookup instead of a model
call. Items are embedded once, offline; only the customer is embedded live. The
`embed` function is injected, exactly as in chapter 4, so this runs against a
stub in tests; in production it is chapter 2's shared encoder,
`all-MiniLM-L6-v2`.

Selection reads the consent-filtered profile from listing 7.2, never the full
card, so a customer who has not permitted personalization gets the same
unpersonalized picks as a customer with no history. The scan over the catalog
is linear to keep the idea visible; at catalog scale the item vectors live in
the vector index chapter 4 already runs.

Runs standalone (pure-Python vectors, stub encoder):
    python3 C03_Menguy_MarketingAISystems.py
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Callable

Vector = list[float]
Embed = Callable[[str], Vector]


@dataclass(frozen=True)
class Item:
    code: str
    title: str
    category: str
    vec: Vector = ()  # embedded once, offline


def cosine(a: Vector, b: Vector) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def stub_embed(text: str, dim: int = 64) -> Vector:
    """Deterministic fake embedding so the file runs with no model installed: a
    hashed bag-of-words, so shared tokens (a category name) pull vectors together.
    Real version: chapter 2's SentenceTransformer('all-MiniLM-L6-v2')."""
    out = [0.0] * dim
    for tok in text.lower().replace(",", " ").split():
        idx = int(hashlib.sha256(tok.encode()).hexdigest(), 16) % dim
        out[idx] += 1.0
    norm = math.sqrt(sum(x * x for x in out)) or 1.0
    return [x / norm for x in out]


def user_vector(profile: dict, embed: Embed) -> Vector:
    parts = [profile.get("segment"), "buyer, likes",
             ", ".join(profile["top_categories"]),
             profile.get("price_band")]
    return embed(" ".join(p for p in parts if p))


def embed_catalog(items: list[Item], embed: Embed) -> list[Item]:
    """Offline pass: embed each item description once."""
    return [Item(i.code, i.title, i.category,
                 embed(f"{i.category}: {i.title}")) for i in items]


def top_items(profile: dict, catalog: list[Item], embed: Embed,
              picks: tuple, k: int = 5) -> list[Item]:
    if not profile.get("top_categories"):
        return list(picks[:k])     # no consent or no history: do not personalize
    uvec = user_vector(profile, embed)
    scored = [(cosine(uvec, item.vec), item)
              for item in catalog]
    scored.sort(key=lambda s: s[0], reverse=True)
    return [item for _, item in scored[:k]]


def sample_catalog(embed: Embed = stub_embed) -> list[Item]:
    """A four-item catalog the other listings reuse for their demos."""
    return embed_catalog([
        Item("cascade", "Cascade waterproof shell", "shells"),
        Item("ridgeline", "Ridgeline insulated jacket", "insulation"),
        Item("summit-pack", "Summit 40L pack", "packs"),
        Item("trail-sock", "Merino trail sock", "accessories"),
    ], embed)


if __name__ == "__main__":
    catalog = sample_catalog()
    picks = (catalog[0],)          # the editor's pick for the launch: the Cascade

    known = {"segment": "loyalty", "top_categories": ("insulation", "shells"),
             "price_band": "premium"}
    print("known customer :",
          [i.code for i in top_items(known, catalog, stub_embed, picks, k=3)])

    # An empty profile is what both cold start and withheld consent look like.
    print("empty profile  :",
          [i.code for i in top_items({}, catalog, stub_embed, picks, k=3)])
