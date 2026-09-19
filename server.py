# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""Soulbound v0.30.44 Logical Modular Core.

The runtime is split into broad, named modules. They intentionally execute in
the preserved legacy order so v0.30.43/v0.30.42 behaviour and global bindings
remain compatible while the codebase becomes easier to navigate.
"""
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_RUNTIME_MODULES = [
    "core_progression.py",
    "items_loot_dungeons.py",
    "world_content_equipment.py",
    "network_gameplay_systems.py",
    "world_runtime_session.py",
    "server_admin_audits.py",
]

_missing = [name for name in _RUNTIME_MODULES if not (_ROOT / name).is_file()]
if _missing:
    raise RuntimeError("Soulbound runtime incomplete. Missing: " + ", ".join(_missing))

for _name in _RUNTIME_MODULES:
    _path = _ROOT / _name
    _source = _path.read_text(encoding="utf-8")
    exec(compile(_source, str(_path), "exec"), globals(), globals())
