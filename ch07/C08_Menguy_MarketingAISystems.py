"""Listing 7.8 - Deterministic user-level assignment with a permanent holdout.

In personalization the treatment is a policy, not an asset, so you test the
generating system against a baseline. Randomize on the customer, not the
impression: a customer who sees a personalized hero on Monday and a generic one
on Tuesday has an incoherent experience and pollutes both arms. Keep a permanent
holdout, a small slice that is never personalized, so you can measure the
long-run effect of the program and catch slow harms.

The assignment hashes twice on purpose. The holdout is hashed on a salt that
belongs to the program, so the same customers sit out every experiment and the
holdout really is permanent. The arm is hashed on the experiment, so each new
test reshuffles everyone else. Both are stable and need no storage.

The statistics that pull a clean signal from noisy outcomes (CUPED, synthetic
controls, causal lift) are chapter 11's subject. This is only the assignment.

Runs standalone:  python3 C08_Menguy_MarketingAISystems.py
"""

from __future__ import annotations

import hashlib


def _unit(salt: str, user_id: str) -> float:
    """A stable, uniform number in [0, 1) from a salt and a customer id."""
    h = hashlib.sha256(f"{salt}:{user_id}".encode()).digest()
    return int.from_bytes(h[:8], "big") / 2**64


def assign(user_id: str, experiment: str, holdout_frac: float = 0.05,
           treat_frac: float = 0.5, program: str = "personalization") -> str:
    """Return 'holdout' | 'control' | 'treatment'.

    The holdout depends only on (program, user), so it is the same slice in
    every experiment. The rest split between control (baseline) and treatment
    (personalized policy) per experiment."""
    holdout = _unit(f"{program}:holdout", user_id)
    if holdout < holdout_frac:
        return "holdout"
    arm = _unit(experiment, user_id)
    return "treatment" if arm < treat_frac else "control"


if __name__ == "__main__":
    from collections import Counter

    users = [f"cust-{i}" for i in range(20_000)]
    spring, summer = "cascade-personalization-2026", "summer-personalization-2026"

    counts = Counter(assign(u, spring) for u in users)
    for arm in ("holdout", "control", "treatment"):
        print(f"{arm:>10}: {counts[arm] / len(users):6.1%}")

    # Stable: the same customer always lands in the same arm of an experiment.
    assert assign("cust-1041", spring) == assign("cust-1041", spring)

    # Permanent: the holdout is the same customers in every experiment.
    h1 = {u for u in users if assign(u, spring) == "holdout"}
    h2 = {u for u in users if assign(u, summer) == "holdout"}
    print(f"holdout is identical across experiments: {h1 == h2} ({len(h1)} customers)")

    # Everyone else is reshuffled per experiment.
    rest = [u for u in users if u not in h1]
    moved = sum(assign(u, spring) != assign(u, summer) for u in rest)
    print(f"non-holdout customers who changed arm: {moved / len(rest):.1%}")
