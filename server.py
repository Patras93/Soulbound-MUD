# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""Soulbound v0.38.4 Hourly Magitek Contracts."""
from pathlib import Path
import os
import socket

_ROOT = Path(__file__).resolve().parent

def _boot_port() -> int:
    # Keep exactly the same precedence as core/bootstrap_economy_professions.py.
    for key in ("RAILWAY_TCP_APPLICATION_PORT", "PORT", "SOULBOUND_PORT"):
        raw = os.getenv(key, "").strip()
        if raw:
            try:
                value = int(raw)
                if 1 <= value <= 65535:
                    return value
            except ValueError:
                pass
    return 4000

# Railway/TCP health must see a listening socket immediately, before the large
# world registry and Generator Core finish loading. asyncio adopts this socket
# later; connections made during boot wait safely in the kernel backlog.
_BOOT_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
_BOOT_SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
_BOOT_SOCKET.bind((os.getenv("SOULBOUND_HOST", "0.0.0.0"), _boot_port()))
_BOOT_SOCKET.listen(128)
_BOOT_SOCKET.setblocking(False)
print(f"Soulbound bootstrap port open: {_BOOT_SOCKET.getsockname()}", flush=True)

_ROOT = Path(__file__).resolve().parent
_RUNTIME_MODULES = [
    "core/bootstrap_economy_professions.py",
    "core/progression_resources.py",
    "core/progression_600.py",
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
    "systems/crafting_expansion_v03114.py",
    "systems/milestone_v0320.py",
    "storage/database.py",
    "storage/crafting_expansion_v03114.py",
    "storage/milestone_v0320.py",
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
    "player/session_mixins/crafting_expansion_v03114.py",
    "player/session_mixins/milestone_v0320.py",
    "player/session_mixins/command_loop.py",
    "player/session.py",
    "server/mud_server.py",
    "admin/help_refresh.py",
    "admin/audits.py",
    "systems/economy_audit_v03060.py",
    "systems/full_systems_audit_v03062.py",
    "admin/crafting_audit_v03114.py",
    "world/uoss_superbosses_v0366.py",
    "world/crypt_party_rebalance_v0368.py",
    "world/crypt_floor_progression_v03610.py",
    "world/crypt_overdrive_v0370.py",
    "world/tower_overdrive_v0381.py",
    "world/magitek_infinite_v0382.py",
    "world/magitek_hourly_quests_v0383.py",
    "world/world_threat_overdrive_v0384.py",
    "world/troll_shaman_density_v03611.py",
    "systems/public_records_v0370.py",
    "admin/party_revive_audit_v0371.py",
    "world/party_combo_ultimate_summary_v0380.py",
    "admin/release_integrity_v0369.py",
]

_missing = [name for name in _RUNTIME_MODULES if not (_ROOT / name).is_file()]
if _missing:
    raise RuntimeError("Soulbound runtime incomplete. Missing: " + ", ".join(_missing))

for _name in _RUNTIME_MODULES:
    _path = _ROOT / _name
    _source = _path.read_text(encoding="utf-8")
    exec(compile(_source, str(_path), "exec"), globals(), globals())

# v0.34.4: run the exhaustive gate against the FINAL assembled runtime,
# after economy/full-system/crafting compatibility layers have finished.
if os.environ.get("SOULBOUND_FULL_AUDIT", "").strip().lower() in ("1", "true", "yes", "on"):
    FULL_GAME_PREDEPLOY_AUDIT_V0336 = full_game_predeploy_audit_v0336()
    if FULL_GAME_PREDEPLOY_AUDIT_V0336["error_count"]:
        raise RuntimeError(
            "Full Game Pre-Deploy Audit v0.38.4 failed: "
            + "; ".join(map(str, FULL_GAME_PREDEPLOY_AUDIT_V0336["errors"][:100]))
        )
else:
    FULL_GAME_PREDEPLOY_AUDIT_V0336 = {
        "version": "0.38.4", "skipped_at_runtime": True,
        "error_count": 0, "warning_count": 0, "errors": [], "warnings": [],
        "reason": "Run before deploy with SOULBOUND_FULL_AUDIT=1; skipped during normal server startup.",
    }

if __name__ == "__main__":
    main()
