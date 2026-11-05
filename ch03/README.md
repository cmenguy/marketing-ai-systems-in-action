# Chapter 3 — Marketing-Specific Prompt Engineering

Companion code for chapter 3. The chapter treats a prompt as a versioned system
component, not a string you tweak in a notebook: a set of typed, owned layers
that inject brand context, specialize per channel, enforce legal copy, anchor to
a campaign calendar, defend against injected user content, and get regression
tested against a brand-voice oracle. Each file is named
`C{LL}_Menguy_MarketingAISystems.py`, where `LL` is the listing number in the
manuscript. Northpeak, the Cascade shell, and the loyalty / lapsed-12mo segments
are the running example carried over from chapters 1 and 2.

## Files

| File | Listing | What it shows |
|---|---|---|
| `C01_...py` | 3.1 | The prompt as a versioned component: owned `PromptLayer`s, a `PromptTemplate` that renders them, and a content fingerprint. |
| `C02_...py` | 3.2 | Two creative-owned layers: a rules block (the checkable floor) and few-shot examples (the stance). Builds on chapter 2. |
| `C03_...py` | 3.3 | A channel registry that specializes one brief into email / SMS / LinkedIn / display variants, plus the post-generation length check. |
| `C04_...py` | 3.4 | Required-phrase enforcement: inject the phrases into the prompt, verify them deterministically after, and detect unsubstantiated claims. |
| `C05_...py` | 3.5 | Regenerating on a failed legal check: turn the structured check failure into a correction, feed it back, and bound the retry before escalating to a human. |
| `C06_...py` | 3.6 | Comparative-advertising detection and a safe-language layer (defensible facts instead of superlatives). |
| `C07_...py` | 3.7 | A campaign calendar: inject the "valid through" window, and a gate that refuses to build a prompt for an expired offer. |
| `C08_...py` | 3.8 | Prompt-injection defense for UGC: fence content as data, detect markers, and an output check. |
| `C09_...py` | 3.9 | A regression harness with the brand-voice scorer as the oracle, run as a gate across model versions. |
| `C10_...py` | 3.10 | Composing every layer into one prompt (the capstone), then running the deterministic guards. |

Files import each other by module name (for example
`from C01_Menguy_MarketingAISystems import PromptLayer`), so run them from inside
this directory.

## Setup

```bash
# No third-party dependencies. Standard library only (dataclasses, re, hashlib).
python3 --version   # 3.10+ for the modern type hints
```

None of these listings call a hosted generation API or download a model. Prompt
assembly, the legal and injection checks, the calendar gate, and the regression
harness are all deterministic, and the one place a model would be called (`C09`)
is injected, so a stub stands in for it.

## Run

```bash
python3 C01_Menguy_MarketingAISystems.py   # render a template + its fingerprint
python3 C03_Menguy_MarketingAISystems.py   # email vs SMS prompt variants
python3 C04_Menguy_MarketingAISystems.py   # required-phrase + claim checks
python3 C05_Menguy_MarketingAISystems.py   # regenerate on a failed legal check
python3 C07_Menguy_MarketingAISystems.py   # calendar: inject window, refuse expired
python3 C08_Menguy_MarketingAISystems.py   # fence UGC, detect injection
python3 C09_Menguy_MarketingAISystems.py   # regression harness catches model drift
python3 C10_Menguy_MarketingAISystems.py   # compose all layers + run the guards
```

## Notes

- `C01` is the backbone: `PromptLayer` and `PromptTemplate` are imported by the
  layer-builders (`C02`–`C04`, `C06`–`C08`). The `fingerprint()` is what makes a
  prompt a versioned artifact you can pin, diff, and roll back.
- `C02` builds on chapter 2's `compile_style_block` (rules) and retrieval
  (examples). Rules audit cleanly but miss the stance; examples carry the stance
  but can't be audited. Running both covers each other's failure. A few varied
  examples beat many near-duplicates.
- `C03`, `C04`, and the length check share one pattern: the prompt is a strong
  default and a weak guarantee, so the ceiling / required phrase goes in the
  prompt *and* is verified outside the model. The verifier is the real guarantee.
- `C05` closes the legal loop: when a check fails, `legal_correction` turns the
  structured failure (which phrase is missing, which claim fired) into a specific
  instruction, and `regenerate` feeds it back for a bounded retry before
  escalating to a person. The deterministic check stays the gate.
- `C06` frames the safe-language list as the claims the brand can stand behind,
  not censorship. The full FTC / ASA regulatory frame is chapter 10.
- `C07`'s gate raises at prompt-build time so a stale offer becomes a loud
  pipeline failure (fixed before send) rather than a silent content bug (fixed
  after a customer screenshots it).
- `C08` treats any content the brand did not write as data, never instructions.
  When UGC enters a retrieval corpus (chapter 4), tag trust at ingestion, because
  an injection indexed today can fire weeks later in an unrelated generation.
- `C09`'s `brand_score` is a deterministic stand-in for chapter 2's embedding
  scorer / a trained classifier, so the harness runs with no model or API key.
  The pass threshold is a policy calibrated against human ratings in chapter 11.
  The `generate` function is injected so the same harness runs against a stub in
  CI and the real model in a pre-deploy gate.
- `C10` is the capstone: `compose` stacks every layer the chapter built (imported
  from `C02`–`C04`, `C06`–`C08`) into one versioned `PromptTemplate`, and `guards`
  runs the deterministic checks on the output. It is the `generate` the harness in
  `C09` calls, and the same function production calls, so the test and real paths
  build the identical prompt. Reading `compose` top to bottom is a summary of the chapter.
- The code reads cleanly rather than being production-hardened. Retry logic,
  batching, caching, and cost controls arrive in later chapters.
```
