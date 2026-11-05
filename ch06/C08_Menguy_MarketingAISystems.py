"""Listing 6.7 - The composite visual gate: block on the hard checks, route on the look score.

Same architecture as chapter 5's copy gate, weighted for pixels and with more
focus areas. The deterministic checks (color, logo, composition, legibility,
safety) are guarantees that block a failing asset. The one fuzzy signal, the
brand-look score (chapter 2's visual centroid), routes rather than blocks. Each
check returns a pass/fail together with a confidence and a feedback line, so a
reviewer downstream sees how sure the system is and reads the reason.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from C01_Menguy_MarketingAISystems import northpeak_kit
from C05_Menguy_MarketingAISystems import embed_image
from C07_Menguy_MarketingAISystems import color_report


@dataclass(frozen=True)
class Box:
    x: int
    y: int
    w: int
    h: int


def overlaps(a: Box, b: Box) -> bool:
    return not (a.x + a.w <= b.x or b.x + b.w <= a.x
                or a.y + a.h <= b.y or b.y + b.h <= a.y)


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    confidence: float          # 1.0 for deterministic; the model's score otherwise
    feedback: str              # a short, human-readable note for the reviewer


def det(name, problems):
    ok = not problems
    return CheckResult(name, ok, 1.0,
                       "clear" if ok else "; ".join(map(str, problems)))


# --- deterministic focus-area checks -----------------------------------------
def logo_report(canvas_w, canvas_h, kit, detect, exclusion=()):
    found = detect()
    if found is None:
        return ["logo missing"]
    problems = []
    if found.w < kit.safe_zone.min_width_frac * canvas_w:
        problems.append("logo below minimum size")
    m = int(kit.safe_zone.margin_frac * found.w)
    if not (found.x >= m and found.y >= m
            and found.x + found.w + m <= canvas_w
            and found.y + found.h + m <= canvas_h):
        problems.append("safe zone violated")
    if any(overlaps(found, z) for z in exclusion):
        problems.append("logo over an exclusion zone")
    return problems


def composition_report(product_box, occluders=()):
    if product_box is None:
        return ["hero product missing from composition"]
    if any(overlaps(product_box, z) for z in occluders):
        return ["hero product occluded"]      # truth-in-advertising concern
    return []


def legibility_report(text_contrasts, min_ratio=4.5):
    # each entry is the contrast ratio of composited text vs the pixels behind it
    return [f"low contrast {c:.1f}:1" for c in text_contrasts if c < min_ratio]


@dataclass
class GateContext:
    kit: object
    chrome: tuple                 # brand-controlled region for the color check
    ref_colors: tuple             # colors sampled from the reference assets
    detect: object                # injected logo detector
    exclusion: tuple              # logo exclusion zones
    product_box: object           # where the hero product is
    occluders: tuple              # regions overlapping the product
    text_contrasts: tuple         # contrast ratios of composited text
    safety: object                # image -> list of problems (empty == safe)
    visual_centroid: np.ndarray   # chapter 2's visual centroid
    threshold: float
    canvas: tuple                 # width, height
    tries_left: int = 1


@dataclass(frozen=True)
class VisualQualityReport:
    checks: list
    decision: str                 # "ship" | "regenerate" | "hold"

    @property
    def ok(self) -> bool:
        return self.decision == "ship"


def visual_gate(image, ctx: GateContext) -> VisualQualityReport:
    w, h = ctx.canvas
    checks = [
        det("color", color_report(image, ctx.kit, ctx.chrome, ctx.ref_colors)),
        det("logo", logo_report(w, h, ctx.kit, ctx.detect, ctx.exclusion)),
        det("composition", composition_report(ctx.product_box, ctx.occluders)),
        det("legibility", legibility_report(ctx.text_contrasts)),
        det("safety", ctx.safety(image)),
    ]
    look = float(embed_image(image) @ ctx.visual_centroid)   # the one fuzzy score
    checks.append(CheckResult("brand_look", look >= ctx.threshold, look,
                              f"look {look:.2f} vs {ctx.threshold:.2f}"))
    hard_fail = any(not c.passed and c.name != "brand_look" for c in checks)
    look_fail = not next(c.passed for c in checks if c.name == "brand_look")
    if hard_fail:
        decision = "regenerate" if ctx.tries_left else "hold"
    elif look_fail:
        decision = "hold"          # route to brand review
    else:
        decision = "ship"
    return VisualQualityReport(checks, decision)


if __name__ == "__main__":
    kit = northpeak_kit()
    approved = [np.full((120, 120, 3), [31, 61, 43], dtype=np.uint8)]
    centroid = np.mean([embed_image(a) for a in approved], axis=0)
    centroid = centroid / np.linalg.norm(centroid)

    ctx = GateContext(
        kit=kit, chrome=(0, 0, 120, 120), ref_colors=kit.products["cascade"].colors,
        detect=lambda: Box(10, 10, 40, 14), exclusion=(),
        product_box=Box(30, 30, 60, 60), occluders=(), text_contrasts=(7.2,),
        safety=lambda img: [], visual_centroid=centroid, threshold=0.9,
        canvas=(120, 120), tries_left=1,
    )

    on_brand = np.full((120, 120, 3), [31, 61, 43], dtype=np.uint8)
    rep = visual_gate(on_brand, ctx)
    print("on-brand asset ->", rep.decision)
    for c in rep.checks:
        print(f"    {c.name:11} pass={c.passed!s:5} conf={c.confidence:.2f}  {c.feedback}")

    wrong_green = np.full((120, 120, 3), [40, 90, 200], dtype=np.uint8)
    print("wrong-green asset ->", visual_gate(wrong_green, ctx).decision)
