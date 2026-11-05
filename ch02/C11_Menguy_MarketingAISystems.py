"""Visual identity as a spec you can validate deterministically (Listing 2.11).

Text has no hex value; a brand's color does. So visual identity is a
machine-readable spec of design tokens, and the check is deterministic, a hard
pass or fail. The distance here is the low-cost "redmean" approximation of
perceptual color distance; Chapter 6 does the real thing (CIEDE2000 over a
rendered asset) plus logo safe zones and typography.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BrandSpec:
    brand: str
    palette: list[str]                  # allowed colors, as hex
    tolerance: float = 24.0             # max perceptual distance to accept


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def color_distance(a: str, b: str) -> float:
    """Redmean: a cheap approximation of perceptual color distance."""
    r1, g1, b1 = _hex_to_rgb(a)
    r2, g2, b2 = _hex_to_rgb(b)
    rbar = (r1 + r2) / 2
    dr, dg, db = r1 - r2, g1 - g2, b1 - b2
    return (
        (2 + rbar / 256) * dr * dr
        + 4 * dg * dg
        + (2 + (255 - rbar) / 256) * db * db
    ) ** 0.5


def nearest_palette_distance(color: str, spec: BrandSpec) -> float:
    """Distance from a color to the closest allowed brand color."""
    return min(color_distance(color, p) for p in spec.palette)


def is_on_palette(color: str, spec: BrandSpec) -> bool:
    """A hard pass/fail: is this color within tolerance of the palette?"""
    return nearest_palette_distance(color, spec) <= spec.tolerance


def northpeak_visual() -> BrandSpec:
    """Northpeak's palette: forest, sand, near-black, white."""
    return BrandSpec(
        brand="Northpeak",
        palette=["#1B3A2F", "#D9CBA3", "#2E2A25", "#FFFFFF"],
    )


if __name__ == "__main__":
    spec = northpeak_visual()
    for color in ["#1C3B30", "#0A84FF", "#D8CAA2"]:
        distance = nearest_palette_distance(color, spec)
        print(f"{color}  distance={distance:6.1f}  "
              f"on_palette={is_on_palette(color, spec)}")
