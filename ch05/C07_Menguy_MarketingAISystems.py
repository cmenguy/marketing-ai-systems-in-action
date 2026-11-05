"""Routing an asset to the flows it needs, with its citations (Listing 5.7).

Not every asset needs all three flows, and routing everything to everyone is how
you bury reviewers. The router decides which flows an asset needs, based on what
the checks found and how risky the asset is, and it consumes chapter 4's review
package so each reviewer sees the sources behind the copy.

Creative always reviews (someone owns whether it is good). A regulated claim or a
high-risk asset always goes to legal. A low brand-voice score routes to brand, the
human behind the gate's proxy. Publish is gated on all required flows clearing;
the slowest flow binds.
"""

from __future__ import annotations

from dataclasses import dataclass

from C01_Menguy_MarketingAISystems import Citation, sample_facts
from C06_Menguy_MarketingAISystems import Ctx, QualityReport, gate

FLOWS = ("legal", "brand", "creative")

REGULATED = ("rating", "recycled", "guaranteed", "clinical")


@dataclass(frozen=True)
class ReviewPackage:
    copy: str
    citations: list[Citation]


@dataclass(frozen=True)
class ApprovalTask:
    flow: str
    package: ReviewPackage
    state: str                # "pending" | "approved" | "rejected"


def makes_regulated_claim(citations) -> bool:
    return any(any(w in c.fact.lower() for w in REGULATED) for c in citations)


def required_flows(report, package, risk):
    flows = {"creative"}
    if makes_regulated_claim(package.citations) or risk == "high":
        flows.add("legal")
    voice = next(r for r in report.results if r.name == "brand_voice")
    if not voice.passed or risk == "high":
        flows.add("brand")
    return flows


def route(package, report, risk):
    needed = required_flows(report, package, risk)
    return {flow: ApprovalTask(flow=flow, package=package, state="pending")
            for flow in needed}


def ready_to_publish(tasks) -> bool:
    return all(t.state == "approved" for t in tasks.values())


if __name__ == "__main__":
    from C01_Menguy_MarketingAISystems import GenerationSpec

    spec = GenerationSpec("brief", "loyalty", "email",
                          "cascade-spring-2026", sample_facts(), "v3")
    clean = ("The shell is here. A 10K/10K waterproof-breathable rating and a "
             "63% recycled face fabric. Spring pricing runs through May 31.")
    report = gate(clean, spec, Ctx())
    package = ReviewPackage(copy=clean, citations=sample_facts())

    claim_asset = route(package, report, risk="normal")
    print("regulated-claim asset ->", sorted(claim_asset))

    plain = ReviewPackage(copy="Our store reopens Monday.", citations=[])
    plain_report = gate("Our store reopens Monday. Come say hi.", spec, Ctx())
    plain_asset = route(plain, plain_report, risk="low")
    print("plain restock notice  ->", sorted(plain_asset))

    assert "legal" in claim_asset, "a regulated claim always goes to legal"
    assert "legal" not in plain_asset, "a claimless notice skips legal"
    assert not ready_to_publish(claim_asset), "nothing publishes while pending"
    print("OK: routing sends each asset only to the flows it needs.")
