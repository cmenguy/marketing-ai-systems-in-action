"""Multi-stage generation: sample and select, self-critique, then refine (Listing 5.2).

One model call is enough for a demo and not for a system. Three techniques do the
work, and each uses a model differently:

1. Best-of-N: a single generation is a sample from the model's distribution, so
   draw several from a cheap, fast model and keep the highest-scoring. The
   brand-voice scorer stops being only a gate and becomes a selector.
2. Self-critique: a stronger model reads the selected draft against the voice,
   names what is off, and rewrites it. This is reflection, and it catches the
   stance failure the deterministic checks cannot see.
3. Refine: chapter 3's bounded auto-correction loop, feeding each specific check
   failure back. It runs last because it is the cheapest and most reliable.

The split of a cheap draft model from a larger final/judge model is model routing;
chapter 8 turns it into real money. The model calls and the check are injected, so
stubs stand in here and hosted models (prefer Claude Sonnet / Opus) in production.

`select_curve` sweeps N on a sample of briefs to find the knee where extra drafts
stop paying, and `plot_curve` renders it (the figure in the chapter).
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from C01_Menguy_MarketingAISystems import GenerationSpec, sample_facts


def compose_prompt(spec: GenerationSpec) -> str:
    """Stand-in for chapter 3's layered, versioned prompt for this spec."""
    return (
        f"You write marketing copy for Northpeak.\n"
        f"Segment framing: {spec.audience_note()}\n"
        f"Facts you may use: {'; '.join(c.fact for c in spec.facts)}\n"
        f"Channel: {spec.channel}\n"
        f"Brief: {spec.brief}"
    )


@dataclass(frozen=True)
class StubReport:
    ok: bool
    fails: tuple[str, ...] = ()

    def correction(self) -> str:
        return "\n\nThe previous draft failed: " + "; ".join(self.fails)


def best_of_n(spec, draft_model, score, n=4):
    drafts = [draft_model(compose_prompt(spec), spec) for _ in range(n)]
    return max(drafts, key=score)          # the scorer selects, not just gates


def self_critique(copy, spec, judge_model):
    ask = (compose_prompt(spec) + "\n\nCritique this draft against "
           "the brand voice, then rewrite it to fix the miss:\n" + copy)
    return judge_model(ask, spec)          # a stronger model rewrites the miss


def refine(copy, spec, final_model, check, max_tries=2):
    for _ in range(max_tries):
        report = check(copy, spec)
        if report.ok:
            return copy
        copy = final_model(compose_prompt(spec) + report.correction(), spec)
    return copy                            # gate decides if it still fails


def select_curve(specs, draft_model, score, ns=(1, 2, 4, 8, 16)):
    """Sweep N on a sample of briefs. For each brief, draft max(ns)
    candidates and score them; best-of-N is the max over the first N draws.
    Returns [(N, avg_selected_score)], averaged across the briefs."""
    rows = []
    for spec in specs:
        s = [score(draft_model(compose_prompt(spec), spec))
             for _ in range(max(ns))]
        rows.append([max(s[:n]) for n in ns])
    return [(n, sum(c) / len(c)) for n, c in zip(ns, zip(*rows))]


def plot_curve(curve, path="output/bestofn.png"):
    """Render the sweep. matplotlib is imported lazily so the rest of this
    file still runs on the standard library alone."""
    import matplotlib.pyplot as plt

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    ns, avg = zip(*curve)
    plt.plot(ns, avg, marker="o")
    plt.xscale("log", base=2)
    plt.xticks(ns, [str(n) for n in ns])
    plt.xlabel("drafts sampled (N)")
    plt.ylabel("avg selected score")
    plt.title("Choosing N in best-of-N")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


if __name__ == "__main__":
    # A cheap draft model whose samples vary in how on-voice they are.
    _samples = iter([
        "Conquer the season in the ultimate shell!",       # off-voice
        "The best shell for spring, now recycled.",        # off-voice
        "The Cascade shell is here. 10K/10K rating, 63% recycled.",  # on
        "New shell. Waterproof. Buy now.",                 # flat
    ])

    def draft_model(prompt, spec):
        return next(_samples)

    def score(copy):
        low = copy.lower()
        s = sum(t in low for t in ("rating", "recycled", "shell", "10k"))
        s -= sum(t in low for t in ("conquer", "ultimate", "best", "!"))
        return s

    def judge_model(prompt, spec):
        # The critic tightens the selected draft toward the voice.
        return ("The Cascade shell is here. A 10K/10K waterproof-breathable "
                "rating, taped seams, and a 63% recycled face fabric. Spring "
                "pricing runs through May 31.")

    def final_model(prompt, spec):
        return judge_model(prompt, spec)

    def check(copy, spec):
        fails = [] if "10K/10K" in copy else ["missing waterproof rating"]
        return StubReport(ok=not fails, fails=tuple(fails))

    spec = GenerationSpec(
        brief="Launch the Cascade shell for spring.", segment="loyalty",
        channel="email", campaign_code="cascade-spring-2026",
        facts=sample_facts(), prompt_fingerprint="copy.email:v3")

    best = best_of_n(spec, draft_model, score, n=4)
    print("best-of-N picked:", best)
    critiqued = self_critique(best, spec, judge_model)
    final = refine(critiqued, spec, final_model, check)
    print("after critique + refine:", final)
    assert "10K/10K" in final, "the pipeline should converge to a clean draft"
    assert score(best) >= 0, "best-of-N should not select an off-voice sample"
    print("OK: sampled and selected, self-critiqued, then refined to clean copy.")

    # Choosing N: sweep it on a sample of briefs and find the knee. The draft
    # model here returns a sampled quality score directly (a stand-in for
    # draft-then-score) drawn from a capped distribution, so the curve shows
    # the diminishing-returns shape.
    import random
    random.seed(7)
    briefs = [GenerationSpec(f"Brief {i} for the Cascade launch.", "loyalty",
                             "email", "cascade-spring-2026", sample_facts(),
                             "copy.email:v3") for i in range(300)]

    def sampled_quality(prompt, spec):
        return round(min(0.80, random.gauss(0.60, 0.10)), 3)

    curve = select_curve(briefs, sampled_quality, score=lambda d: d)
    print("N -> avg selected score:", [(n, round(a, 2)) for n, a in curve])
    assert curve[0][1] < curve[2][1] < curve[-1][1], "more drafts, higher max"
    assert curve[-1][1] - curve[2][1] < curve[2][1] - curve[0][1], \
        "gains diminish: 4->16 adds less than 1->4"
    try:
        plot_curve(curve)
        print("wrote output/bestofn.png (needs matplotlib)")
    except Exception as exc:  # matplotlib missing or a headless-backend issue
        print("skipped plot:", exc)
    print("OK: the sweep shows diminishing returns; N=4-8 is the knee.")
