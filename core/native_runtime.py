# -*- coding: utf-8 -*-
"""Native/explicit hybrid runtime for Soulbound v0.60.0.

v0.40.0 still executed legacy source files into ``server.py``'s globals.  This
loader keeps the proven load order and final-symbol compatibility, but every
runtime source is now executed as a real Python module registered in
``sys.modules`` under its package name.  No source text is executed with a
project-level ``exec`` call.

Why the compatibility symbol sync still exists:
    Soulbound grew for many versions as one concatenated runtime.  A number of
    old functions intentionally look up symbols that are defined by later
    milestone modules.  The native loader therefore synchronizes the resolved
    runtime symbols between module dictionaries after imports.  That preserves
    the old late-binding behaviour while giving each source file a real module
    identity, precise tracebacks and an independently inspectable namespace.

v0.43.0 adds a reviewed explicit-module lane. Those modules are never seeded
from the compatibility namespace and never receive late symbol synchronization;
only exports declared in the runtime manifest are published to legacy code.

New code should use explicit imports.  The symbol synchronization is a bridge
for untouched historical code, not the authoring model for new systems.
"""
from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import MutableMapping

from core.runtime_manifest import (
    EXPECTED_OVERRIDE_ORDER,
    EXPECTED_SESSION_METHOD_DUPLICATES,
    EXPLICIT_RUNTIME_EXPORTS,
    RUNTIME_MODULES,
)

_MODULE_META = {
    "__name__", "__package__", "__loader__", "__spec__", "__file__",
    "__cached__", "__builtins__", "__doc__",
}


def module_name_for_path(relative_path: str) -> str:
    """Return the canonical import name for a runtime source path."""
    path = str(relative_path).replace("\\", "/")
    if not path.endswith(".py"):
        raise ValueError(f"Runtime path is not a Python source: {relative_path}")
    return path[:-3].replace("/", ".")


def _source_definition_index(source: str, filename: str) -> tuple[list[str], list[dict], set[str]]:
    tree = ast.parse(source, filename=filename)
    top_level: list[str] = []
    top_level_functions: set[str] = set()
    methods: list[dict] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            top_level.append(node.name)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            top_level_functions.add(node.name)
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append({
                        "class": node.name,
                        "method": child.name,
                        "line": int(child.lineno),
                    })
    return top_level, methods, top_level_functions


def _seed_module(module: ModuleType, runtime: dict[str, object]) -> dict[str, object]:
    """Inject currently resolved runtime symbols before normal module execution."""
    target = module.__dict__
    for name, value in runtime.items():
        if name not in _MODULE_META:
            target[name] = value
    return {name: target.get(name) for name in tuple(target) if name not in _MODULE_META}


def _sync_modules(
    modules: list[ModuleType], runtime: dict[str, object], names: set[str] | None = None
) -> None:
    """Make late-defined compatibility symbols visible to imported modules.

    During loading we propagate only symbols authored by the newest module; a
    full synchronization is needed only at the end.  This keeps startup fast
    even with a large runtime registry.
    """
    if names is None:
        payload = {k: v for k, v in runtime.items() if k not in _MODULE_META}
    else:
        payload = {k: runtime[k] for k in names if k in runtime and k not in _MODULE_META}
    if not payload:
        return
    for module in modules:
        module.__dict__.update(payload)


def _execute_native_module(
    path: Path, module_name: str, runtime: dict[str, object],
    compatibility_modules: list[ModuleType], deferred_function_names: set[str],
    explicit_exports: tuple[str, ...] | None = None,
) -> tuple[ModuleType, set[str]]:
    """Execute one runtime source.

    Legacy modules receive the compatibility namespace exactly as before.
    Explicit modules receive no injected gameplay symbols and publish only the
    exports declared in ``core.runtime_manifest.EXPLICIT_RUNTIME_EXPORTS``.
    """
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot build module spec for {module_name} ({path})")

    module = importlib.util.module_from_spec(spec)
    explicit = explicit_exports is not None
    before = {} if explicit else _seed_module(module, runtime)

    if explicit and deferred_function_names:
        raise RuntimeError(
            f"Explicit runtime module cannot use legacy override dispatch: {module_name}: "
            + ", ".join(sorted(deferred_function_names))
        )

    # Historical modules sometimes override a global function and, later in the
    # SAME source file, call an older helper that looks that function up.  This
    # bridge is intentionally available only to legacy compatibility modules.
    deferred_restore = {}
    for name in deferred_function_names:
        if name not in runtime:
            continue
        previous = runtime[name]
        deferred_restore[name] = previous

        def _late_bound(*args, __name=name, __module=module, __previous=previous, **kwargs):
            target = __module.__dict__.get(__name, __previous)
            return target(*args, **kwargs)

        _late_bound.__name__ = name
        _late_bound.__qualname__ = name
        runtime[name] = _late_bound
        for loaded in compatibility_modules:
            loaded.__dict__[name] = _late_bound

    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        if sys.modules.get(module_name) is module:
            del sys.modules[module_name]
        for name, previous in deferred_restore.items():
            runtime[name] = previous
            for loaded in compatibility_modules:
                loaded.__dict__[name] = previous
        raise

    if explicit:
        missing = [name for name in explicit_exports if name not in module.__dict__]
        if missing:
            raise RuntimeError(
                f"Explicit runtime exports missing from {module_name}: " + ", ".join(missing)
            )
        changed = set(explicit_exports)
    else:
        changed: set[str] = set()
        for name, value in module.__dict__.items():
            if name in _MODULE_META:
                continue
            if name not in before or before[name] is not value:
                changed.add(name)
        # ``del name`` had global meaning in the old concatenated runtime too.
        for name in before:
            if name not in module.__dict__:
                runtime.pop(name, None)

    for name in changed:
        runtime[name] = module.__dict__[name]
    return module, changed


def load_native_runtime(root: Path, namespace: MutableMapping[str, object]) -> dict:
    """Load Soulbound runtime files as real modules and publish the final API.

    ``namespace`` is normally the bootstrap ``server.py`` namespace.  It is
    updated only after modules have been imported, preserving the public API
    expected by pre-deploy audits and by the tiny bootstrap file.
    """
    root = Path(root)
    missing = [name for name in RUNTIME_MODULES if not (root / name).is_file()]
    if missing:
        raise RuntimeError("Soulbound runtime incomplete. Missing: " + ", ".join(missing))

    # Seed with bootstrap/runtime-independent names that legacy modules could
    # historically see when they were concatenated into server.py.
    runtime: dict[str, object] = {
        key: value for key, value in namespace.items()
        if key not in _MODULE_META
    }

    seen: dict[str, list[str]] = {}
    method_seen: dict[str, list[str]] = {}
    source_index: dict[str, dict] = {}
    method_index: dict[str, list[dict]] = {}
    module_index: dict[str, dict] = {}
    modules: list[ModuleType] = []
    compatibility_modules: list[ModuleType] = []

    for relative in RUNTIME_MODULES:
        path = root / relative
        source = path.read_text(encoding="utf-8")
        symbols, methods, top_level_functions = _source_definition_index(source, str(path))

        for symbol in symbols:
            owners = seen.setdefault(symbol, [])
            if owners and symbol not in EXPECTED_OVERRIDE_ORDER:
                raise RuntimeError(
                    f"Unexpected runtime symbol override: {symbol}: "
                    f"{owners[-1]} -> {relative}. Add an explicit policy only after review."
                )
            owners.append(relative)
            source_index[symbol] = {"file": relative, "module": module_name_for_path(relative)}

        for method in methods:
            row = {"file": relative, "module": module_name_for_path(relative), **method}
            method_index.setdefault(method["method"], []).append(row)
            if method["class"].startswith("Session") and method["class"].endswith("Mixin"):
                method_seen.setdefault(method["method"], []).append(f"{relative}:{method['class']}")

        module_name = module_name_for_path(relative)
        deferred = {name for name in top_level_functions if name in EXPECTED_OVERRIDE_ORDER and name in runtime}
        explicit_exports = EXPLICIT_RUNTIME_EXPORTS.get(relative)
        module, changed = _execute_native_module(
            path, module_name, runtime, compatibility_modules, deferred, explicit_exports
        )
        modules.append(module)
        if explicit_exports is None:
            compatibility_modules.append(module)
        module_index[module_name] = {
            "file": relative,
            "authored_symbol_count": len(changed),
            "dependency_mode": "explicit" if explicit_exports is not None else "legacy-compat",
            "declared_exports": tuple(explicit_exports or ()),
        }
        # Only legacy modules receive compatibility symbol synchronization.
        # Explicit modules keep their normal Python namespace permanently.
        _sync_modules(compatibility_modules, runtime, changed)

    observed = {name: owners for name, owners in seen.items() if len(owners) > 1}
    if observed != EXPECTED_OVERRIDE_ORDER:
        raise RuntimeError(
            "Runtime override policy mismatch. Observed override order differs from manifest."
        )

    observed_method_dupes = {name: owners for name, owners in method_seen.items() if len(owners) > 1}
    if observed_method_dupes != EXPECTED_SESSION_METHOD_DUPLICATES:
        unexpected = {
            k: v for k, v in observed_method_dupes.items()
            if EXPECTED_SESSION_METHOD_DUPLICATES.get(k) != v
        }
        changed = {
            k: v for k, v in EXPECTED_SESSION_METHOD_DUPLICATES.items()
            if observed_method_dupes.get(k) != v
        }
        raise RuntimeError(
            "Session method collision policy mismatch. "
            f"Unexpected={unexpected}; missing/changed={changed}"
        )

    runtime["RUNTIME_SYMBOL_SOURCE_INDEX"] = source_index
    runtime["RUNTIME_METHOD_SOURCE_INDEX"] = method_index
    runtime["RUNTIME_NATIVE_MODULE_INDEX"] = module_index

    # One final late-binding sync includes the diagnostic indexes as well.
    _sync_modules(compatibility_modules, runtime)

    state = {
        "version": "0.60.0",
        "module_count": len(modules),
        "modules": tuple(RUNTIME_MODULES),
        "native_module_names": tuple(module_name_for_path(p) for p in RUNTIME_MODULES),
        "override_symbol_count": len(observed),
        "session_method_collision_count": len(observed_method_dupes),
        "indexed_method_count": sum(len(rows) for rows in method_index.values()),
        "override_order": observed,
        "direct_exec_locations": (),
        "runtime_mode": "hybrid-explicit-modules-with-legacy-bridge",
        "explicit_module_count": len(EXPLICIT_RUNTIME_EXPORTS),
        "legacy_compat_module_count": len(compatibility_modules),
        "explicit_modules": tuple(EXPLICIT_RUNTIME_EXPORTS),
    }
    runtime["RUNTIME_ARCHITECTURE_STATE"] = state
    _sync_modules(compatibility_modules, runtime)

    # Publish only after a successful complete import, so the bootstrap cannot
    # observe a half-assembled runtime.
    namespace.update(runtime)
    return state
