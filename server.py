# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""Soulbound v0.31.12 Tech Crafting & Socket Expansion."""
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
    "world/machine_expansion_v0314.py",
    "world/magitek_dungeon_v0319.py",
    "systems/tech_crafting_v03111.py",
    "world/equipment_help.py",
    "world/economy_quests.py",
    "world/dynamic_content.py",
    "network/protocol_gameplay_utils.py",
    "network/tech_runes_v03111.py",
    "storage/database.py",
    "player/character.py",
    "world/generation_systems.py",
    "world/runtime_progression.py",
    "world/world_state.py",
    "systems/professions_v03053.py",
    "systems/crafting_quality_v03054.py",
    "player/session_mixins/core_progression.py",
    "player/session_mixins/io_auth_character.py",
    "player/session_mixins/equipment_stats.py",
    "player/session_mixins/perception_maps.py",
    "player/session_mixins/world_progression.py",
    "player/session_mixins/help_codex_profile.py",
    "player/session_mixins/movement_party_social.py",
    "player/session_mixins/professions_storage_guide.py",
    "player/session_mixins/admin_gathering_sales.py",
    "player/session_mixins/crafting_inventory_equipment.py",
    "player/session_mixins/quests.py",
    "player/session_mixins/skills_combat.py",
    "player/session_mixins/forge_guilds.py",
    "player/session_mixins/social_expansion.py",
    "player/session_mixins/progression_accessibility_v03052.py",
    "player/session_mixins/professions_v03053.py",
    "player/session_mixins/tech_crafting_v03111.py",
    "player/session_mixins/command_loop.py",
    "player/session.py",
    "server/mud_server.py",
    "admin/help_refresh.py",
    "admin/audits.py",
    "systems/economy_audit_v03060.py",
    "systems/full_systems_audit_v03062.py",
]

_missing = [name for name in _RUNTIME_MODULES if not (_ROOT / name).is_file()]
if _missing:
    raise RuntimeError("Soulbound runtime incomplete. Missing: " + ", ".join(_missing))

for _name in _RUNTIME_MODULES:
    _path = _ROOT / _name
    _source = _path.read_text(encoding="utf-8")
    exec(compile(_source, str(_path), "exec"), globals(), globals())

if __name__ == "__main__":
    main()
