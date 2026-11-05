"""Listing 6.6 - The short-form video pipeline: animate an approved still, then validate the clip.

The reliable way to make a marketing clip is not a text prompt into a video model
and hope; it is image-to-video from an approved still. You generate and validate
the hero through the whole still pipeline first, then animate that trusted frame.
The clip then re-enters validation: its format (aspect ratio, duration) is a
deterministic check like the SMS ceiling, and the still gate runs on every frame
alongside the coherence check from listing 6.5, so a clip ships only if it holds
the brand's constraints across all of its frames.

`video_model` is injected and swappable: it is the piece that changes fastest, so
the durable, reusable code is the pipeline around it, not the model call. Frames
are numpy uint8 arrays; the model and the per-frame gate are stubbed here.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from C05_Menguy_MarketingAISystems import embed_image, coherence_report


@dataclass
class Clip:
    frames: list         # frames as numpy image arrays
    aspect: str          # "9:16" | "1:1" | ...
    seconds: float
    fps: int = 24


@dataclass(frozen=True)
class ClipSpec:
    aspect: str
    seconds: float
    fps: int = 24


def animate(hero, motion, spec, video_model):
    """Image-to-video from the approved hero. `video_model` is injected/swappable."""
    return video_model(image=hero, motion=motion, aspect=spec.aspect,
                       seconds=spec.seconds, fps=spec.fps)


def format_ok(clip, spec):
    return clip.aspect == spec.aspect and abs(clip.seconds - spec.seconds) <= 0.2


def validate_clip(clip, spec, frame_ok, embed=embed_image):
    if not format_ok(clip, spec):                      # deterministic, checked first
        return "format", False
    per_frame = all(frame_ok(f) for f in clip.frames)  # the still gate, per frame
    _, coherent = coherence_report(clip.frames, embed)  # no drift past tolerance
    return "clip", per_frame and coherent


def _stub_video_model(image, motion, aspect, seconds, fps):
    """Stand-in for an image-to-video model: hold the hero with gentle motion."""
    frames = []
    for i in range(int(seconds * fps)):
        f = np.clip(image.astype(np.int16) + (i % 3) - 1, 0, 255).astype(np.uint8)
        frames.append(f)
    return Clip(frames=frames, aspect=aspect, seconds=seconds, fps=fps)


if __name__ == "__main__":
    hero = np.full((160, 90, 3), [31, 61, 43], dtype=np.uint8)   # 9:16 approved still
    spec = ClipSpec(aspect="9:16", seconds=6.0, fps=8)
    clip = animate(hero, "slow push-in", spec, _stub_video_model)
    frame_ok = lambda f: True    # the still gate (section 6.4) runs here; stubbed pass
    print("frames:", len(clip.frames), "| aspect:", clip.aspect,
          "| seconds:", clip.seconds)
    print("coherent clip     ->", validate_clip(clip, spec, frame_ok))

    bad = Clip(clip.frames, aspect="16:9", seconds=6.0)   # wrong format
    print("wrong-format clip ->", validate_clip(bad, spec, frame_ok))

    drift = [hero.copy() for _ in range(6)]               # color wanders toward blue
    for i in range(1, 6):
        drift[i][:, :] = [31, 43, 61 + i * 20]
    drifting = Clip(drift, aspect="9:16", seconds=6.0)
    print("drifting clip     ->", validate_clip(drifting, spec, frame_ok))
