"""Listing 6.6 - Color compliance against the reference assets and the guideline palette.

The naive check (every pixel on palette) is a category error: a photograph carries
whatever colors the scene had. You check the brand-controlled region against TWO
references: the guideline palette AND the colors sampled from the real product and
logo assets, because the brand's true colors live in its assets and the guideline
is a lossy summary. A background can match the reference asset and miss the
guideline, or the reverse; the smallest distance to any approved color is the
"difference factor," checked against the kit tolerance.

`color_distance`/`_hex_to_rgb` are restated from chapter 2 so this file runs alone.
"""
from __future__ import annotations

import numpy as np

from C01_Menguy_MarketingAISystems import VisualBrandKit, northpeak_kit


def _hex_to_rgb(value: str):
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def color_distance(a: str, b: str) -> float:
    """Redmean: a cheap perceptual color distance (chapter 2, listing 2.11)."""
    r1, g1, b1 = _hex_to_rgb(a)
    r2, g2, b2 = _hex_to_rgb(b)
    rbar = (r1 + r2) / 2
    dr, dg, db = r1 - r2, g1 - g2, b1 - b2
    return ((2 + rbar / 256) * dr * dr + 4 * dg * dg
            + (2 + (255 - rbar) / 256) * db * db) ** 0.5


def _rgb_to_hex(rgb) -> str:
    return "#{:02X}{:02X}{:02X}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))


def crop(image, region):
    x, y, w, h = region
    return image[y:y + h, x:x + w]


def dominant_colors(area, k=6, bucket=16):
    pix = area.reshape(-1, 3)
    q = np.clip((pix // bucket) * bucket + bucket // 2, 0, 255)
    colors, counts = np.unique(q, axis=0, return_counts=True)
    order = np.argsort(-counts)[:k]
    total = counts.sum()
    return [(_rgb_to_hex(colors[i]), counts[i] / total) for i in order]


def color_report(image, kit: VisualBrandKit, region=None, reference_colors=()):
    area = crop(image, region) if region is not None else image
    approved = tuple(kit.palette) + tuple(reference_colors)   # guideline + assets
    offenders = []
    for hexc, share in dominant_colors(area):
        d = min(color_distance(hexc, p) for p in approved)    # difference factor
        if d > kit.tolerance and share >= 0.05:
            offenders.append((hexc, round(d, 1)))
    return offenders                            # empty means on brand


if __name__ == "__main__":
    kit = northpeak_kit()
    ref = kit.products["cascade"].colors        # colors from the real product asset

    on_brand = np.full((200, 200, 3), [31, 61, 43], dtype=np.uint8)   # #1F3D2B
    print("on-brand background:", color_report(on_brand, kit, reference_colors=ref))

    off_brand = np.full((200, 200, 3), [40, 90, 200], dtype=np.uint8)  # too blue
    print("off-brand background:", color_report(off_brand, kit, reference_colors=ref))
