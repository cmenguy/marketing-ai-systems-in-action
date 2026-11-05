"""Agentic retrieval: decompose a multi-hop question, run each step, synthesize
(Listing 4.8).

The question from chapter 1, "what did we say about the Cascade during last
spring's EMEA push, and did legal sign off?", is not one retrieval. It is a chain:
find the Cascade campaigns, filter to EMEA and the spring quarter, retrieve what
they said, and check each approval record. A single embedding of the whole
question answers none of the four parts well.

Agentic retrieval keeps the structure by decomposing the question into steps and
running retrieval per step. An LLM plans the steps (vector or graph) and
synthesizes the evidence into a cited answer. Here `plan` and `synthesize` are
injected so the control flow is visible and testable without a live model; in
production they are model calls (prefer a capable model such as Claude Sonnet /
Opus, with the API key read from the environment).

This is the retrieval loop chapter 9's full campaign agent is built around.
"""

from __future__ import annotations

from dataclasses import dataclass

from C07_Menguy_MarketingAISystems import sample_graph


@dataclass(frozen=True)
class Step:
    kind: str          # "vector" | "graph"
    query: str


def agentic_retrieve(question, tools, plan, synthesize):
    steps = plan(question)                          # LLM decomposes the question
    evidence = []
    for step in steps:
        if step.kind == "graph":
            hits = tools["graph"](step.query)
        else:
            hits = tools["vector"](step.query)
        evidence.append((step, hits))
    return synthesize(question, evidence)           # cited answer


if __name__ == "__main__":
    g = sample_graph()

    # Stub planner: decompose the chapter-1 multi-hop question.
    def plan(question):
        return [
            Step("graph", "cascade campaigns in EMEA"),
            Step("vector", "approved copy per campaign"),
            Step("graph", "approval record per campaign"),
        ]

    # Stub tools wrapping the genealogy graph and a stand-in vector search.
    tools = {
        "graph": lambda q: g.campaigns_for("cascade", "EMEA"),
        "vector": lambda q: ["10K/10K waterproof, 63% recycled face fabric"],
    }

    # Stub synthesizer: assemble a cited answer from the collected evidence.
    def synthesize(question, evidence):
        lines = [f"Q: {question}"]
        for step, hits in evidence:
            lines.append(f"  [{step.kind}] {step.query} -> {hits}")
        camps = evidence[0][1]
        approvals = [g.approved_by.get(c) for c in camps]
        lines.append(f"  answer: {camps} approved by {approvals}")
        return "\n".join(lines)

    print(agentic_retrieve(
        "What did we say about the Cascade in last spring's EMEA push, "
        "and did legal sign off?",
        tools, plan, synthesize))
