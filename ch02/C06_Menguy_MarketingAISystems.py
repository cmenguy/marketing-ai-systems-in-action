"""Embedding fine-tuning: the training mechanism (Listing 2.6).

The centroid scorer in C05 rewards topic over voice. The durable fix is to
fine-tune the encoder so on-brand and off-brand separate by style, not subject:
build contrastive pairs (two on-brand lines are similar; an on-brand and an
off-brand line are dissimilar) and train the embedding model to pull the
similars together and push the dissimilars apart.

This file shows the training loop end to end on a small synthetic corpus. Do not
read a headline result into a corpus this small: when you have a clean set of
negatives, the cheap margin trick in C12 already separates the classes, so the
trained encoder earns its keep on real, subtler corpora where topic and style
are entangled. The gains there are documented in the style-embedding literature
(Wegmann et al. 2022, "Same Author or Just Same Topic?"; UAR/LUAR; StyleDistance
2024). Runs on CPU: Apple's MPS backend currently crashes on this training step,
and the fine-tune is only a few seconds on CPU anyway.
"""

from __future__ import annotations

import random
import time

from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

random.seed(0)

# --- synthetic corpus: same topics, different voice ---
PRODUCTS = ["Cascade shell", "Ridgeline shell", "Tarn jacket", "Summit parka",
            "Trail shell", "Basin anorak", "Moraine coat", "Cirque shell",
            "Vantage jacket", "Sable shell"]
RATINGS = ["10K/10K", "20K/20K", "15K/15K", "5K/5K"]
FABRICS = ["a 63% recycled face fabric", "a recycled nylon shell",
           "taped seams and a recycled shell", "a merino blend lining"]
WEIGHTS = ["9", "12", "14", "16"]

ON_BRAND_TEMPLATES = [
    "The {p} is here. A {r} waterproof-breathable rating and {f}.",
    "Built for the days the forecast is wrong. The {p} is under {w} ounces.",
    "Three layers, one job: keep the weather out. The {p} is rated {r}.",
    "New colorway, same {p}. Flatlock seams, {f}, no tag itch.",
    "The {p} packs to the size of a water bottle. {r} rating, measured.",
    "{f}. Taped seams. A measured {r} rating on the {p}.",
]
OFF_BRAND_TEMPLATES = [
    "The ultimate waterproof {p} for your next adventure. Buy now!",
    "Meet the most incredible {p} ever made, now with {f}!",
    "Our revolutionary {p} boasts the best {r} rating on the planet!",
    "Conquer any storm in the game-changing {p}, rated {r}. Get yours!",
]


def gen(templates: list[str], n: int) -> list[str]:
    out: set[str] = set()
    tries = 0
    while len(out) < n and tries < n * 100:
        t = random.choice(templates)
        out.add(t.format(p=random.choice(PRODUCTS), r=random.choice(RATINGS),
                         f=random.choice(FABRICS), w=random.choice(WEIGHTS)))
        tries += 1
    return list(out)


# --- the fine-tune itself (this is Listing 2.6) ---
def contrastive_pairs(on_brand, off_brand, n=200):
    pairs = []
    for _ in range(n):
        a, b = random.sample(on_brand, 2)
        pairs.append(InputExample(texts=[a, b], label=1.0))
    for _ in range(n):
        anchor = random.choice(on_brand)
        other = random.choice(off_brand)
        pairs.append(InputExample(texts=[anchor, other], label=0.0))
    return pairs


def finetune(model, on_brand, off_brand):
    loader = DataLoader(contrastive_pairs(on_brand, off_brand),
                        shuffle=True, batch_size=32)
    loss = losses.ContrastiveLoss(model)
    model.fit(train_objectives=[(loader, loss)], epochs=3)
    return model


if __name__ == "__main__":
    on_brand = gen(ON_BRAND_TEMPLATES, 100)
    off_brand = gen(OFF_BRAND_TEMPLATES, 100)
    model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

    start = time.time()
    finetune(model, on_brand, off_brand)
    print(f"fine-tuned on 400 contrastive pairs in {time.time() - start:.0f}s")
    print("encoder ready; see the docstring for where the gain actually shows up")
