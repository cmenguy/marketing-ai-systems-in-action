# Chapter 8 — Cost, Latency, and Multi-Tenant Architecture

Companion code for chapter 8. One Cascade email costs a fraction of a cent; run it
tens of thousands of times a month across hundreds of brands and the token bill is
a budget line, latency is an SLA, and tenant isolation is a clause in a contract.
These listings size the unit economics, then build the model router, the cache
layers, the multi-tenant boundary, and the metering that turns usage into a bill.

Each file is named `C{LL}_Menguy_MarketingAISystems.py`, where `LL` is the listing
number in the manuscript. Northpeak and the Cascade launch are the running example;
Ridgeline is a second, competing tenant used to make isolation concrete.

## Files

| File | Listing | What it shows |
|---|---|---|
| `C01_...py` | 8.1 | The cost model. `RATE_CARD` (representative per-million-token prices) and `STAGE_TOKENS` drive `call_cost`, `price_asset`, and `price_campaign`. `price_asset_all_final` sizes the naive all-strong-model pipeline so routing's saving is visible. Prints the per-asset ($0.0129), campaign ($517), and ~69% routing-cut figures the chapter quotes. |
| `C02_...py` | 8.2 | Capacity planning. `plan_batch` costs a batch before it runs and routes non-urgent work to the discounted async tier; `split_on_ceiling` admits an over-budget refresh in chunks instead of refusing it. Imports `price_campaign` from C01. |
| `C03_...py` | 8.3 | The model router. `route(stage, spec, risk)` returns a model *tier* (a name the runtime resolves, never a provider id), promoting a draft to the strong tier on high risk or an audited channel; `draft_count` sets N by segment. Carries a minimal `GenerationSpec` with the fields the router reads. |
| `C04_...py` | 8.4 | The three cache layers wired end to end. `prefix_key`/`retrieval_key`/`asset_key` build the keys; `LayeredCache.invalidate` drops exactly the entries a corpus version produced; `build_call` puts the static prefix first and flags it cacheable (the one provider-specific line); `generate` runs a request through retrieval cache -> generation cache -> provider call in cost order. `__main__` runs it twice against a stub provider (showing the second call hit the generation cache with no provider call and the prefix flagged cacheable), then a corpus refresh forces a regeneration. Provider and retrieve are injected, so it runs with no API key. |
| `C05_...py` | 8.5 | `TenantContext`: one object, created at the edge, that scopes the retrieval filter, the cache key, the prompt source, and the log fields by `tenant_id`, so the boundary is drawn in one place rather than at four call sites. |
| `C06_...py` | 8.6 | The structural guard. `scoped_key` and `checked_filters` raise `TenantError` rather than return a wrong answer when a tenant is missing, so an unscoped operation is impossible to express; `belongs_to` is the test assertion that a key is one tenant's and no other's. |
| `C07_...py` | 8.7 | Metering. `meter` appends one `Usage` row per call tagged with tenant/campaign/asset/tier/tokens; `cost_of` bills a cache hit at zero against the fill that paid; `rollup` totals the ledger by any key. Imports `call_cost` (C01) and `TenantContext` (C05). |
| `C08_...py` | 8.8 | The client-facing statement. `tenant_statement` turns the ledger into the per-tenant monthly numbers: assets served, model calls, cache-hit rate, cost, and a per-campaign breakdown. Imports from C05 and C07. |

## Setup

```bash
python3 --version   # 3.10+ for the modern type hints
```

The listings need only the standard library (`dataclasses`, `collections`,
`typing`). There is no model call anywhere in this chapter: the cost model works
from a rate card and token counts, not from a provider, so every file runs with no
API key and nothing installed.

The prices in `RATE_CARD` are representative placeholders chosen to be internally
consistent with the figures in the chapter. Rates move; replace them with your
provider's current rate card and the structure holds.

## Running

Run any file directly; each has a `__main__` demo:

```bash
python3 C01_Menguy_MarketingAISystems.py   # the cost figures
python3 C08_Menguy_MarketingAISystems.py   # a tenant statement
```

C02, C07, and C08 import from sibling files (C01, C05, C07), so run them from
inside this directory, where Python puts the script's folder on the path.
