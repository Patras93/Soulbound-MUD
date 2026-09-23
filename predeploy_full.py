#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run Soulbound's exhaustive historical pre-deploy audit without starting the TCP server loop."""
from __future__ import annotations

import os
import runpy
import socket
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
os.environ.pop("SOULBOUND_FULL_AUDIT", None)
os.environ.setdefault("SOULBOUND_HOST", "127.0.0.1")
os.environ.setdefault("SOULBOUND_WORLD_SEED", "SOULBOUND-PREDEPLOY-V0510")

# Pick a free local port for the bootstrap socket used during import.
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
    probe.bind(("127.0.0.1", 0))
    os.environ["PORT"] = str(probe.getsockname()[1])

with tempfile.TemporaryDirectory(prefix="soulbound-v0571-full-audit-") as temp_dir:
    os.environ["SOULBOUND_DB"] = str(Path(temp_dir) / "audit.db")
    ns = runpy.run_path(str(ROOT / "server.py"), run_name="soulbound_predeploy")

arch = ns["ARCHITECTURE_STABILIZATION_AUDIT_V0390"]
maintenance = ns["MAINTENANCE_ARCHITECTURE_AUDIT_V0400"]
native = ns["NATIVE_MODULE_ARCHITECTURE_AUDIT_V0410"]
modular = ns["MODULAR_SERVICES_AUDIT_V0420"]
explicit = ns["EXPLICIT_DEPENDENCIES_AUDIT_V0430"]
explicit_gameplay = ns["EXPLICIT_GAMEPLAY_DEPENDENCIES_AUDIT_V0440"]
explicit_persistence = ns["EXPLICIT_PERSISTENCE_AUDIT_V0460"]
combat_arch = ns["COMBAT_ARCHITECTURE_AUDIT_V0470"]
catalog_ownership = ns["CATALOG_OWNERSHIP_AUDIT_V0480"]
command_registry = ns["COMMAND_REGISTRY_AUDIT_V0490"]
maintainable = ns["MAINTAINABLE_CORE_AUDIT_V0500"]
progression_pace = ns["PROGRESSION_PACE_AUDIT_V0501"]
long_term_balance = ns["LONG_TERM_BALANCE_AUDIT_V0502"]
difficulty_pressure = ns["DIFFICULTY_PRESSURE_AUDIT_V0503"]
world_expansion = ns["WORLD_EXPANSION_I_AUDIT_V0510"]
world_expansion_ii = ns["WORLD_EXPANSION_II_AUDIT_V0520"]
railway_packaging = ns["RAILWAY_PACKAGING_AUDIT_V0521"]
postal_quest_rewards = ns["POSTAL_QUEST_REWARDS_AUDIT_V0522"]
courier_guild = ns["COURIER_GUILD_AUDIT_V0530"]
courier_achievements = ns["COURIER_ACHIEVEMENTS_AUDIT_V0540"]
courier_prestige_tavern = ns["COURIER_PRESTIGE_TAVERN_AUDIT_V0550"]
living_npcs_activity = ns["LIVING_NPCS_ACTIVITY_AUDIT_V0560"]
modular_refactor = ns["MODULAR_REFACTOR_AUDIT_V0570"]
titles_progress = ns["TITLES_PROGRESS_AUDIT_V0580"]
release = ns["CUMULATIVE_RELEASE_INTEGRITY_AUDIT_V0369"]
full = ns["full_game_predeploy_audit_v0336"]()
runtime_state = ns["RUNTIME_ARCHITECTURE_STATE"]

if arch["error_count"] or maintenance["error_count"] or native["error_count"] or modular["error_count"] or explicit["error_count"] or explicit_gameplay["error_count"] or explicit_persistence["error_count"] or combat_arch["error_count"] or catalog_ownership["error_count"] or command_registry["error_count"] or maintainable["error_count"] or progression_pace["error_count"] or long_term_balance["error_count"] or difficulty_pressure["error_count"] or world_expansion["error_count"] or world_expansion_ii["error_count"] or railway_packaging["error_count"] or postal_quest_rewards["error_count"] or courier_guild["error_count"] or courier_achievements["error_count"] or courier_prestige_tavern["error_count"] or living_npcs_activity["error_count"] or modular_refactor["error_count"] or titles_progress["error_count"] or release["error_count"] or full["error_count"]:
    raise SystemExit(1)

print("Soulbound v0.58.0 FULL PREDEPLOY PASS")
print(f"Architecture: {arch['error_count']} errors; {arch['registered_simple_commands']} registered simple commands")
print(f"Maintenance: {maintenance['error_count']} errors; {maintenance['metrics']['maintenance_area_count']} repair areas")
print(f"Native modules: {native['error_count']} errors; {native['checked_native_modules']} verified module identities")
print(f"Modular services: {modular['error_count']} errors; {modular['catalog_owner_count']} separated catalogs; {len(modular['event_listeners'])} event types wired")
print(f"Explicit dependencies: {explicit['error_count']} errors; {explicit['explicit_module_count']} explicit modules")
print(f"Gameplay dependency migration: {explicit_gameplay['error_count']} errors; {explicit_gameplay['explicit_module_count']} explicit modules")
print(f"Persistence migration: {explicit_persistence['error_count']} errors; {explicit_persistence['explicit_module_count']} explicit modules; {explicit_persistence['legacy_implicit_reference_total']} legacy implicit refs")
print(f"Combat architecture: {combat_arch['error_count']} errors; {combat_arch['focused_combat_module_count']} focused modules; {combat_arch['legacy_implicit_reference_total']} legacy implicit refs")
print(f"Catalog ownership: {catalog_ownership['error_count']} errors; {catalog_ownership['raw_direct_catalog_writes']} direct writes; {catalog_ownership['tracked_key_count']} tracked keys")
print(f"Commands registry: {command_registry['error_count']} errors; {command_registry['alias_count']} aliases; {command_registry['registered_command_count']} handlers; {command_registry['manual_command_branch_count']} manual parser branches")
print(f"Maintainable core: {maintainable['error_count']} errors; {maintainable['explicit_module_count']} explicit / {maintainable['legacy_module_count']} legacy; {maintainable['legacy_implicit_reference_total']}/{maintainable['legacy_dependency_budget']} legacy refs; {maintainable['versioned_gameplay_filename_count']} versioned gameplay filenames")
print(f"Progression pace: {progression_pace['error_count']} errors; Character x{progression_pace['character_requirement_multiplier']:.1f}; Górnictwo x{progression_pace['mining_requirement_multiplier']:.1f}; Kilof x{progression_pace['pickaxe_requirement_multiplier']:.1f}")
print(f"Long-term balance: {long_term_balance['error_count']} errors; stat target {long_term_balance['target_actions']['stat']} actions; character/stat parity x{long_term_balance['character_stat_power_parity']:.3f}")
print(f"Difficulty pressure: {difficulty_pressure['error_count']} errors; world HP x{difficulty_pressure['profiles']['world']['hp']:.2f}/DMG x{difficulty_pressure['profiles']['world']['damage']:.2f}; mythic crypt HP x{difficulty_pressure['profiles']['mythic_crypt']['hp']:.2f}/DMG x{difficulty_pressure['profiles']['mythic_crypt']['damage']:.2f}")
print(f"World Expansion I: {world_expansion['error_count']} errors; {world_expansion['settlement_count']} settlements; {world_expansion['hunting_zone_count']} hunting zones; {world_expansion['new_room_count']} new rooms")
print(f"World Expansion II: {world_expansion_ii['error_count']} errors; {world_expansion_ii['capital_count']} capital + {world_expansion_ii['village_count']} villages; {world_expansion_ii['hunting_zone_count']} hunting zones; {world_expansion_ii['new_room_count']} new rooms")
print(f"Railway packaging: {railway_packaging['error_count']} errors; {railway_packaging['required_package_count']} required packages; {len(railway_packaging['missing_docker_copies'])} missing Docker COPY entries")
print(f"Postal/quest rewards: {postal_quest_rewards['error_count']} errors; {postal_quest_rewards['settlement_count']} settlements; refresh {postal_quest_rewards['refresh_seconds']} s")
print(f"Courier Guild: {courier_guild['error_count']} errors; {courier_guild['rank_count']} ranks; {courier_guild['package_class_count']} package classes")
print(f"Courier achievements: {courier_achievements['error_count']} errors; thresholds {courier_achievements['delivery_thresholds']}; {courier_achievements['city_count']} cities")
print(f"Courier prestige/tavern: {courier_prestige_tavern['error_count']} errors; {courier_prestige_tavern['city_achievement_count']} city achievements; {courier_prestige_tavern['package_achievement_count']} package achievements; {courier_prestige_tavern['tavern_hourly_count']} tavern hourlies")
print(f"Living NPCs/activity: {living_npcs_activity['error_count']} errors; {living_npcs_activity['tavern_count']} new taverns; {living_npcs_activity['tavern_hourly_count']} tavern hourlies; {living_npcs_activity['generated_hourly_count']} generated NPC hourlies; {living_npcs_activity['npc_without_quest_count']} NPCs without quests")
print(f"Modular refactor: {modular_refactor['error_count']} errors; social {modular_refactor['social_lines']} lines; courier {modular_refactor['courier_lines']} lines; db_schema {modular_refactor['db_schema_lines']} lines; {modular_refactor['focused_schema_module_count']} schema modules")
print(f"Titles 2.0/progress: {titles_progress['error_count']} errors; {titles_progress['exploration_title_count']} exploration titles; {titles_progress['boss_title_count']} boss titles; {titles_progress['profession_count']} professions")
print(f"Runtime mode: {runtime_state['runtime_mode']}; {runtime_state['explicit_module_count']} explicit / {runtime_state['legacy_compat_module_count']} legacy-compat")
print(f"Release integrity: {release['preserved_count']}/{release['checked']} milestones preserved")
print(f"Full game audit: {full['error_count']} errors, {full.get('warning_count', 0)} warnings")
print(f"World rooms: {len(ns['ROOMS'])}")
