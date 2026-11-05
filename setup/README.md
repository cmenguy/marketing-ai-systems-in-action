# Setting up your environment

## Python

The code needs Python 3.10 or newer and was tested with 3.12. Check your
version with:

```bash
python3 --version
```

## Virtual environment

Use a virtual environment so the book's dependencies stay separate from your
system Python. With the standard library `venv`:

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
```

## Optional dependencies

`requirements.txt` installs only NumPy, which covers most listings. Install
`requirements-extras.txt` when you reach a listing that needs more:

| What | Packages | Where it is used |
|---|---|---|
| Fine-tuning and embeddings | torch, transformers, peft, trl, datasets, sentence-transformers | Chapter 2; the optional cross-encoder in chapter 4 |
| Image processing | pillow | Chapter 6 |
| Hosted model clients | anthropic, openai | Listings and extras that call a live model |

```bash
pip install -r requirements-extras.txt
```

The chapter 2 fine-tuning listings download small open-weight models from the
Hugging Face Hub on first run. They run on a CPU, but a GPU or Apple
Silicon (MPS) makes them much faster.

## API keys

Listings that call a hosted model read their key from the environment, never
from the code. Copy the template and fill in only what you need:

```bash
cp .env.example .env
set -a; source .env; set +a      # export the keys into your shell
```

Every listing that calls a model takes it as an injected function and ships
with a stub, so you can follow the book without any key.

## Checking your setup

From the repository root, run every listing your installed packages support:

```bash
python scripts/run_listings.py
```

Listings whose packages or API keys are missing are reported as skipped, not
failed.
