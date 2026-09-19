# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""Soulbound v0.30.46 Fine-Grained Modular Core."""
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_RUNTIME_MODULES = [
    "core/bootstrap_economy_professions.py",
    "core/progression_resources.py",
    "core/classes_skills.py",
    "core/mines_threat.py",
    "systems/items_resources.py",
    "systems/equipment_crafting.py",
    "systems/content_registry.py",
    "systems/dungeons_regions.py",
    "world/expansions.py",
    "world/equipment_help.py",
    "world/economy_quests.py",
    "world/dynamic_content.py",
    "network/protocol_gameplay_utils.py",
    "storage/database.py",
    "player/character.py",
    "world/generation_systems.py",
    "world/runtime_progression.py",
    "world/world_state.py",
    "player/session.py",
    "server/mud_server.py",
    "admin/help_refresh.py",
    "admin/audits.py",
]

_missing = [name for name in _RUNTIME_MODULES if not (_ROOT / name).is_file()]
if _missing:
    raise RuntimeError("Soulbound runtime incomplete. Missing: " + ", ".join(_missing))

for _name in _RUNTIME_MODULES:
    _path = _ROOT / _name
    _source = _path.read_text(encoding="utf-8")
    exec(compile(_source, str(_path), "exec"), globals(), globals())
