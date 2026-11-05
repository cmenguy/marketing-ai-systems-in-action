"""Listing 8.5 - A tenant context that scopes retrieval, cache, prompt, and logs.

At a martech vendor one system serves many brands, and no brand's context may ever
reach another. Four subsystems hold tenant data: retrieval, prompt assembly,
evaluation, and logging. Rather than remember the boundary at four call sites,
build it once in an object every request carries. A TenantContext is created at
the edge when a request's tenant is identified, and from then on every filter,
key, prompt source, and log line comes through it.

Runs with no API key and nothing installed (standard library only).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TenantContext:
    tenant_id: str
    corpus_version: str

    def retrieval_filters(self, base: dict) -> dict:
        """Every query carries the tenant filter the index enforces."""
        return {**base, "tenant_id": self.tenant_id}

    def cache_key(self, kind: str, *parts: str) -> str:
        """Every cache key is namespaced by tenant and never collides."""
        return ":".join([self.tenant_id, kind, *parts])

    def style_source(self, corpora: dict) -> object:
        """The prompt is built from this tenant's corpus alone."""
        return corpora[self.tenant_id]

    def log_fields(self, **extra) -> dict:
        """Every log line records the tenant it belongs to."""
        return {"tenant_id": self.tenant_id, **extra}


if __name__ == "__main__":
    ctx = TenantContext("northpeak", "corpus-2026Q2")
    print("retrieval filters:",
          ctx.retrieval_filters({"campaign_code": "cascade-spring"}))
    print("cache key:        ",
          ctx.cache_key("asset", "cascade-spring", "loyalty", "email"))
    corpora = {"northpeak": "<northpeak style guide>",
               "ridgeline": "<ridgeline style guide>"}
    print("style source:     ", ctx.style_source(corpora))
    print("log fields:       ", ctx.log_fields(campaign="cascade-spring"))
