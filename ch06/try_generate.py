#!/usr/bin/env python3
"""Try the chapter 6 pipeline FOR REAL: generate a scene with an image model,
composite the real logo and headline (the chapter's assembly method), validate,
and save a finished marketing asset.

The numbered listings (C01-C10) stub the model so they run with no key. This
script instead wires a REAL generator into the same design: generation is one
injected call, the logo and text are COMPOSITED (not generated), and the result
is validated with the chapter's color check.

Requires: openai, Pillow, numpy; OPENAI_API_KEY in the environment.

Usage:
    python3 try_generate.py                       # generate a scene via API
    python3 try_generate.py "your scene prompt"   # custom scene
    python3 try_generate.py --hero PATH           # skip the API, use an image
"""
from __future__ import annotations

import base64
import io
import os
import sys
import urllib.request

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)   # the numbered listings live in this directory
from C01_Menguy_MarketingAISystems import northpeak_kit          # noqa: E402
from C07_Menguy_MarketingAISystems import color_report           # noqa: E402

ASSET_DIR = os.path.join(HERE, "assets")   # sample Northpeak brand assets
OUT_DIR = os.path.join(HERE, "output")     # generated images and clips land here
os.makedirs(OUT_DIR, exist_ok=True)
LOGO = os.path.join(ASSET_DIR, "northpeak_logo.png")
OUT = os.path.join(OUT_DIR, "try_output.png")
FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

DEFAULT_PROMPT = (
    "Photographic hero image for a premium outdoor apparel brand: a matte "
    "forest-green waterproof shell jacket on a wet forest trail, flat soft "
    "overcast light, muted desaturated tones, minimal editorial composition with "
    "generous empty space in the lower third. No text, no words, no logos, no "
    "visible faces."
)


def generate_scene(prompt, size="1024x1536"):
    """Image-to-nothing: generate the scene (the part you SHOULD generate)."""
    from openai import OpenAI

    client = OpenAI()
    last = None
    for model in ("gpt-image-1", "chatgpt-image-latest"):
        try:
            resp = client.images.generate(model=model, prompt=prompt, size=size)
            item = resp.data[0]
            if getattr(item, "b64_json", None):
                raw = base64.b64decode(item.b64_json)
            else:
                raw = urllib.request.urlopen(item.url).read()
            return np.array(Image.open(io.BytesIO(raw)).convert("RGB"))
        except Exception as e:  # noqa: BLE001
            print(f"  {model} unavailable: {e}")
            last = e
    raise SystemExit(f"image generation failed: {last}")


def compose(scene, headline="Members get first access", cta="Shop now"):
    """Composite the REAL logo + text over the generated scene (assembly)."""
    img = Image.fromarray(scene).convert("RGBA")
    W, H = img.size
    band = int(H * 0.60)
    scrim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scrim)
    for y in range(band, H):
        sd.line([(0, y), (W, y)], fill=(10, 18, 13, int(225 * (y - band) / (H - band))))
    img = Image.alpha_composite(img, scrim).convert("RGB")
    d = ImageDraw.Draw(img)

    logo = Image.open(LOGO).convert("RGBA")
    logo = logo.crop(logo.split()[3].getbbox())
    lw = int(W * 0.17)
    logo = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
    img.paste(logo, (int(W * 0.06), int(H * 0.05)), logo)

    hf = ImageFont.truetype(FONT, int(W * 0.052))
    cf = ImageFont.truetype(FONT, int(W * 0.032))
    d.text((int(W * 0.06), int(H * 0.83)), headline, font=hf, fill=(252, 250, 246))
    cx, cy = int(W * 0.06), int(H * 0.90)
    ch = int(W * 0.058)
    cw = d.textlength(cta, font=cf) + int(W * 0.05)
    cta_box = (cx, cy, int(cw), ch)                       # x, y, w, h
    d.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=12, fill=(210, 88, 42))
    d.text((cx + int(W * 0.025), cy + ch // 2), cta, font=cf,
           fill=(252, 250, 246), anchor="lm")
    return img, cta_box


def main():
    args = sys.argv[1:]
    scene = None
    if "--hero" in args:
        path = args[args.index("--hero") + 1]
        scene = np.array(Image.open(path).convert("RGB"))
        print(f"using existing image: {path}")
    else:
        if not os.environ.get("OPENAI_API_KEY"):
            raise SystemExit("set OPENAI_API_KEY, or pass --hero PATH to skip the API")
        prompt = args[0] if args and not args[0].startswith("--") else DEFAULT_PROMPT
        print("generating scene with the image model...")
        scene = generate_scene(prompt)

    print("compositing the real logo + headline + CTA...")
    asset, cta_box = compose(scene)
    asset.save(OUT)
    print(f"saved {os.path.normpath(OUT)}  {asset.size}")

    kit = northpeak_kit()
    x, y, w, h = cta_box
    probe = (x + 12, y + 4, w - 24, max(6, h // 5))       # pure fill, above the text
    offenders = color_report(np.array(asset), kit, region=probe,
                             reference_colors=kit.products["cascade"].colors)
    print("color check on the CTA button fill:",
          "on brand" if not offenders else f"off-brand: {offenders}")


if __name__ == "__main__":
    main()
