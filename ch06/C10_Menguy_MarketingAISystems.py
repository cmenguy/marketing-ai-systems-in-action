"""Listing 6.9 - Registering an approved asset in the DAM with provenance and version.

The approved asset lives in the DAM, the same system the pipeline read the product
references and logo from at the start, so the loop closes: assets you generate
become assets you can ground the next generation in. Registration carries the
whole trail (provenance, kit version, approvals, license) and a content hash that
pins the exact bytes. A new version supersedes the prior one rather than
overwriting it, because a campaign that ran on last quarter's asset needs that
asset to still exist. This is chapter 4's supersession rule applied to pixels.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

import numpy as np

from C09_Menguy_MarketingAISystems import VisualProvenance, sign_manifest, _demo_sign


@dataclass(frozen=True)
class AssetRecord:
    asset_id: str
    version: int
    content_hash: str
    provenance: VisualProvenance
    approvals: tuple            # which flows cleared: legal, brand, creative
    license: dict               # the rights record
    supersedes: int | None


@dataclass
class InMemoryDAM:
    _by_id: dict = field(default_factory=dict)   # asset_id -> list[AssetRecord]

    def latest(self, asset_id: str):
        versions = self._by_id.get(asset_id)
        return versions[-1] if versions else None

    def put(self, record: AssetRecord, image: np.ndarray):
        self._by_id.setdefault(record.asset_id, []).append(record)


class BynderDAM:
    """Illustrative: a real DAM behind the same latest/put interface.

    Not runnable here (no SDK); the exact methods live in the provider's docs and
    change over time. The same thin adapter wraps any DAM (Bynder, Cloudinary,
    Brandfolder, or an in-house object store) -- keep
    the latest/put interface in your own code and the vendor stays swappable.
    """

    def __init__(self, client):          # a configured Bynder SDK client
        self.client = client

    def latest(self, asset_id):
        hits = self.client.assets(query=asset_id, order="-version")
        return hits[0] if hits else None

    def put(self, record, image):
        from dataclasses import asdict
        self.client.upload(image, metadata=asdict(record))


def image_bytes(image: np.ndarray) -> bytes:
    return image.tobytes()


def register_asset(dam, image, prov, approvals, license_record):
    content_hash = hashlib.sha256(image_bytes(image)).hexdigest()[:16]
    prior = dam.latest(prov.asset_id)
    version = (prior.version + 1) if prior else 1
    record = AssetRecord(
        asset_id=prov.asset_id, version=version, content_hash=content_hash,
        provenance=prov, approvals=tuple(approvals), license=license_record,
        supersedes=(prior.version if prior else None),
    )
    dam.put(record, image)
    return record


if __name__ == "__main__":
    from datetime import date

    dam = InMemoryDAM()
    prov = VisualProvenance(
        asset_id="cascade-spring-2026:hero:email", model="image-model",
        model_version="2026.03", seed=42, prompt="Cascade hero shot",
        product_ref="dam://northpeak/products/cascade_shell.png",
        template="figma://northpeak/templates/email_hero",
        conditioning={"palette": ["#1F3D2B"]}, kit_version="2026-Q2",
        rights_basis="brand-owned-refs", created=date(2026, 3, 1),
    )
    license_record = {"commercial": True, "signed_manifest":
                      sign_manifest(prov, _demo_sign)["signature"]}

    img_v1 = np.full((100, 100, 3), [31, 61, 43], dtype=np.uint8)
    rec1 = register_asset(dam, img_v1, prov, ("legal", "brand", "creative"),
                          license_record)
    print(f"registered v{rec1.version}, supersedes={rec1.supersedes}, "
          f"hash={rec1.content_hash}")

    img_v2 = img_v1.copy(); img_v2[0, 0] = [242, 237, 228]   # a small revision
    rec2 = register_asset(dam, img_v2, prov, ("legal", "brand", "creative"),
                          license_record)
    print(f"registered v{rec2.version}, supersedes={rec2.supersedes}, "
          f"hash={rec2.content_hash}")
