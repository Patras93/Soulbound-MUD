# -*- coding: utf-8 -*-
"""Soulbound v0.39.0 architecture stabilization audit.

This audit changes no gameplay. It verifies the structural invariants introduced
in v0.39.0 so later feature work cannot silently drift back to scattered exec
loading or a giant simple-command elif chain.
"""

def architecture_stabilization_audit_v0390():
    import ast
    from pathlib import Path
    from core.runtime_manifest import EXPECTED_OVERRIDE_ORDER, RUNTIME_MODULES

    errors = []
    root = Path(globals().get("_ROOT", Path.cwd()))

    def read(rel):
        path = root / rel
        if not path.is_file():
            errors.append(f"missing architecture file: {rel}")
            return ""
        return path.read_text(encoding="utf-8")

    server_source = read("server.py")
    loader_source = read("core/runtime_loader.py")
    native_loader_source = read("core/native_runtime.py")
    bootstrap_source = read("core/bootstrap_economy_professions.py")
    loop_source = read("player/session_mixins/command_loop.py")
    registry_source = read("player/session_mixins/command_registry.py")

    if "exec(" in server_source:
        errors.append("server.py still contains direct exec loading")
    # v0.39 introduced one controlled exec boundary. v0.41 supersedes it with
    # normal module loading; either architecture preserves the v0.39 goal that
    # server.py itself never concatenates source directly.
    if "load_native_runtime" not in server_source and loader_source.count("exec(") != 1:
        errors.append("neither the v0.39 controlled loader nor the v0.41 native loader is active")
    if "load_native_runtime" in server_source and "exec(" in native_loader_source:
        errors.append("native runtime regressed to direct exec loading")
    if "_EMBEDDED_" in bootstrap_source or "_load_embedded_runtime_module" in bootstrap_source:
        errors.append("bootstrap still contains embedded runtime source blobs")

    for rel in (
        "core/generator_core.py",
        "world/topology_generator.py",
        "world/dynamic_world_generator.py",
        "world/logic_validator.py",
    ):
        if not (root / rel).is_file():
            errors.append(f"missing extracted engine module: {rel}")

    try:
        registry_tree = ast.parse(registry_source, filename="command_registry.py")
        registry_assign = next(
            node for node in registry_tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "COMMAND_REGISTRY" for t in node.targets)
        )
        registry_count = len(registry_assign.value.keys) if isinstance(registry_assign.value, ast.Dict) else 0
    except Exception as exc:
        registry_count = 0
        errors.append(f"command registry parse failed: {type(exc).__name__}: {exc}")

    if registry_count < 200:
        errors.append(f"command registry only has {registry_count} commands; expected >=200")
    if "dispatch_registered_command(command, args)" not in loop_source:
        errors.append("command loop does not delegate simple commands to registry")
    if loop_source.count('elif command ==') > 25:
        errors.append("command loop regressed to a large direct elif router")

    missing_runtime = [rel for rel in RUNTIME_MODULES if not (root / rel).is_file()]
    if missing_runtime:
        errors.append("runtime manifest missing files: " + ", ".join(missing_runtime[:20]))
    if len(RUNTIME_MODULES) != len(set(RUNTIME_MODULES)):
        errors.append("runtime manifest contains duplicate module paths")
    if len(EXPECTED_OVERRIDE_ORDER) != 16:
        errors.append(
            f"intentional override policy changed: {len(EXPECTED_OVERRIDE_ORDER)} symbols, expected 16"
        )

    return {
        "version": "0.39.0",
        "runtime_modules": len(RUNTIME_MODULES),
        "registered_simple_commands": registry_count,
        "intentional_override_symbols": len(EXPECTED_OVERRIDE_ORDER),
        "error_count": len(errors),
        "errors": errors,
    }


ARCHITECTURE_STABILIZATION_AUDIT_V0390 = architecture_stabilization_audit_v0390()
if ARCHITECTURE_STABILIZATION_AUDIT_V0390["error_count"]:
    raise RuntimeError(
        "Architecture Stabilization Audit v0.39.0 failed: "
        + "; ".join(ARCHITECTURE_STABILIZATION_AUDIT_V0390["errors"][:100])
    )
