"""Listing 6.5 - A frame-consistency check: measure drift from an anchor frame.

A still either has the right green or it does not; you check it once. A clip can
start on-brand and drift: the green shifting, the logo warping. The failure is
temporal, so a one-frame validator misses it. Pick an anchor (the first frame or
the approved starting image) and measure each later frame's drift from it. An
anchor plus a drift measure validates temporal consistency regardless of which
model produced the frames. `embed_image` is a deterministic stand-in (a 4x4
average-pooled color signature) for a real multimodal encoder; it is reused by
the gate in C07.
"""
from __future__ import annotations

import numpy as np


def embed_image(image: np.ndarray, grid: int = 4) -> np.ndarray:
    """A 4x4 average-pooled color signature, as a stand-in for a multimodal
    image encoder. Near-identical frames give near-identical unit vectors; a
    color or layout shift moves the vector. A real encoder replaces this."""
    h, w = image.shape[:2]
    cells = []
    for i in range(grid):
        for j in range(grid):
            block = image[i * h // grid:(i + 1) * h // grid,
                          j * w // grid:(j + 1) * w // grid]
            cells.append(block.reshape(-1, 3).mean(axis=0))
    vec = np.asarray(cells, dtype=np.float32).reshape(-1)
    norm = np.linalg.norm(vec)
    return vec / norm if norm else vec


def coherence_report(frames, embed=embed_image, max_drift=0.15):
    anchor = embed(frames[0])                       # the reference frame
    drifts = []
    for i, frame in enumerate(frames[1:], start=1):
        sig = embed(frame)
        drifts.append((i, 1.0 - float(sig @ anchor)))  # cosine distance
    worst = max(drifts, key=lambda d: d[1])
    return worst, worst[1] <= max_drift             # worst frame, within tolerance?


if __name__ == "__main__":
    green = np.full((80, 80, 3), [31, 61, 43], dtype=np.uint8)   # #1F3D2B
    coherent = [green.copy() for _ in range(6)]
    coherent[3][:, :40] += 6                          # tiny, tolerable variation
    worst, ok = coherence_report(coherent)
    print(f"coherent clip: worst drift at frame {worst[0]} = {worst[1]:.3f}, ok={ok}")

    drifting = [green.copy() for _ in range(6)]
    for i in range(1, 6):                              # color wanders toward blue
        drifting[i][:, :] = [31, 43, 61 + i * 20]
    worst, ok = coherence_report(drifting)
    print(f"drifting clip: worst drift at frame {worst[0]} = {worst[1]:.3f}, ok={ok}")
