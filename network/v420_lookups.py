# -*- coding: utf-8 -*-
"""Native historical helper extraction; unchanged function bodies."""
def find_by_name(mapping, query, name_field="name"):
    q = normalize_lookup_text(query)
    if not q:
        return None

    # v0.71.5: exact item lookups are O(1); partial searches reuse normalized
    # names/aliases instead of normalizing tens of thousands of strings again.
    # Cache lives on this already-existing function, so the architectural global
    # dependency budget does not grow.
    if mapping is ITEMS and name_field == "name":
        cache = getattr(find_by_name, "_v0715_cache", None)
        if not isinstance(cache, dict) or cache.get("size") != len(ITEMS):
            rows = []
            exact = {}
            for key, value in ITEMS.items():
                key_name = normalize_lookup_text(key)
                name = normalize_lookup_text(value.get("name", key))
                aliases = tuple(
                    normalize_lookup_text(alias)
                    for alias in (value.get("aliases") or ())
                    if str(alias or "").strip()
                )
                rows.append((key, value, key_name, name, aliases))
                for token in (key_name, name, *aliases):
                    if token and token not in exact:
                        exact[token] = (key, value)
            cache = {"size": len(ITEMS), "rows": tuple(rows), "exact": exact}
            find_by_name._v0715_cache = cache
        hit = cache["exact"].get(q)
        if hit is not None:
            return hit
        partial = []
        for key, value, key_name, name, aliases in cache["rows"]:
            if q in name or q in key_name or any(q in alias for alias in aliases):
                partial.append((key, value))
                if len(partial) > 1:
                    return None
        return partial[0] if partial else None

    exact = []
    partial = []
    for key, value in mapping.items():
        key_name = normalize_lookup_text(key)
        name = normalize_lookup_text(value[name_field])
        aliases = [
            normalize_lookup_text(alias)
            for alias in (value.get("aliases") or ())
            if str(alias or "").strip()
        ]
        if q == key_name or q == name or q in aliases:
            exact.append((key, value))
        elif (
            q in name or q in key_name or
            any(q in alias for alias in aliases)
        ):
            partial.append((key, value))
    if exact:
        return exact[0]
    if len(partial) == 1:
        return partial[0]
    return None

