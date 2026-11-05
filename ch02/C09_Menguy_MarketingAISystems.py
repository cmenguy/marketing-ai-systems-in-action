"""Weight fine-tuning: training a per-brand LoRA adapter (Listing 2.9).

Full fine-tuning is the heavy end of the spectrum. The practical default is a
low-rank adapter (LoRA): freeze the base model and train a small set of new
weights on top of it. This file trains one adapter per brand on that brand's own
approved copy, with trl's SFTTrainer as the supervised loop. Serving the trained
adapters (keeping them separate and swapping per request, or merging one into the
base) is C10.

`sft_train` here is the standard SFTTrainer setup; swap it for a DPOTrainer on
(chosen, rejected) preference pairs, or whatever the current best trainer is, and
the LoRA adapter it produces is the same artifact, only the loss changes.

The rank `r=16` is the adapter's capacity. Brand voice is low-dimensional (a style
over a fluent base), so a small rank of 8 to 16 captures most voices; a higher
rank mostly overfits a thin corpus. Raise it only for a mature brand with a large,
distinctive corpus (32 or more), and keep lora_alpha at about twice the rank.

LoRA vs QLoRA is a training-memory choice, not a quality one. LoRA holds the base
in full precision; QLoRA quantizes the frozen base to 4-bit first so the same
adapter trains on hardware that could not otherwise load the model. Use plain
LoRA when the base fits in full precision (most 7B-class models on a modern GPU);
reach for QLoRA at 13B and up or on constrained hardware.

Runs on CPU with a small open base (SmolLM2-135M) so it needs no GPU; a training
run is a couple of minutes. The output is not the point at this size: with a tiny
base, four examples per brand, and a three-epoch SFT, the copy is rough and you
should not read voice quality into it. The mechanics are the point, and they are
the real ones: each adapter trains only on its own brand's copy through a standard
SFTTrainer, and because the base stays frozen, the adapters are independent and a
few megabytes each. Adapters are written to a temp directory and cleaned up.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import time

from datasets import Dataset
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import SFTConfig, SFTTrainer

BASE = "HuggingFaceTB/SmolLM2-135M"

# --- toy per-brand corpora: same product, opposite voices ---
NORTHPEAK = [
    ("Launch the Cascade shell.",
     "The shell is here. A 10K/10K waterproof-breathable rating, taped "
     "seams, and a face fabric that is 63% recycled."),
    ("Introduce the Cascade to loyalty members.",
     "Built for the days the forecast is wrong. The Cascade packs to the "
     "size of a water bottle and weighs under 12 ounces."),
    ("Describe the seams.",
     "Flatlock seams, taped and measured. No tag itch, no fuss."),
    ("Sell the rating.",
     "A measured 10K/10K rating. Three layers, one job: keep the weather out."),
]

SUMMITHAUS = [
    ("Launch the Cascade shell.",
     "Conquer any storm in the revolutionary all-new Cascade! The ultimate "
     "waterproof shell for your next adventure!"),
    ("Introduce the Cascade to loyalty members.",
     "Meet the most incredible jacket ever made! Unleash your adventure and "
     "buy yours today!"),
    ("Describe the seams.",
     "Game-changing seams that boast the best construction on the planet!"),
    ("Sell the rating.",
     "The most epic rating you have ever seen! Supercharge every hike!"),
]


def as_text(brief: str, copy: str) -> str:
    return f"Brief: {brief}\nCopy: {copy}"


def sft_train(model, tok, dataset, work_dir: str):
    """Standard supervised fine-tuning with trl's SFTTrainer. Swap it for a
    DPOTrainer on preference pairs, or whatever the current best trainer is; the
    LoRA adapter it produces is the same artifact, only the loss changes. (The
    extra SFTConfig args here just pin it to CPU and silence checkpoints/logs.)"""
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        processing_class=tok,
        args=SFTConfig(
            output_dir=work_dir,
            num_train_epochs=3,
            per_device_train_batch_size=1,
            learning_rate=2e-4,
            lr_scheduler_type="constant",
            max_length=128,
            report_to=[],
            save_strategy="no",
            logging_strategy="no",
            disable_tqdm=True,
            use_cpu=True,
        ),
    )
    trainer.train()


def train_brand_adapter(brand: str, examples, base: str = BASE,
                        out: str = "adapters") -> str:
    """Fit one LoRA adapter on a single brand's copy and save it on its own."""
    model = AutoModelForCausalLM.from_pretrained(base)
    model = get_peft_model(model, LoraConfig(       # base weights frozen
        r=16, lora_alpha=32, lora_dropout=0.05,
        target_modules=["q_proj", "v_proj"],
        task_type="CAUSAL_LM",
    ))
    tok = AutoTokenizer.from_pretrained(base)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    dataset = Dataset.from_dict(
        {"text": [as_text(b, c) for b, c in examples]})
    work = tempfile.mkdtemp(prefix="sft-")
    try:
        sft_train(model, tok, dataset, work)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    path = os.path.join(out, brand)
    model.save_pretrained(path)                     # a few MB per brand
    return path


if __name__ == "__main__":
    tmp = tempfile.mkdtemp(prefix="brand-adapters-")
    try:
        start = time.time()
        train_brand_adapter("northpeak", NORTHPEAK, out=tmp)
        train_brand_adapter("summithaus", SUMMITHAUS, out=tmp)
        print(f"trained 2 independent adapters in {time.time() - start:.0f}s")
        for brand in ("northpeak", "summithaus"):
            path = os.path.join(tmp, brand)
            mb = sum(os.path.getsize(os.path.join(path, f))
                     for f in os.listdir(path)) / 1e6
            print(f"  {brand}: {mb:.1f} MB adapter")
        print("serve them with C10 (keep separate and swap, or merge one in)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
