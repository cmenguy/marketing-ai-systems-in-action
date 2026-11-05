# Chapter 6 — Creative Image and Video Generation

Companion code for chapter 6. Visual generation for marketing is a **grounding**
problem before it is a prompting problem: the brand already owns the things that
define how it looks (products, logo, color, templates, approved creative), so the
system grounds generation in those real assets, generates only what must be
generated (usually a background), validates every variant and localization against
measurable constraints, and carries rights and provenance for paid advertising.

Each file is named `C{LL}_Menguy_MarketingAISystems.py`, where `LL` is the listing
number in the manuscript. Northpeak, the Cascade shell, its forest-green palette
(`#1F3D2B`), and the loyalty / lapsed segments are the running example carried over
from chapters 1–5.

## Files

| File | Listing | What it shows |
|---|---|---|
| `C01_...py` | 6.1 | The `VisualBrandKit`: the brand's **assets** and rules in one spec — the real `logo`, `products` and `templates` (as `ReferenceAsset`s), plus the guideline palette (the fallback), tolerance, safe zone, and forbidden treatments. The backbone the other files read at both ends. |
| `C02_...py` | 6.2 | The conditioning request. `build_request` grounds generation in the **product reference** (identity), distinct from **style references** (mood), plus structure and a palette steer. The product is resolved from the DAM by code. `generate_image` takes the model as an argument. |
| `C03_...py` | 6.3 | **Assembly** (the primary path): `assemble` composites the real product and logo into a template and inpaints only the background, so identity is correct by construction. numpy uint8 images; inpainter and loader stubbed. |
| `C04_...py` | 6.4 | Customized variant generation: `build_variant` frames the headline per **audience** (loyalty/lapsed) and per **locale**, grounds the hero in the real product (via `build_request`), and checks the text fits; `expand_campaign` fans one campaign into the audience × locale grid (figure 6.6). German overflows and is held; RTL locales flip the layout. On-image text is composited, never generated. |
| `C05_...py` | 6.5 | The video frame-consistency check: `coherence_report` measures each frame's drift from an anchor. `embed_image` (a 4×4 pooled color signature) is a deterministic stand-in for a multimodal encoder, reused by C06 and the gate in C08. |
| `C06_...py` | 6.6 | The **short-form video pipeline**: `animate` does image-to-video from the approved hero (the `video_model` is injected/swappable), `format_ok` checks aspect ratio and duration, and `validate_clip` runs the still gate on every frame plus the coherence check. The durable code is the pipeline around the model, not the model call. |
| `C07_...py` | 6.7 | Color compliance against **two** references: the guideline palette AND the colors sampled from the real product/logo assets. The smallest distance to any approved color is the "difference factor," checked vs the kit tolerance (chapter 2's `color_distance`, restated). |
| `C08_...py` | 6.8 | The composite `visual_gate` → `VisualQualityReport` (`ship`/`regenerate`/`hold`). Deterministic focus areas (color, logo, composition/product-visibility, text legibility/contrast, safety) **block**; the fuzzy brand-look score **routes**. `CheckResult` carries a **confidence** and a **feedback** line. |
| `C09_...py` | 6.9 | Provenance: `VisualProvenance` records model, version, seed, prompt, conditioning, **the product ref and template it was assembled from**, kit version, and rights basis; `sign_manifest` is a C2PA-style signed claim; `to_citation` reuses chapter 4's `Citation`. |
| `C10_...py` | 6.10 | DAM registration: `register_asset` pins the exact bytes with a content hash, versions the asset, and supersedes the prior version rather than overwriting it — chapter 4's supersession rule applied to visual assets. `InMemoryDAM` is the runnable stand-in for the `dam` handle; `BynderDAM` illustrates a real DAM behind the same `latest`/`put` interface (not runnable — no SDK). |

## Setup

```bash
python3 --version   # 3.10+ for the modern type hints
pip install numpy    # the only third-party dependency
```

Only `numpy` is required. No GPU, no model download, no API key: the image and
video generation calls (`generate_image`, `inpaint`), the logo `detect`or, the
`safety` classifier, and `embed_image` are injected or stubbed, and the validators
work on ordinary numpy image arrays. In production those become real generators,
detectors, a multimodal encoder, and a DAM/Figma client, with any API key read
from the environment.

## Run

```bash
python3 C01_Menguy_MarketingAISystems.py   # the visual brand kit (assets + rules)
python3 C02_Menguy_MarketingAISystems.py   # conditioning grounded on the product
python3 C03_Menguy_MarketingAISystems.py   # assembly: composite product+logo, gen bg
python3 C04_Menguy_MarketingAISystems.py   # localization: per-locale fit / overflow
python3 C05_Menguy_MarketingAISystems.py   # video frame-consistency check
python3 C06_Menguy_MarketingAISystems.py   # short-form video: animate + validate clip
python3 C07_Menguy_MarketingAISystems.py   # color vs reference assets + guideline
python3 C08_Menguy_MarketingAISystems.py   # the composite gate: ship/regenerate/hold
python3 C09_Menguy_MarketingAISystems.py   # signed C2PA-style provenance manifest
python3 C10_Menguy_MarketingAISystems.py   # DAM registration + asset versioning
```

Files import each other by module name (for example
`from C01_Menguy_MarketingAISystems import northpeak_kit`), so run them from
inside this directory.

## Generate for real (optional)

The numbered listings stub the model so they run key-free. Four extra scripts wire
a real provider into the same design, so you can actually produce assets — they
are the "current instance" of the injected model interface (`generate_image`,
`video_model`); the listings stay provider-agnostic on purpose. They read the
sample Northpeak logo and hero image from `assets/` and write what they generate
to `output/`.

- `try_generate.py` — generates a scene with a hosted image model (OpenAI, text-only
  `images.generate`), then composites the real logo + headline + CTA (assembly) and
  runs the color check from `C07`. `--hero PATH` skips the API to try compositing.
- `try_generate_grounded.py` — the full listing 6.2 request against OpenAI's
  image-INPUT endpoint (`images.edit`), so the product/style reference images
  actually reach the model, with each image's role named in the prompt. `--dry`
  prints the exact payload; `--style PATH` adds a style reference.
- `try_assemble.py` — the runnable form of listing 6.3: generates the background
  scene, then composites the real logo, a product cutout (generated transparent by
  default, or `--product PATH`), and a headline into a proper template, and runs the
  color check. `--dry` prints the plan.
- `try_video.py` — animates the approved still into a clip and validates it with
  `C06` (format + coherence). `--backend kenburns` (default) needs no key or GPU
  and saves a GIF; `--backend veo` calls Google Veo for real image-to-video
  (needs `google-genai`, `imageio[ffmpeg]`, and `GEMINI_API_KEY`) and saves an MP4.

```bash
python3 try_generate.py        # OPENAI_API_KEY set: generate a real asset
python3 try_generate_grounded.py --dry   # full 6.2 request -> images.edit payload
python3 try_assemble.py --dry            # listing 6.3 template assembly plan
python3 try_video.py           # no key: Ken Burns clip + validation
python3 try_video.py --backend veo    # GEMINI_API_KEY set: real Veo clip
```

## Notes

- The through-line is **asset-first grounding**. `C01`'s kit carries the real
  product and logo assets and templates; `C02` conditions on the product for
  identity; `C03` composites the real assets and generates only the scene. The
  strongest brand constraints are enforced by *not* generating them.
- `C04` generates each variant customized on two axes at once: audience framing
  (loyalty leads with the product; lapsed with what changed) and locale (the
  headline per market, the hero grounded in the real product). Then it validates:
  translated text does not fit the same box, so expansion, overflow, and RTL are
  validation problems, and every variant re-enters validation. `expand_campaign`
  is the fan-out that produces figure 6.6's grid.
- `C05`/`C06` are the video pipeline: `C05` measures temporal drift from an anchor
  frame, and `C06` animates an approved still and validates the clip (format, the
  still gate per frame, and coherence). The `video_model` is injected because it is
  the piece that changes fastest; the durable code is the pipeline around it.
- `C07`/`C08` are the deterministic core. `C07` checks color against the reference
  assets *and* the guideline. `C08` is the whole gate: deterministic focus areas
  (color, logo, composition, legibility, safety) block; the visual-centroid look
  score routes; each result carries a confidence and a feedback line.
- `C09`/`C10` make the asset defensible and reusable: record provenance (including
  which product and template it was assembled from) at generation time, then
  register it in the DAM with a content hash and versioning that supersedes rather
  than overwrites. Chapter 9's agents pull from this DAM; chapter 10's incident
  response queries this provenance.
- The code reads cleanly rather than being production-hardened. Real diffusion and
  video generators, a real logo detector and safety stack, a real multimodal
  encoder and DAM/Figma client, and the cost arithmetic for image and video at
  scale arrive in later chapters (8, 9, 10) and in the companion repository.
