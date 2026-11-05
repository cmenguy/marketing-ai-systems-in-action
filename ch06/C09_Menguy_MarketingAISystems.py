"""Listing 6.8 - A signed provenance manifest, C2PA in spirit.

Provenance answers the same question chapter 4's citation did for a copy claim:
where did this come from. You record everything needed to answer a rights or an
incident question later (model, version, seed, prompt, conditioning, the product
reference and template the asset was assembled from, kit version, rights basis)
and sign it, because reconstructing it after the asset ships is impossible while
recording it at generation is nearly free. Recording the product ref and template
also buys reproducibility (regenerate or re-localize later). `to_citation` reuses
chapter 4's Citation so provenance reaches approval the same way.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import date


@dataclass(frozen=True)
class Citation:                    # chapter 4's Citation shape (restated)
    source_id: str
    quarter: str
    approval_state: str
    fact: str


@dataclass(frozen=True)
class VisualProvenance:
    asset_id: str
    model: str                     # "image-model-2026.03"
    model_version: str
    seed: int
    prompt: str
    product_ref: str | None        # the product asset it was assembled from
    template: str | None           # the approved template used
    conditioning: dict             # structure map, style-reference ids, palette
    kit_version: str               # which brand kit produced this
    rights_basis: str              # "model-terms:commercial" | "brand-owned-refs"
    created: date


def sign_manifest(prov: VisualProvenance, sign):
    payload = json.dumps(asdict(prov), sort_keys=True, default=str)  # stable
    return {"manifest": payload, "signature": sign(payload)}          # C2PA-style


def to_citation(prov: VisualProvenance) -> Citation:
    return Citation(source_id=prov.asset_id, quarter=prov.kit_version,
                    approval_state="generated", fact=prov.prompt)


def _demo_sign(payload: str) -> str:
    import hashlib
    return hashlib.sha256(("northpeak-key:" + payload).encode()).hexdigest()[:16]


if __name__ == "__main__":
    prov = VisualProvenance(
        asset_id="cascade-spring-2026:hero:email",
        model="image-model", model_version="2026.03", seed=42,
        prompt="Cascade shell on a wet trail, hero product shot",
        product_ref="dam://northpeak/products/cascade_shell.png",
        template="figma://northpeak/templates/email_hero",
        conditioning={"structure": "layout-map-3", "style_refs": ["fall_01"],
                      "palette": ["#1F3D2B", "#F2EDE4"]},
        kit_version="2026-Q2", rights_basis="brand-owned-refs",
        created=date(2026, 3, 1),
    )
    signed = sign_manifest(prov, _demo_sign)
    print("signature:", signed["signature"])
    print("assembled from:", prov.product_ref, "+", prov.template)
    print("citation: ", to_citation(prov))
