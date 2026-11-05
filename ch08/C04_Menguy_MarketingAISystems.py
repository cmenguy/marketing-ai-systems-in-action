"""Listing 8.4 - The three cache layers wired into one request, with the prompt
prefix engaged on the provider's side.

Three layers remove repeated work:
  - the retrieval cache reuses grounded facts for a query + corpus version;
  - the generation cache reuses a whole deterministic asset;
  - the prompt-prefix cache lives on the provider, engaged by flagging the
    static bytes of the prompt so the provider charges them once while warm.

The provider and the retrieve function are injected, so this is a complete,
runnable end-to-end example with no API key and nothing installed. Swap the stub
`provider` for a real client (marking the first block cacheable is the one
provider-specific line) and the flow is unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GenerationSpec:
    campaign_code: str
    segment: str
    channel: str
    prompt_fingerprint: str


@dataclass(frozen=True)
class Request:
    tenant: str
    query: str
    prefix: str            # the brand's static prompt prefix (stable bytes)
    spec: GenerationSpec


def prefix_key(tenant, fingerprint):
    """The prefix's identity. Its cache lives on the provider, not here; this
    names it for the invalidation table and for flushing when the prompt moves."""
    return ":".join([tenant, "prefix", fingerprint])


def retrieval_key(tenant, query, corpus_version):
    return ":".join([tenant, "retr", corpus_version, query])


def asset_key(tenant, spec, corpus_version):
    return ":".join([tenant, "asset", spec.campaign_code, spec.segment,
                     spec.channel, spec.prompt_fingerprint, corpus_version])


class LayeredCache(dict):
    def invalidate(self, corpus_version):
        dead = [k for k in self if corpus_version in k.split(":")]
        for k in dead:
            del self[k]
        return len(dead)


def render(spec, facts):
    """The variable tail of the prompt: the per-request brief and facts."""
    return f"[{spec.segment}/{spec.channel}] facts={list(facts)}"


def build_call(spec, prefix, facts):
    # Stable bytes first and flagged cacheable; the variable tail comes last.
    # The flag is what a real provider's prompt cache keys on. Some providers
    # need no flag and cache the longest matching prefix on their own, so the
    # static-first ordering is what engages them either way.
    return {"blocks": [{"text": prefix, "cache": True},
                       {"text": render(spec, facts)}]}


def generate(req, cache, retrieve, provider, corpus_version):
    """Run a request through the three layers in cost order."""
    rk = retrieval_key(req.tenant, req.query, corpus_version)
    if rk not in cache:
        cache[rk] = retrieve(req.query)          # retrieval layer
    ak = asset_key(req.tenant, req.spec, corpus_version)
    if ak in cache:
        return cache[ak], "generation-cache"     # whole asset reused
    call = build_call(req.spec, req.prefix, cache[rk])
    asset = provider(call)                        # provider caches the prefix
    cache[ak] = asset
    return asset, "generated"


def anthropic_provider(model, max_tokens=1024):
    """An illustrative `provider` for Anthropic's API (not run by the demo).

    The flagged blocks become system blocks with a cache_control marker; the
    variable tail goes in the user message. SDKs change between releases, so
    check the provider's current docs before relying on this. The SDK is
    imported here so the rest of the file runs without it installed.
    """
    import anthropic
    client = anthropic.Anthropic()        # reads ANTHROPIC_API_KEY

    def provider(call):
        blocks = call["blocks"]
        system = [{"type": "text", "text": b["text"],
                   "cache_control": {"type": "ephemeral"}}
                  for b in blocks if b.get("cache")]
        tail = "\n\n".join(b["text"] for b in blocks
                           if not b.get("cache"))
        resp = client.messages.create(
            model=model, max_tokens=max_tokens, system=system,
            messages=[{"role": "user", "content": tail}])
        return "".join(b.text for b in resp.content
                       if b.type == "text")

    return provider


if __name__ == "__main__":
    # A stub provider stands in for a real client. It records whether the
    # first (prefix) block was flagged cacheable, which is what engages a real
    # provider's prompt cache.
    calls = []

    def provider(call):
        head = call["blocks"][0]
        calls.append({"cached_prefix": head.get("cache", False),
                      "prefix_chars": len(head["text"])})
        return "<generated asset>"

    retrievals = []

    def retrieve(query):
        retrievals.append(query)
        return ("spring price through May 31", "recycled-content clause")

    cache = LayeredCache()
    brand_prefix = "Northpeak voice block + legal rules. " * 32   # static bytes
    spec = GenerationSpec("cascade-spring", "loyalty", "email", "pf-7")
    req = Request("northpeak", "cascade offer terms", brand_prefix, spec)
    cv = "corpus-2026Q2"

    a1, how1 = generate(req, cache, retrieve, provider, cv)
    a2, how2 = generate(req, cache, retrieve, provider, cv)
    print(f"first call:  {how1}")      # generated
    print(f"second call: {how2}")      # generation-cache, no provider call
    print(f"provider calls: {len(calls)}   retrievals: {len(retrievals)}")
    print(f"prefix flagged cacheable on the call: {calls[0]['cached_prefix']}")

    dropped = cache.invalidate(cv)     # a quarterly corpus refresh
    a3, how3 = generate(req, cache, retrieve, provider, cv)
    print(f"after refresh dropped {dropped} entries: {how3}")   # generated
