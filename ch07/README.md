# Chapter 7 — Personalization with LLMs

Companion code for chapter 7. Traditional personalization *selects* among
pre-created, human-approved variants; LLM personalization *generates* the variant
on demand. That inversion is the whole chapter: the output space stops being
finite and reviewed, generation moves onto the serving path where a latency
budget is real, the model needs a representation of the customer it can reason
over, and the prompt becomes a data flow under privacy law. These listings build
that serving layer, reusing the parts earlier chapters produced: chapter 2's
shared embedding space and brand centroid, chapter 4's retriever and `Citation`
provenance, chapter 5's `GenerationSpec` shape and its reviewed segment assets
(the fallback when the model is too slow).

Each file is named `C{LL}_Menguy_MarketingAISystems.py`, where `LL` is the
listing number in the manuscript. Northpeak, the Cascade shell, and the
`loyalty` / `lapsed_12mo` segments are the running example carried over from
chapters 1–5. This chapter adds a third state, `prospect`, for a customer who
has never bought.

## Files

| File | Listing | What it shows |
|---|---|---|
| `C01_...py` | 7.1 | `build_profile` projects a raw event stream into a `ProfileCard` of derived traits. Recency derives the same `loyalty` / `lapsed_12mo` segments chapter 5 used; a customer with no purchase is a `prospect`, and a customer with fewer than `MIN_EVENTS` events has no category lean (cold start). Categories in `SENSITIVE_CATEGORIES` (ones that imply a protected trait, such as maternity) never count toward the lean, so the inference never reaches the card, the shortlist, or the cache key. `render_card` renders only the fields the consent gate let through. |
| `C02_...py` | 7.2 | `assemble_for_prompt(card, consent, purpose)`: the gate that decides what may enter a prompt for one use. `NEVER_IN_PROMPT` excludes identifiers and sensitive categories outright; `FIELD_PURPOSES` lists the purposes each trait may serve; `ConsentState.permits` is where an opt-out (do-not-sell-or-share blocks the advertising purpose) or a deletion takes effect. Returns the fields, an audit basis, and a region route. |
| `C03_...py` | 7.3 | Co-embedding: `user_vector` and `top_items` place customers and items in one space so candidate selection is a cheap nearest-neighbor lookup before the expensive model runs. Selection reads the consent-filtered profile, and returns the editor's picks when the profile has no category lean (no consent, or no history). `embed` is injected; a deterministic `stub_embed` and a pure-Python `cosine` keep it runnable with nothing installed. |
| `C04_...py` | 7.4 | `PersonalRequest` + `build_request`: the per-user analogue of chapter 5's `GenerationSpec`. Combines the gated profile (C02), the shortlist selected from that same profile (C03), and grounded offer facts (each with a chapter-4 `Citation`, stubbed here). The request also carries the `Campaign` (code, offer id, corpus version, picks), the audit basis, and the region route. `render_prompt` builds the final prompt. |
| `C05_...py` | 7.5 | `dispatch`: the channel's latency budget picks the strategy. A live LLM call is allowed only when the budget covers the model's p99, and its result has to pass the checks before it is cached or shown; otherwise cache or template. |
| `C06_...py` | 7.6 | `VariantCache`, addressed by request through `cache_key` = bucket + items + channel + offer + corpus version. `bucket_of` reads the gated profile, so the key holds no identifier. `warm` is the one fill path (a whole launch, or one event) and stores nothing that fails the checks. `reclaim` frees stale versions. |
| `C07_...py` | 7.7 | `serve`: the fallback ladder (cache → live → reviewed segment default → house asset) with a `CircuitBreaker` that opens after consecutive failures and lets exactly one probe through after the cool-off. A live result that fails the checks falls down the ladder. |
| `C08_...py` | 7.8 | `assign`: deterministic, storage-free user-level assignment. The holdout is hashed on a program-level salt, so it is the same customers in every experiment; the arm is hashed on the experiment. Stats deferred to chapter 11. |
| `C09_...py` | 7.9 | `evaluate`: scores served variants in layers per segment, with the outcome and the guardrail measured as lift against the same segment's holdout. Flags segments whose guardrail breached, and gives no verdict below `min_n`. A breach is the input to the shutoff that drops a segment to the reviewed baseline without a deploy. |

## Setup

```bash
python3 --version   # 3.10+ for the modern type hints
```

The listings need only the standard library (`dataclasses`, `hashlib`, `math`,
`collections`, `statistics`, `datetime`, `re`, `time`). There is no API key and
nothing to install. Every model-shaped dependency is injected or stubbed:

- `embed` (C03, C04) is injected; a deterministic `stub_embed` stands in for
  chapter 2's `SentenceTransformer("all-MiniLM-L6-v2")`.
- `retrieve` (C04) is injected; `stub_retrieve` returns grounded facts with a
  stubbed chapter-4 `Citation`.
- `generate` (C05, C06, C07) is injected; `stub_generate` builds a line from the
  bucket and the facts.
- `passes` (C05, C06, C07) is injected; `stub_passes` stands in for chapter 5's
  gate without the judge (format and legal checks plus the embedding voice
  score) by rejecting any percentage that is not in an approved fact.
- `voice_score` (C09) is injected. In production these become calls to a capable
  model and to chapter 2's brand-voice scorer, with any API key read from the
  environment.

Files import each other by module name, so run them from inside this directory:

```bash
python3 C01_Menguy_MarketingAISystems.py   # profile card, prospect, cold start, flagged categories
python3 C02_Menguy_MarketingAISystems.py   # consent gate: what enters the prompt
python3 C03_Menguy_MarketingAISystems.py   # co-embed users + items, shortlist
python3 C04_Menguy_MarketingAISystems.py   # assemble a grounded personal request
python3 C05_Menguy_MarketingAISystems.py   # dispatch by latency budget, gated
python3 C06_Menguy_MarketingAISystems.py   # bucket cache, composite key, warm
python3 C07_Menguy_MarketingAISystems.py   # fallback ladder + circuit breaker
python3 C08_Menguy_MarketingAISystems.py   # user-level A/B + permanent holdout
python3 C09_Menguy_MarketingAISystems.py   # layered eval, lift vs the holdout
```
