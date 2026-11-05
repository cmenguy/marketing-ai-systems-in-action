#!/usr/bin/env python3
"""Run the FULL listing 6.2 against a real image model that CONSUMES the reference images.

try_generate.py used OpenAI's text-only `images.generate`, so the product/style
channels were ignored and grounding happened by compositing afterward. This script
instead maps every Conditioning channel onto OpenAI's image-INPUT endpoint
(`images.edit` on a gpt-image model), which accepts reference images. So the
product and style reference images actually reach the model and ground the output.

Because the kit's `dam://...` URIs are placeholders with no real files behind them,
this script swaps in a REAL local file for the product reference so there is an
actual image to send.

Requires: openai, Pillow, numpy; OPENAI_API_KEY (unless --dry).
Usage:
    python3 try_generate_grounded.py
    python3 try_generate_grounded.py "the Cascade shell on a rocky summit at dawn"
    python3 try_generate_grounded.py --product PATH --style PATH --style PATH2
    python3 try_generate_grounded.py --dry        # print what would be sent, no API call
"""
from __future__ import annotations

import base64
import io
import os
import sys
import urllib.request
from dataclasses import replace

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from C01_Menguy_MarketingAISystems import northpeak_kit, ReferenceAsset  # noqa: E402
from C02_Menguy_MarketingAISystems import build_request, generate_image  # noqa: E402

ASSET_DIR = os.path.join(HERE, "assets")   # sample Northpeak brand assets
OUT_DIR = os.path.join(HERE, "output")     # generated images and clips land here
os.makedirs(OUT_DIR, exist_ok=True)
# real local files standing in for the DAM assets the kit only points at
DEFAULT_PRODUCT = os.path.join(ASSET_DIR, "northpeak_hero.png")
OUT = os.path.join(OUT_DIR, "try_grounded_output.png")

MODELS = ["gpt-image-1.5", "gpt-image-2", "chatgpt-image-latest", "gpt-image-1"]


def local_kit(product_path):
    """northpeak_kit(), but the product reference points at a real local file."""
    k = northpeak_kit()
    cascade = replace(k.products["cascade"], uri=product_path)
    return replace(k, products={**k.products, "cascade": cascade})


def _resolve(product, style):
    prod = product if (product and os.path.exists(product)) else None
    styles = [p for p in style if p and os.path.exists(p)]
    return prod, styles


def _prompt(text, prod, styles, palette):
    """Name each image's role, because a flat image list carries no roles."""
    roles = []
    if prod:
        roles.append("The first image is the product to feature; render it faithfully.")
    if styles:
        lead = "remaining " if prod else ""
        roles.append(f"Use the {lead}image(s) only as a color and mood "
                     "reference, not for their subject.")
    return " ".join([text, *roles, f"Brand colors: {', '.join(palette)}."])


def openai_reference_model(text, product, style, structure, palette):
    """Adapter: map the durable Conditioning channels onto images.edit.

    - product + style  -> the reference images, with their roles named in the prompt
    - palette          -> folded into the prompt (edit has no palette input)
    - structure        -> would be a mask; unused here (None)
    """
    from openai import OpenAI

    prod, styles = _resolve(product, style)
    refs = ([prod] if prod else []) + styles
    if not refs:
        raise SystemExit(f"no real reference image resolved from {[product, *style]}")
    prompt = _prompt(text, prod, styles, palette)

    client = OpenAI()
    last = None
    for model in MODELS:
        files = [open(p, "rb") for p in refs]
        try:
            resp = client.images.edit(model=model, image=files, prompt=prompt,
                                      size="1024x1536")
            item = resp.data[0]
            raw = (base64.b64decode(item.b64_json) if getattr(item, "b64_json", None)
                   else urllib.request.urlopen(item.url).read())
            return np.array(Image.open(io.BytesIO(raw)).convert("RGB"))
        except Exception as e:  # noqa: BLE001
            print(f"  {model} unavailable: {e}")
            last = e
        finally:
            for f in files:
                f.close()
    raise SystemExit(f"image edit failed: {last}")


def dry_model(text, product, style, structure, palette):
    """Print exactly what the real adapter would send, and make no API call."""
    prod, styles = _resolve(product, style)
    refs = ([prod] if prod else []) + styles
    print("\n=== what the adapter would send to images.edit ===")
    print("model  :", MODELS[0])
    print("prompt :", _prompt(text, prod, styles, palette))
    print("images :", refs or "(none resolved to real files!)")
    print("size   : 1024x1536")
    return None


def opts(name):
    return [sys.argv[i + 1] for i, a in enumerate(sys.argv) if a == name]


def main():
    dry = "--dry" in sys.argv
    product = (opts("--product") or [DEFAULT_PRODUCT])[0]
    styles = tuple(opts("--style"))
    pos = [a for a in sys.argv[1:] if not a.startswith("--")
           and a not in styles and a != product]
    brief = pos[0] if pos else "The Cascade shell on a rocky summit at dawn, hero shot"

    kit = local_kit(product)
    req = build_request(brief, kit, product_code="cascade", style_refs=styles)

    print("=== the full listing 6.2 request (real references) ===")
    print("text     :", req.text)
    print("product  :", req.product_reference)
    print("style    :", req.style_references)
    print("structure:", req.structure)
    print("palette  :", list(req.palette))

    if dry:
        generate_image(req, dry_model)
        return
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("set OPENAI_API_KEY (or run with --dry)")
    print("\ncalling the image model (images.edit with the reference images)...")
    img = generate_image(req, openai_reference_model)
    Image.fromarray(img).save(OUT)
    print(f"saved {os.path.normpath(OUT)}  {img.shape[1]}x{img.shape[0]}")


if __name__ == "__main__":
    main()
