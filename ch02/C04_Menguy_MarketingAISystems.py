"""Retrieval over brand corpora: nearest approved examples as few-shot (2.4).

The lightest way to make a model sound on-brand without training anything: at
generation time, retrieve the approved copy most similar to the task and show it
to the model as examples. Chapter 4 builds the real retrieval layer.
"""

from __future__ import annotations

import numpy as np

from C02_Menguy_MarketingAISystems import APPROVED_COPY
from C03_Menguy_MarketingAISystems import embed


def nearest_examples(task: str, corpus: list[str], k: int = 3) -> list[str]:
    """Return the k approved snippets most similar to the task."""
    corpus_vecs = embed(corpus)
    task_vec = embed([task])[0]
    scores = corpus_vecs @ task_vec          # cosine; vectors are normalized
    top = np.argsort(-scores)[:k]
    return [corpus[i] for i in top]


def few_shot_prompt(task: str, corpus: list[str], k: int = 3) -> str:
    """Build a prompt whose brand voice comes from retrieved examples."""
    examples = nearest_examples(task, corpus, k)
    shown = "\n\n".join(f"Example:\n{e}" for e in examples)
    return (
        "Write in the same voice as these approved examples.\n\n"
        f"{shown}\n\n"
        f"Task: {task}"
    )


if __name__ == "__main__":
    task = "Announce the Cascade shell to loyalty members, spring pricing."
    print(few_shot_prompt(task, APPROVED_COPY, k=2))
