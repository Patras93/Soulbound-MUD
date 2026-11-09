# -*- coding: utf-8 -*-
"""Durable v109 startup attestation, issued only after an approved predeploy.

This module does not approve a release: it verifies the already-approved ZIP,
then hashes the staged files that must remain identical after installation.
The permanent marker lives in LIVE_CONTENT, never in Soulbound_PREDEPLOY.
"""
from __future__ import annotations
import hashlib
import json
from functools import lru_cache
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MARKER = 'LIVE_CONTENT/v109_release_activation.json'
VERSION = '109.00.0'
SOURCE_VERSION = '108.00.0'
REQUIRED = (
    'VERSION', 'server.py', 'server/mud_server.py',
    'server_parts_v109/__init__.py',
    'server_parts_v109/sessions.py',
    'server_parts_v109/party_members.py',
    'server_parts_v109/engagement.py',
    'validation/v10900_server_modules_regression.py',
    'narzedzia/porzadki_bat.py',
    'validation/v10900_bat_cleanup_regression.py',
    'player/session_mixins/museum_bounty.py',
    'player/session_mixins/museum_parts_v109/__init__.py',
    'player/session_mixins/museum_parts_v109/dependencies.py',
    'player/session_mixins/museum_parts_v109/titles.py',
    'player/session_mixins/museum_parts_v109/museum.py',
    'player/session_mixins/museum_parts_v109/achievements.py',
    'player/session_mixins/museum_parts_v109/bounty_catalog.py',
    'player/session_mixins/museum_parts_v109/bounty_board.py',
    'player/session_mixins/museum_parts_v109/collection.py',
    'player/session_mixins/museum_parts_v109/kill_progress.py',
    'validation/v10900_museum_bounty_modules_regression.py',
    'player/session_mixins/guild_readonly_parts_v109/__init__.py',
    'player/session_mixins/guild_readonly_parts_v109/membership.py',
    'player/session_mixins/guild_readonly_parts_v109/bonuses.py',
    'player/session_mixins/guild_readonly_parts_v109/permissions.py',
    'player/session_mixins/guild_readonly_parts_v109/money.py',
    'player/session_mixins/forge_guilds.py',
    'validation/v10900_guild_readonly_modules_regression.py',
    'player/session_mixins/world_events_endgame.py',
    'player/session_mixins/world_events_parts_v109/__init__.py',
    'player/session_mixins/world_events_parts_v109/dependencies.py',
    'player/session_mixins/world_events_parts_v109/frontier_weather.py',
    'player/session_mixins/world_events_parts_v109/factions.py',
    'player/session_mixins/world_events_parts_v109/expeditions_transport.py',
    'player/session_mixins/world_events_parts_v109/ascension.py',
    'player/session_mixins/world_events_parts_v109/projects_contracts.py',
    'player/session_mixins/world_events_parts_v109/bosses_gauntlets.py',
    'player/session_mixins/world_events_parts_v109/artifacts.py',
    'player/session_mixins/world_events_parts_v109/world_rotation.py',
    'validation/v10900_world_events_modules_regression.py',
    'player/session_mixins/sales.py',
    'player/session_mixins/sales_parts_v109/__init__.py',
    'player/session_mixins/sales_parts_v109/dependencies.py',
    'player/session_mixins/sales_parts_v109/pricing.py',
    'player/session_mixins/sales_parts_v109/market.py',
    'player/session_mixins/sales_parts_v109/profession_exp.py',
    'player/session_mixins/sales_parts_v109/bulk.py',
    'player/session_mixins/sales_parts_v109/equipment.py',
    'player/session_mixins/sales_parts_v109/resources.py',
    'validation/v10900_sales_modules_regression.py',
    'core/bootstrap_economy_professions.py',
    'world/dynamic_content.py', 'world/v10900_horizons.py',
    'world/v10900_horizon_index.py',
    'player/session_mixins/social_expansion.py',
    'systems/v10700_activation.py', 'systems/v10700_live_equipment.py',
    'systems/v10800_seasonal_events.py',
    'systems/v10900_activation.py', 'systems/v10900_staging_guard.py',
    'systems/v10900_gifts.py',
    'predeploy_v109_z_zewnatrz.py', 'wdroz_v109_z_zewnatrz.py',
    'validation/v10900_actual_modular_source.py',
    'validation/v10900_external_bridge_regression.py',
    'predeploy_v109_standard_router.py', 'PREDEPLOY_NOWEJ_WERSJI.bat',
    'validation/v10900_standard_predeploy_router_regression.py',
    'validation/v10900_snapshot_preservation.py',
    'validation/v10900_snapshot_preservation_regression.py',
    'data/items.py',
    'data/rooms.py',
    'data/mobs.py',
    'data/npcs.py',
    'data/quests.py',
    'data/catalogs_v109/__init__.py',
    'data/catalogs_v109/items_01.py',
    'data/catalogs_v109/items_02.py',
    'data/catalogs_v109/items_03.py',
    'data/catalogs_v109/items_04.py',
    'data/catalogs_v109/items_05.py',
    'data/catalogs_v109/items_06.py',
    'data/catalogs_v109/items_07.py',
    'data/catalogs_v109/rooms_01.py',
    'data/catalogs_v109/rooms_02.py',
    'data/catalogs_v109/rooms_03.py',
    'data/catalogs_v109/rooms_04.py',
    'data/catalogs_v109/npcs_01.py',
    'data/catalogs_v109/npcs_02.py',
    'data/catalogs_v109/mobs_01.py',
    'data/catalogs_v109/mobs_02.py',
    'data/catalogs_v109/quests_01.py',
    'data/catalogs_v109/quests_02.py',
    'data/catalogs_v109/quests_03.py',
    'data/help_topics_v405/__init__.py',
    'data/descriptions_v405/__init__.py',
    'world/horizons_v109/__init__.py',
    'systems/gifts_v109/__init__.py',

    'data/help_base_catalog_v405.py',
    'data/world_description_catalog_v405.py',
    'data/help_topics_v405/economy_social.py',
    'data/help_topics_v405/navigation_craft.py',
    'data/help_topics_v405/quests_resources.py',
    'data/help_topics_v405/world_exploration.py',
    'data/help_topics_v405/professions_equipment.py',
    'data/help_topics_v405/progression.py',
    'data/descriptions_v405/npc.py',
    'data/descriptions_v405/mob.py',
    'data/descriptions_v405/stat.py',
    'data/descriptions_v405/system.py',
    'world/horizons_v109/entry.py',
    'world/horizons_v109/przebudzenie.py',
    'world/horizons_v109/zapomniani.py',
    'world/horizons_v109/wiecznosc.py',
    'systems/gifts_v109/policy.py',
    'systems/gifts_v109/rewards.py',
    'systems/gifts_v109/legacy.py',
    'systems/gifts_v109/payout.py',
    'systems/gifts_v109/delivery.py',
    'validation/v10900_modular_boundaries_regression.py',
    'validation/v4050_catalog_modularization.py',
    'validation/v4200_modularization.py',
    'validation/v4200_virtual_source.py',
    'validation/v10400_fast_predeploy_isolation.py',


    'storage/db_inventory.py',
    'storage/db_inventory_parts_v109/__init__.py',
    'storage/db_inventory_parts_v109/dependencies.py',
    'storage/db_inventory_parts_v109/bank_currency.py',
    'storage/db_inventory_parts_v109/bank_items.py',
    'storage/db_inventory_parts_v109/inventory.py',
    'storage/db_inventory_parts_v109/shop_lots.py',
    'storage/db_inventory_parts_v109/mail.py',
    'storage/db_inventory_parts_v109/equipment.py',
    'storage/db_inventory_parts_v109/gems.py',
    'storage/db_inventory_parts_v109/professions.py',
    'storage/db_inventory_parts_v109/enchant.py',
    'storage/db_inventory_parts_v109/tools.py',
    'storage/db_inventory_parts_v109/storage.py',
    'storage/db_inventory_parts_v109/crafting.py',
    'storage/db_inventory_parts_v109/forge.py',
    'storage/db_inventory_parts_v109/hunters.py',
    'storage/db_inventory_parts_v109/protection.py',
    'validation/v10900_db_inventory_modules_regression.py',

    'storage/db_accounts.py',
    'storage/db_accounts_parts_v109/__init__.py',
    'storage/db_accounts_parts_v109/dependencies.py',
    'storage/db_accounts_parts_v109/password_recovery.py',
    'storage/db_accounts_parts_v109/legacy_email.py',
    'storage/db_accounts_parts_v109/master_accounts.py',
    'storage/db_accounts_parts_v109/account_identity.py',
    'storage/db_accounts_parts_v109/character_deletion.py',
    'storage/db_accounts_parts_v109/character_roster.py',
    'storage/db_accounts_parts_v109/character_slots.py',
    'storage/db_accounts_parts_v109/presence.py',
    'storage/db_accounts_parts_v109/character_names.py',
    'storage/db_accounts_parts_v109/friends.py',
    'storage/db_accounts_parts_v109/wallet_read.py',
    'validation/v10900_db_accounts_modules_regression.py',
    'storage/db_world.py',
    'storage/db_world_parts_v109/__init__.py',
    'storage/db_world_parts_v109/dependencies.py',
    'storage/db_world_parts_v109/activity_achievements.py',
    'storage/db_world_parts_v109/bestiary_codex.py',
    'storage/db_world_parts_v109/bounties_quests.py',
    'storage/db_world_parts_v109/collections.py',
    'storage/db_world_parts_v109/dungeons_checkpoints.py',
    'storage/db_world_parts_v109/exploration.py',
    'storage/db_world_parts_v109/fishing.py',
    'storage/db_world_parts_v109/instances_chests.py',
    'storage/db_world_parts_v109/mercenaries_expeditions.py',
    'storage/db_world_parts_v109/mines.py',
    'storage/db_world_parts_v109/nemesis_ascension.py',
    'storage/db_world_parts_v109/projects_contracts.py',
    'storage/db_world_parts_v109/reputations_lifetime.py',
    'validation/v10900_db_world_modules_regression.py',
    'player/session_mixins/era_sky_v1700.py',
    'player/session_mixins/sky_parts_v109/__init__.py',
    'player/session_mixins/sky_parts_v109/dependencies.py',
    'player/session_mixins/sky_parts_v109/summon_state.py',
    'player/session_mixins/sky_parts_v109/companion_healing.py',
    'player/session_mixins/sky_parts_v109/summon_commands.py',
    'player/session_mixins/sky_parts_v109/summon_specializations.py',
    'player/session_mixins/sky_parts_v109/summon_combat.py',
    'player/session_mixins/sky_parts_v109/cities_classes.py',
    'player/session_mixins/exp_terrain.py',
    'player/session_mixins/exp_terrain_parts_v109/__init__.py',
    'player/session_mixins/exp_terrain_parts_v109/dependencies.py',
    'player/session_mixins/exp_terrain_parts_v109/safety.py',
    'player/session_mixins/exp_terrain_parts_v109/recommendations.py',
    'player/session_mixins/exp_terrain_parts_v109/calculation.py',
    'player/session_mixins/exp_terrain_parts_v109/terrain_ui.py',
    'validation/v10900_sky_modules_regression.py',
    'validation/v10900_exp_terrain_modules_regression.py',
    'player/session_mixins/admin_tools.py',
    'player/session_mixins/admin_tools_parts_v109/__init__.py',
    'player/session_mixins/admin_tools_parts_v109/guardian_controls.py',
    'player/session_mixins/admin_tools_parts_v109/session_safety.py',
    'validation/v10900_admin_tools_modules_regression.py',
    'player/session_mixins/admin_tools_parts_v109/boss_chests.py',
    'player/session_mixins/admin_tools_parts_v109/wipe_safety.py',
    'player/session_mixins/admin_tools_parts_v109/owner_dashboard.py',
    'validation/v10900_admin_wipe_safety_regression.py',
    'player/session_mixins/combat_damage.py',
    'player/session_mixins/combat_damage_parts_v109/__init__.py',
    'player/session_mixins/combat_damage_parts_v109/combat_mastery.py',
    'player/session_mixins/combat_damage_parts_v109/incoming_damage.py',
    'player/session_mixins/combat_damage_parts_v109/consider_rating.py',
    'player/session_mixins/combat_damage_parts_v109/health_readonly.py',
    'validation/v10900_combat_damage_modules_regression.py',
    'player/session_mixins/combat_survival.py',
    'player/session_mixins/combat_survival_parts_v109/__init__.py',
    'player/session_mixins/combat_survival_parts_v109/escape.py',
    'player/session_mixins/combat_survival_parts_v109/death.py',
    'player/session_mixins/combat_rewards.py',
    'player/session_mixins/combat_rewards_parts_v109/__init__.py',
    'player/session_mixins/combat_rewards_parts_v109/milestones.py',
    'player/session_mixins/help_system.py',
    'player/session_mixins/help_parts_v109/__init__.py',
    'player/session_mixins/help_parts_v109/history.py',
    'player/session_mixins/help_parts_v109/skills.py',
    'validation/v10900_combat_survival_modules_regression.py',
    'validation/v10900_combat_rewards_modules_regression.py',
    'validation/v10900_help_modules_regression.py',

    'validation/v10900_release_readiness.py',
    'validation/v10900_activation_regression.py',
    'validation/v10900_install_rollback_regression.py',
    'validation/v10900_predeploy_contract_regression.py',
    'validation/v10900_horizons_regression.py',
    'validation/v10900_gifts_regression.py',
    'predeploy_nowej_wersji.py', 'testuj_soulbound_windows.py',
    'aktualizuj_soulbound.py', 'wdroz_po_predeploy.py',
)


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as src:
        for data in iter(lambda:src.read(1024*1024),b''):
            h.update(data)
    return h.hexdigest()


def _digest_ok(value):
    return isinstance(value,str) and len(value)==64 and all(c in '0123456789abcdef' for c in value)


def _approved_state(state,archive):
    return (isinstance(state,dict) and state.get('status')=='PASS'
        and state.get('quality_gate')=='ULTIMATE-60-PLUS'
        and type(state.get('returncode')) is int and state['returncode']==0
        and type(state.get('completed_stages')) is int and state['completed_stages']==60
        and type(state.get('required_stages')) is int and state['required_stages']==60
        and state.get('version')==VERSION and state.get('installed_at_test')==SOURCE_VERSION
        and state.get('v109_release_gates_pass') is True
        and _digest_ok(state.get('sha256')) and digest(archive)==state['sha256'])


def activation_manifest(state,archive_path,staged_root):
    """Installer-only; fail before STOP on stale proof or modified staging."""
    from aktualizuj_soulbound import archive_mapping
    archive=Path(archive_path)
    stage=Path(staged_root)
    if not _approved_state(state,archive):
        raise ValueError('v109: brak zatwierdzonego PREDEPLOY 60/60 + bramek v109')
    with zipfile.ZipFile(archive) as z:
        mapping=archive_mapping(z)
        if set(mapping) != {p.relative_to(stage) for p in stage.rglob('*') if p.is_file()}:
            raise ValueError('v109: staging jest inny niz zatwierdzona paczka')
        for rel,info in mapping.items():
            p=stage/rel
            if p.is_symlink() or not p.is_file() or hashlib.sha256(z.read(info)).hexdigest()!=digest(p):
                raise ValueError('v109: niespojny plik stagingu '+str(rel))
    hashes={}
    for rel in REQUIRED:
        p=stage/rel
        if not p.is_file() or p.is_symlink():
            raise ValueError('v109: brakuje '+rel)
        hashes[rel]=digest(p)
    return dict(schema=1,version=VERSION,installed_at_test=SOURCE_VERSION,
                status='PASS',quality_gate='ULTIMATE-60-PLUS',
                completed_stages=60,required_stages=60,returncode=0,
                v109_release_gates_pass=True,sha256=state['sha256'],files=hashes)


def _check(root):
    root=Path(root)
    if not (root/'VERSION').is_file() or (root/'VERSION').read_text(encoding='utf-8-sig').strip()!=VERSION:
        return False
    marker_path=root/MARKER
    if marker_path.is_symlink() or not marker_path.is_file():
        return False
    marker=json.loads(marker_path.read_text(encoding='utf-8'))
    if (not isinstance(marker,dict) or type(marker.get('schema')) is not int or marker['schema']!=1
        or marker.get('version')!=VERSION or marker.get('installed_at_test')!=SOURCE_VERSION
        or marker.get('status')!='PASS' or marker.get('quality_gate')!='ULTIMATE-60-PLUS'
        or type(marker.get('completed_stages')) is not int or marker['completed_stages']!=60
        or type(marker.get('required_stages')) is not int or marker['required_stages']!=60
        or type(marker.get('returncode')) is not int or marker['returncode']!=0
        or marker.get('v109_release_gates_pass') is not True
        or not _digest_ok(marker.get('sha256'))):
        return False
    checks=marker.get('files')
    if not isinstance(checks,dict) or set(checks)!=set(REQUIRED):
        return False
    for rel,expected in checks.items():
        p=root/rel
        if not _digest_ok(expected) or p.is_symlink() or not p.is_file() or digest(p)!=expected:
            return False
    return True


@lru_cache(maxsize=1)
def production_approved():
    return verify_root_for_test(ROOT)


def verify_root_for_test(root):
    try:return _check(root)
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, json.JSONDecodeError):
        return False
