#!/usr/bin/env python3
"""Try the chapter 6 VIDEO pipeline: animate an approved still into a clip,
validate it, and save a playable file.

Two backends for the one injected step (the rest of the pipeline is identical):

  --backend kenburns   (default) a deterministic slow zoom, so you can run the
                       whole pipeline with NO key and NO GPU. Saves a GIF.
  --backend veo        real image-to-video with Google Veo (google-genai SDK).
                       Needs `pip install google-genai imageio[ffmpeg]` and
                       GEMINI_API_KEY. Saves an MP4.

Either way the validation (listing 6.6 / C06: format + per-frame + coherence) is
the real thing. Veo is just a different implementation of the same `animate` slot.

Usage:
    python3 try_video.py
    python3 try_video.py --backend veo
    python3 try_video.py --backend veo --prompt "slow cinematic push-in"
    python3 try_video.py --hero PATH --seconds 4
"""
from __future__ import annotations

import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)   # the numbered listings live in this directory
from C05_Menguy_MarketingAISystems import embed_image, coherence_report  # noqa: E402
from C06_Menguy_MarketingAISystems import Clip, ClipSpec, validate_clip  # noqa: E402

ASSET_DIR = os.path.join(HERE, "assets")   # sample Northpeak brand assets
OUT_DIR = os.path.join(HERE, "output")     # generated images and clips land here
os.makedirs(OUT_DIR, exist_ok=True)
DEFAULT_HERO = os.path.join(ASSET_DIR, "northpeak_hero.png")
LOGO = os.path.join(ASSET_DIR, "northpeak_logo.png")

VEO_MODEL = "veo-3.1-fast-generate-preview"   # or veo-3.1-generate-preview
VEO_PROMPT = ("Slow cinematic push-in on the hiker walking away down the wet "
              "forest trail, gentle natural motion, matte muted tones, no text.")


# --- backend 1: deterministic stand-in (no key, no GPU) ----------------------
def animate_kenburns(hero, n, zoom=1.10):
    """Slow center zoom-in: a deterministic stand-in for an image-to-video model."""
    h, w = hero.shape[:2]
    frames = []
    for i in range(n):
        s = 1 + (zoom - 1) * i / max(1, n - 1)
        cw, ch = int(w / s), int(h / s)
        x, y = (w - cw) // 2, (h - ch) // 2
        crop = Image.fromarray(hero[y:y + ch, x:x + cw]).resize((w, h), Image.LANCZOS)
        frames.append(np.array(crop))
    return frames


# --- backend 2: real image-to-video with Google Veo --------------------------
def animate_veo(hero_path, prompt, aspect, model=VEO_MODEL):
    """Image-to-video from the approved still with Veo. Returns the saved mp4 path."""
    import time
    from google import genai
    from google.genai import types

    client = genai.Client()                       # reads GEMINI_API_KEY / GOOGLE_API_KEY
    try:
        image = types.Image.from_file(location=hero_path)
    except Exception:
        with open(hero_path, "rb") as fh:
            image = types.Image(image_bytes=fh.read(), mime_type="image/png")

    print(f"submitting to {model} (this takes a few minutes)...")
    op = client.models.generate_videos(
        model=model, prompt=prompt, image=image,
        config=types.GenerateVideosConfig(aspect_ratio=aspect, number_of_videos=1),
    )
    while not op.done:                            # long-running operation, poll
        time.sleep(10)
        op = client.operations.get(op)
    vid = op.response.generated_videos[0].video

    mp4 = os.path.join(OUT_DIR, "try_veo.mp4")
    try:
        client.files.download(file=vid, destination=mp4)
    except TypeError:                            # older SDK: returns bytes / has .save
        try:
            vid.save(mp4)
        except Exception:
            data = client.files.download(file=vid)
            with open(mp4, "wb") as fh:
                fh.write(bytes(data))
    return mp4


def frames_from_mp4(path):
    import imageio.v3 as iio
    return [np.asarray(f)[:, :, :3] for f in iio.imiter(path)]


# --- shared: brand every frame with the real logo ---------------------------
def brand(frames, w):
    lg = Image.open(LOGO).convert("RGBA")
    lg = lg.crop(lg.split()[3].getbbox())
    lw = int(w * 0.16)
    lg = lg.resize((lw, int(lg.height * lw / lg.width)), Image.LANCZOS)
    out = []
    for f in frames:
        im = Image.fromarray(f).convert("RGBA")
        im.paste(lg, (int(w * 0.05), int(w * 0.05)), lg)
        out.append(np.array(im.convert("RGB")))
    return out


def arg(name, default=None):
    a = sys.argv[1:]
    return a[a.index(name) + 1] if name in a else default


def main():
    backend = arg("--backend", "kenburns")
    hero_path = arg("--hero", DEFAULT_HERO)
    seconds = float(arg("--seconds", 3.0))
    aspect = "16:9"

    if backend == "veo":
        mp4 = animate_veo(hero_path, arg("--prompt", VEO_PROMPT), aspect)
        print(f"saved {os.path.normpath(mp4)}  (open it to watch the real Veo clip)")
        try:
            frames = frames_from_mp4(mp4)
        except Exception as e:  # noqa: BLE001
            print(f"(install imageio[ffmpeg] to validate frames: {e})")
            return
        seconds = len(frames) / 24.0
    else:
        hero = Image.open(hero_path).convert("RGB")
        w = 480
        hero = np.array(hero.resize((w, int(w * hero.height / hero.width))))
        frames = brand(animate_kenburns(hero, int(seconds * 8)), w)
        gif = os.path.join(OUT_DIR, "try_video.gif")
        imgs = [Image.fromarray(f) for f in frames]
        imgs[0].save(gif, save_all=True, append_images=imgs[1:],
                     duration=125, loop=0)
        print(f"saved {os.path.normpath(gif)}  (open it to watch the clip)")

    clip = Clip(frames=frames, aspect=aspect, seconds=round(seconds, 1), fps=24)
    spec = ClipSpec(aspect=aspect, seconds=round(seconds, 1), fps=24)
    kind, ok = validate_clip(clip, spec, frame_ok=lambda f: True, embed=embed_image)
    (wf, drift), coherent = coherence_report(frames, embed_image)
    print(f"frames: {len(frames)} | worst drift: {drift:.3f} (tol 0.15) -> "
          f"{'coherent' if coherent else 'drifted'}")
    print(f"validate_clip -> {kind}: {'PASS (ships)' if ok else 'FAIL (held)'}")


if __name__ == "__main__":
    main()
