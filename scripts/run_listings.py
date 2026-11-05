"""Run every book listing that the current environment can support.

Each chNN/C*_Menguy_MarketingAISystems.py file is executed from inside its
chapter folder, so sibling listings import by module name as they do in the
book. A listing is skipped, not failed, when one of its top-level imports is
not installed or when it needs an API key that is not set.

Usage:
    python scripts/run_listings.py            # all chapters
    python scripts/run_listings.py ch04 ch05  # selected chapters
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LISTING_GLOB = "C[0-9][0-9]_Menguy_MarketingAISystems.py"
TOP_LEVEL_IMPORT = re.compile(r"^(?:from|import)\s+([A-Za-z_][\w]*)", re.MULTILINE)

# Hosted-model SDKs whose clients read a key from the environment.
KEY_FOR_MODULE = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}


def chapter_dirs(selected: list[str]) -> list[Path]:
    dirs = sorted(p for p in ROOT.glob("ch[0-9][0-9]") if p.is_dir())
    if selected:
        dirs = [d for d in dirs if d.name in selected]
    return dirs


def external_imports(listing: Path) -> set[str]:
    """Top-level imports of a listing, following imports of sibling listings."""
    siblings = {p.stem: p for p in listing.parent.glob("*.py")}
    seen, todo, modules = set(), [listing], set()
    while todo:
        path = todo.pop()
        if path in seen:
            continue
        seen.add(path)
        for module in TOP_LEVEL_IMPORT.findall(path.read_text()):
            if module in siblings:
                todo.append(siblings[module])
            else:
                modules.add(module)
    return modules


def skip_reason(listing: Path) -> str | None:
    """Return why a listing cannot run here, or None if it can."""
    for module in sorted(external_imports(listing)):
        if module == "__future__":
            continue
        if importlib.util.find_spec(module) is None:
            return f"missing package '{module}'"
        key = KEY_FOR_MODULE.get(module)
        if key and not os.environ.get(key):
            return f"{key} not set"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("chapters", nargs="*", help="chapter folders, e.g. ch04")
    parser.add_argument("--timeout", type=int, default=600, help="seconds per listing")
    args = parser.parse_args()

    dirs = chapter_dirs(args.chapters)
    if not dirs:
        print("no chapter folders found")
        return 0

    passed, skipped, failed = [], [], []
    for chapter in dirs:
        for listing in sorted(chapter.glob(LISTING_GLOB)):
            name = f"{chapter.name}/{listing.name}"
            reason = skip_reason(listing)
            if reason:
                skipped.append(name)
                print(f"SKIP  {name}  ({reason})")
                continue
            start = time.monotonic()
            try:
                result = subprocess.run(
                    [sys.executable, listing.name],
                    cwd=chapter,
                    capture_output=True,
                    text=True,
                    timeout=args.timeout,
                )
                ok, output = result.returncode == 0, result.stderr or result.stdout
            except subprocess.TimeoutExpired:
                ok, output = False, f"timed out after {args.timeout}s"
            elapsed = time.monotonic() - start
            if ok:
                passed.append(name)
                print(f"PASS  {name}  ({elapsed:.1f}s)")
            else:
                failed.append(name)
                print(f"FAIL  {name}  ({elapsed:.1f}s)")
                print("\n".join("      " + line for line in output.strip().splitlines()[-20:]))

    print(f"\n{len(passed)} passed, {len(skipped)} skipped, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
