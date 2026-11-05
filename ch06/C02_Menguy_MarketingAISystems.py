"""Listing 6.2 - Building a conditioning request grounded in the product reference.

Conditioning gives the model the brand's real assets, not just a text prompt. The
channels do different jobs: a PRODUCT reference controls identity (the output is
the Cascade, not a lookalike), a STYLE reference controls mood, a STRUCTURE input
controls composition, and a PALETTE hint steers color. Treating every reference
as style produces an on-mood photograph of the wrong product. The product asset
is resolved from the DAM by code, so the reference is always the current cleared
asset. `generate_image` takes the model as an argument: the piece most expected
to be replaced.
"""
from __future__ import annotations

from dataclasses import dataclass

from C01_Menguy_MarketingAISystems import VisualBrandKit, northpeak_kit


@dataclass(frozen=True)
class Conditioning:
    text: str                            # the scene, in words
    product_reference: str | None = None  # the real product asset: identity
    style_references: tuple[str, ...] = ()  # approved images: mood
    structure: object | None = None      # a control map: layout, depth, edges
    palette: tuple[str, ...] = ()         # a soft color steer


def build_request(brief: str, kit: VisualBrandKit, product_code: str | None = None,
                  layout: object | None = None, style_refs=()) -> Conditioning:
    product = kit.products.get(product_code) if product_code else None
    text = (
        f"{brief}. Photographic, natural light, matte finish. "
        f"Avoid: {', '.join(kit.forbidden)}."
    )
    return Conditioning(
        text=text,
        product_reference=product.uri if product else None,   # identity
        style_references=tuple(style_refs),                    # mood
        structure=layout, palette=tuple(kit.palette),
    )


def generate_image(req: Conditioning, model):
    """`model` is injected: any diffusion or multimodal generator."""
    return model(text=req.text, product=req.product_reference,
                 style=req.style_references,
                 structure=req.structure, palette=req.palette)


def _stub_model(text, product, style, structure, palette):
    return {"kind": "image", "grounded_on_product": product is not None,
            "product": product, "n_style_refs": len(style),
            "steered_palette": list(palette)}


if __name__ == "__main__":
    kit = northpeak_kit()
    req = build_request("The Cascade shell on a wet trail, hero shot", kit,
                        product_code="cascade",
                        style_refs=("dam://northpeak/hero/fall_01.png",))
    print("PROMPT:      ", req.text)
    print("PRODUCT REF: ", req.product_reference, "(identity)")
    print("STYLE REFS:  ", req.style_references, "(mood)")
    print("GENERATED:   ", generate_image(req, _stub_model))
