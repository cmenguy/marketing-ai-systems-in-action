"""The escalation policy: retry, halt, or hard-stop by failure class (Listing 5.8).

A system that ships on its own has to know when to stop on its own. Escalation has
two triggers: the gate cannot clear an asset, or the asset belongs to a class the
system is not allowed to ship without a human no matter what the checks say. Both
end with the asset in front of a person.

The bounded-retry logic catches the transient miss. The always-escalate classes,
a comparison to a named competitor or a regulated category, stop for a human on
the first sign, regardless of retry budget, because the check is a proxy for a
legal judgment the system is not qualified to make.
"""

from __future__ import annotations

from dataclasses import dataclass

ALWAYS_ESCALATE = {"comparative_claim", "regulated_category"}


@dataclass(frozen=True)
class Result:
    name: str
    passed: bool


@dataclass(frozen=True)
class Report:
    results: list


def escalate_decision(report, tries_left):
    failed = {r.name for r in report.results if not r.passed}
    if failed & ALWAYS_ESCALATE:
        return "human"                # never auto-retry this class
    if not failed:
        return "ship"
    fixable = failed - {"brand_voice"}
    if fixable and tries_left:
        return "regenerate"
    return "human"                    # out of retries, or fuzzy-only failure


if __name__ == "__main__":
    def report(*failed):
        names = ("length", "required_phrases", "comparative_claim",
                 "brand_voice")
        return Report([Result(n, n not in failed) for n in names])

    print("all clear          ->", escalate_decision(report(), 2))
    print("missing phrase     ->", escalate_decision(report("required_phrases"), 2))
    print("out of retries     ->", escalate_decision(report("required_phrases"), 0))
    print("low voice only     ->", escalate_decision(report("brand_voice"), 2))
    print("competitor compare ->", escalate_decision(report("comparative_claim"), 5))

    assert escalate_decision(report(), 2) == "ship"
    assert escalate_decision(report("required_phrases"), 2) == "regenerate"
    assert escalate_decision(report("required_phrases"), 0) == "human"
    assert escalate_decision(report("brand_voice"), 2) == "human"
    assert escalate_decision(report("comparative_claim"), 5) == "human", \
        "a comparative claim halts regardless of retry budget"
    print("OK: fixable retries, fuzzy-only holds, comparative always escalates.")
