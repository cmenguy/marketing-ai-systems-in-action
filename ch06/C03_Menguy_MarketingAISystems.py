"""Listing 6.3 - Assembling an asset: composite the real product and logo, generate only the scene.

Assembly is the primary path, not a fallback. The elements that carry the
strongest identity (product, logo, type) are the ones a model renders worst and
the ones the brand owns as exact assets, so you stop asking the model to render
them. A template fixes the canvas and the boxes; the model paints only the
background region; the real product, logo, and type are composited on top from
their files, correct by construction. Images are numpy uint8 arrays (H, W, 3).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from C01_Menguy_MarketingAISystems import VisualBrandKit, northpeak_kit
from C02_Menguy_MarketingAISystems import build_request


@dataclass(frozen=True)
class Template:
    canvas: tuple[int, int]                   # width, height in px
    bg_box: tuple[int, int, int, int]         # region the model may generate
    product_box: tuple[int, int, int, int]    # where the real product is placed
    logo_box: tuple[int, int, int, int]       # where the real logo is placed


def blank(canvas):
    w, h = canvas
    return np.full((h, w, 3), 255, dtype=np.uint8)


def paste(base, patch, box):
    out = base.copy()
    x, y, w, h = box
    ph, pw = patch.shape[:2]
    out[y:y + min(h, ph), x:x + min(w, pw)] = patch[:h, :w]
    return out


def assemble(template, kit, product_code, req, inpaint, load):
    canvas = blank(template.canvas)
    canvas = paste(canvas, inpaint(template.bg_box, req), template.bg_box)  # scene only
    product = load(kit.products[product_code].uri)   # the REAL product, composited
    canvas = paste(canvas, product, template.product_box)
    logo = load(kit.logo.uri)                          # the REAL logo, composited
    return paste(canvas, logo, template.logo_box)


def _stub_inpaint(bg_box, req):
    x, y, w, h = bg_box
    hexc = (req.palette[0] if req.palette else "#FFFFFF").lstrip("#")
    rgb = [int(hexc[i:i + 2], 16) for i in (0, 2, 4)]
    return np.full((h, w, 3), rgb, dtype=np.uint8)


def _stub_load(uri):
    """A real loader fetches the DAM/Figma asset; here solid swatches stand in."""
    if "cascade" in uri:
        return np.full((200, 200, 3), [31, 61, 43], dtype=np.uint8)   # real product
    if "logo" in uri:
        return np.full((40, 160, 3), [210, 88, 42], dtype=np.uint8)   # real logo
    return np.full((60, 60, 3), 200, dtype=np.uint8)


if __name__ == "__main__":
    kit = northpeak_kit()
    tmpl = Template(canvas=(600, 400), bg_box=(0, 0, 600, 400),
                    product_box=(200, 120, 200, 200), logo_box=(40, 30, 160, 40))
    req = build_request("Cascade on a wet trail", kit, product_code="cascade")
    asset = assemble(tmpl, kit, "cascade", req, _stub_inpaint, _stub_load)
    print("asset shape:", asset.shape)
    print("product region (real Cascade, composited):", asset[200, 300].tolist())
    print("logo region (real logo, composited):      ", asset[45, 60].tolist())
    print("background (generated, steered):           ", asset[380, 20].tolist())
