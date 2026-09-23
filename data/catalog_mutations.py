# -*- coding: utf-8 -*-
"""Controlled runtime mutations for Soulbound gameplay catalogs.

Static base definitions still live in :mod:`data.*`.  Runtime/world expansion
modules must change those dictionaries through this module instead of writing
straight into ROOMS/ITEMS/NPCS/QUESTS/MOB_TEMPLATES/SHOPS/recipe tables.

The mutation API intentionally preserves ordinary ``dict`` semantics while
recording provenance.  That gives maintenance tools one place to answer
"who changed this catalog entry?" without changing gameplay data structures.
"""
from __future__ import annotations

from collections import Counter, deque
import inspect
import operator
from typing import Any, Iterable

KNOWN_CATALOGS = frozenset({
    "ROOMS", "ITEMS", "NPCS", "QUESTS", "MOB_TEMPLATES", "SHOPS",
    "CRAFT_RECIPES", "ALCHEMY_RECIPES",
})

# Keep only recent detailed entries so procedural runtime generation cannot grow
# memory without bound.  Aggregate counters and last-writer ownership are kept
# separately and remain complete for the process lifetime.
CATALOG_MUTATION_LOG = deque(maxlen=5000)
CATALOG_MUTATION_COUNTS: Counter[tuple[str, str, str]] = Counter()
CATALOG_LAST_WRITER: dict[tuple[str, Any], str] = {}


def _caller_module() -> str:
    frame = inspect.currentframe()
    try:
        frame = frame.f_back if frame else None
        while frame is not None:
            name = str(frame.f_globals.get("__name__", "") or "")
            if name and name != __name__:
                return name
            frame = frame.f_back
    finally:
        del frame
    return "<unknown>"


def _validate_catalog_name(name: str) -> str:
    name = str(name)
    if name not in KNOWN_CATALOGS:
        raise KeyError(f"Unknown Soulbound catalog: {name}")
    return name


def _at_path(catalog: dict, path: Iterable[Any]):
    obj: Any = catalog
    for key in tuple(path):
        obj = obj[key]
    return obj


def _record(name: str, key: Any, action: str, *, owner: str | None = None, path=()) -> None:
    name = _validate_catalog_name(name)
    owner = str(owner or _caller_module())
    root_key = key
    CATALOG_MUTATION_COUNTS[(owner, name, action)] += 1
    CATALOG_LAST_WRITER[(name, root_key)] = owner
    CATALOG_MUTATION_LOG.append({
        "owner": owner,
        "catalog": name,
        "key": root_key,
        "action": action,
        "path": tuple(path),
    })


def catalog_set_path(name: str, catalog: dict, path: Iterable[Any], value: Any, *, owner: str | None = None):
    """Equivalent to ``catalog[a][b] = value`` while recording ownership."""
    owner = str(owner or _caller_module())
    path = tuple(path)
    if not path:
        raise ValueError("catalog_set_path requires at least one key")
    parent = _at_path(catalog, path[:-1])
    parent[path[-1]] = value
    _record(name, path[0], "set", owner=owner, path=path)
    return value



def catalog_assign(value: Any, name: str, catalog: dict, path: Iterable[Any], *, owner: str | None = None):
    """Assignment helper with RHS-first evaluation order matching Python ``=``."""
    return catalog_set_path(name, catalog, path, value, owner=owner)

def catalog_update_path(name: str, catalog: dict, path: Iterable[Any], *args, owner: str | None = None, **kwargs):
    """Equivalent to ``catalog[..].update(...)`` with provenance tracking."""
    owner = str(owner or _caller_module())
    path = tuple(path)
    target = _at_path(catalog, path)
    # Resolve keys before update where practical, exactly as dict.update would.
    preview = dict(*args, **kwargs)
    target.update(*args, **kwargs)
    if path:
        _record(name, path[0], "update", owner=owner, path=path)
    else:
        for key in preview:
            _record(name, key, "update", owner=owner, path=(key,))
    return None


def catalog_setdefault_path(name: str, catalog: dict, path: Iterable[Any], key: Any, default: Any = None, *, owner: str | None = None):
    """Equivalent to ``catalog[..].setdefault(key, default)``."""
    owner = str(owner or _caller_module())
    path = tuple(path)
    target = _at_path(catalog, path)
    existed = key in target
    value = target.setdefault(key, default)
    root_key = path[0] if path else key
    if not existed:
        _record(name, root_key, "setdefault", owner=owner, path=path + (key,))
    return value


def catalog_pop_path(name: str, catalog: dict, path: Iterable[Any], key: Any, *default, owner: str | None = None):
    """Equivalent to ``catalog[..].pop(key[, default])``."""
    owner = str(owner or _caller_module())
    if len(default) > 1:
        raise TypeError(f"pop expected at most 2 arguments, got {2 + len(default)}")
    path = tuple(path)
    target = _at_path(catalog, path)
    existed = key in target
    if default:
        value = target.pop(key, default[0])
    else:
        value = target.pop(key)
    if existed:
        root_key = path[0] if path else key
        _record(name, root_key, "pop", owner=owner, path=path + (key,))
    return value


_AUGMENTED_OPERATORS = {
    "Add": operator.iadd,
    "Sub": operator.isub,
    "Mult": operator.imul,
    "MatMult": operator.imatmul,
    "Div": operator.itruediv,
    "FloorDiv": operator.ifloordiv,
    "Mod": operator.imod,
    "Pow": operator.ipow,
    "LShift": operator.ilshift,
    "RShift": operator.irshift,
    "BitOr": operator.ior,
    "BitXor": operator.ixor,
    "BitAnd": operator.iand,
}


def catalog_aug_path(name: str, catalog: dict, path: Iterable[Any], op_name: str, value: Any, *, owner: str | None = None):
    """Preserve Python augmented-assignment semantics for a catalog path."""
    owner = str(owner or _caller_module())
    path = tuple(path)
    if not path:
        raise ValueError("catalog_aug_path requires at least one key")
    parent = _at_path(catalog, path[:-1])
    op = _AUGMENTED_OPERATORS.get(str(op_name))
    if op is None:
        raise ValueError(f"Unsupported augmented catalog operator: {op_name}")
    result = op(parent[path[-1]], value)
    parent[path[-1]] = result
    _record(name, path[0], "aug", owner=owner, path=path)
    return result


def catalog_last_writer(name: str, key: Any) -> str | None:
    """Return the module that most recently changed a top-level catalog key."""
    return CATALOG_LAST_WRITER.get((_validate_catalog_name(name), key))


def catalog_recent_changes(name: str | None = None, key: Any = None, limit: int = 20):
    """Return recent provenance rows, optionally filtered by catalog/key."""
    if name is not None:
        name = _validate_catalog_name(name)
    wanted = max(1, min(500, int(limit or 20)))
    rows = []
    for row in reversed(CATALOG_MUTATION_LOG):
        if name is not None and row.get("catalog") != name:
            continue
        if key is not None and row.get("key") != key:
            continue
        rows.append(dict(row))
        if len(rows) >= wanted:
            break
    return tuple(rows)


def catalog_mutation_summary() -> dict:
    """Return a maintenance-friendly snapshot without exposing mutable internals."""
    by_catalog = Counter()
    by_owner = Counter()
    by_action = Counter()
    for (owner, catalog, action), count in CATALOG_MUTATION_COUNTS.items():
        by_catalog[catalog] += int(count)
        by_owner[owner] += int(count)
        by_action[action] += int(count)
    return {
        "mutation_count": sum(CATALOG_MUTATION_COUNTS.values()),
        "tracked_key_count": len(CATALOG_LAST_WRITER),
        "by_catalog": dict(sorted(by_catalog.items())),
        "by_owner": dict(sorted(by_owner.items())),
        "by_action": dict(sorted(by_action.items())),
        "recent": tuple(CATALOG_MUTATION_LOG),
    }
