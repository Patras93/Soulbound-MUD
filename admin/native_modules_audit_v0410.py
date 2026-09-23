# -*- coding: utf-8 -*-
"""Soulbound v0.41.0 - native module architecture audit.

Structural only: this milestone changes how source is loaded and diagnosed, not
combat, progression, content, economy or persistence semantics.
"""


def native_modules_audit_v0410():
    import sys
    from pathlib import Path
    from core.native_runtime import module_name_for_path
    from core.runtime_manifest import RUNTIME_MODULES

    root = Path(globals().get("_ROOT", Path.cwd()))
    errors = []

    def read(rel):
        path = root / rel
        if not path.is_file():
            errors.append(f"missing native architecture file: {rel}")
            return ""
        return path.read_text(encoding="utf-8")

    server_source = read("server.py")
    native_source = read("core/native_runtime.py")
    legacy_loader_source = read("core/runtime_loader.py")

    if "from core.native_runtime import load_native_runtime" not in server_source:
        errors.append("server.py does not use the v0.41 native runtime")
    if "load_native_runtime(_ROOT, globals())" not in server_source:
        errors.append("server.py native runtime bootstrap call missing")
    if "exec(" in server_source or "exec(" in native_source or "exec(" in legacy_loader_source:
        errors.append("direct project-level exec source loading is still present")
    if "spec.loader.exec_module(module)" not in native_source:
        errors.append("native runtime is not using Python module loader execution")

    # Every source loaded before this audit must already exist as a canonical
    # Python module and point back to the expected physical source file.
    current = "admin/native_modules_audit_v0410.py"
    current_index = RUNTIME_MODULES.index(current) if current in RUNTIME_MODULES else len(RUNTIME_MODULES)
    checked_modules = 0
    for rel in RUNTIME_MODULES[: current_index + 1]:
        name = module_name_for_path(rel)
        module = sys.modules.get(name)
        if module is None:
            errors.append(f"runtime source is not a loaded module: {rel} -> {name}")
            continue
        checked_modules += 1
        module_file = Path(getattr(module, "__file__", "") or "")
        try:
            actual = module_file.resolve().relative_to(root.resolve()).as_posix()
        except Exception:
            actual = module_file.as_posix()
        if actual != rel:
            errors.append(f"module source mismatch: {name}: {actual!r} != {rel!r}")

    identity_checks = (
        ("Database", globals().get("Database"), "storage.database"),
        ("Character", globals().get("Character"), "player.character"),
        ("Session", globals().get("Session"), "player.session"),
        ("MudServer", globals().get("MudServer"), "server.mud_server"),
    )
    identity_results = {}
    for label, obj, expected_module in identity_checks:
        actual = str(getattr(obj, "__module__", "")) if obj is not None else ""
        identity_results[label] = actual
        if actual != expected_module:
            errors.append(f"{label} module identity={actual!r}, expected {expected_module!r}")

    # A representative historical override must also retain its real source
    # module, rather than looking as though it came from server.py.
    combat_template = globals().get("v0190_apply_combat_template")
    combat_module = str(getattr(combat_template, "__module__", ""))
    if combat_module != "world.global_difficulty_overdrive":
        errors.append(
            "final combat template override has wrong module identity: "
            f"{combat_module!r}"
        )

    return {
        "version": "0.41.0",
        "runtime_mode": "native-modules-with-legacy-symbol-sync",
        "checked_native_modules": checked_modules,
        "identity_results": identity_results,
        "final_combat_template_module": combat_module,
        "direct_exec_count": 0 if not errors or not any("exec" in e for e in errors) else 1,
        "error_count": len(errors),
        "errors": errors,
    }


NATIVE_MODULE_ARCHITECTURE_AUDIT_V0410 = native_modules_audit_v0410()
if NATIVE_MODULE_ARCHITECTURE_AUDIT_V0410["error_count"]:
    raise RuntimeError(
        "Native Module Architecture Audit v0.41.0 failed: "
        + "; ".join(NATIVE_MODULE_ARCHITECTURE_AUDIT_V0410["errors"][:100])
    )
