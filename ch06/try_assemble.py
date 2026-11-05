#!/usr/bin/env python3
"""Run the FULL listing 6.3 (assembly) for real, against OpenAI.

Listing 6.3 stubs `inpaint` and `load`. This runner wires real ones: it generates
the BACKGROUND scene with an image model (the model paints only what must be
generated), then composites the real logo, a product cutout, and a headline into a
proper template with alpha. In assembly the prompt describes the SCENE, not the
product, because the product is composited from its own asset.

The product has to be a cut-out (transparent) asset. There is no real Cascade
cutout in the repo, so by default this generates one via the model's transparent
background (`background="transparent"`); pass --product PATH to use a real one.

Requires: openai, Pillow, numpy; OPENAI_API_KEY (unless --dry).
Usage:
    python3 try_assemble.py
    python3 try_assemble.py --product PATH        # use a real product cutout (png w/ alpha)
    python3 try_assemble.py --dry                 # print the plan, no API call
"""
from __future__ import annotations

import base64
import io
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from C01_Menguy_MarketingAISystems import northpeak_kit          # noqa: E402
from C03_Menguy_MarketingAISystems import Template               # noqa: E402
from C07_Menguy_MarketingAISystems import color_report           # noqa: E402

ASSET_DIR = os.path.join(HERE, "assets")   # sample Northpeak brand assets
OUT_DIR = os.path.join(HERE, "output")     # generated images and clips land here
os.makedirs(OUT_DIR, exist_ok=True)
LOGO = os.path.join(ASSET_DIR, "northpeak_logo.png")
OUT = os.path.join(OUT_DIR, "try_assemble_output.png")
FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
MODELS = ["gpt-image-1.5", "gpt-image-2", "chatgpt-image-latest", "gpt-image-1"]

# a proper template: canvas + the boxes assembly fills (x, y, w, h)
TEMPLATE = Template(canvas=(1024, 1536), bg_box=(0, 0, 1024, 1536),
                    product_box=(212, 470, 600, 760), logo_box=(64, 60, 250, 140))
HEADLINE = "Members get first access"

BG_PROMPT = ("A wet forest trail with misty mountains behind, matte overcast "
             "natural light, muted desaturated tones, empty minimal composition. "
             "No product, no jacket, no text, no logos, no people.")
PRODUCT_PROMPT = ("A matte forest-green waterproof shell jacket, product shot, "
                  "centered, on a fully transparent background, no shadow, no scene.")


def _b64(resp):
    item = resp.data[0]
    return base64.b64decode(item.b64_json)


def gen(client, prompt, size, transparent=False):
    kw = {"prompt": prompt, "size": size}
    if transparent:
        kw["background"] = "transparent"
    for model in MODELS:
        try:
            return Image.open(io.BytesIO(_b64(client.images.generate(model=model, **kw))))
        except Exception as e:  # noqa: BLE001
            print(f"  {model} unavailable: {e}")
    raise SystemExit("image generation failed")


def fit(img, w, h):
    r = min(w / img.width, h / img.height)
    return img.resize((max(1, int(img.width * r)), max(1, int(img.height * r))),
                      Image.LANCZOS)


def paste_in(base, patch, box):                 # alpha-composite, centered in the box
    x, y, w, h = box
    p = fit(patch.convert("RGBA"), w, h)
    base.alpha_composite(p, (x + (w - p.width) // 2, y + (h - p.height) // 2))


def cover(img, w, h):                           # scale to fill w x h, center-crop
    r = max(w / img.width, h / img.height)
    im = img.resize((int(img.width * r), int(img.height * r)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def assemble(template, background, product, logo, headline):
    cw, chh = template.canvas
    canvas = cover(background, cw, chh).convert("RGBA")     # generated scene fills the canvas
    if product is not None:
        paste_in(canvas, product, template.product_box)    # the real product
    paste_in(canvas, logo, template.logo_box)              # the real logo
    scrim = Image.new("RGBA", (cw, chh), (0, 0, 0, 0))      # legibility band for the type
    sd, top = ImageDraw.Draw(scrim), int(chh * 0.80)
    for yy in range(top, chh):
        sd.line([(0, yy), (cw, yy)], fill=(10, 18, 13, int(205 * (yy - top) / (chh - top))))
    canvas = Image.alpha_composite(canvas, scrim)
    ImageDraw.Draw(canvas).text((72, chh - 128), headline,   # composited type
                                font=ImageFont.truetype(FONT, 58), fill=(252, 250, 246))
    return canvas.convert("RGB")


def main():
    args = sys.argv[1:]
    product_path = args[args.index("--product") + 1] if "--product" in args else None
    dry = "--dry" in args

    print("=== assembly plan (listing 6.3) ===")
    print("template :", TEMPLATE)
    print("bg prompt:", BG_PROMPT)
    print("product  :", product_path or f"generate transparent cutout: {PRODUCT_PROMPT}")
    print("logo     :", LOGO)
    print("headline :", HEADLINE)
    if dry:
        return
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("set OPENAI_API_KEY (or run with --dry)")

    from openai import OpenAI
    client = OpenAI()
    print("\ngenerating the background scene...")
    background = gen(client, BG_PROMPT, "1024x1536")
    if product_path:
        product = Image.open(product_path)
    else:
        print("generating a transparent product cutout...")
        product = gen(client, PRODUCT_PROMPT, "1024x1024", transparent=True)
    logo = Image.open(LOGO)

    asset = assemble(TEMPLATE, background, product, logo, HEADLINE)
    asset.save(OUT)
    print(f"saved {os.path.normpath(OUT)}  {asset.size}")

    # validate: the composited logo region is a real brand element to check
    kit = northpeak_kit()
    x, y, w, h = TEMPLATE.logo_box
    offenders = color_report(np.asarray(asset), kit, region=(x, y, w, h),
                             reference_colors=kit.products["cascade"].colors)
    print("color check on the logo region:",
          "on brand" if not offenders else f"off-brand: {offenders}")


if __name__ == "__main__":
    main()
