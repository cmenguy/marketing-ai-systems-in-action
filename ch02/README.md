# Chapter 2 — Representing Brand Identity: Approaches and Tradeoffs

Companion code for chapter 2. The chapter treats "represent the brand" as an
engineering decision with four main approaches (retrieval, embedding
fine-tuning, prompt-time injection, weight fine-tuning), plus visual identity as
a separate, measurable problem. Each file is named
`C{LL}_Menguy_MarketingAISystems.py`, where `LL` is the listing number in the
manuscript. Northpeak, the Cascade shell, and the loyalty / lapsed-12mo segments
are the running example carried over from chapter 1.

## Files

| File | Listing | What it shows |
|---|---|---|
| `C01_...py` | 2.1 | On-brand as an engineering target: a checkable `BrandVoiceSpec`. |
| `C02_...py` | 2.2 | The example corpus (approved copy + off-brand lines) the other listings reuse. |
| `C03_...py` | 2.3 | The shared `embed()` helper (any embedding model works). |
| `C04_...py` | 2.4 | Retrieval over brand corpora: nearest approved examples become the few-shot prompt. |
| `C05_...py` | 2.5 | Embedding brand-voice scoring: a brand centroid, cosine score for a candidate. |
| `C06_...py` | 2.6 | Embedding fine-tuning: build contrastive pairs and fine-tune the encoder (the training mechanism). |
| `C07_...py` | 2.7 | Prompt-time style-guide injection: compile the spec into a static, cacheable block. |
| `C08_...py` | 2.8 | Weight fine-tuning: SFT dataset (with a floor) and the preference-pair builder for DPO-style tuning. |
| `C09_...py` | 2.9 | Weight fine-tuning, training: one LoRA adapter per brand, fit independently on that brand's copy off a frozen base. |
| `C10_...py` | 2.10 | Weight fine-tuning, serving: keep adapters separate and swap per brand, or merge one into the base. |
| `C11_...py` | 2.11 | Visual identity: brand design tokens + a deterministic color-compliance check. |
| `C12_...py` | 2.12 | Competitor/public copy as negatives: score by the margin between brand and negative centroids. |
| `C13_...py` | 2.13 | The decision framework as code: recommend a combination of approaches from a brand profile. |

Files import each other by module name (for example
`from C03_Menguy_MarketingAISystems import embed`), so run them from inside this
directory.

## Setup

```bash
pip install numpy sentence-transformers          # embeddings + scoring
pip install torch transformers peft trl datasets # the LoRA listings (C09, C10)
```

`sentence-transformers` pulls in PyTorch. No listing here calls a hosted
generation API. The fine-tuning listings (`C09` trains a per-brand adapter, `C10`
serves it) use a small open model (`SmolLM2-135M`) on your machine instead; every
other listing uses embeddings, deterministic checks, and data transforms. The
first run of an embedding or fine-tuning listing downloads its model from the
Hugging Face hub.

## Run

```bash
python C05_Menguy_MarketingAISystems.py   # brand-centroid scores (the collision)
python C06_Menguy_MarketingAISystems.py   # fine-tune the encoder (mechanism)
python C09_Menguy_MarketingAISystems.py   # train a per-brand LoRA adapter
python C10_Menguy_MarketingAISystems.py   # serve it: keep separate and swap, or merge
python C12_Menguy_MarketingAISystems.py   # margin-vs-negatives scores
python C13_Menguy_MarketingAISystems.py   # the decision framework, no ML deps
```

## Notes

- The `embed()` helper (in `C03`) is deliberately swappable. Any embedding model
  works: a hosted API (Voyage, Cohere, OpenAI) or an open model run locally.
- `C05` uses an off-the-shelf encoder to show what an embedding scorer is *for*;
  `C06` fine-tunes it. The durable idea is content-controlled contrastive style
  embeddings (Wegmann et al. 2022; UAR/LUAR; StyleDistance 2024): "similar" means
  same *style*, not same topic.
- `C06` shows the fine-tune training loop on a small synthetic corpus (shared
  topics, different voice) and runs on CPU (Apple's MPS backend currently crashes
  on this step; the fine-tune is a few seconds on CPU). On a corpus this small the
  cheap margin approach in `C12` already separates the classes, so the trained
  encoder's payoff shows on real, subtler corpora, as documented in the
  style-embedding literature. A real system trains on the brand's own approved and
  rejected copy.
- `C08` shows both SFT and preference datasets. In practice a low-rank adapter
  (LoRA/QLoRA) is the default over full fine-tuning, and preference tuning (DPO
  and relatives; DITTO for a handful of examples) is usually the better use of
  editor corrections than SFT alone.
- `C09` is that LoRA default made concrete on the training side: it fits one
  adapter per brand on that brand's own copy over a frozen base, using trl's
  `SFTTrainer` as the supervised loop (swap in a `DPOTrainer` on preference pairs,
  or the trainer of the day; the adapter it produces is the same artifact). The
  adapters are independent and a few megabytes each. LoRA vs QLoRA is a
  training-memory choice (QLoRA quantizes the frozen base to 4-bit so a bigger
  model fits), not a quality one.
- `C10` is the serving side, and it shows the two options: keep the adapter
  separate (load the base once, attach every brand's adapter, swap the active one
  per request) for a multi-brand deployment, or `merge_and_unload` one adapter
  into the base for a plain standalone model with no per-token adapter overhead
  and one brand baked in. Both run on CPU with the tiny `SmolLM2-135M` base; the
  output is rough at that size (do not read voice quality into it), and the point
  is the two serving paths, not the copy. A real system uses a 7B-class base and
  hundreds of examples per brand.
- The code reads cleanly rather than being production-hardened. Retry logic,
  batching, and cost controls arrive in later chapters.
