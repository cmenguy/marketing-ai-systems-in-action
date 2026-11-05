"""A campaign genealogy graph, and retrieval scoped by walking it (Listing 4.7).

Supersession is one relationship between documents; it is not the only one.
Campaigns have a genealogy: this spring's launch derives from last spring's, runs
as an EMEA variant, targets a product, and carries an approval record. Those are
edges in a graph, and some marketer questions are really questions about the
edges, not the text of any one document.

Vector search finds nodes by what their text is about; graph traversal finds them
by how they connect. The traversals return campaign codes, not documents, so
graph_scoped_retrieve connects them back to the pipeline: it walks the graph to
decide which campaigns are eligible, then hands that narrowed corpus to retrieve
(C06) unchanged. Legal and style copy are exempt from the scoping, because they
are not campaign-scoped and must come back whatever the traversal returns. In
production the graph is a graph database or a library like networkx; the idea is
independent of the tool.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from C06_Menguy_MarketingAISystems import retrieve


@dataclass
class Genealogy:
    parent: dict[str, str] = field(default_factory=dict)
    product: dict[str, str] = field(default_factory=dict)
    region: dict[str, str] = field(default_factory=dict)
    approved_by: dict[str, str] = field(default_factory=dict)

    def add(self, code, *, parent=None, product=None,
            region=None, approval=None):
        if parent:
            self.parent[code] = parent
        if product:
            self.product[code] = product
        if region:
            self.region[code] = region
        if approval:
            self.approved_by[code] = approval

    def lineage(self, code: str) -> list[str]:
        """Walk parent edges to recover a campaign's ancestry."""
        chain = [code]
        while code in self.parent:
            code = self.parent[code]
            chain.append(code)
        return chain

    def campaigns_for(self, product: str, region: str) -> list[str]:
        """Answer a product-and-region question by structure, not similarity."""
        return [c for c, p in self.product.items()
                if p == product and self.region.get(c) == region]


def graph_scoped_retrieve(question, graph, chunks, want, embed, score,
                          today, product, region, k=5):
    codes = set(graph.campaigns_for(product, region))
    for code in list(codes):
        codes.update(graph.lineage(code))   # include ancestry
    scoped = [c for c in chunks
              if c.meta.doc_type != "brief"
              or c.meta.campaign_code in codes]
    return retrieve(question, scoped, want, embed, score, today, k)


def sample_graph() -> Genealogy:
    # The Cascade genealogy from the chapter's graph figure: the 2026 launch
    # derives from 2025, and the EMEA variant derives from 2026, runs in EMEA,
    # and is approved under record rec-4821.
    g = Genealogy()
    g.add("cascade-spring-2025", product="cascade", region="US",
          approval="rec-3990")
    g.add("cascade-spring-2026", parent="cascade-spring-2025",
          product="cascade", region="US", approval="rec-4800")
    g.add("cascade-spring-2026-emea", parent="cascade-spring-2026",
          product="cascade", region="EMEA", approval="rec-4821")
    return g


if __name__ == "__main__":
    import re
    from datetime import date

    from C01_Menguy_MarketingAISystems import sample_corpus
    from C03_Menguy_MarketingAISystems import chunk_corpus
    from C04_Menguy_MarketingAISystems import bow

    def lexical_score(query: str, text: str) -> float:
        # Dependency-free stand-in for a cross-encoder (C06 loads a real one).
        q = set(re.findall(r"[a-z0-9]+", query.lower()))
        t = set(re.findall(r"[a-z0-9]+", text.lower()))
        return float(len(q & t))

    g = sample_graph()
    print("lineage:", g.lineage("cascade-spring-2026-emea"))
    print("Cascade campaigns in EMEA:", g.campaigns_for("cascade", "EMEA"))
    print("approved by:", g.approved_by["cascade-spring-2026-emea"])

    chunks = chunk_corpus(sample_corpus())
    want = {"channel": "email", "segment": "loyalty"}
    question = "What did we say about the Cascade in EMEA?"

    codes = set(g.campaigns_for("cascade", "EMEA"))
    for code in list(codes):
        codes.update(g.lineage(code))
    print("\ngraph selected campaigns:", sorted(codes))

    hits = graph_scoped_retrieve(question, g, chunks, want, bow,
                                 lexical_score, date.today(),
                                 product="cascade", region="EMEA")
    print("graph-scoped retrieval (briefs in scope, legal exempt):")
    for c in hits:
        print(f"  {c.chunk_id}  quarter={c.meta.quarter} type={c.meta.doc_type}")
