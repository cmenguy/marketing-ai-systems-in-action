"""Two brand-voice signals: the cheap embedding scorer and an LLM judge (Listing 5.4).

Chapter 2 built a brand-voice scorer and said where it would be used: as the
output-side gate in the copywriting pipeline. The embedding scorer measures
geometric closeness to the brand centroid, so it is nearly free but can tell you a
draft is off without telling you why. An LLM-as-judge covers that blind spot: a
stronger model reads the draft against the actual style guide and returns a score
with a reason, the way a brand editor would (the pattern chapter 1 named).

Both are proxies with error, calibrated against human ratings so a number means
something (chapter 11). The embedding scorer runs on every asset; the judge runs
on the ambiguous and high-risk ones, because it is a full model call per asset.
`margin_score` and the judge call are stubbed so this file runs with no model.
"""

from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    score: float | None       # None for deterministic checks
    detail: str


def margin_score(copy: str, brand_c=None, neg_c=None) -> float:
    """Stand-in for chapter 2's margin_score(copy, brand_c, neg_c)."""
    low = copy.lower()
    off = ("best", "unbeatable", "conquer", "ultimate", "revolutionary",
           "don't miss", "hurry", "last chance")
    on = ("rating", "recycled", "shell", "face fabric", "seams", "spec")
    score = 0.30 + 0.10 * sum(t in low for t in on)
    score -= 0.25 * sum(t in low for t in off)
    if "!" in copy:
        score -= 0.15
    return max(-1.0, min(1.0, score))


def voice_check(copy, brand_c, neg_c, threshold):        # embedding scorer
    margin = margin_score(copy, brand_c, neg_c)
    return CheckResult("brand_voice", margin >= threshold, margin,
                       "on-voice" if margin >= threshold
                       else f"margin {margin:.2f} below {threshold:.2f}")


JUDGE = ("You are Northpeak's brand editor. Score the copy 1-5 for how "
         "well it holds this voice, and name the single biggest miss.\n"
         "Voice: {voice}\nCopy: {copy}\n"
         'Return JSON: {{"score": int, "miss": str}}')


def judge_check(copy, voice, judge_model, floor=4):      # LLM-as-judge
    verdict = json.loads(judge_model(JUDGE.format(voice=voice, copy=copy)))
    return CheckResult("brand_voice_judge", verdict["score"] >= floor,
                       float(verdict["score"]), verdict["miss"])


if __name__ == "__main__":
    voice = ("Plainspoken and technical. No hype, no invented urgency. "
             "State a spec, not a slogan.")
    on_voice = ("The Cascade shell is here. A 10K/10K waterproof-breathable "
                "rating, taped seams, and a 63% recycled face fabric.")
    off_voice = "Don't miss your last chance at the season's best shell!"

    # The embedding scorer: nearly free, runs on every asset.
    good, bad = voice_check(on_voice, None, None, 0.30), \
        voice_check(off_voice, None, None, 0.30)
    print(f"scorer on-voice : {good.score:.2f} -> {good.detail}")
    print(f"scorer off-voice: {bad.score:.2f} -> {bad.detail}")

    # A stub judge: a real one is a call to a capable model returning JSON.
    def judge_model(prompt):
        copy = prompt.split("Copy: ", 1)[1].split("\n", 1)[0]
        if any(t in copy.lower() for t in ("best", "don't miss", "!")):
            return json.dumps({"score": 2, "miss": "manufactured urgency"})
        return json.dumps({"score": 5, "miss": "none"})

    jgood = judge_check(on_voice, voice, judge_model)
    jbad = judge_check(off_voice, voice, judge_model)
    print(f"judge on-voice  : {jgood.score:.0f}/5 -> {jgood.detail}")
    print(f"judge off-voice : {jbad.score:.0f}/5 -> {jbad.detail}")

    assert good.passed and not bad.passed, "the scorer splits the two"
    assert jgood.passed and not jbad.passed, "the judge splits the two, with a reason"
    print("OK: scorer gives a number, judge gives a number and a reason.")
