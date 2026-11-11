# -*- coding: utf-8 -*-
"""Static dependency checks for Soulbound's explicit-module migration.

The legacy runtime intentionally supports late-bound global names.  Modules
listed in ``EXPLICIT_RUNTIME_EXPORTS`` are different: they must be ordinary
Python modules with real imports and may not depend on compatibility symbol
injection.  This validator makes that rule machine-checkable.
"""
from __future__ import annotations

import ast
import builtins
import symtable
from pathlib import Path

_BUILTINS = frozenset(dir(builtins)) | frozenset({"__file__", "__name__", "__package__", "__spec__", "__loader__", "__cached__"})


def _module_defined_names(table: symtable.SymbolTable) -> set[str]:
    result: set[str] = set()
    for symbol in table.get_symbols():
        if symbol.is_assigned() or symbol.is_imported() or symbol.is_namespace():
            result.add(symbol.get_name())
    return result


def implicit_global_references(path: Path) -> tuple[str, ...]:
    """Names read as globals without being defined/imported by this module."""
    path = Path(path)
    source = path.read_text(encoding="utf-8")
    table = symtable.symtable(source, str(path), "exec")
    module_defined = _module_defined_names(table)
    referenced: set[str] = set()

    def visit(scope: symtable.SymbolTable) -> None:
        for symbol in scope.get_symbols():
            if symbol.is_referenced() and symbol.is_global():
                referenced.add(symbol.get_name())
        for child in scope.get_children():
            visit(child)

    visit(table)
    return tuple(sorted(referenced - module_defined - _BUILTINS))


def module_import_roots(path: Path) -> tuple[str, ...]:
    tree = ast.parse(Path(path).read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return tuple(sorted(roots))


def _top_level_defined(path: Path) -> set[str]:
    """Names that are available in the module namespace after normal import.

    Explicit modules may intentionally re-export imported catalog objects, and
    top-level unpacking assignments are also legitimate compatibility exports.
    The old v0.43 checker only recognized simple assignments, which made valid
    explicit re-export surfaces look missing during the second migration wave.
    """
    tree = ast.parse(Path(path).read_text(encoding="utf-8"), filename=str(path))
    result: set[str] = set()

    def add_target(target):
        if isinstance(target, ast.Name):
            result.add(target.id)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for child in target.elts:
                add_target(child)

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            result.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                add_target(target)
        elif isinstance(node, ast.AnnAssign):
            add_target(node.target)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                result.add(alias.asname or alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name != "*":
                    result.add(alias.asname or alias.name)
    return result


def validate_explicit_runtime_modules(root, explicit_exports, runtime_modules):
    root = Path(root)
    errors: list[str] = []
    rows: dict[str, dict] = {}
    runtime_set = set(runtime_modules)
    for rel, exports in explicit_exports.items():
        path = root / rel
        if rel not in runtime_set:
            errors.append(f"explicit module missing from runtime manifest: {rel}")
            continue
        if not path.is_file():
            errors.append(f"missing explicit runtime module: {rel}")
            continue
        implicit = implicit_global_references(path)
        authored = _top_level_defined(path)
        missing_exports = sorted(set(exports) - authored)
        if implicit:
            errors.append(f"explicit module has injected/global dependencies: {rel}: {', '.join(implicit)}")
        if missing_exports:
            errors.append(f"explicit module exports missing: {rel}: {', '.join(missing_exports)}")
        rows[rel] = {
            "exports": tuple(exports),
            "implicit_globals": implicit,
            "import_roots": module_import_roots(path),
        }
    return {"error_count": len(errors), "errors": errors, "modules": rows}


def validate_layer_imports(root):
    """Protect one-way architecture for new clean layers."""
    root = Path(root)
    errors: list[str] = []

    # data may depend on config and other data, never on gameplay/runtime code.
    forbidden_data = {"core", "systems", "world", "player", "storage", "network", "server", "admin"}
    for path in sorted((root / "data").glob("*.py")):
        bad = sorted(set(module_import_roots(path)) & forbidden_data)
        if bad:
            errors.append(f"data layer imports gameplay/runtime code: {path.relative_to(root)} -> {bad}")

    # config is the bottom layer and must never import the game runtime.
    forbidden_config = forbidden_data | {"data", "events", "validation"}
    for path in sorted((root / "config").glob("*.py")):
        bad = sorted(set(module_import_roots(path)) & forbidden_config)
        if bad:
            errors.append(f"config layer imports higher layer: {path.relative_to(root)} -> {bad}")

    # Event contracts/bus/listeners communicate through event objects/session
    # interfaces.  Importing concrete gameplay modules would recreate coupling.
    forbidden_events = {"core", "systems", "world", "player", "storage", "network", "server", "admin", "data"}
    for path in sorted((root / "events").rglob("*.py")):
        bad = sorted(set(module_import_roots(path)) & forbidden_events)
        if bad:
            errors.append(f"event layer imports concrete gameplay code: {path.relative_to(root)} -> {bad}")

    return {"error_count": len(errors), "errors": errors}


def legacy_dependency_metrics(root, runtime_modules, explicit_exports):
    root = Path(root)
    explicit = set(explicit_exports)
    rows = {}
    total = 0
    for rel in runtime_modules:
        if rel in explicit:
            continue
        deps = implicit_global_references(root / rel)
        rows[rel] = len(deps)
        total += len(deps)
    return {
        "legacy_module_count": len(rows),
        "legacy_implicit_reference_total": total,
        "largest": tuple(sorted(rows.items(), key=lambda pair: (-pair[1], pair[0]))[:20]),
    }
