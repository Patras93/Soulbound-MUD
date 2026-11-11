# -*- coding: utf-8 -*-
"""Static guards for controlled Soulbound runtime catalog ownership."""
from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path

CATALOG_NAMES = frozenset({
    "ROOMS", "ITEMS", "NPCS", "QUESTS", "MOB_TEMPLATES", "SHOPS",
    "CRAFT_RECIPES", "ALCHEMY_RECIPES",
})
_MUTATING_METHODS = frozenset({"update", "setdefault", "pop", "clear"})


def _root_catalog_and_path(node):
    keys = []
    cur = node
    while isinstance(cur, ast.Subscript):
        keys.append(cur.slice)
        cur = cur.value
    if isinstance(cur, ast.Name) and cur.id in CATALOG_NAMES:
        return cur.id, tuple(reversed(keys))
    return None, ()


def raw_catalog_writes(path: Path):
    """Return direct catalog writes that bypass data.catalog_mutations."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    rows = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                name, keys = _root_catalog_and_path(target)
                if name:
                    rows.append((int(node.lineno), name, "assign", len(keys)))
                    break
        elif isinstance(node, ast.AnnAssign):
            name, keys = _root_catalog_and_path(node.target)
            if name:
                rows.append((int(node.lineno), name, "annassign", len(keys)))
        elif isinstance(node, ast.AugAssign):
            name, keys = _root_catalog_and_path(node.target)
            if name:
                rows.append((int(node.lineno), name, "augassign", len(keys)))
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr not in _MUTATING_METHODS:
                continue
            name, keys = _root_catalog_and_path(node.func.value)
            if name:
                rows.append((int(node.lineno), name, node.func.attr, len(keys)))
    return tuple(sorted(rows))


def validate_runtime_catalog_ownership(root, runtime_modules):
    root = Path(root)
    violations = []
    counts = Counter()
    modules = set()
    for rel in runtime_modules:
        path = root / rel
        if not path.is_file():
            continue
        rows = raw_catalog_writes(path)
        if rows:
            modules.add(rel)
        for line, catalog, action, depth in rows:
            counts[catalog] += 1
            violations.append({
                "file": rel, "line": line, "catalog": catalog,
                "action": action, "path_depth": depth,
            })
    return {
        "error_count": len(violations),
        "errors": [
            f"direct catalog write: {row['file']}:{row['line']} {row['catalog']} {row['action']}"
            for row in violations
        ],
        "violation_count": len(violations),
        "violating_module_count": len(modules),
        "by_catalog": dict(sorted(counts.items())),
        "violations": tuple(violations),
    }
