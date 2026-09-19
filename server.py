# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""Soulbound v0.30.45 Structured Modular Core.

Runtime files live in functional directories, while execution order is kept
identical to v0.30.44 so legacy globals and initialization remain compatible.
"""
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_RUNTIME_MODULES = [
    "core/progression.py",
    "systems/items_loot_dungeons.py",
    "world/content_equipment.py",
    "network/gameplay_systems.py",
    "world/runtime_session.py",
    "admin/server_audits.py",
]

_missing = [name for name in _RUNTIME_MODULES if not (_ROOT / name).is_file()]
if _missing:
    raise RuntimeError("Soulbound runtime incomplete. Missing: " + ", ".join(_missing))

for _name in _RUNTIME_MODULES:
    _path = _ROOT / _name
    _source = _path.read_text(encoding="utf-8")
    exec(compile(_source, str(_path), "exec"), globals(), globals())
