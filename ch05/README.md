# Chapter 5 — AI Copywriting Systems

Companion code for chapter 5. A copy *demo* is the generation box running once with
a human watching. A production copywriting *system* wraps it in an input spec,
multi-stage generation, a quality gate, three approval flows on three clocks, and a
feedback loop that turns editor corrections into training and test data. These
listings build that system, assembling the parts the earlier chapters produced:
chapter 2's brand-voice scorer as an output gate, chapter 3's versioned prompt and
legal checks, and chapter 4's grounded facts and provenance.

Each file is named `C{LL}_Menguy_MarketingAISystems.py`, where `LL` is the listing
number in the manuscript. Northpeak, the Cascade shell, and the loyalty /
lapsed-12mo segments are the running example carried over from chapters 1–4.

## Files

| File | Listing | What it shows |
|---|---|---|
| `C01_...py` | 5.1 | The `GenerationSpec`: the structured, reproducible unit of work. Carries the brief, segment, channel, campaign code, grounded facts (chapter 4's `Citation`), and the versioned prompt fingerprint. `sample_facts()` is the Cascade fact set the other files import. |
| `C02_...py` | 5.2 | Multi-stage generation, three techniques that each use a model differently: `best_of_n` samples several drafts from a cheap model and selects with the brand-voice scorer; `self_critique` has a stronger model rewrite the selected draft's miss (reflection); `refine` runs chapter 3's bounded check-correction loop. The cheap-draft / large-final split is model routing (chapter 8). All model calls and the check are injected. `select_curve` sweeps N on a sample of briefs to find the knee where extra drafts stop paying, and `plot_curve` renders that curve (the chapter figure; needs matplotlib). |
| `C03_...py` | 5.3 | The batch runner: concurrent (`ThreadPoolExecutor`), resumable (skips done specs), and non-fatal on partial failure, producing a manifest. Carries the `expand` helper (variant expansion: one brief fans into the segment × channel product, two of each is four specs) to build the specs it batches. `__main__` fails one variant, then resumes and fills only the hole. |
| `C04_...py` | 5.4 | Two brand-voice signals behind one interface: `voice_check` is chapter 2's embedding scorer (`margin_score`, stubbed), nearly free and run on every asset; `judge_check` is an LLM-as-judge that reads the copy against the style guide and returns a JSON score plus a reason, run on the ambiguous and high-risk assets. Both are calibrated proxies that route rather than block. |
| `C05_...py` | 5.5 | Deterministic checks: `within_ceiling` (chapter 3's channel ceiling), an SMS opt-out check, and a dependency-free `reading_grade`. Run first because they are free and absolute. |
| `C06_...py` | 5.6 | The composite `gate`: it hard-blocks on the deterministic legal/format checks and routes (never blocks) on the fuzzy voice score, returning a `QualityReport` with decision `ship` / `regenerate` / `hold`. `legal_checks` restates chapter 3's `verify_required` / `find_unsubstantiated` / `check_comparative`. |
| `C07_...py` | 5.7 | Approval routing: `required_flows` sends an asset only to the flows it needs (creative always; legal on a regulated claim or high risk; brand on a low voice score or high risk), consuming a `ReviewPackage` so the citations travel with the copy. `ready_to_publish` gates on all flows clearing. |
| `C08_...py` | 5.8 | The escalation policy: bounded retry for fixable failures, hold for fuzzy-only failures, and a hard stop for the `ALWAYS_ESCALATE` classes (comparative claim, regulated category) regardless of retry budget. |
| `C09_...py` | 5.9 | Editor corrections as a gold dataset: `EditorCorrection` captures (rejected, chosen) with a failure tag; `to_preference_pair` (chapter 2 DPO) and `to_regression_case` (chapter 3 suite) emit the two downstream forms. |

## Setup

```bash
python3 --version   # 3.10+ for the modern type hints
```

The listings need only the standard library (`dataclasses`, `re`,
`concurrent.futures`). The one optional extra is matplotlib, used by
`plot_curve` in C02 to draw the best-of-N figure; it is imported lazily and the
plot is skipped if it is missing, so every file still runs with no API key and
nothing installed. Every model call and cross-chapter dependency is either
injected or stubbed:

- `compose_prompt` (C02), `margin_score` (C04), `within_ceiling` / `reading_grade`
  (C05), and `legal_checks` (C06) are lightweight stand-ins for the real
  chapter-2/3 code, so each file runs on its own.
- The `generate` calls (C02) and the batch's `generate_one` (C03) are injected;
  stubs stand in here. In production those become calls to a capable model (prefer
  Claude Sonnet / Opus), with the API key read from the environment.

## Run

```bash
python3 C01_Menguy_MarketingAISystems.py   # the generation spec + grounded facts
python3 C02_Menguy_MarketingAISystems.py   # draft, then refine on the failures
python3 C03_Menguy_MarketingAISystems.py   # batch: expand a brief, run concurrent + resumable
python3 C04_Menguy_MarketingAISystems.py   # two brand-voice signals: scorer + judge
python3 C05_Menguy_MarketingAISystems.py   # deterministic length/format/readability
python3 C06_Menguy_MarketingAISystems.py   # the composite gate: ship/regenerate/hold
python3 C07_Menguy_MarketingAISystems.py   # route to legal/brand/creative
python3 C08_Menguy_MarketingAISystems.py   # escalation: retry, hold, hard-stop
python3 C09_Menguy_MarketingAISystems.py   # editor correction -> pair + test case
```

Files import each other by module name (for example
`from C01_Menguy_MarketingAISystems import GenerationSpec`), so run them from
inside this directory.

## Notes

- `C01` is the backbone. The `GenerationSpec` is complete and pinned: a downstream
  stage never reconstructs where a fact came from or which prompt produced the
  asset. The `segment` field is where marketing structure enters generation
  (loyalty leads with the product; lapsed leads with what changed).
- `C02` runs three techniques that use a model differently: best-of-N sampling
  with the scorer as selector, self-critique (reflection) on a stronger model,
  and chapter 3's bounded correction loop. Sampling wide on a cheap model and
  finishing on a large one is model routing; chapter 8 prices it.
- `C03` treats the campaign, not the asset, as the unit of work. It expands one
  brief into the segment × channel variants, then batches them: partial failure is
  normal at volume, so the batch collects failures instead of aborting, and a
  re-run regenerates only the holes. This is the object chapter 8 prices.
- `C04` carries two brand-voice signals: the near-free embedding scorer on every
  asset, and an LLM-as-judge (a JSON score plus a reason) on the ambiguous ones.
  `C04` vs `C06` is the whole design of the gate: both voice signals are proxies
  that *route* (a low score sends the asset to brand review), while the
  deterministic legal/format checks are guarantees that *block*. `C06` builds that
  distinction into `hard_fail` vs `voice_fail`.
- `C07` writes the calibrated-trust policy down as routing: legal sees the smallest
  slice (only assets with claims the deterministic gate could not fully clear),
  because most assets carry claims already cleared. Publish waits on all required
  flows; the slowest one binds.
- `C08`'s `ALWAYS_ESCALATE` set is the explicit line: the system is trusted to
  auto-correct mechanical failures and forbidden to auto-correct the ones where a
  wrong answer is a liability.
- `C09` is the feedback loop that makes the system improve. One correction becomes
  a preference pair (chapter 2), a permanent regression case (chapter 3), and a
  calibration signal (chapter 11). The gold dataset is only as good as the
  judgment behind the corrections, which is why the human reviewers are the
  system's ground truth, not a cost to minimize.
- The code reads cleanly rather than being production-hardened. Real embedding
  scorers, a real approval-workflow store and review UI, concurrency limits and
  cost controls, and the aggregate measurement program arrive in later chapters
  (8, 11) and in the companion repository's fuller versions.
```