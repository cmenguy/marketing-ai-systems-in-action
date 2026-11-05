# Marketing AI Systems in Action

This repository holds the companion code for *Marketing AI Systems in Action:
Build, scale, and govern brand-safe generative AI pipelines* by Charles Menguy
(Manning Publications).

- Book page at Manning: <!-- TODO: mng.bz short link from the editor -->
- Source code repository: https://github.com/cmenguy/marketing-ai-systems-in-action

To get a copy of the code, run:

```bash
git clone --depth 1 https://github.com/cmenguy/marketing-ai-systems-in-action.git
```

If you downloaded this code as a zip from the Manning website, the GitHub
repository above is where fixes and updates land first.

## Getting started

The [setup guide](setup/README.md) covers the Python version, virtual
environment, and optional dependencies. In short:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt            # enough for most listings
pip install -r requirements-extras.txt     # fine-tuning, image, and live-model listings
cp .env.example .env                       # only needed for listings that call a hosted model
```

Most listings use only the standard library and NumPy. They run offline with no
API key because model calls are injected as plain callables and replaced by
stubs in each file's `__main__` block. A few listings need the extras: the
chapter 2 fine-tuning code and the chapter 6 image pipeline. The live-model
demos also need a provider key. Each chapter's README says which files need what.

## How the code is organized

There is one folder per chapter. Each listing in the book maps to one file named
`C{LL}_Menguy_MarketingAISystems.py`, where `LL` is the listing number in that
chapter (listing 4.6 is `ch04/C06_Menguy_MarketingAISystems.py`). Files inside a
chapter import each other by module name, so run them from inside the chapter
folder:

```bash
cd ch04
python C06_Menguy_MarketingAISystems.py
```

Code that is not printed in the book, such as the chapter 6 live-model demos,
lives in an `extras/` subfolder of its chapter.

To run every listing that your installed dependencies support:

```bash
python scripts/run_listings.py            # all chapters
python scripts/run_listings.py ch04 ch05  # selected chapters
```

## Table of contents

| Chapter | Code |
|---|---|
| 1. The Generative Marketing Stack | [ch01](ch01) |
| 2. Representing Brand Identity: Approaches and Tradeoffs | [ch02](ch02) |
| 3. Marketing-Specific Prompt Engineering | [ch03](ch03) |
| 4. Retrieval over Brand Knowledge | [ch04](ch04) |
| 5. AI Copywriting Systems | [ch05](ch05) |
| 6. Creative Image and Video Generation | [ch06](ch06) |
| 7. Personalization with LLMs | [ch07](ch07) |
| 8. Cost, Latency, and Multi-Tenant Architecture | [ch08](ch08) |
| 9. Marketing Agents and Copilots | coming soon |
| 10. Safety, Governance, and Regulatory Compliance | coming soon |
| 11. Evaluation and Business Impact | coming soon |

## The running example

All examples use Northpeak, a fictional outdoor-apparel brand, together with its
campaigns, segments, and brand guidelines. Any resemblance to a real company is
coincidental.

## Questions and errata

If you find a bug or a mismatch between the book and the code, please open an
issue on this repository. For questions about the book itself, use the liveBook
discussion forum on the Manning website.

## License

The code is released under the terms in [LICENSE](LICENSE). The book text and
figures are copyright Manning Publications and are not covered by this license.
