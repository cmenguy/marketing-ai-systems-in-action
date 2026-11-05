"""Deterministic checks: length, format completeness, readability (Listing 5.5).

Below the fuzzy score sit the deterministic checks, and they are the ones you run
first, because they are free, absolute, and catch the most common failures
outright. A piece of copy either fits the channel ceiling or it does not, either
has its required structure or is missing it, either ends an SMS with an opt-out or
is not legal to send.

`within_ceiling` and the channel ceilings restate chapter 3's registry so this
file runs on its own. `reading_grade` is a dependency-free Flesch-Kincaid-style
approximation; production may swap in a fuller readability library.
"""

from __future__ import annotations

import re

from C04_Menguy_MarketingAISystems import CheckResult

CHAR_CEILING = {"email": 900, "sms": 160, "linkedin": 1300, "display": 90}


def within_ceiling(copy: str, channel: str) -> bool:
    return len(copy) <= CHAR_CEILING[channel]


def reading_grade(copy: str) -> float:
    """A cheap grade-level proxy: longer words and sentences read higher."""
    sentences = max(1, len(re.findall(r"[.!?]+", copy)))
    words = re.findall(r"[A-Za-z]+", copy)
    if not words:
        return 0.0
    syllables = sum(max(1, len(re.findall(r"[aeiouy]+", w.lower()))) for w in words)
    return (0.39 * len(words) / sentences
            + 11.8 * syllables / len(words) - 15.59)


def format_checks(copy, spec):
    results = []
    ceiling = CHAR_CEILING[spec.channel]
    results.append(CheckResult(
        "length", within_ceiling(copy, spec.channel), None,
        f"{len(copy)} chars vs ceiling {ceiling}"))
    if spec.channel == "sms":
        has_optout = bool(re.search(r"\bstop\b", copy, re.I))
        results.append(CheckResult(
            "opt_out", has_optout, None,
            "STOP opt-out present" if has_optout else "missing opt-out"))
    grade = reading_grade(copy)
    results.append(CheckResult(
        "readability", grade <= 9.0, grade, f"grade level {grade:.1f}"))
    return results


if __name__ == "__main__":
    from C01_Menguy_MarketingAISystems import GenerationSpec, sample_facts

    def spec(channel):
        return GenerationSpec("brief", "loyalty", channel,
                              "cascade-spring-2026", sample_facts(), "v3")

    good_sms = ("Northpeak: Cascade shell is in. 10K/10K waterproof, 63% "
                "recycled. Spring pricing through May 31. Txt STOP to opt out.")
    for r in format_checks(good_sms, spec("sms")):
        print(f"  {r.name:11s} pass={r.passed}  {r.detail}")

    over = "x" * 175  # blows the 160 ceiling and has no opt-out
    fails = [r for r in format_checks(over, spec("sms")) if not r.passed]
    print(f"over-ceiling SMS failed {len(fails)} deterministic checks")
    assert len(fails) >= 2, "an overlong SMS with no opt-out is caught, for free"
    print("OK: length and opt-out are enforced deterministically, not requested.")
