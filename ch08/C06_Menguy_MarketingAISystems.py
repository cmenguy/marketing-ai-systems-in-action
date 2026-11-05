"""Listing 8.6 - Primitives that make an unscoped operation a hard error.

A context the code can bypass is a convention, and conventions leak. The step that
turns the tenant boundary into a guarantee is making the unscoped operation
impossible to express: a key built without a tenant or a query sent without a
tenant filter raises instead of returning a wrong answer. A loud failure in a test
or in staging is cheap; a silent cross-tenant hit in production is the breach the
whole structure exists to prevent.

Runs with no API key and nothing installed (standard library only).
"""
from __future__ import annotations


class TenantError(Exception):
    """Raised when an operation would run without a tenant scope."""


def scoped_key(tenant_id: str, kind: str, *parts: str) -> str:
    """Build a cache key, refusing to produce one with no tenant."""
    if not tenant_id:
        raise TenantError("cache key built with no tenant")
    return ":".join([tenant_id, kind, *parts])


def checked_filters(filters: dict) -> dict:
    """Pass retrieval filters through only if they carry a tenant."""
    if not filters.get("tenant_id"):
        raise TenantError("retrieval with no tenant filter")
    return filters


def belongs_to(key: str, tenant_id: str) -> bool:
    """A test assertion: this key is this tenant's and no other's."""
    return key.split(":", 1)[0] == tenant_id


if __name__ == "__main__":
    good = scoped_key("northpeak", "asset", "cascade-spring")
    print("scoped key:", good)
    print("belongs to northpeak:", belongs_to(good, "northpeak"))
    print("belongs to ridgeline:", belongs_to(good, "ridgeline"))

    for label, thunk in [
        ("empty tenant key", lambda: scoped_key("", "asset", "x")),
        ("no tenant filter", lambda: checked_filters({"campaign": "x"})),
    ]:
        try:
            thunk()
        except TenantError as err:
            print(f"{label} -> refused: {err}")
