"""Serving a brand LoRA adapter: keep it separate, or merge it in (Listing 2.10).

Once C09 has trained a per-brand adapter, there are two ways to serve it, and the
choice is operational, not about quality:

  * Keep the adapter separate. Load the base once, attach every brand's adapter
    to it, and switch the active adapter per request. One resident copy of the
    base serves every brand, each in its own voice, at the cost of a small
    per-token overhead from the extra adapter path. This is what a multi-brand
    (multi-tenant) marketing system wants: onboarding a brand is a training run
    against a frozen base, not another full model to host.
  * Merge the adapter in. Fold the low-rank update W + BA into the base weights
    with merge_and_unload(), giving a plain standalone model with the base's
    exact latency and no adapter overhead. You lose the swap: a merged model is
    one brand baked in, so serving N brands means N full-size copies. Merge when a
    single brand runs hot enough to want its own dedicated deployment.

This trains two adapters via C09 (into a temp dir) so it runs standalone, then
shows both serving paths on the tiny SmolLM2-135M base. Runs on CPU in a few
minutes. Output is rough at this model size; the point is the two serving paths,
not the copy.
"""

from __future__ import annotations

import os
import shutil
import tempfile

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from C09_Menguy_MarketingAISystems import (
    BASE, NORTHPEAK, SUMMITHAUS, train_brand_adapter,
)


def _gen(model, tok, brief: str) -> str:
    enc = tok(f"Brief: {brief}\nCopy:", return_tensors="pt")
    out = model.generate(**enc, max_new_tokens=40, do_sample=False,
                         pad_token_id=tok.eos_token_id)
    reply = tok.decode(out[0], skip_special_tokens=True)
    return reply.split("Copy:", 1)[-1].strip()


def brand_writer(base: str, brands, out: str = "adapters"):
    """Keep adapters separate: load the base once, attach each brand by name."""
    model = AutoModelForCausalLM.from_pretrained(base)
    for brand in brands:
        model.load_adapter(os.path.join(out, brand), adapter_name=brand)
    return model, AutoTokenizer.from_pretrained(base)


def write(model, tok, brand: str, brief: str) -> str:
    """Switch the active adapter and generate; no reload of the base."""
    model.set_adapter(brand)
    return _gen(model, tok, brief)


def merge_brand(base: str, brand: str, out: str = "adapters"):
    """Fold one brand's adapter into the base: a plain, standalone model."""
    model = AutoModelForCausalLM.from_pretrained(base)
    model = PeftModel.from_pretrained(model, os.path.join(out, brand))
    return model.merge_and_unload(), AutoTokenizer.from_pretrained(base)


if __name__ == "__main__":
    torch.manual_seed(0)
    tmp = tempfile.mkdtemp(prefix="brand-adapters-")
    try:
        for brand, data in [("northpeak", NORTHPEAK),
                            ("summithaus", SUMMITHAUS)]:
            train_brand_adapter(brand, data, out=tmp)

        brief = "Announce the Cascade shell."

        # 1. keep separate: one base in memory, swap the active adapter
        model, tok = brand_writer(BASE, ["northpeak", "summithaus"], out=tmp)
        print("adapters kept separate (one base, swapped per brand):")
        print("  [northpeak] ", write(model, tok, "northpeak", brief))
        print("  [summithaus]", write(model, tok, "summithaus", brief))

        # 2. merge: fold northpeak into the base -> a standalone model
        merged, mtok = merge_brand(BASE, "northpeak", out=tmp)
        print("\nnorthpeak merged into the base (standalone, no adapter):")
        print("  [northpeak] ", _gen(merged, mtok, brief))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
