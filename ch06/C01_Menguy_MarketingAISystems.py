"""Listing 6.1 - The visual brand kit: the brand's assets and rules in one spec.

The brand's identity lives in its assets, not in a description of its rules. This
kit extends chapter 2's BrandSpec (palette + tolerance) with the brand's real
assets: the logo file, the product references (keyed by code), and the approved
templates, alongside the safe-zone rule, the type family, and forbidden
treatments. The guideline palette is the fallback; the reference assets carry the
truth. One object, read at both ends of the pipeline (grounding and validation).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SafeZone:
    margin_frac: float       # clear space around the logo, fraction of its width
    min_width_frac: float    # logo at least this fraction of the canvas width


@dataclass(frozen=True)
class ReferenceAsset:
    asset_id: str
    kind: str                # "product" | "logo" | "hero" | "template"
    uri: str                 # in the DAM, or exported from Figma
    colors: tuple[str, ...] = ()   # approved colors sampled from the asset itself


@dataclass(frozen=True)
class VisualBrandKit:
    brand: str
    palette: list[str]       # guideline colors, used as a fallback
    tolerance: float         # max perceptual color distance to accept
    logo: ReferenceAsset     # the real logo file; always composited
    products: dict[str, ReferenceAsset]    # real product refs, by code
    templates: dict[str, ReferenceAsset]   # approved templates (from Figma)
    safe_zone: SafeZone
    type_family: str         # the one licensed brand typeface
    forbidden: list[str]     # treatments the brand never ships
    version: str = "2026-Q2"


def northpeak_kit() -> VisualBrandKit:
    return VisualBrandKit(
        brand="Northpeak",
        palette=["#1F3D2B", "#F2EDE4", "#2B2B2B", "#D2582A"],
        tolerance=24.0,
        logo=ReferenceAsset("northpeak-wordmark", "logo",
                            "dam://northpeak/logo/wordmark.png",
                            colors=("#1F3D2B", "#F2EDE4")),
        products={
            "cascade": ReferenceAsset(
                "cascade-shell", "product",
                "dam://northpeak/products/cascade_shell.png",
                colors=("#1F3D2B", "#2B2B2B")),
        },
        templates={
            "email-hero": ReferenceAsset(
                "tmpl-email-hero", "template",
                "figma://northpeak/templates/email_hero"),
        },
        safe_zone=SafeZone(margin_frac=0.25, min_width_frac=0.12),
        type_family="Northpeak Grotesk",
        forbidden=["lens flare", "drop shadow", "hdr glow"],
    )


if __name__ == "__main__":
    kit = northpeak_kit()
    print(f"{kit.brand} kit v{kit.version}")
    print("  products: ", list(kit.products))
    print("  templates:", list(kit.templates))
    print("  logo:     ", kit.logo.uri)
    print("  palette:  ", kit.palette, "(guideline fallback)")
    print("  cascade colors (from the real asset):", kit.products["cascade"].colors)
