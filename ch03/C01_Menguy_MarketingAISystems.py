"""The prompt as a versioned component, not a string (Listing 3.1).

In a demo a prompt is a string you edit until the output looks right. In
production it is a component with typed, owned layers and a version. Modeling it
this way is what lets you route a change to its owner, test a version, pin the
exact prompt that produced an asset, and roll back to the fingerprint that
worked. The other listings in this chapter fill the layers; this one fixes the
shape they go in.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class PromptLayer:
    """One owned piece of a prompt."""

    name: str      # "brand_voice", "legal_required", ...
    owner: str     # "creative", "legal", "engineering"
    content: str


@dataclass(frozen=True)
class PromptTemplate:
    """An ordered set of owned layers with an id and a version."""

    template_id: str
    version: int
    layers: tuple[PromptLayer, ...]

    def render(self) -> str:
        """Assemble the layers into the single string the model reads."""
        return "\n\n".join(
            f"[{layer.name}]\n{layer.content}" for layer in self.layers
        )

    def owned_by(self, owner: str) -> list[str]:
        """The layer names a given team owns, so a change can be routed."""
        return [layer.name for layer in self.layers if layer.owner == owner]

    def fingerprint(self) -> str:
        """A content hash: a changed prompt is a changed artifact."""
        body = self.render().encode("utf-8")
        return hashlib.sha256(body).hexdigest()[:12]


def demo_template() -> PromptTemplate:
    return PromptTemplate(
        template_id="copy.launch",
        version=1,
        layers=(
            PromptLayer("system", "engineering",
                        "You write marketing copy for Northpeak."),
            PromptLayer("brand_voice", "creative",
                        "Plainspoken and technical. No hype."),
            PromptLayer("legal_required", "legal",
                        "Include the waterproof rating and an opt-out."),
            PromptLayer("brief", "marketing",
                        "Launch the Cascade waterproof shell for spring."),
        ),
    )


if __name__ == "__main__":
    tpl = demo_template()
    print(tpl.render())
    print("\n---")
    print("legal owns:", tpl.owned_by("legal"))
    print("fingerprint:", tpl.fingerprint())
