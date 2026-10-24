#!/usr/bin/env python3
"""Run the complete production-runtime gameplay audit on a disposable database.

SOULBOUND_FULL_AUDIT enables expensive semantic verification, while historical
developer/style audit modules remain a separate opt-in lane.
"""
from __future__ import annotations

import os
import socket
import tempfile


_original_npc_ids_v3103 = None  # Immutable baseline captured by main().

def main():
    global _original_npc_ids_v3103
    with tempfile.TemporaryDirectory(prefix="soulbound-full-audit-") as directory:
        os.environ["SOULBOUND_DB"] = os.path.join(directory, "audit.db")
        os.environ["SOULBOUND_FULL_AUDIT"] = "1"
        os.environ["SOULBOUND_HOST"] = "127.0.0.1"  # Always private during audits.
        os.environ.pop("SOULBOUND_HISTORICAL_AUDITS", None)
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            os.environ["SOULBOUND_PORT"] = str(probe.getsockname()[1])
        # Skill catalogue's immutable release identity must be audited BEFORE
        # runtime bootstrap. Some historical server initializers and scenario
        # tests add temporary learned-skill context to the shared Bard catalog.
        from validation.v1110_unique_skill_names import run_regression as _v1110_names
        print(f"UNIKALNE NAZWY SKILLI v11.00.10: {_v1110_names()} checks PASS")
        import server
        # v11.00.11: direct HELP skill lookups before any mutating historical checks.
        from validation.v1111_skill_help_dispatch import run_regression as _v1111_skill_help
        print(f"HELP SKILLI v11.00.11: {_v1111_skill_help()} checks PASS")
        # v11.00.12: named teachers, 24 real quests, class help and mountain chests.
        from validation.v1112_teacher_quests import run_regression as _v1112_teacher_quests
        print(f"NAUCZYCIELE/QUESTY/SKRZYNIE v11.00.12: {_v1112_teacher_quests()} checks PASS")
        from validation.v10205_readme_cleanup import run as _v10205_cleanup
        print(f'V102.00.5 README CLEANUP: {_v10205_cleanup()} checks PASS', flush=True)
        from validation.v9604_release_tcp import run as _v9604_release_tcp
        print(f"V96.00.4 RELEASE TCP: {_v9604_release_tcp()} checks PASS", flush=True)
        _original_npc_ids_v3103 = frozenset(server.NPCS)
        from validation.v3101_single_npc import run_regression as _single_npc_v3101
        print(f"JEDEN NPC NA POKOJ v3.10.1 FULL: {_single_npc_v3101(server.ROOMS, server.NPCS, server.SINGLE_NPC_ROOMS_V3101, server.SHOP_SELLERS)} checks PASS")
        from validation.v3100_legends_foundation import run_regression_full as _legends_full_v3100
        print(f"LEGENDY v3.10.0 FULL: {_legends_full_v3100(server)} checks PASS")
        from validation.v3007_ep_command import run_regression as _ep_command_v3007
        print(f"EP KOMENDA v3.00.7 FULL: {_ep_command_v3007()} checks PASS")
        from validation.v3007_boris_fishing_quests import run_regression as _boris_v3007
        print(f"BORYS WEDKARSTWO v3.00.7 FULL: {_boris_v3007()} checks PASS")
        from validation.v3006_queue_help import run_regression as _queue_help_v3006
        print(f"QUEUE HELP v3.00.6 FULL: {_queue_help_v3006(vars(server))} checks PASS")
        from validation.v3005_auto_learn_queue import test as _auto_queue_v3005
        print(f"AUTO CZARY I SKILLE / BEZ LIMITU v3.00.5 FULL: {_auto_queue_v3005()} checks PASS")
        from validation.v3004_ep_fame import run_regression as _ep_fame_v3004
        print(f"EP JAK FAME v3.00.4 FULL: {_ep_fame_v3004()} checks PASS")
        from validation.v3004_teacher_learn import run_regression as _teacher_learn_v3004
        print(f"TEACHER LEARN v3.00.4 FULL: {_teacher_learn_v3004()} checks PASS")
        from validation.v3002_help_wipe_mercenaries import run_regression as _help_wipe_v3002
        print(f"HELP / WIPE NAJEMNIKOW v3.00.3 FULL: {_help_wipe_v3002()} checks PASS")
        from validation.v3001_hybrid_equipment import run_regression as _hybrid_v3001
        print(f'EQ MULTICLASS v3.00.1 FULL: {_hybrid_v3001()} checks PASS')
        from validation.v3000_underlevel_balance import run_regression as _underlevel_v3000
        print(f'BALANS TRUDNOSCI v3.00.0 FULL: {_underlevel_v3000()} checks PASS')
        from validation.v23213_stop_supervisor import run_regression as _stop_supervisor_v23213
        print(f'STOP + WATCHDOG v2.32.13 FULL: {_stop_supervisor_v23213()} checks PASS')
        from validation.v23212_auto_mining_move import run_runtime_regression as _mine_move_runtime_v23212
        print(f"AUTO MINING MOVE v2.32.12 RUNTIME: {_mine_move_runtime_v23212()} checks PASS")
        from validation.v1705_windows_clean_stop import run_regression as _clean_stop_v1705
        print(f'WINDOWS CLEAN STOP v1.70.5 FULL: {_clean_stop_v1705()} checks PASS')
        from validation.v1704_short_fame import run_regression as _fame_short_v1704
        print(f'FAME SHORT STATUS v1.70.4 FULL: {_fame_short_v1704()} checks PASS')
        from validation.v1702_living_summons import run_regression as _living_v1702
        print(f'LIVING SUMMONS v1.70.2 FULL: {_living_v1702()} checks PASS')
        from validation.v1702_mage_elementals import run_regression as _mage_v1702
        print(f'MAGE ELEMENTALS v1.70.2 FULL: {_mage_v1702()} checks PASS')
        from validation.v1702_druid_fame import run_regression as _druid_fame_v1702
        print(f'DRUID PINECONES + FAME v1.70.2 FULL: {_druid_fame_v1702()} checks PASS')
        from validation.v1701_colored_souls import run_regression as _colored_souls_v1701
        print(f"COLORED SOULSTONES v1.70.1 FULL: {_colored_souls_v1701(server)} checks PASS")
        from validation.v3102_front_officers import run_regression as _fronts_v3102
        print(f"FRONTY ERA LEGEND v3.10.2 FULL: {_fronts_v3102(server)} checks PASS")
        from validation.v1600_era_legends import run_era_legends_v1600
        _era_v1600=run_era_legends_v1600(server)
        assert not _era_v1600['errors'], _era_v1600['errors'][:20]
        print(f"ERA LEGEND v1.60.1 FULL: {_era_v1600['checks']} checks PASS; "
              f"walk do Orków {_era_v1600['road_steps']} steps")
        from validation.v1407_progression_from50 import run_progression_from50_regression_v1407
        _prog1407=run_progression_from50_regression_v1407()
        assert not _prog1407['errors'], _prog1407['errors'][:20]
        print(f"PROGRESSION FROM 50 v1.40.7 FULL: {_prog1407['checks']} checks PASS")
        from validation.v1408_pleasant_grind import run_pleasant_grind_v1408
        _pleasant_v1408=run_pleasant_grind_v1408()
        assert not _pleasant_v1408['errors'], _pleasant_v1408['errors'][:20]
        print(f"PLEASANT GRIND v1.40.8 FULL: {_pleasant_v1408['checks']} checks PASS")
        from validation.v1406_orders_regression import run_orders_regression_v1406
        _order_v1406=run_orders_regression_v1406()
        print(f"PROFESSION ORDERS v1.40.6 FULL: {_order_v1406['checks']} checks PASS")
        from validation.v1405_admin_orders_regression import run_admin_orders_v1405
        _admin_orders_v1405 = run_admin_orders_v1405(runtime=server)
        assert not _admin_orders_v1405['errors'], _admin_orders_v1405['errors']
        print(f"ADMIN + ORDERS v1.40.5 RUNTIME: {_admin_orders_v1405['checks']} checks PASS")
        from validation.v1405_mob_regen import run_mob_regen_regression_v1405
        _mob_regen_v1405 = run_mob_regen_regression_v1405(runtime=server)
        assert not _mob_regen_v1405['errors'], _mob_regen_v1405['errors']
        print(f"MOB REGEN v1.40.5 RUNTIME: {_mob_regen_v1405['checks']} checks PASS")
        from validation.profession_xp_v1401 import run_profession_xp_regression_v1401
        _xp_v1401 = run_profession_xp_regression_v1401()
        assert not _xp_v1401['errors'], _xp_v1401['errors'][:20]
        print(f"PROFESSION XP v1.40.1: {_xp_v1401['checks']} checks PASS")
        from validation.tool_xp_v1402 import run_tool_xp_regression_v1402
        _tools_v1402 = run_tool_xp_regression_v1402()
        assert not _tools_v1402['errors'], _tools_v1402['errors'][:20]
        print(f"TOOL XP v1.40.2: {_tools_v1402['checks']} checks PASS")
        from validation.v1403_docker_guard import run_docker_generator_guard_v1403
        _docker_guard = run_docker_generator_guard_v1403()
        assert not _docker_guard['errors'], _docker_guard['errors']
        print(f"RAILWAY GENERATOR GUARD v1.40.3: {_docker_guard['checks']} checks PASS")
        from validation.v1380_great_audit import run_great_audit_v1380
        _v1380 = run_great_audit_v1380()
        assert _v1380['error_count'] == 0, _v1380['errors']
        print(f"GREAT AUDIT v1.38.0: {_v1380['checks']} checks PASS")
        from validation.admin_error_cleanup_v1371_test import run_admin_error_cleanup_v1371
        assert run_admin_error_cleanup_v1371()["errors"] == 0
        print("ADMIN ERROR CLEANUP v1.37.1: migration, resolved state, safe purge PASS")
        from validation.admin_error_cleanup_v1371_test import run_admin_error_commands_v1371
        assert run_admin_error_commands_v1371()["errors"] == 0
        print("ADMIN ERROR COMMANDS v1.37.1: 9 dispatch, permissions and confirmation tests PASS")
        # v1.39.0: six deterministic virtual sessions sharing real disposable
        # SQLite. Does not open player sockets or touch the deployment database.
        from validation.v1390_world_stress import run_stress_v1390
        _stress_v1390 = run_stress_v1390(players=6, rounds=120)
        assert not _stress_v1390['errors'], _stress_v1390['failures'][:20]
        print(f"WORLD STRESS v1.39.0: {_stress_v1390['simulated_operations']} operations, "
              f"{_stress_v1390['checks']} checks, "
              f"p95={_stress_v1390['p95_actor_batch_ms']}ms, "
              "6 virtual players, 0 errors; NOT live TCP load")
        # v1.40.0: one boss must never grant two rewards when party, AoE and
        # mercenary kill callbacks interleave on the same event loop.
        from validation.v1400_combat_stability import run_combat_stability_v1400
        _combat_v1400 = run_combat_stability_v1400()
        assert not _combat_v1400['errors'], _combat_v1400['failures']
        print(f"COMBAT STABILITY v1.40.0: {_combat_v1400['checks']} checks PASS; "
              "4 simultaneous kill callbacks; 24 unbounded summons")
        # v1.37.0: test the actual command routing in the assembled runtime.
        from player.session import Session
        from player.session_mixins.command_registry import COMMAND_REGISTRY, resolve_session_command
        from systems.legendary_achievements_v1370 import CATALOG_V1370
        from validation.legendary_achievements_v1370_test import run_legendary_achievement_regression_v1370
        _legendary_v1370 = run_legendary_achievement_regression_v1370()
        assert _legendary_v1370['catalog'] == 588
        assert resolve_session_command('medale') == 'medale'
        assert resolve_session_command('kronikapostaci') == 'kronikapostaci'
        assert resolve_session_command('legendy') == 'legendaryrares'
        assert resolve_session_command('legendarneosiagniecia') == 'medale'
        assert callable(getattr(Session, 'legendary_achievements_v1370', None))
        assert callable(getattr(Session, 'show_server_chronicle_v03811', None))
        print('LEGENDARNE OSIAGNIECIA v1.37.0 RUNTIME: 588 definitions, 126 titles, '
              '12 SQLite tests, session and command integration PASS')
        try:
            from validation.era_awakening_v1300 import audit_awakening_v1300
            _awakening = audit_awakening_v1300(server.ROOMS, server.NPCS, server.SHOPS,
                server.MOB_TEMPLATES, server.MOB_SPAWNS, server.QUESTS, server.ITEMS)
            print(f"ERA PRZEBUDZENIA v1.30.1: {_awakening['checks']} checks, "
                  f"{_awakening['authored_rooms']} authored rooms, "
                  f"{_awakening['error_count']} errors")
            if _awakening['error_count']:
                raise SystemExit('ERA PRZEBUDZENIA: ' + '; '.join(_awakening['errors'][:30]))
            from validation.orc_boss_summon_v1301 import audit_orc_summons_v1301
            _orc = audit_orc_summons_v1301(server.ROOMS, server.MOB_TEMPLATES, server.MOB_SPAWNS, server.NPCS, server.QUESTS)
            print(f"ORC KINGDOM & SUMMONS v1.30.1: {_orc['checks']} checks, {_orc['error_count']} errors")
            if _orc['error_count']:
                raise SystemExit('ORC SUMMONS: ' + '; '.join(_orc['errors']))
            from validation.six_eras_v1310 import audit_six_eras_v1310
            _six = audit_six_eras_v1310(server.ROOMS, server.NPCS, server.SHOPS,
                server.MOB_TEMPLATES, server.MOB_SPAWNS, server.QUESTS, server.ITEMS)
            print(f'SIX ERAS v1.31.0: {_six["checks"]} checks, {_six["rooms"]} rooms, {_six["error_count"]} errors')
            if _six['error_count']:
                raise SystemExit('SIX ERAS: ' + '; '.join(_six['errors'][:25]))
            ns = vars(server)
            from validation.final_stability_v1203 import audit_final_stability_v1203
            _final = audit_final_stability_v1203()
            print(f"FINAL STABILITY v1.20.3 RUNTIME: {_final['checks']} checks, {_final['error_count']} errors")
            if _final['error_count']:
                raise SystemExit('FINAL STABILITY: ' + '; '.join(_final['errors']))
            from validation.enchanting_vendor_v1202 import audit_enchanting_vendor_v1202
            _enchanting_vendor = audit_enchanting_vendor_v1202()
            print(f"ENCHANTING VENDOR v1.20.2 RUNTIME: {_enchanting_vendor['checks']} checks, {_enchanting_vendor['error_count']} errors")
            if _enchanting_vendor['error_count']:
                raise SystemExit('ENCHANTING VENDOR: ' + '; '.join(_enchanting_vendor['errors']))
            # v1.17.2: test actual post-Generator class EQ, not merely early
            # recipe templates.  This catches missing Mec INT/WILL channels.
            from validation.class_balance_v1172 import (
                audit_class_skill_balance_v1172,
                audit_class_equipment_balance_v1172,
            )
            from systems.items_resources import CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER
            from systems.crafting_expansion import TECH_SET_ITEMS_V03114
            _class_v1172 = audit_class_skill_balance_v1172()
            _eq_v1172 = audit_class_equipment_balance_v1172(
                ns["ITEMS"], CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER, TECH_SET_ITEMS_V03114
            )
            print(f"CLASS BALANCE v1.17.2: {_class_v1172['classes']} classes, "
                  f"{_class_v1172['skills']} skills, {_class_v1172['checks']} checks, "
                  f"{_class_v1172['error_count']} errors")
            print(f"CLASS EQUIPMENT v1.17.2: {_eq_v1172['classes']} classes, "
                  f"{_eq_v1172['checks']} checks, {_eq_v1172['error_count']} errors")
            if _class_v1172['error_count'] or _eq_v1172['error_count']:
                for _error in (_class_v1172['errors'] + _eq_v1172['errors'])[:60]:
                    print('CLASS BALANCE ERROR: ' + _error)
                raise SystemExit(1)
            # v1.17.3: actual adaptive scaling with final EQ, Haste and party sizes.
            from validation.combat_balance_v1173 import (
                audit_combat_balance_runtime_v1173,
                audit_party_support_runtime_v1173,
            )
            _combat_v1173 = audit_combat_balance_runtime_v1173(
                ns["ITEMS"], CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER
            )
            _support_v1173 = audit_party_support_runtime_v1173()
            print(f"COMBAT BALANCE v1.17.3 RUNTIME: {_combat_v1173['checks']} checks, "
                  f"{_combat_v1173['classes']} classes, {_combat_v1173['error_count']} errors")
            print(f"PARTY SUPPORT v1.17.3: {_support_v1173['checks']} checks, "
                  f"{_support_v1173['error_count']} errors")
            if _combat_v1173['error_count'] or _support_v1173['error_count']:
                for _issue in (_combat_v1173['errors'] + _support_v1173['errors'])[:100]:
                    print('COMBAT BALANCE ERROR: ' + _issue)
                raise SystemExit(1)
            # v1.17.4: real post-Generator gear, fractional crafting perks,
            # handcrafted legendary sources and persisted variant restoration.
            from validation.equipment_balance_v1174 import audit_equipment_balance_runtime_v1174
            _equipment_v1174 = audit_equipment_balance_runtime_v1174(
                ns["ITEMS"], CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER
            )
            print(f"EQUIPMENT BALANCE v1.17.4: {_equipment_v1174['checks']} checks, "
                  f"{_equipment_v1174['error_count']} errors, "
                  f"sources={_equipment_v1174['sources']}")
            if _equipment_v1174['error_count']:
                for _issue in _equipment_v1174['errors'][:80]:
                    print('EQUIPMENT BALANCE ERROR: ' + _issue)
                raise SystemExit(1)
            # v1.17.5: canonical merchant prices, profession availability and
            # real SQLite purchase->sell/bank/transfer anti-arbitrage.
            from validation.economy_final_v1175 import audit_economy_final_v1175
            _economy_v1175 = audit_economy_final_v1175()
            print(f"ECONOMY FINAL v1.17.5: {_economy_v1175['checks']} checks, "
                  f"{_economy_v1175['professions']} professions, "
                  f"{_economy_v1175['offers']} static offers, "
                  f"{_economy_v1175['at_risk_before']} pre-fix price risks, "
                  f"{_economy_v1175['error_count']} errors")
            if _economy_v1175['error_count']:
                for _issue in _economy_v1175['errors'][:80]:
                    print('ECONOMY ERROR: ' + _issue)
                raise SystemExit(1)
            # v1.17.6: 14 professions are assembled by runtime after server import.
            from validation.profession_balance_v1176 import audit_profession_balance_v1176
            _professions_v1176 = audit_profession_balance_v1176(runtime=True)
            print(f"PROFESSIONS v1.17.6 RUNTIME: {_professions_v1176['checks']} checks, "
                  f"{_professions_v1176['professions']} professions, "
                  f"{_professions_v1176['error_count']} errors")
            if _professions_v1176['error_count']:
                for _issue in _professions_v1176['errors'][:80]:
                    print('PROFESSIONS ERROR: ' + _issue)
                raise SystemExit(1)
            # v1.17.7: runtime Character passives for 14 races (legacy Smoczy too).
            from validation.race_balance_v1177 import audit_race_balance_v1177
            _race_v1177 = audit_race_balance_v1177(runtime=True)
            print(f"RACES v1.17.7 RUNTIME: {_race_v1177['checks']} checks, "
                  f"{_race_v1177['combos']} race/class pairs, "
                  f"{_race_v1177['error_count']} errors")
            if _race_v1177['error_count']:
                for _error in _race_v1177['errors'][:60]:
                    print('RACES ERROR: ' + _error)
                raise SystemExit(1)
            # v1.17.8: verify simultaneous combat output and SQLite queue saves.
            from validation.stability_v1178 import audit_stability_v1178
            _stable_v1178 = audit_stability_v1178()
            print(f"STABILITY v1.17.8 RUNTIME: {_stable_v1178['checks']} checks, "
                  f"{_stable_v1178['clients']} clients, "
                  f"{_stable_v1178['error_count']} errors")
            if _stable_v1178['error_count']:
                for _issue in _stable_v1178['errors'][:50]:
                    print('STABILITY ERROR: ' + _issue)
                raise SystemExit(1)
            # v1.18.0: read-only accessibility commands and history filters.
            from validation.qol_v1180 import audit_qol_v1180
            _qol_v1180 = audit_qol_v1180()
            print(f"QUALITY OF LIFE v1.18.0 RUNTIME: {_qol_v1180['checks']} checks, "
                  f"{_qol_v1180['error_count']} errors")
            if _qol_v1180['error_count']:
                raise RuntimeError('QOL: ' + '; '.join(_qol_v1180['errors']))
            from validation.world_secrets_v1190 import audit_world_secrets_v1190
            _secrets_v1190 = audit_world_secrets_v1190()
            print(f"WORLD SECRETS v1.19.0 RUNTIME: {_secrets_v1190['checks']} checks, {_secrets_v1190['error_count']} errors")
            if _secrets_v1190['error_count']:
                raise RuntimeError('SECRETS: ' + '; '.join(_secrets_v1190['errors']))
            from validation.great_world import audit_great_world_v1200
            _great_world_v1200 = audit_great_world_v1200()
            print(f"GREAT WORLD v1.20.0 RUNTIME: {_great_world_v1200['checks']} checks, {_great_world_v1200['error_count']} errors")
            if _great_world_v1200['error_count']:
                raise RuntimeError("GREAT WORLD v1.20.0: " + "; ".join(_great_world_v1200['errors']))

            from validation.legendary_expeditions import audit_legendary_expeditions_v1210
            _legendary_v1210 = audit_legendary_expeditions_v1210()
            print(f"LEGENDARY EXPEDITIONS v1.21.0 RUNTIME: {_legendary_v1210['checks']} checks, {_legendary_v1210['error_count']} errors")
            if _legendary_v1210['error_count']:
                raise RuntimeError("LEGENDARY EXPEDITIONS v1.21.0: " + "; ".join(_legendary_v1210['errors']))

            from validation.order_turnin_hotfix_v1201 import audit_order_turnin_hotfix_v1201
            _order_hotfix_v1201 = audit_order_turnin_hotfix_v1201()
            print(f"ORDER TURNIN v1.20.1 RUNTIME: {_order_hotfix_v1201['checks']} checks, {_order_hotfix_v1201['error_count']} errors")
            if _order_hotfix_v1201['error_count']:
                raise RuntimeError("ORDER TURNIN: " + "; ".join(_order_hotfix_v1201['errors']))
            from validation.upgrade_v1193 import audit_upgrade_v1193
            _upgrade_v1193 = audit_upgrade_v1193()
            print(f"NAV/CAREER/PARTY v1.19.3 RUNTIME: {_upgrade_v1193['checks']} checks, {_upgrade_v1193['error_count']} errors")
            if _upgrade_v1193['error_count']:
                raise RuntimeError('UPGRADE: ' + '; '.join(_upgrade_v1193['errors']))
            # v1.15.0: new loot and recipes must exist in the fully assembled runtime.
            from systems.legendary_reborn import legendary_reborn_audit_v1150
            from systems.equipment_crafting import CRAFT_RECIPES, JEWELCRAFT_RECIPES
            from systems.professions import V03053_CRAFT_RECIPES
            _legendary_v1150 = legendary_reborn_audit_v1150(
                CRAFT_RECIPES, JEWELCRAFT_RECIPES, V03053_CRAFT_RECIPES
            )
            if _legendary_v1150["errors"]:
                print("LEGENDARY REBORN ERRORS:", _legendary_v1150["errors"])
                raise SystemExit(1)
            print(f"LEGENDARY REBORN: {_legendary_v1150['checks']} checks, 0 errors")
            full = ns["FULL_GAME_PREDEPLOY_AUDIT_V0336"]
            # v1.14.7: real native-runtime progression, save/reopen, helpers.
            from validation.release_stability import audit_release_stability_runtime_v1147
            from validation.profession_market_v1148 import audit_profession_market_v1148
            from validation.profession_drops_v1149 import audit_profession_drops_v1149
            drops = audit_profession_drops_v1149()
            print(f"PROFESSION DROPS: {drops['checks']} checks; {drops['error_count']} errors")
            if drops['error_count']:
                for error in drops['errors']:
                    print("DROP ERROR:", error)
                raise SystemExit(1)
            market = audit_profession_market_v1148()
            print(f"PROFESSION MARKET RUNTIME: {market['checks']} checks, "
                  f"{market['error_count']} errors; groups={market['groups']}")
            for error in market['errors'][:60]:
                print("PROFESSION MARKET ERROR: " + error)
            if market['error_count']:
                raise SystemExit(1)
            stability = audit_release_stability_runtime_v1147(ns)
            print(f"RELEASE STABILITY RUNTIME: {stability['checks']} checks, "
                  f"{stability['error_count']} errors")
            for error in stability['errors']:
                print("RELEASE STABILITY ERROR: " + error)
            if stability['error_count']:
                raise SystemExit(1)
            print(
                "LEGACY FULL GAME AUDIT v0.33.6: "
                f"{full['error_count']} advisory findings, "
                f"{full.get('warning_count', 0)} warnings"
            )
            for error in full.get("errors", ())[:100]:
                print(f"LEGACY ADVISORY: {error}")

            # v1.13.30 — audit audytów. Runtime modules may expose diagnostics
            # without raising during production startup. Full predeploy collects every
            # audit report from the assembled compatibility namespace and rejects the
            # image here instead.
            audit_failures = []
            audit_advisories = []
            audit_reports = 0
            # v1.13.37 cleanup baseline: the historical full-game audit is
            # clean again, so new findings are deploy blockers rather than a
            # permanently ignored advisory backlog.
            nonblocking_legacy_audits = set()
            for name, value in sorted(ns.items()):
                if "AUDIT" not in str(name).upper() or not isinstance(value, dict):
                    continue
                if "error_count" not in value:
                    continue
                audit_reports += 1
                try:
                    error_count = int(value.get("error_count", 0) or 0)
                except (TypeError, ValueError, OverflowError):
                    audit_failures.append(
                        f"{name}: invalid error_count={value.get('error_count')!r}"
                    )
                    continue
                if error_count:
                    errors = tuple(value.get("errors", ()) or ())
                    target = (
                        audit_advisories
                        if name in nonblocking_legacy_audits
                        else audit_failures
                    )
                    if errors:
                        target.extend(
                            f"{name}: {error}" for error in errors[:100]
                        )
                    else:
                        target.append(
                            f"{name}: error_count={error_count} without error details"
                        )
            print(
                f"RUNTIME AUDIT REGISTRY: {audit_reports} reports, "
                f"{len(audit_failures)} blocking failures, "
                f"{len(audit_advisories)} legacy advisory findings"
            )
            for error in audit_advisories[:100]:
                print(f"RUNTIME AUDIT ADVISORY: {error}")
            for error in audit_failures[:300]:
                print(f"RUNTIME AUDIT ERROR: {error}")
            if audit_failures:
                raise SystemExit(1)

            from admin.cross_system_audit_v1001 import audit as audit_cross_system_v1001
            cross = audit_cross_system_v1001(server)
            print(
                f"CROSS SYSTEM: {len(cross['errors'])} errors, "
                f"{len(cross['warnings'])} warnings; "
                f"{cross['quests']} quests, {cross['mobs']} mobs, "
                f"{cross['items']} items, {cross['rooms']} rooms, {cross['npcs']} NPCs"
            )
            for error in cross.get("errors", ()):
                print(f"CROSS ERROR: {error}")
            for warning in cross.get("warnings", ())[:100]:
                print(f"CROSS WARNING: {warning}")
            if cross["errors"]:
                raise SystemExit(1)

            # v1.13.37 — Deep Dungeon lazy-generation smoke. The entry may point
            # at a room that does not exist until first use, but the creator must
            # materialize that exact destination with a reciprocal return path.
            deep_errors = []
            deep_entry_id = ns.get(
                "UOSS_DEEP_DUNGEON_ENTRY_V11331",
                "uoss_deep_dungeon_entry_v11331",
            )
            deep_entry = ns.get("ROOMS", {}).get(deep_entry_id, {})
            deep_target = (deep_entry.get("exits") or {}).get("down")
            deep_creator = ns.get(
                "create_infinite_uoss_deep_dungeon_floor_definition_v11331"
            )
            if not callable(deep_creator):
                deep_errors.append("Deep Dungeon floor creator missing")
            else:
                try:
                    floor1_id, _ = deep_creator(1)
                    if deep_target != floor1_id:
                        deep_errors.append(
                            f"entry down={deep_target!r}, creator floor1={floor1_id!r}"
                        )
                    floor1 = ns["ROOMS"].get(floor1_id, {})
                    if (floor1.get("exits") or {}).get("up") != deep_entry_id:
                        deep_errors.append("Deep Dungeon floor 1 does not return to entry")
                    floor25_id, _floor25_created_spawns = deep_creator(25)
                    floor25_spawns = [
                        (room_id, template_id)
                        for room_id, template_id in ns.get("MOB_SPAWNS", ())
                        if str(room_id) == str(floor25_id)
                    ]
                    # A lazy floor can already exist by the time this smoke runs,
                    # so its creator may correctly return no *new* spawns. Audit
                    # the assembled runtime spawn table rather than only the delta.
                    if not floor25_spawns:
                        floor25_spawns = list(_floor25_created_spawns)
                    if not any(
                        (
                            int(
                                ns["MOB_TEMPLATES"].get(template_id, {}).get(
                                    "uoss_deep_dungeon_apanda_floor", 0
                                ) or 0
                            ) == 25
                            and str(
                                ns["MOB_TEMPLATES"].get(template_id, {}).get(
                                    "boss_mechanic", ""
                                )
                            ) == "uoss_deep_dungeon_apanda"
                        )
                        for _room_id, template_id in floor25_spawns
                    ):
                        deep_errors.append("Deep Dungeon floor 25 has no Apanda gate")
                    floor100_id, _ = deep_creator(100)
                    floor100 = ns["ROOMS"].get(floor100_id, {})
                    if int(floor100.get("uoss_deep_dungeon_floor", 0) or 0) != 100:
                        deep_errors.append("Deep Dungeon floor 100 metadata missing")
                    if int(ns.get(
                        "UOSS_DEEP_DUNGEON_SERPENTARIUS_UNLOCK_FLOOR_V11331", 0
                    ) or 0) != 100:
                        deep_errors.append("Serpentarius unlock floor is not 100")
                except Exception as exc:
                    deep_errors.append(
                        f"Deep Dungeon lazy smoke exception: {type(exc).__name__}: {exc}"
                    )
            print(
                f"DEEP DUNGEON LAZY SMOKE: {len(deep_errors)} errors; "
                "floors 1/25/100 checked"
            )
            for error in deep_errors:
                print(f"DEEP DUNGEON ERROR: {error}")
            if deep_errors:
                raise SystemExit(1)

            # v1.13.37 — verify boss chests resolve to the latest real boss spawn
            # after floor expansion, never to the old landing room.
            chest_errors = []
            chest_meta = {
                "giant": ("giant_fortress_boss", "giant_fortress_floor", "giant_fortress_"),
                "crypt": ("crypt_boss", "crypt_floor", "crypt_floor_"),
                "astral": ("astral_boss", "astral_floor", "astral_floor_"),
                "mythic_crypt": ("mythic_crypt_boss", "mythic_crypt_floor", "mythic_crypt_floor_"),
                "mythic_astral": ("mythic_astral_boss", "mythic_astral_floor", "mythic_astral_floor_"),
            }
            expected_rooms = {}
            representative_specs = {
                "crypt": (
                    "CRYPT_BOSS_FLOORS", "is_crypt_boss_floor", "crypt_floor_id",
                    "crypt_boss", "crypt_floor",
                ),
                "astral": (
                    "ASTRAL_BOSS_FLOORS", "is_astral_boss_floor", "astral_floor_id",
                    "astral_boss", "astral_floor",
                ),
                "mythic_crypt": (
                    "MYTHIC_BOSS_FLOORS", "is_mythic_crypt_boss_floor",
                    "mythic_crypt_floor_id", "mythic_crypt_boss", "mythic_crypt_floor",
                ),
                "mythic_astral": (
                    "MYTHIC_BOSS_FLOORS", "is_mythic_astral_boss_floor",
                    "mythic_astral_floor_id", "mythic_astral_boss", "mythic_astral_floor",
                ),
                "giant": (
                    "GIANT_FORTRESS_BOSS_FLOORS", "is_giant_fortress_boss_floor",
                    "giant_fortress_floor_id", "giant_fortress_boss", "giant_fortress_floor",
                ),
            }

            # v0.11 removes pregenerated instance rooms/spawns on startup.
            # Materialize one fresh boss checkpoint per dungeon through the real
            # World.ensure_runtime_room() path, exactly as production movement does.
            # predeploy imports the server bootstrap module but does not start its
            # async main(), so create the same World object directly for this smoke.
            audit_world = ns["World"]()
            for kind, (
                floors_name, predicate_name, room_id_name, boss_flag, floor_key,
            ) in representative_specs.items():
                authored_floors = tuple(ns.get(floors_name, ()) or ())
                floor = (max(map(int, authored_floors)) + 10) if authored_floors else 10
                predicate = ns[predicate_name]
                room_id_fn = ns[room_id_name]
                chosen_room = None
                for _attempt in range(200):
                    candidate_room = room_id_fn(floor)
                    if predicate(floor) and candidate_room not in ns.get("ROOMS", {}):
                        chosen_room = candidate_room
                        break
                    floor += 10
                if not chosen_room:
                    chest_errors.append(
                        f"{kind}: could not find a fresh lazy boss checkpoint"
                    )
                    continue
                if not audit_world.ensure_runtime_room(chosen_room):
                    chest_errors.append(
                        f"{kind} {floor}: World.ensure_runtime_room failed"
                    )
                    continue

                boss_rooms = []
                for mob in audit_world.mobs.values():
                    template = ns.get("MOB_TEMPLATES", {}).get(mob.template_id, {})
                    if not template.get(boss_flag):
                        continue
                    try:
                        mob_floor = int(template.get(floor_key, 0) or 0)
                    except (TypeError, ValueError, OverflowError):
                        mob_floor = 0
                    if mob_floor == floor:
                        boss_rooms.append(str(mob.room_id))
                boss_rooms = sorted(set(boss_rooms))
                if len(boss_rooms) != 1:
                    chest_errors.append(
                        f"{kind} {floor}: expected one real boss room, got {boss_rooms!r}"
                    )
                    continue
                expected_rooms[(kind, floor)] = boss_rooms[0]

            if len(expected_rooms) != len(representative_specs):
                chest_errors.append(
                    "boss chest smoke did not materialize all five dungeon families; "
                    f"checked={len(expected_rooms)} expected={len(representative_specs)}"
                )
            for (kind, floor), expected_room in sorted(expected_rooms.items()):
                actual_room = ns["boss_floor_chest_room_id"](kind, floor)
                if actual_room != expected_room:
                    chest_errors.append(
                        f"{kind} {floor}: chest room {actual_room!r} != boss room {expected_room!r}"
                    )
                    continue
                spec = ns["_boss_floor_chest_spec"](actual_room)
                if not spec or tuple(spec[:2]) != (kind, floor):
                    chest_errors.append(
                        f"{kind} {floor}: no chest spec in actual boss room {actual_room!r}"
                    )
                canonical = f"{chest_meta[kind][2]}{floor}"
                if canonical != actual_room and ns["_boss_floor_chest_spec"](canonical) is not None:
                    chest_errors.append(
                        f"{kind} {floor}: chest leaked back to landing room {canonical!r}"
                    )
            print(
                f"BOSS CHEST RUNTIME: {len(chest_errors)} errors; "
                f"{len(expected_rooms)} boss checkpoints checked"
            )
            for error in chest_errors[:100]:
                print(f"BOSS CHEST ERROR: {error}")
            if chest_errors:
                raise SystemExit(1)

            # v1.28.6: do not silently regress dynamic Crypt boss chests after
            # the legacy spawn registry is pruned or compacted.
            from validation.chest_floor_v1286 import check_dynamic_boss_chests_v1286
            _chest_v1286 = check_dynamic_boss_chests_v1286(ns)
            print(f"DYNAMIC BOSS CHESTS v1.28.6: {_chest_v1286['checks']} checks, "
                  f"{_chest_v1286['error_count']} errors")
            for issue in _chest_v1286['errors'][:50]:
                print('DYNAMIC CHEST ERROR: ' + issue)
            if _chest_v1286['error_count']:
                raise SystemExit(1)

            # v1.28.8: smoke the actual player-visible chest lifecycle and
            # corpse key, which room-only tests missed in earlier releases.
            from validation.chest_cycle_v1288 import check_chest_lifecycle_v1288
            _cycle_v1288 = check_chest_lifecycle_v1288(ns, audit_world, expected_rooms)
            print(f"BOSS CHEST LIFECYCLE v1.28.8: {_cycle_v1288['checks']} checks, "
                  f"{_cycle_v1288['error_count']} errors")
            for issue in _cycle_v1288['errors'][:50]:
                print('BOSS CHEST CYCLE ERROR: ' + issue)
            if _cycle_v1288['error_count']:
                raise SystemExit(1)

            # v1.28.9: class quests rotate every two hours and old hourly
            # guild saves retain in-progress tasks within the same window.
            from validation.v1289_class_quest_cadence import audit_class_quest_cadence_v1289
            _class_quest_1289 = audit_class_quest_cadence_v1289()
            print(f"CLASS QUESTS v1.28.9: {_class_quest_1289['checks']} checks, "
                  f"{_class_quest_1289['error_count']} errors")
            for issue in _class_quest_1289['errors'][:50]:
                print('CLASS QUEST CADENCE ERROR: ' + issue)
            if _class_quest_1289['error_count']:
                raise SystemExit(1)

            # v1.33.0: check resolved runtime templates and wired Session commands.
            from systems.soul_ancients_v1330 import ANCIENT_STYLES, audit as _soul_audit
            from player.session import Session as _SessionV1330
            from player.session_mixins.command_registry import COMMAND_REGISTRY as _reg1330
            _soul_audit()
            assert _reg1330['dziedzictwo'][0] == 'soul_legacy_v1330'
            assert callable(getattr(_SessionV1330, 'soul_legacy_v1330', None))
            for _ancient_id in ANCIENT_STYLES:
                _ancient_template = server.MOB_TEMPLATES.get(_ancient_id, {})
                assert _ancient_template.get('ancient_avatar_v1330'), _ancient_id
                assert _ancient_template.get('world_boss'), _ancient_id
                assert any(mob_id == _ancient_id for _room, mob_id in server.MOB_SPAWNS), _ancient_id
            print('SOUL AND ANCIENTS v1.33.0 RUNTIME: four Ancient bosses, command and skill rules PASS')
            # Two separate Ancient entities share a true combat room.
            from systems.soul_evolutions_v1332 import audit as _evo_audit, council_allies
            _evo_audit()
            _council='v1332_ancients_council_arena'
            assert server.ROOMS[_council]['exits']['south']=='v1332_ancients_council_entry'
            assert server.ROOMS['v1310_anc_sky_sanctum']['exits']['east']=='v1332_ancients_council_entry'
            assert {tid for room,tid in server.MOB_SPAWNS if room==_council} == {
                'v1310_anc_deep_boss','v1310_anc_sky_boss'
            }
            assert callable(getattr(_SessionV1330, 'boss_summon_wave_v1301', None))
            assert callable(getattr(_SessionV1330, 'boss_attack_profile', None))
            print('CLASS EVOLUTIONS / ANCIENT COUNCIL v1.33.2: authored shared arena and hooks PASS')
            from validation.soul_council_v1332 import audit_council_combat_v1332
            _council_runtime = audit_council_combat_v1332()
            print(f"ANCIENT COUNCIL v1.33.2 REAL COMBAT: {_council_runtime['checks']} checks, 2 active bosses, true guardian and ally heal PASS")

            from admin.mob_display_name_audit_v11129 import audit_mob_display_names_v11129
            mob_names = audit_mob_display_names_v11129(server)
            print(
                f"MOB DISPLAY NAMES: {mob_names['error_count']} errors; "
                f"{mob_names['checked']} runtime mob templates checked"
            )
            for error in mob_names.get("errors", ())[:100]:
                print(f"MOB NAME ERROR: {error}")
            if mob_names["error_count"]:
                raise SystemExit(1)

            from validation.ocean_contract_v1001 import audit_ocean_contract_v1001
            contract = audit_ocean_contract_v1001()
            print(f"OCEAN CONTRACT: {contract['error_count']} errors, {contract['routes']} routes")
            if contract["error_count"]:
                raise SystemExit(1)

            from admin.fast_predeploy_audit_v0571 import FAST_PREDEPLOY_AUDIT_V0571 as fast
            print(
                "FINAL AUDIT SUMMARY: "
                f"{fast['duplicate_literal_key_count']} duplicate dict keys; "
                f"{fast['swallowed_exception_count']} swallowed exceptions; "
                f"{fast.get('intentional_swallowed_exception_count', 0)} intentional passes; "
                f"{fast['todo_fixme_count']} TODO/FIXME; "
                f"{len(cross['warnings'])} cross-system warnings"
            )
            from collections import Counter
            swallowed_hotspots = Counter(
                site.split(":", 1)[0] for site in fast.get("swallowed_exception_sites", ())
            )
            todo_hotspots = Counter(
                site.split(":", 1)[0] for site in fast.get("todo_sites", ())
            )
            swallowed_text = ",".join(
                f"{path}={count}" for path, count in swallowed_hotspots.most_common(6)
            ) or "none"
            todo_text = ",".join(
                f"{path}={count}" for path, count in todo_hotspots.most_common(6)
            ) or "none"
            print(
                "FULL AUDIT PASS: "
                f"{fast['duplicate_literal_key_count']} duplicate dict keys; "
                f"{fast['swallowed_exception_count']} swallowed exceptions; "
                f"{fast.get('intentional_swallowed_exception_count', 0)} intentional passes; "
                f"{fast['todo_fixme_count']} TODO/FIXME; "
                f"{len(cross['warnings'])} cross-system warnings; "
                f"swallowed hotspots [{swallowed_text}]; "
                f"TODO hotspots [{todo_text}]"
            )
        finally:
            server._BOOT_SOCKET.close()


        # v2.10.3: live reward gateways, Fame queue, all quest money definitions.
        from validation.v2103_fame_exploration_quest_currency import run_regression as _reward_v2103
        _reward_result_v2103 = _reward_v2103()
        print(f"FAME/EP/QUEST GOLD v2.10.3 FULL: {_reward_result_v2103} PASS")


# v72: atomic offline character package, explicit cycle-checked quest prerequisites
# and custom ordinary boss phase policies. Isolated child; fail CLOSED.
def _v7200_gate():
    import subprocess as _sp, sys as _sys
    from pathlib import Path as _Path
    result=_sp.run([_sys.executable,'-u','-m','validation.v7200_admin_live_advancement'],
        cwd=str(_Path(__file__).resolve().parent),stdin=_sp.DEVNULL,
        capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
    output=(result.stdout+'\n'+result.stderr).strip()
    if result.returncode!=0 or 'V72.00.0 ADVANCEMENT: 92 PASS' not in output:
        raise AssertionError('Admin Live v72 failed: '+output[-4000:])
    print(result.stdout.strip(),flush=True)
    return 92
print(f'ADMIN LIVE v72.00.0: {_v7200_gate()} checks PASS',flush=True)

if __name__ == "__main__":
    main()

from validation.v1708_druid_call import run_regression as _call_full_v1708
print(f"DRUID CALL v1.70.8 FULL: {_call_full_v1708()} checks PASS")

# v1.70.9: richer biome-dependent druid calls, level gates and squirrel biome.
from validation.v1709_terrain_fauna import run_regression as _terrain_fauna_v1709
print(f'TERRAIN FAUNA v1.70.9: {_terrain_fauna_v1709()} checks PASS')

# v1.70.10: preserve former guild economy while extending ceiling to 800.
from validation.v1710_summons import run_regression as _summon_mastery_full_v1710
print(f'SUMMON MASTERY v1.70.10 FULL: {_summon_mastery_full_v1710()} checks PASS')
from validation.v1710_guild800 import run_regression as _guild_full_v1710
print(f'GUILD 800 v1.70.10 FULL: {_guild_full_v1710()} checks PASS')

# v1.80.8: prove venom, burn, freeze and lightning on active summons.
from validation.v1808_summon_status import run_regression as _summon_status_full_v1808
print(f'SUMMON STATUS v1.80.8 FULL: {_summon_status_full_v1808()} checks PASS')

# v1.90.0: verify authored routes, real drops/recipes and boss phases.
from validation.v1900_ancient_kingdoms import run_regression as _ancient_full_v1900
print(f'ANCIENT KINGDOMS v1.90.0 FULL: {_ancient_full_v1900()} checks PASS')

# v1.90.1: ten AoE opponents use only local AI candidates; necromancy preserved.
from validation.v1901_aoe_ai_performance import run_regression as _aoe_ai_perf_v1901
print(f'AOE AI v1.90.1 FULL: {_aoe_ai_perf_v1901()} checks PASS')

# v2.00.0: real map links and party-safe reputation/arena credits.
from validation.v2000_parallel_worlds import run_regression as _v2000_full
print(f'PARALLEL WORLDS v2.00.0 FULL: {_v2000_full()} checks PASS')

# v2.00.1: compact catalogue must match the original numeric defaults.
from validation.v2001_catalogue_streaming import run_regression as _catalogue_full_v2001
print(f'CATALOGUE STREAMING v2.00.1 FULL: {_catalogue_full_v2001()} checks PASS')

# v2.00.2: SQLite history retains 40 immediately durable events per player,
# while minion synchronization avoids repeated owner HP calculations.
from validation.v2002_engine_performance import run_regression as _engine_perf_v2002
print(f"ENGINE PERFORMANCE v2.00.2 FULL: {_engine_perf_v2002()} checks PASS")

# v2.00.3: independent cross-system performance regression.
from validation.v2003_engine_optimization import run_regression as _engine_opt_full_v2003
print(f'ENGINE OPTIMIZATION v2.00.3 FULL: {_engine_opt_full_v2003()} checks PASS')

# v2.00.5: normal bandits no longer gain disproportionate low-level HP-based damage.
from validation.v2005_beginner_encounters import run_regression as _beginner_v2005
print(f"BEGINNER ENCOUNTERS v2.00.5 FULL: {_beginner_v2005()} checks PASS")

# v2.00.6: prevent pseudo-random difficulty for beginner world mobs.
from validation.v2006_region_balance import run_regression as _regions_v2006
print(f'REGIONAL WORLD v2.00.6 FULL: {_regions_v2006()} checks PASS')

# v2.00.7: actual CONSIDER must display region stage without NameError.
from validation.v2007_consider_region_import import run_regression as _consider_v2007
print(f"CONSIDER REGION v2.00.7 FULL: {_consider_v2007()} checks PASS")

# v2.00.8: Elementals inherit the Mage's real magical striking power.
from validation.v2008_elemental_damage import run_regression as _elemental_damage_v2008
print(f'MAGE ELEMENTAL DAMAGE v2.00.8: {_elemental_damage_v2008()} checks PASS')

# v2.00.9: one per-award cap; boss overcap; permanent SQLite Fame; real stairs.
from validation.v2009_expcap_fame_stairs import run_regression as _cap_stairs_full_v2009
print(f'EXP CAP / FAME / STAIRS v2.00.9 FULL: {_cap_stairs_full_v2009()} checks PASS')

# v2.00.10: unlocked portal-to-portal movement, party checks and catacombs.
from validation.v2010_unlocked_portals import run_regression as _portals_v2010
print(f'UNLOCKED PORTALS v2.00.10 FULL: {_portals_v2010()} checks PASS')

# v2.00.11: persistent, per-axis overflow and cap-safe repayment.
from validation.v2011_experience_bank import run_regression as _xp_bank_v2011
print(f"EXP BANK v2.00.11 FULL: {_xp_bank_v2011()} checks PASS")

# v2.10.0: repeat the scoped gameplay regression in the full audit.
from validation.v2100_titans import run_regression as _titans_v2100
print(f"TYTANI / LOCHY v2.10.0 FULL: {_titans_v2100()} checks PASS")

# The real five-player TCP stage is executed separately by TESTUJ_Soulbound.bat.
from validation.v2102_tcp_six_players import run_contract as _tcp6_guard_v2102
print(f"TCP FIVE PLAYERS v3.31.5 FULL SAFE CONFIG: {_tcp6_guard_v2102()} checks PASS; "
      "real TCP tests run as Windows stage 3")

# Repeat the controller contract during the exhaustive predeploy.
from validation.v2102_tcp_six_players import run_sqlite_cleanup_regression as _check_sqlite_close_v2301
print(f'TCP SQLITE CLEANUP v2.30.1: {_check_sqlite_close_v2301()} checks PASS')

from validation.v2102_predeploy_contract import run_regression as _quality_gate_selftest_v2102
print(f"QUALITY GATE v2.10.2 FULL: {_quality_gate_selftest_v2102()} controller checks PASS")

# v2.10.2: enumerate ALL  command aliases and quest definitions, exercise SQLite for each.
from validation.v2102_command_quest_coverage import main as _command_quest_coverage_v2102
_command_quest_coverage_v2102()

# v2.30.2: exhaustive registry and per-quest cross-account persistence tests.
from validation.v2302_exhaustive_game_coverage import run_exhaustive as _v2302_exhaustive
_v2302_exhaustive()

# v2.31.0: do not synthesize quest progress. Replay real database-event methods
# for every compatible quest and report other kinds as NOT TESTED.
from validation.v2400_real_quest_events import run_event_coverage as _real_events_v2310
_real_events_v2310()

# v2.20.0: independent end-to-end fixture checks in FULL too.
from validation.v2200_master_depths_ai import run_regression as _check_v2200
print(f"AI / PROFESJE / OCEAN v2.20.0 FULL: {_check_v2200()} checks PASS")

# v2.20.1: craft and ship modules end-to-end isolated SQLite regression.
from validation.v2201_fleet_mastery import run_regression as _check_v2201
print(f"MISTRZOWIE / MODULY FLOTY v2.20.1: {_check_v2201()} checks PASS")

# v2.30.0: additional authored AI, mastery and ocean release regression.
from validation.v2300_world_professions_ocean import run_regression as _v2300_regression
print(f'WIELKA ERA v2.30.0 AI / PROFESJE / OCEAN: {_v2300_regression()} checks PASS')


# v2.32.0: mapping of authored NPCs and shortest routes is only a graph
# audit; the TCP gate below exercises a real dialogue/combat separately.
from validation.v2320_autonomous_routes import audit_world_npc_routes as _journey_routes_v2320
import server as _runtime_v2320
_journey_routes = _journey_routes_v2320(_runtime_v2320.ROOMS, _runtime_v2320.NPCS, _runtime_v2320.QUESTS)
print('AUTOGRACZ v2.32.0: graf NPC/quest, '
      f'{_journey_routes["quest_count"]} zadan; '
      f'{_journey_routes["checks"]} mapowan PASS; '
      f'niezmapowane={_journey_routes["unknown"]}; '
      'NOT TESTED: rzeczywiste przejscia zamkniete fabula', flush=True)

# v2.32.1: live spawn, fixed lair and respawn of Matka Popiolu.
from validation.v2321_ash_matron_spawn import run_regression as _matron_spawn_v2321
print(f"MATKA POPIOLU v2.32.2 FULL: {_matron_spawn_v2321()} checks PASS")

# v2.32.2: automatic EP for silent guided transitions and one-time award.
from validation.v2322_auto_exploration import run_regression as _auto_ep_v2322
print(f"AUTO EP v2.32.3: {_auto_ep_v2322()} checks PASS")

# v2.32.15: full regression of persistent 14-class ownership / global cap.
from validation.v23215_multi_cap import run_regression as _multi_cap_v23215
print(f'MULTI CAP + MULTICLASS 14 v2.32.15 FULL: {_multi_cap_v23215()} checks PASS')

# v2.32.16: level shows all owned levels; final Multi Cap matches live EXP pipeline.
from validation.v23216_level_overview import run_regression as _level_overview_v23216
print(f'LEVEL OVERVIEW v2.32.16 FULL: {_level_overview_v23216()} checks PASS')

# v2.32.17: shared non-linear 10-level Multi Cap and Soul XP under level.
from validation.v23217_curve_soul_level import run_regression as _curve_soul_v23217
print(f'MULTI CAP CURVE + SOUL XP v2.32.17: {_curve_soul_v23217()} checks PASS')

# v2.32.18: each active class and axis gets full independent Multi Cap.
from validation.v23218_full_cap_per_axis import run_regression as _full_axis_v23218
print(f'FULL MULTI CAP PER AXIS v2.32.18: {_full_axis_v23218()} checks PASS')

# v2.32.19: real profession and sale XP bank integration.
from validation.v23219_profession_cap_balance import run_regression as _prof_cap_v23219
print(f'PROFESSION / TOOL MULTI CAP v2.32.19 FULL: {_prof_cap_v23219()} checks PASS')

# v3.10.4 - final invariant AFTER every historical audit and dynamic fixture.
# Snapshot was captured at the beginning of main(); fail closed if it is unavailable.
assert _original_npc_ids_v3103 is not None, "Missing baseline snapshot for the final NPC predeploy"
# This catches a late test or content generator putting two NPCs back together.
from validation.v3101_single_npc import run_regression as _single_npc_final_v3101
import server as _world_final_v3101
print(f"JEDEN NPC NA POKOJ v3.10.1 PO CALYM AUDYCIE: {_single_npc_final_v3101(_world_final_v3101.ROOMS, _world_final_v3101.NPCS, _world_final_v3101.SINGLE_NPC_ROOMS_V3101, _world_final_v3101.SHOP_SELLERS, original_npc_ids=_original_npc_ids_v3103)} checks PASS")

# v3.20.0: one release gate for all seven expansions and genuine ore -> ring
# purchase / professional-storage / two-crafts lifecycle. Uses TEMP SQLite.
from validation.v3200_seven_legends import check_all as _check_all_legends_v3200
_check_all_legends_v3200()

# v3.30.0: actual reward-turnin guard and v3.20 story events on isolated SQLite.
from validation.v3300_gameplay_audit import run_audit as _v3300_gameplay_audit
import server as _v3300_audit_runtime
_v3300_gameplay_audit(_v3300_audit_runtime)

# v3.31.0: full coverage of every XP level requirement, reward-only invariants.
from validation.v3310_all_xp_requirements import run_regression as _all_xp_v3310
print(f"ALL PROGRESSION XP v3.31.0: {_all_xp_v3310()} checks PASS")

# v3.31.1: all thirteen bandit-family mobs, persistent quest credit, essential NVDA messages.
from validation.v3311_bandit_progress import run_regression as _bandit_progress_v3311
import server as _bandit_runtime_v3311
print(f"BANDYCI QUEST PROGRESS v3.31.1: {_bandit_progress_v3311(_bandit_runtime_v3311)} checks PASS")

# v3.31.2: event professions, archaeology and unified live event atlas.
from validation.v3312_all_world_events import run_regression as _all_world_events_v3312
print(f"WYDARZENIA I WYKOPALISKA v3.31.2: {_all_world_events_v3312()} checks PASS")

# v3.31.3: all professions have action-backed early repeatable quests.
from validation.v3313_profession_paths import run_regression as _profession_paths_v3313
import server as _professions_runtime_v3313
print(f"SCIEZKI 14 PROFESJI v3.31.3 FULL: {_profession_paths_v3313(_professions_runtime_v3313)} PASS")

# v3.31.4: extra x2 progression requirements on all axes from level 1.
from validation.v3314_required_xp import run_regression as _xp_v3314
print(f"WYMAGANIA EXP v3.31.4: {_xp_v3314()} checks PASS")

# v3.31.5: fail-closed five-player TCP and scenario coverage contract.
from validation.v3315_predeploy_5_players import run_regression as _five_players_v3315
print(f"PREDEPLOY 5 GRACZY v3.31.5: {_five_players_v3315()} checks PASS")

# v4.00.0: full added-world playable catalogue, 14 existing professions,
# five ocean fleets, superboss phases and intelligent companion tactics.
from validation.v4000_imperium import run_regression as _imperium_4000
print(f"IMPERIUM v4.00.0: {_imperium_4000()} PASS")

# v4.00.0: real crafting transaction in a private 14-profession SQLite DB.
from validation.v4000_craft_runtime import run_regression as _v4000_craft
print(f"CRAFTING v4.00.0: {_v4000_craft()} checks PASS")

# v4.00.2: historical AST contracts + repeated source evaluation isolation.
from validation.v4010_modularization import run_regression as _modular_v4010
print(f"MODULY SILNIKA v4.00.2: {_modular_v4010()} checks PASS")

# v4.00.3: increased tool XP thresholds, never touch rewards or SQLite.
from validation.v4030_tool_xp_pacing import run_regression as _tool_pace_v4030
print(f"NARZEDZIA XP v4.00.3 FULL: {_tool_pace_v4030()} checks PASS")

# v4.00.5: split base content definitions while preserving original runtime semantics.
from validation.v4050_catalog_modularization import run_regression as _catalogs_4050
print(f"KATALOGI MODULOWE v4.00.5 FULL: {_catalogs_4050()} checks PASS")

# v4.00.6: externalized original audit functions, no gameplay changes.
from validation.v4060_audit_rules import run_regression as _audit_rules_4060
print(f"MODULOWE AUDYTY v4.00.6 FULL: {_audit_rules_4060()} checks PASS")

# v4.00.7: preserve the authored northern frontier, field quests and forest logic.
from validation.v4070_frontier_modularization import run_regression as _frontier_v407
print(f"MODULY ROZBUDOWY SWIATA v4.00.7 FULL: {_frontier_v407()} checks PASS")

# v4.10.0: large-scale audited modularization.
from validation.v4100_large_modularization import run_regression as _v4100_modular_regression
print(f"KOMPLEKSOWA MODULARYZACJA v4.10.0 FULL: {_v4100_modular_regression()} checks PASS")

# v4.20.0: final modularization safety and API/MRO guards.
from validation.v4200_modularization import run_regression as _sb420_regression
print(f"FINALNA MODULARYZACJA v4.20.0 FULL: {_sb420_regression()} checks PASS")

# v4.21.0: balance every XP requirement axis 1-800 without touching XP rewards.
from validation.v4210_balanced_requirements import run_regression as _xp_v4210
print(f"ROWNE EXP v4.21.0 FULL: {_xp_v4210()} checks PASS")
from validation.v4211_independent_xp_rewards import run_regression as _v4211_independent_rewards
print(f"NIEZALEZNE NAGRODY EXP v4.21.1: {_v4211_independent_rewards()} checks PASS")

# v5.00.0: full catalog, phase logic and reward independence check.
from validation.v5000_war_of_gods import run_regression as _v5000_war_of_gods
print(f"WOJNA BOGOW v5.00.0 FULL: {_v5000_war_of_gods()} PASS")
from validation.v5000_crafting_runtime import run_regression as _v5000_craft_real
print(f"v5.00.0 NOWE RECEPTURY SQLITE: {_v5000_craft_real()} checks PASS")
from validation.v2400_real_quest_events import run_event_coverage as _v5000_event_runtime
_v5000_events = _v5000_event_runtime({k:v for k,v in __import__('server').QUESTS.items() if k.startswith('v500_')})
assert _v5000_events['accepted_via_handler']==200 and _v5000_events['executed']==163 and not _v5000_events['errors']
print(f"v5.00.0 QUEST SQLITE: {_v5000_events['checks']} checks PASS")
from validation.v5000_ocean_runtime import run_regression as _v5000_ocean_real
print(f"v5.00.0 OCEAN REAL SQLITE: {_v5000_ocean_real()} checks PASS")

# v5.00.1: registration/login/owner code recovery, old e-mail paths disabled.
from validation.v5001_recovery_codes import audit_v5001_recovery_codes as _recovery_v5001
print(f"KODY W GRZE v5.00.1 FULL: {_recovery_v5001()} checks PASS")

# v5.00.1: list only skills currently eligible to be learned.
from validation.v5001_learn_available import audit_v5001_learn_available as _learn_available_v5001
print(f"LEARN DOSTEPNE v5.00.1 FULL: {_learn_available_v5001()} checks PASS")

# v6.00.1: all eight full 120-stage journeys; real action/tier, SQLite, NPC tests.
from validation.v601_profession_paths import run_regression as _v601_paths
print(f"DROGA MISTRZA 8x120 v6.00.1: {_v601_paths()} checks PASS")

# v7.00.0: native story, all profession mastery, project/material and SQLite regression.
from validation.v700_living_empire import run_regression as _v700_regression
print(f"ZYWIĄCE IMPERIUM v7.00.0: {_v700_regression()} checks PASS")
# v7.10.0: verify all 64 mentor prerequisites and fail-closed atomic transactions.
from validation.v710_quality_polish import run_regression as _v710_regression
print(f"WIELKI SZLIF IMPERIUM v7.10.0: {_v710_regression()} checks PASS")
# v7.10.1: isolated SQLite class migration, single-class XP and class equipment.
from validation.v71101_single_class import run_regression as _v71101_single_class
print(f'JEDNA KLASA v7.10.1: {_v71101_single_class()} checks PASS')

# v8.00.0: 14x120 native class sagas, NPC/quest/SQLite/reward checks.
from validation.v800_class_sagas import run_regression as _v800_paths
print(f"DROGA LEGENDY 14x120 v8.00.0 FULL: {_v800_paths()} checks PASS")

# v9.00.0: eight new classes/races and Soul Weapons, 960 quests, SQLite.
from validation.v900_heroes import run_regression as _v900_heroes
print(f"NOWI BOHATEROWIE v9.00.0: {_v900_heroes()} checks PASS")
from validation.v1000_horizons import run_regression as _v1000_horizons
print(f"ZAPOMNIANE HORYZONTY v10.00.0: {_v1000_horizons()} checks PASS")
from validation.v1100_fame_multicap import run_regression as _v1100_fame
from validation.v1100_eternal_glory import run_regression as _v1100_world
print(f"FAME v11: {_v1100_fame()} checks PASS")
from validation.v1802_fame_expansion import run_regression as _v1100_fame_targets
_v1100_scope = _v1100_fame_targets()
assert _v1100_scope['targets'] >= 500 and _v1100_scope['pending_payout_once']
print(f"FAME 6.0 CELE: {_v1100_scope['targets']} waznych celow, normalne moby BEZ FAME PASS")
print(f"NOWY SWIAT v11: {_v1100_world()} checks PASS")

from systems.eternal_glory_companions_v1100 import run_regression as _v1100_companions
print(f'NAJEMNICY I PRZYWOLANIA v11: {_v1100_companions()} checks PASS')
from validation.v1100_worldcraft_depths import run_regression as _v1100_content_checks
print(f"PODZIEMIA, RZEMIOSLO, OCEAN v11: {_v1100_content_checks()} checks PASS")

# V11 additional real-class/elemental skill validation
from core.class_mastery_v1100 import run_regression as _v1100_classes_regression
print(f"KLASY 22 / ZYWIOLOWA SYNERGIA v11: {_v1100_classes_regression()} checks PASS")

from validation.v1100_guild_tactics import run_regression as _v1100_guild_regression
print(f"GILDIE 7.0 BUDYNKI SQLITE v11: {_v1100_guild_regression()} checks PASS")
from validation.v1101_quests_mercenaries import run_regression as _v1101_class_mercenaries
print(f"QUESTY GILDYJNE 22 KLAS / DROGA LEGENDY ETAP 2 / 22 NAJEMNIKOW v11.00.1: {_v1101_class_mercenaries()} checks PASS")
from validation.v1103_help_global import run_regression as _global_help_1103
print(f"GLOBAL HELP v11.00.3: {_global_help_1103()} checks PASS")
from validation.v1104_tools_board import run_regression as _tools_board_1104
print(f"NARZEDZIA 22 / TABLICA GILDII v11.00.4: {_tools_board_1104()} checks PASS")
from validation.v1105_profession_soul import run_regression as _profession_soul_1105
print(f"PROFESJE BEZ SOUL XP v11.00.5: {_profession_soul_1105()} checks PASS")
from validation.v1106_readable_commands import run_regression as _readable_commands_1106
print(f"PROSTE KOMENDY v11.00.6: {_readable_commands_1106()} checks PASS")
from validation.v1107_global_commands_help import run_regression as _global_commands_help_1107
print(f"GLOBALNE KOMENDY / HELP v11.00.7: {_global_commands_help_1107()} checks PASS")

from validation.v1108_wood_planks import run_regression as _wood_planks_1108
print(f"DESKI / DRWALSTWO v11.00.8: {_wood_planks_1108()} checks PASS")
from validation.v1109_quest_progress_visibility import run_regression as _quest_visibility_1109
print(f"POSTEP QUESTOW v11.00.9: {_quest_visibility_1109()} checks PASS")

# v11.00.20: 57 high-level minions, class restriction, persistence, level gates.
from validation.v1120_high_class_minions import run_regression as _v1120_high_minions
print(f"LEGENDARNE MINIONY KLAS 200/400/600 v11.00.20: {_v1120_high_minions()} checks PASS")

# v11.00.19: actual summon persistence, class coverage, full HP and death guards.
from validation.v1119_class_minions_and_guards import run_regression as _v1119_guards
print(f"MINIONY 22 KLAS / LECZENIE / TELEPORT v11.00.19: {_v1119_guards()} checks PASS")
from validation.v1119_party_bounty import run_regression as _v1119_party_bounty
print(f"BOUNTY DLA DRUZYNY v11.00.19: {_v1119_party_bounty()} checks PASS")

# v12: actual SQLite inventory/wallet/XP rollback; autonomous class decisions.
from validation.v1200_ai_professions import run_regression as _v1200_ai_professions
print(f'V12 AI 22 KLAS / JAMMER / 22 PROFESJE: {_v1200_ai_professions()} checks PASS')
from validation.v1201_profession_pacing_board import run_regression as _v1201_professions
print(f'V12.00.1 EXP PROFESJE / NARZEDZIA / TABLICA: {_v1201_professions()} checks PASS')
from validation.v1201_xp_chat import run_regression as _v1201_xp_chat
print(f'V12.00.1 KANAL ROZMOW XP: {_v1201_xp_chat()} checks PASS')
from validation.v1201_world_fame import run_regression as _v1201_world_fame
print(f'V12.00.1 CALY SWIAT FAME: {_v1201_world_fame()} checks PASS')
from validation.v1201_crypt_balancing import run_regression as _v1201_crypt
print(f'V12.00.1 KRYPTA / EXP / FAME: {_v1201_crypt()} checks PASS')

# v12.00.2: real stages of Crypt / Giants / Astral Towers / Magitek.
from validation.v1202_dungeon_endgame import run_regression as _v1202_dungeons
print(f"V12.00.2 KRYPTY / WIEZE / LOCHY: {_v1202_dungeons()} checks PASS")

# v12.00.2 HOTFIX: jewelry crafts and cutting gem XP, pliers and material tiers.
from validation.v1203_all_professions_quests import run_regression as _v1203_professions
print(f"V12.00.3 WSZYSTKIE 22 PROFESJE, NARZEDZIA I 2221 QUESTOW: {_v1203_professions()} checks PASS")
from validation.v1204_news_channel import run_regression as _v1204_news
print(f"V12.00.4 KANAL NEWS: {_v1204_news()} checks PASS")
from validation.v1204_live_content import run_regression as _v1204_live
print(f"V12.00.4 HOT RELOAD SWIATA / SQLITE: {_v1204_live()} checks PASS")
from validation.v1205_full_olc import run_regression as _v1205_olc
print(f"V12.00.5 PELNY EDYTOR OLC / PUBLIKACJA: {_v1205_olc()} checks PASS")
from validation.v1206_live_progression_qol import run_regression as _v1206_live_qol
print(f"V12.00.6 OLC PROFESJE / NARZEDZIA / SKILLE / REPLY / LOOK / KONIEC WALKI: {_v1206_live_qol()} checks PASS")
from validation.v1207_resource_live_olc import run_regression as _v1207_resource_live
print(f"V12.00.7 INDYWIDUALNE EXP SUROWCOW / IMPORT JSON / COFANIE: {_v1207_resource_live()} checks PASS")
from validation.v1208_sound_events import run_regression as _v1208_sound
print(f"V12.00.8 SOUND EVENT / BANK / CAP / HP / PLAYER / TELL: {_v1208_sound()} checks PASS")
from validation.v1209_quest_news_olc import run_regression as _v1209_quest_news
print(f"V12.00.9 QUESTY / EXP / NEWS OLC: {_v1209_quest_news()} checks PASS")
from validation.v1209_profession_quest_olc import run_regression as _v1209_professions_olc
print(f"V12.00.9 QUESTY 22 PROFESJI / EXP / NARZĘDZIA: {_v1209_professions_olc()} checks PASS")
from validation.v1202_jewelcraft_xp import run_regression as _v1202_jewelcraft
print(f"V12.00.2 JUBILERSTWO / SZLIFOWANIE / SZCZYPCE: {_v1202_jewelcraft()} checks PASS")

from validation.v12010_live_reward_modes import run_regression as _v12010_modes
print(f"V12.00.10 AUTO/RECZNE NAGRODY/OBNIZANIE: {_v12010_modes()} checks PASS")

from validation.v12010_edit_preview import run_regression as _v12010_preview
print(f"V12.00.10 PODGLAD POL EDYCJI: {_v12010_preview()} checks PASS")
from validation.v12011_olc4_catalog import run_regression as _v12011_olc4
print(f"V12.00.11 OLC4 KATALOGI/SKLEPY/NPC: {_v12011_olc4()} checks PASS")
from validation.v12012_olc4_boss_phases import run as _v12012_bosses
print(f"V12.00.12 OLC4 NOWE BOSSY/FAZY/COFANIE: {_v12012_bosses()} checks PASS")
from validation.v12013_new_skills_olc import run as _v12013_skills
print(f"V12.00.13 OLC4 NOWE SKILLE KLAS I BEZPIECZNY HOT RELOAD: {_v12013_skills()} checks PASS")

from validation.v12100_big_olc import run as _v12100_big_olc
print(f'V12.10.0 WIELKIE OLC 4.0: {_v12100_big_olc()} checks PASS')
from validation.v1300_olc5_world import run as _v1300_olc5
print(f'V13.00.0 OLC5 IMPERIUM ZYWEGO SWIATA: {_v1300_olc5()} checks PASS')

from validation.v1310_existing_skill_editor import run as _v1310_edit_skills
print(f'V13.10.0 EDYCJA ISTNIEJACYCH SKILLI / OLC6: {_v1310_edit_skills()} checks PASS')
from validation.v1400_olc7_world_master import run as _v1400_olc7
print(f'V14.00.0 OLC7 WLADCA SWIATA: {_v1400_olc7()} checks PASS')

# v15 OLC8 — retained historical systems plus new data-only runtime features.
from validation.v1500_olc8_world import run as _v1500_olc8
print(f'V15.00.0 OLC8 / SKILLE / BOSS / QUEST / EQ / PROF / BALANS / NPC / PANEL: {_v1500_olc8()} checks PASS')

from validation.v1520_olc10_passive_and_boss import run as _v1520_olc10
print(f"V15.20.0 OLC10 / PASYWNE BOOSTY I PRIORYTET BOSSOW: {_v1520_olc10()} checks PASS")
from validation.v1530_olc11_boss_guardians import run as _v1530_olc11
print(f"V15.30.0 OLC11 / FALE POMOCNIKOW BOSSOW: {_v1530_olc11()} checks PASS")
from validation.v1510_olc9_runtime import run as _v1510_olc9
print(f"V15.10.0 OLC9 / SKILLE / BOSS ELEMENTY / RECEPTURY: {_v1510_olc9()} checks PASS")

# v15.40.0: ordinary boss guardian EXP/currency and OLC revision safety.
from validation.v1540_olc12_guardian_rewards import run as _v1540_olc12
print(f'V15.40.0 OLC12 / NAGRODY POMOCNIKOW: {_v1540_olc12()} checks PASS')

# v16.00.0 — full audit includes OLC mass edit, persistence and guards.
from validation.v1600_olc13_mass_editor import run as _v1600_mass_olc
print(f'V16.00.0 OLC13 / OPERACJE GRUPOWE: {_v1600_mass_olc()} checks PASS')


# v17.00.0 OLC14: multiple quest prerequisites and bounded existing craft/item batches.

# v18.00.0 OLC15: multi-objective kill+talk+collect, SQLite persistence and regressions.
from validation.v1800_multi_objective_quests import run as _v1800_multigoal
print(f"V18.00.0 OLC15 / WIELOCELOWE QUESTY: {_v1800_multigoal()} checks PASS")

from validation.v1700_olc14_dependencies_crafting import run as _v1700_olc14
print(f"V17.00.0 OLC14 / WIELE QUESTOW / RECEPTURY / PRZEDMIOTY: {_v1700_olc14()} checks PASS")

# Soulbound v19.00.0: isolated real status turn engine + OLC chance validators.
from validation.v1900_olc_status_skills import run as _v1900_status_run
print(f"V19.00.0 OLC16 / SKILLE STATUSY: {_v1900_status_run()} checks PASS")

# v20.00.0 OLC17: validated staged tactical boss profiles and configurable on-hit DOT.
from validation.v2000_olc17_phase_tactics import run as _v2000_phase_tactics
print(f'V20.00.0 OLC17 / FAZY BOSSOW I EFEKTY SKILLI: {_v2000_phase_tactics()} checks PASS')
from validation.v2000_olc17_sqlite import run as _v2000_olc_sqlite
print(f'V20.00.0 OLC17 / SQLITE / AUTO / OCHRONA UOSS: {_v2000_olc_sqlite()} checks PASS')

# v21.00.0 / OLC18: 9 phase strategy controls, direct AI paths, SQLite persist/undo.
from validation.v2100_olc18_phase_strategy import run as _v2100_strategy
print(f'V21.00.0 OLC18 / TAKTYKI FAZOWE BOSSOW: {_v2100_strategy()} checks PASS')
# v22.00.0 / OLC19–26: eight-domain controls, real runtime reward/event/AI paths, SQLite undo.
from validation.v2200_olc26_empire import run as _v2200_grand
print(f'V22.00.0 OLC19-26 / WIELKI OLC 8 SYSTEMOW: {_v2200_grand()} checks PASS')
from validation.v2300_olc27_growth import run as _v2300_growth
print(f'V23.00.0 OLC27 / MULTI CAP PRZYWOLANIA EVENTY: {_v2300_growth()} checks PASS')
from validation.v35004_uoss_source_hp import run as _v35004_uoss_hp
print(f'V35.00.4 SOURCE UOSS HP / GLOBAL HP OCHRONA: {_v35004_uoss_hp()} checks PASS')
from validation.v2400_olc28_35 import run as _v2400_revolution
print(f'V24.00.0 OLC28-35 / 8 OBSZAROW + SQLITE: {_v2400_revolution()} checks PASS')
from validation.v2401_quest_gold_olc import run as _v2401_quest_gold
print(f'V24.00.1 QUEST GOLD OLC / WYPLATY I RESTART: {_v2401_quest_gold()} checks PASS')

# v25.00.0 OLC36-43: atomic workflows, UOSS rewards, events, regeneration, 80 cap steps.
from validation.v2500_olc36_43 import run as _v2500_empire
print(f'V25.00.0 OLC36-43 / IMPERIUM KONTROLI: {_v2500_empire()} checks PASS')
from validation.v2600_olc44_51 import run as _v2600_empire
print(f'V26.00.0 OLC44-51 / OSIEM OBSZAROW: {_v2600_empire()} checks PASS')
from validation.v2700_olc52_59 import run as _v2700_master
print(f'V27.00.0 OLC52-59 / OSIEM OBSZAROW: {_v2700_master()} checks PASS')

# v28 / OLC60-67: data-only rules + eight runtime consumers, SQLite revision.
from validation.v2800_olc60_67 import run as _v2800_expansion
print(f'V28.00.0 OLC60-67 / OSIEM OBSZAROW: {_v2800_expansion()} checks PASS')

# v28: numerowana lista NEWS i odczyt jednego artykulu.
from validation.v2800_news_read import run as _v28_news_read
print(f'V28 NEWS READ: {_v28_news_read()} checks PASS')

# v29 / OLC68-75 — eight creation workflows, persisted revisions and real runtime integration.
from validation.v2900_olc68_75 import run as _v2900_creation
print(f'V29.00.0 OLC68-75 / 8 SYSTEMOW: {_v2900_creation()} checks PASS')

# v29.10: odswiezanie expowisk po level-up, dobieranie poziomu i NVDA.
from validation.v2910_dynamic_exp_areas import run as _v2910_exp_refresh
print(f'V29.10.0 DYNAMICZNE EXPOWISKA / LEVEL UP: {_v2910_exp_refresh()} checks PASS')

# v30: prawdziwe krainy 401-800 + fazy UOSS i moc nowych summonow.
from validation.v3000_world_olc import run as _v3000_world
print(f'V30.00.0 KRAINY 401-800 + OLC: {_v3000_world()} checks PASS')

# v31.00.0: realne cztery kroniki endgame 401-800, 24 zadania, NPC i EXP.
from validation.v3100_chronicles_401_800 import run as _v3100_chronicles
print(f'V31.00.0 CZTERY KRONIKI 401-800: {_v3100_chronicles()} checks PASS')

# v32: OLC76–83, 8 runtime integrations, SQLite rollback and editor safety.
from validation.v3200_olc76_83 import run as _v3200_olc
print(f'V32.00.0 OLC76-83 / 8 SYSTEMOW: {_v3200_olc()} checks PASS')

# Soulbound v33.00.0 — osiem realnych integracji mechaniki i ich transakcje OLC.
from validation.v3300_olc84_91 import run as _v3300_olc
print(f'V33.00.0 OLC84-91 / 8 MECHANIK: {_v3300_olc()} checks PASS')

# Soulbound v34.00.0 — osiem działających integracji OLC 92–99.
from validation.v3400_integration import run as _v3400_integration
print(f'V34.00.0 OLC92-99 / 8 INTEGRACJI: {_v3400_integration()} checks PASS')

# Soulbound v35.00.0 — four integrated endgame systems, transactional SQLite.
from validation.v3500_four_systems import run as _v3500_four_systems
print(f'V35.00.0 CZTERY SYSTEMY / OLC100-103: {_v3500_four_systems()} checks PASS')

# v35.00.5 owner-only emergency combat tools.
from validation.v35005_admin_guardian import run as _v35005_admin_guardian
print(f'V35.00.5 ADMIN GUARDIAN GOD / CIOSY: {_v35005_admin_guardian()} checks PASS')

# v36 Admin Guardian 2.0: delegated read-only roles, zero-reward arena, cautious quest repair.
from validation.v3600_admin_guardian2 import run as _v3600_guardian
print(f'V36.00.0 ADMIN GUARDIAN 2.0: {_v3600_guardian()} checks PASS')

# v36.00.1 - numeric error ID triage and deliberately conservative quest repair.
from validation.v36001_error_quest_recovery import run as _v36001_quest_error
print(f'V36.00.1 ADMIN BLAD NUMER / QUESTY: {_v36001_quest_error()} checks PASS')

# v36.00.2: no-write evidence for quest completion, mobs, NPC and inventory.
from validation.v36002_quest_evidence import run as _v36002_quest_evidence
print(f'V36.00.2 ADMIN QUEST TROP / NPC / SKAN: {_v36002_quest_evidence()} checks PASS')

# v37 Guardian 3: seven admin areas, guarded writes and no reward leaks.
from validation.v3700_guardian3 import run as _v3700_guardian3
print(f'V37.00.0 ADMIN GUARDIAN 3: {_v3700_guardian3()} checks PASS')
from validation.v3800_guardian4 import run as _v3800_guardian4
print(f'V38.00.0 ADMIN GUARDIAN 4: {_v3800_guardian4()} checks PASS')

# v39: owner-only Guardian5, six independent quest stat-XP rewards,
# atomic OLC apply/revert and real payout path with per-stat EXP banking.
from validation.v3900_admin_guardian5 import run as _v3900_guardian5
print(f'V39.00.0 ADMIN GUARDIAN 5 / QUEST STAT EXP: {_v3900_guardian5()} checks PASS')

# v40: atomic quest reward batches, owner permissions and read-only OLC/boss diagnostics.
from validation.v4000_admin_guardian6 import run as _v4000_guardian6
print(f'V40.00.0 ADMIN GUARDIAN 6 / QUESTY OLC: {_v4000_guardian6()} checks PASS')

# v41 source-driven private LAB, safe preview and undoable quest corrections.
# v70.00.1: the older Guardian7 suite mutates UOSS catalog fixtures.  Run it
# in its own clean child interpreter, verify its full result and exit status,
# then leave the long shared-runtime audit catalogs untouched.
def _v7001_guardian7_isolated():
    import os as _os, re as _re, socket as _socket, subprocess as _subprocess
    import sys as _sys
    from pathlib import Path as _Path
    with _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM) as _sock:
        _sock.bind(('127.0.0.1', 0))
        _free_port = _sock.getsockname()[1]
    _env = dict(_os.environ)
    _env.update({'SOULBOUND_HOST': '127.0.0.1', 'SOULBOUND_PORT': str(_free_port),
                 'PORT': '', 'RAILWAY_TCP_APPLICATION_PORT': ''})
    _res = _subprocess.run(
        [_sys.executable, '-u', '-m', 'validation.v4100_admin_guardian7'],
        cwd=str(_Path(__file__).resolve().parent), env=_env,
        stdin=_subprocess.DEVNULL, capture_output=True, text=True,
        encoding='utf-8', errors='replace', timeout=180,
    )
    _text = (_res.stdout + '\n' + _res.stderr).strip()
    _match = _re.search(r'GUARDIAN7 v41:\s*(\d+)\s+checks PASS', _text)
    if _res.returncode or not _match or int(_match.group(1)) < 90:
        raise AssertionError('Guardian7 isolated regression FAIL: ' + _text[-3000:])
    return int(_match.group(1))
print(f'V41.00.0 ADMIN GUARDIAN 7 / UOSS LAB I QUESTY: {_v7001_guardian7_isolated()} checks PASS')

# v70.00.1: fully execute Guardian/Admin Live v42-v60 in a clean
# interpreter, avoiding mutations from legacy OLC fixtures earlier in this
# monolithic historical audit.  Exit and representative markers are mandatory.
_V7001_MIDDLE_ADMIN_SUITE = '# Guardian 8.0 isolated simulator + atomic mult-quest DRAFT regressions.\nfrom validation.v4200_admin_guardian8 import run as _v4200_admin_guardian8_check\nprint(f"V42.00.0 ADMIN GUARDIAN 8: {_v4200_admin_guardian8_check()} checks PASS")\nfrom validation.v4300_admin_guardian9 import run as _v4300_admin_guardian9_check\nprint(f"V43.00.0 ADMIN GUARDIAN 9: {_v4300_admin_guardian9_check()} checks PASS")\nfrom validation.v4400_admin_guardian10 import run as _v4400_admin_guardian10_check\nprint(f"V44.00.0 ADMIN GUARDIAN 10: {_v4400_admin_guardian10_check()} checks PASS")\nfrom validation.v4500_admin_guardian11 import run as _v4500_admin_guardian11_check\nprint(f"V45.00.0 ADMIN GUARDIAN 11: {_v4500_admin_guardian11_check()} checks PASS")\nfrom validation.v4500_admin_live_bridge import run as _v4500_admin_live_bridge_check\nprint(f"V45.00.0 ADMIN LIVE BRIDGE: {_v4500_admin_live_bridge_check()} checks PASS")\nfrom validation.v4600_admin_live_ultimate import run as _v4600_admin_live_ultimate_check\nprint(f"V46.00.0 ADMIN LIVE ULTIMATE: {_v4600_admin_live_ultimate_check()} checks PASS")\nfrom validation.v4700_admin_live_release import run as _v4700_admin_live_release_check\nprint(f"V47.00.0 ADMIN LIVE SAFETY: {_v4700_admin_live_release_check()} checks PASS")\nfrom validation.v4800_admin_live_expansion import run as _v4800_admin_live_expansion_check\nprint(f"V48.00.0 ADMIN LIVE ROZSZERZENIA: {_v4800_admin_live_expansion_check()} checks PASS")\nfrom validation.v4900_admin_live_integrity import run as _v4900_admin_live_integrity_check\nprint(f"V49.00.0 ADMIN LIVE AUDYT QUESTOW LAB: {_v4900_admin_live_integrity_check()} checks PASS")\n\n# v50 Admin Live complete: safe DRAFT correction, graph SCCs and isolated LAB.\nfrom validation.v5000_admin_live_final import run as _v5000_admin_live_final_check\nprint(f"V50.00.0 ADMIN LIVE KOREKTY QUESTOW: {_v5000_admin_live_final_check()} checks PASS")\n\n# v51 Admin Live: canonical quest transactions, 22-class isolated laboratory.\nfrom validation.v5100_admin_live_complete import run as _v5100_admin_live_complete_check\nprint(f"V51 ADMIN LIVE ULTIMATE: {_v5100_admin_live_complete_check()} checks PASS")\nfrom validation.v5200_admin_live_level_caps import run as _v5200_admin_live_caps_check\n_v5200_admin_live_caps_check()\nfrom validation.v5200_admin_live_eq_caps import run as _v5200_admin_live_eq_caps_check\n_v5200_admin_live_eq_caps_check()\nfrom validation.v5300_eq_growth import run as _v5300_admin_live_eq_growth_check\n_v5300_admin_live_eq_growth_check()\n\n# v54: one read-only Admin Live final audit, NVDA-friendly commands and owner guards.\nfrom validation.v5400_admin_live_finish import run as _v5400_admin_live_finish_check\nprint(f\'V54 ADMIN LIVE FINISH: {_v5400_admin_live_finish_check()} checks PASS\')\n\n# v55: real >800 crafting loop integration, stable nested craftq IDs, owner-only read-only preview.\nfrom validation.v5500_endless_crafting import run as _v5500_endless_crafting\nprint(f\'V55 RZEMIOSLO EQ >800: {_v5500_endless_crafting()} checks PASS\')\n\n# v56: verify actual normal mob equipment drop integration and NVDA preview.\nfrom validation.v5600_endless_loot import run as _v5600_endless_loot\nprint(f\'V56 GLEBINOWY ZWYKLY DROP: {_v5600_endless_loot()} checks PASS\')\n\n# v57 actual post-roll chest rewards and owner-only read-only forecast.\nfrom validation.v5700_boss_chests import run as _v5700_chest_run\nprint(f\'V57 BOSS CHESTS: {_v5700_chest_run()} checks PASS\')\n\n# v58 chest equipment + quest item catalogue, read-only checks.\nfrom validation.v5800_chest_equipment import run as _v5800_run\nprint(f"V58 EQ SKRZYNIE/QUESTY: {_v5800_run()} checks PASS")\n\n# v59: world-level post-800 EQ + owner-approved dependency replacement in OLC DRAFT.\nfrom validation.v5900_world_quest_dependencies import run as _v5900_run\nprint(f"V59 EQ SWIAT/ZAMIAN ZALEZNOSCI: {_v5900_run()} checks PASS")\n\n# v60: typed item / target quest-ID repairs, owner-only transactional OLC DRAFT.\nfrom validation.v6000_quest_id_repairs import run as _v6000_run\nprint(f"V60 QUEST ID DRAFT REPAIRS: {_v6000_run()} checks PASS")\n\n'
def _v7001_isolated_middle_admin_suites():
    import os as _os, socket as _socket, subprocess as _subprocess
    import sys as _sys
    from pathlib import Path as _Path
    with _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM) as _sock:
        _sock.bind(('127.0.0.1', 0))
        _free_port = _sock.getsockname()[1]
    _env = dict(_os.environ)
    _env.update({'SOULBOUND_HOST':'127.0.0.1','SOULBOUND_PORT':str(_free_port),
                 'PORT':'','RAILWAY_TCP_APPLICATION_PORT':''})
    _result = _subprocess.run(
        [_sys.executable,'-u','-c',_V7001_MIDDLE_ADMIN_SUITE],
        cwd=str(_Path(__file__).resolve().parent),env=_env,
        stdin=_subprocess.DEVNULL,capture_output=True,text=True,
        encoding='utf-8',errors='replace',timeout=240,
    )
    _output = (_result.stdout+'\n'+_result.stderr).strip()
    _required = ('V42.00.0 ADMIN GUARDIAN 8: 68 checks PASS',
                 'V45.00.0 ADMIN LIVE BRIDGE: 35 checks PASS',
                 'V50.00.0 ADMIN LIVE KOREKTY QUESTOW: 104 checks PASS',
                 'V59 EQ SWIAT/ZAMIAN ZALEZNOSCI: 110 checks PASS',
                 'V60 QUEST ID DRAFT REPAIRS: 105 checks PASS')
    if _result.returncode != 0 or not all(x in _output for x in _required):
        raise AssertionError('Guardian v42-v60 isolated regressions FAIL: '+_output[-4500:])
    print(_result.stdout.strip(),flush=True)
    return len(_required)
print(f'ADMIN LIVE v42-v60: {_v7001_isolated_middle_admin_suites()} wymaganych kontroli PASS',flush=True)
# v70.00.1: earlier OLC suites mutate global QUESTS/MOBS fixtures in the
# monolithic historical predeploy interpreter.  The v61-v70 contract is still
# fully executed; a child process guarantees clean authored catalogs, and both
# its exit code and final marker are verified fail-closed.
_V7001_FULL_LATE_SUITE = '# v61: NPC, resource and multi-objective repairs with atomic OLC DRAFT checks.\nfrom validation.v6100_quest_refs import run as _v6100_run\nprint(f"V61 QUEST REFS NPC RESOURCE OBJECTIVES: {_v6100_run()} checks PASS")\n\n# v62: consolidated multi-mode OLC changes, quest EQ and mastery-cap audit.\nfrom validation.v6200_admin_live_bundle import run as _v6200_run\nprint(f"V62 LIVE BUNDLE QUEST EQ SKILLS: {_v6200_run()} checks PASS")\n\n# v63: combined scalar/ID quest OLC transactions and cap-aware lab progression.\nfrom validation.v6300_admin_live_cap_bundle import run as _v6300_run\nprint(f"V63 ADMIN LIVE QUEST BUNDLE CLASS MASTERY: {_v6300_run()} checks PASS")\n\n# v64: atomic linked quest objective/count repairs and admin NVDA commands.\nfrom validation.v6400_admin_live_atomic_quest_goals import run as _v6400_run\nprint(f"V64 ADMIN LIVE ATOMIC QUEST GOALS: {_v6400_run()} checks PASS")\n\n# v65: real UOSS status immunity under private LAB gear and helper passives.\nfrom validation.v6500_admin_live_uoss_source_equipment import run as _v6500_run\nprint(f"V65 ADMIN LIVE UOSS SOURCE EQ: {_v6500_run()} checks PASS")\n\n# v66: real sourced UOSS helper decisions in isolated Admin Live preview.\nfrom validation.v6600_admin_live_uoss_helper_source import run as _v6600_run\nprint(f"V66 ADMIN LIVE UOSS SOURCE HELPERS: {_v6600_run()} checks PASS")\n\n# v67: deterministic source-balanced helper support on detached Admin Live arena.\nfrom validation.v6700_admin_live_uoss_helper_support import run as _v6700_run\nprint(f"V67 ADMIN LIVE UOSS HELPER SUPPORT: {_v6700_run()} checks PASS")\n\n# v68: exact helper party target selection on detached Admin Live arena.\nfrom validation.v6800_admin_live_uoss_party_support import run as _v6800_run\nprint(f"V68 ADMIN LIVE UOSS PARTY SUPPORT: {_v6800_run()} checks PASS")\n\n# v69 Admin Live read-only operator controls.\nfrom validation.v6900_admin_live_centrum import run as _v69_run\nprint(f"V69 ADMIN LIVE: {_v69_run()} checks PASS")\n\n# v70 Admin Live read-only operator controls.\nfrom validation.v7000_admin_live_odbior import run as _v70_run\nprint(f"V70 ADMIN LIVE: {_v70_run()} checks PASS")\n'
def _v7001_isolated_final_admin_suites():
    import os as _os, re as _re, socket as _socket, subprocess as _subprocess
    import sys as _sys
    from pathlib import Path as _Path
    with _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM) as _sock:
        _sock.bind(('127.0.0.1', 0))
        _free_port = _sock.getsockname()[1]
    _env = dict(_os.environ)
    _env.update({'SOULBOUND_HOST': '127.0.0.1', 'SOULBOUND_PORT': str(_free_port),
                 'PORT': '', 'RAILWAY_TCP_APPLICATION_PORT': ''})
    _res = _subprocess.run(
        [_sys.executable, '-u', '-c', _V7001_FULL_LATE_SUITE],
        cwd=str(_Path(__file__).resolve().parent), env=_env,
        stdin=_subprocess.DEVNULL, capture_output=True, text=True,
        encoding='utf-8', errors='replace', timeout=180,
    )
    _text = (_res.stdout+'\n'+_res.stderr).strip()
    _expected = ('V61 QUEST REFS NPC RESOURCE OBJECTIVES: 128 checks PASS',
                 'V62 LIVE BUNDLE QUEST EQ SKILLS: 103 checks PASS',
                 'V63 ADMIN LIVE QUEST BUNDLE CLASS MASTERY: 74 checks PASS',
                 'V64 ADMIN LIVE ATOMIC QUEST GOALS: 82 checks PASS',
                 'V65 ADMIN LIVE UOSS SOURCE EQ: 69 checks PASS',
                 'V66 ADMIN LIVE UOSS SOURCE HELPERS: 73 checks PASS',
                 'V67 ADMIN LIVE UOSS HELPER SUPPORT: 65 checks PASS',
                 'V68 ADMIN LIVE UOSS PARTY SUPPORT: 86 checks PASS',
                 'V69 ADMIN LIVE: 43 checks PASS',
                 'V70 ADMIN LIVE: 38 checks PASS')
    if _res.returncode != 0 or not all(item in _text for item in _expected):
        raise AssertionError('Admin Live v61-v70 isolated regressions FAIL: '+_text[-4000:])
    print(_res.stdout.strip(),flush=True)
    return len(_expected)
print(f'ADMIN LIVE v61-v70: {_v7001_isolated_final_admin_suites()} zestawow PASS',flush=True)

# v70.00.2: fail-closed three-gap Admin Live regression on a clean interpreter.
# Older audit suites may alter global catalog fixtures; keep the new proof isolated.
def _v7002_three_gap_gate():
    import subprocess as _sb_subprocess,sys as _sb_sys
    from pathlib import Path as _sb_Path
    _result=_sb_subprocess.run(
        [_sb_sys.executable,'-u','-m','validation.v7002_admin_live_three_gaps'],
        cwd=str(_sb_Path(__file__).resolve().parent),
        stdin=_sb_subprocess.DEVNULL,capture_output=True,text=True,
        encoding='utf-8',errors='replace',timeout=180)
    _out=(_result.stdout+'\n'+_result.stderr).strip()
    if _result.returncode!=0 or 'V70.00.2 THREE GAPS: 141 PASS' not in _out:
        raise AssertionError('Admin Live v70.00.2 failed: '+_out[-3500:])
    print(_result.stdout.strip(),flush=True)
    return 141
print(f'ADMIN LIVE v70.00.2: {_v7002_three_gap_gate()} checks PASS',flush=True)

# v70.00.3: independent, fail-closed regression for shop progression, skill
# editing and cap-aware validators. Never writes a real player database.
def _v7003_extension_gate():
    import subprocess as _sb_subprocess, sys as _sb_sys
    from pathlib import Path as _sb_Path
    _result = _sb_subprocess.run(
        [_sb_sys.executable, '-u', '-m', 'validation.v7003_admin_live_extensions'],
        cwd=str(_sb_Path(__file__).resolve().parent),
        stdin=_sb_subprocess.DEVNULL, capture_output=True, text=True,
        encoding='utf-8', errors='replace', timeout=180)
    _out = (_result.stdout + '\n' + _result.stderr).strip()
    if _result.returncode != 0 or 'V70.00.3 ADMIN LIVE: 70 PASS' not in _out:
        raise AssertionError('Admin Live v70.00.3 failed: ' + _out[-3500:])
    print(_result.stdout.strip(), flush=True)
    return 70
print(f'ADMIN LIVE v70.00.3: {_v7003_extension_gate()} checks PASS', flush=True)



# v71: eight-area administrative regression, independent of the player database.
def _v7100_gate():
    import subprocess as _sb_subprocess,sys as _sb_sys
    from pathlib import Path as _sb_Path
    result=_sb_subprocess.run(
        [_sb_sys.executable,'-u','-m','validation.v7100_admin_live_eight_areas'],
        cwd=str(_sb_Path(__file__).resolve().parent),
        stdin=_sb_subprocess.DEVNULL,capture_output=True,text=True,
        encoding='utf-8',errors='replace',timeout=180)
    output=(result.stdout+'\n'+result.stderr).strip()
    if result.returncode!=0 or 'V71.00.0 EIGHT AREAS: 75 PASS' not in output:
        raise AssertionError('Admin Live v71 failed: '+output[-3500:])
    print(result.stdout.strip(),flush=True)
    return 75
print(f'ADMIN LIVE v71.00.0: {_v7100_gate()} checks PASS',flush=True)


# v73: final-graph multiquest edits, multistage boss edits and scripted UOSS protection.
def _v7300_gate():
    import subprocess as _sp, sys as _sys
    from pathlib import Path as _Path
    result=_sp.run([_sys.executable,'-u','-m','validation.v7300_admin_live_quest_boss_batches'],
        cwd=str(_Path(__file__).resolve().parent),stdin=_sp.DEVNULL,
        capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
    output=(result.stdout+'\n'+result.stderr).strip()
    if result.returncode!=0 or 'V73.00.0 QUEST BOSS BATCHES: 73 PASS' not in output:
        raise AssertionError('Admin Live v73 failed: '+output[-4000:])
    print(result.stdout.strip(),flush=True)
    return 73
print(f'ADMIN LIVE v73.00.0: {_v7300_gate()} checks PASS',flush=True)


# v74: safe legacy quest parent edits and source UOSS inspections; fail closed.
def _v7400_gate():
    import subprocess as _sp, sys as _sys
    from pathlib import Path as _Path
    result=_sp.run([_sys.executable,'-u','-m','validation.v7400_admin_live_legacy_dependencies_uoss'],
        cwd=str(_Path(__file__).resolve().parent),stdin=_sp.DEVNULL,
        capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
    output=(result.stdout+'\n'+result.stderr).strip()
    if result.returncode!=0 or 'V74.00.0 LEGACY QUEST AND UOSS: 131 PASS' not in output:
        raise AssertionError('Admin Live v74 failed: '+output[-4000:])
    print(result.stdout.strip(),flush=True)
    return 131
print(f'ADMIN LIVE v74.00.0: {_v7400_gate()} checks PASS',flush=True)


# v75: verified actual UOSS runtime hooks, reversibility and quest null shadow.
def _v7500_gate():
    import subprocess as _sp, sys as _sys
    from pathlib import Path as _Path
    result=_sp.run([_sys.executable,'-u','-m','validation.v7500_admin_live_real_mechanics'],
        cwd=str(_Path(__file__).resolve().parent),stdin=_sp.DEVNULL,
        capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
    output=(result.stdout+'\n'+result.stderr).strip()
    if result.returncode!=0 or 'V75.00.0 ADMIN LIVE VERIFIED: 59 PASS' not in output:
        raise AssertionError('Admin Live v75 failed: '+output[-4000:])
    print(result.stdout.strip(),flush=True)
    return 59
print(f'ADMIN LIVE v75.00.0: {_v7500_gate()} checks PASS',flush=True)


# v76: real character creator, saved race, passive and restart SQLite on disposable data.
def _v7600_gate():
    import subprocess as _sp, sys as _sys
    from pathlib import Path as _Path
    result=_sp.run([_sys.executable,'-u','-m','validation.v7600_playable_races'],
        cwd=str(_Path(__file__).resolve().parent),stdin=_sp.DEVNULL,
        capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
    output=(result.stdout+'\n'+result.stderr).strip()
    if result.returncode!=0 or 'V76.00.0 PLAYABLE RACES: 41 PASS' not in output:
        raise AssertionError('v76 real playable races failed: '+output[-4000:])
    print(result.stdout.strip(),flush=True)
    return 35
print(f'ADMIN LIVE v76.00.0: {_v7600_gate()} checks PASS',flush=True)

# v77: external isolated SQLite and creator-class validations (after previous gates).
def _v7700_gate():
    import subprocess as _sp,sys as _sys
    r=_sp.run([_sys.executable,'-u','-m','validation.v7700_playable_classes'],
              capture_output=True,text=True,timeout=180)
    result=(r.stdout+'\n'+r.stderr)
    if r.returncode or 'V77.00.0 PLAYABLE CLASSES:' not in result or ' PASS' not in result:
        raise AssertionError('v77 playable classes failed: '+result[-3500:])
    return result.strip().split(':')[-1].strip()
print('ADMIN LIVE v77.00.0: '+_v7700_gate(),flush=True)

# v78: source damage on detached actual actor; isolated LAB state and RNG.
def _v7800_gate():
    import subprocess as _sp,sys as _sys
    from pathlib import Path as _Path
    r=_sp.run([_sys.executable,'-u','-m','validation.v7800_arena_real_basic_damage'],
              cwd=str(_Path(__file__).resolve().parent),
              capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
    result=(r.stdout+'\n'+r.stderr)
    if r.returncode or 'V78.00.0 REAL SOURCE BASIC ATTACK: 36 PASS' not in result:
        raise AssertionError('v78 detached source damage failed: '+result[-3500:])
    return 36
print(f'ADMIN LIVE v78.00.0: {_v7800_gate()} checks PASS',flush=True)

# v79: real production boss defense on isolated clones, without DB/game effects.
def _v7900_gate():
    import subprocess as _sp,sys as _sys
    from pathlib import Path as _Path
    r=_sp.run([_sys.executable,'-u','-m','validation.v7900_arena_real_defense'],
        cwd=str(_Path(__file__).resolve().parent),stdin=_sp.DEVNULL,
        capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
    result=(r.stdout+'\n'+r.stderr)
    if r.returncode or 'v79 production boss defense: 26 PASS' not in result:
        raise AssertionError('v79 real defense gate failed: '+result[-3500:])
    print(r.stdout.strip(),flush=True)
    return 26
print(f'ADMIN LIVE v79.00.0: {_v7900_gate()} checks PASS',flush=True)


# v80: same critical/weapon hit formulas used by real realtime combat and LAB.
def _v8000_gate():
    import subprocess as _sp,sys as _sys
    from pathlib import Path as _Path
    r=_sp.run([_sys.executable,'-u','-m','validation.v8000_arena_real_weapon'],
        cwd=str(_Path(__file__).resolve().parent),stdin=_sp.DEVNULL,
        capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
    result=(r.stdout+'\n'+r.stderr)
    if r.returncode or 'v80 weapon source parity + isolation: 44 PASS' not in result:
        raise AssertionError('v80 weapon parity gate failed: '+result[-3500:])
    return 44
print(f'ADMIN LIVE v80.00.0: {_v8000_gate()} checks PASS',flush=True)

# v81: production post-hit Echo/lifesteal/mana shared with private arena.
def _v8100_gate():
    import subprocess as _sp, sys as _sys
    from pathlib import Path as _Path
    r=_sp.run([_sys.executable,'-u','-m','validation.v8100_arena_soul_weapon_effects'],
        cwd=str(_Path(__file__).resolve().parent),stdin=_sp.DEVNULL,
        capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
    result=r.stdout+'\n'+r.stderr
    if r.returncode or 'V81 SOURCE POST-HIT EFFECTS AND ISOLATION: 42 PASS' not in result:
        raise AssertionError('v81 source effects failed: '+result[-4000:])
    return 42
print(f'ADMIN LIVE v81.00.0: {_v8100_gate()} checks PASS',flush=True)


# v82: source queue selection parity (normal fight vs read-only LAB).
def _v8200_gate():
    import subprocess as _sp, sys as _sys
    from pathlib import Path as _Path
    r = _sp.run([_sys.executable,'-u','-m','validation.v8200_uoss_queue_source_choice'],
        cwd=str(_Path(__file__).resolve().parent), stdin=_sp.DEVNULL,
        capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=180)
    output = r.stdout+'\n'+r.stderr
    if r.returncode or 'V82 REAL SKILL QUEUE CHOICE + DB ISOLATION: 99 PASS' not in output:
        raise AssertionError('v82 queue choice failed: '+output[-4000:])
    return 99
print(f'ADMIN LIVE v82.00.0: {_v8200_gate()} checks PASS',flush=True)


# v83: isolated actual simple skill casts and safety regression.
def _v8300_gate():
    import subprocess as _sp, sys as _sys
    from pathlib import Path as _Path
    r = _sp.run([_sys.executable,'-u','-m','validation.v8300_arena_plain_skill_cast'],
        cwd=str(_Path(__file__).resolve().parent), stdin=_sp.DEVNULL,
        capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=180)
    output = r.stdout+'\n'+r.stderr
    if r.returncode or 'v83 DETACHED PLAIN SKILL CAST: 37 PASS' not in output:
        raise AssertionError('v83 isolated skill cast failed: '+output[-4000:])
    return 37
print(f'ADMIN LIVE v83.00.0: {_v8300_gate()} checks PASS',flush=True)

# v84: real native runtime clone safety gate; no live gameplay data is modified.
def _v8400_gate():
    import subprocess as _sp, sys as _sys
    from pathlib import Path as _Path
    r=_sp.run([_sys.executable,'-u','-m','validation.v8400_native_full_combat_isolation'],
        cwd=str(_Path(__file__).resolve().parent),stdin=_sp.DEVNULL,
        capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90)
    output=r.stdout+'\n'+r.stderr
    if r.returncode or 'UOSS NATIVE ISOLATION: 41 PASS' not in output:
        raise AssertionError('v84 native isolated full server safety gate FAILED: '+output[-4000:])
    return 41
print(f'UOSS NATIVE V84.00.0: {_v8400_gate()} checks PASS',flush=True)

# v85: actual playable TCP encounter; never uses user DB, only a synthetic
# source and a disposable second native runtime. Fails if a kill isn't durable.
def _v8500_native_tcp_gate():
    import subprocess as _sp, sys as _sys
    from pathlib import Path as _Path
    r = _sp.run([_sys.executable, '-u', '-m', 'validation.v8500_native_tcp_full_journey'],
        cwd=str(_Path(__file__).resolve().parent), stdin=_sp.DEVNULL,
        capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=250)
    output = r.stdout + '\n' + r.stderr
    if r.returncode or 'UOSS FULL TCP & ISOLATION: 10 PASS' not in output:
        raise AssertionError('v85 real TCP/SQLite encounter FAIL: ' + output[-5000:])
    return 10
print(f'UOSS NATIVE TCP v85.00.0: {_v8500_native_tcp_gate()} checks PASS', flush=True)

# v86: owner-only native arena lifecycle on real private TCP server.
# Independent of production DB: uses a temporary synthetic source SQLite.
def _v8600_native_admin_gate():
    import subprocess as _sp, sys as _sys
    from pathlib import Path as _Path
    r = _sp.run([_sys.executable, '-u', '-m', 'validation.v8600_admin_live_native_arena'],
        cwd=str(_Path(__file__).resolve().parent), stdin=_sp.DEVNULL,
        capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=120)
    output = r.stdout + '\n' + r.stderr
    if r.returncode or 'ADMIN LIVE NATIVE UOSS v86: 19 PASS' not in output:
        raise AssertionError('v86 admin live native arena FAIL: ' + output[-4500:])
    return 19
print(f'ADMIN LIVE NATIVE v86.00.0: {_v8600_native_admin_gate()} checks PASS', flush=True)

# v87: atomic whole-quest dependency and multi-scripted-boss native OLC.
def _v8700_big_update_gate():
    import subprocess as _sp, sys as _sys
    from pathlib import Path as _Path
    r=_sp.run([_sys.executable,'-u','-m','validation.v8700_admin_live_large_update'],
        cwd=str(_Path(__file__).resolve().parent),stdin=_sp.DEVNULL,
        capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
    output=r.stdout+'\n'+r.stderr
    if r.returncode or 'ADMIN LIVE v87 BIG UPDATE: 71 PASS' not in output:
        raise AssertionError('v87 Admin Live comprehensive OLC FAIL: '+output[-5000:])
    return 71
print(f'ADMIN LIVE BIG v87.00.0: {_v8700_big_update_gate()} checks PASS',flush=True)

# v87: actual fresh isolated native runtime, no access to production DB.
def _v8700_fresh_tcp_gate():
    import subprocess as _sp, sys as _sys
    from pathlib import Path as _Path
    r=_sp.run([_sys.executable,'-u','-m','validation.v8700_native_fresh_tcp'],
        cwd=str(_Path(__file__).resolve().parent),stdin=_sp.DEVNULL,
        capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
    output=r.stdout+'\n'+r.stderr
    if r.returncode or 'ARENA UOSS FRESH TCP: 9 PASS' not in output:
        raise AssertionError('v87 native fresh real-TCP gate FAILED: '+output[-5000:])
    return 9
print(f'UOSS NATIVE FRESH v87.00.0: {_v8700_fresh_tcp_gate()} checks PASS',flush=True)

# v88: one atomic cross-system plan, no player DB mutation on DRAFT stages.
def _v8800_integrated_gate():
    import subprocess as _sp, sys as _sys
    from pathlib import Path as _Path
    r=_sp.run([_sys.executable,'-u','-m','validation.v8800_admin_live_integrated_release'],
        cwd=str(_Path(__file__).resolve().parent),stdin=_sp.DEVNULL,
        capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
    output=r.stdout+'\n'+r.stderr
    if r.returncode or 'ADMIN LIVE v88 INTEGRATED: 117 PASS' not in output:
        raise AssertionError('v88 Admin Live integrated changeset FAILED: '+output[-4500:])
    return 117
print(f'ADMIN LIVE v88 INTEGRATED: {_v8800_integrated_gate()} checks PASS',flush=True)

# v89: exact runtime publication safety preflight with SQLite invariants.
def _v8900_publication_gate():
    import subprocess as _sp, sys as _sys
    from pathlib import Path as _Path
    r=_sp.run([_sys.executable,'-u','-m','validation.v8900_publication_preflight'],
        cwd=str(_Path(__file__).resolve().parent),stdin=_sp.DEVNULL,
        capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
    output=r.stdout+'\n'+r.stderr
    if r.returncode or 'ADMIN LIVE v89 PREFLIGHT: 46 PASS' not in output:
        raise AssertionError('v89 safe publication preflight FAILED: '+output[-5000:])
    return 46
print(f'ADMIN LIVE v89 PUBLICATION: {_v8900_publication_gate()} checks PASS',flush=True)

# v90: durable revision history, DRAFT-only recovery, conflict-safe publication.
def _v9000_recovery_gate():
    import subprocess as _sp, sys as _sys
    from pathlib import Path as _Path
    result=_sp.run([_sys.executable,'-u','-m','validation.v9000_revision_recovery'],
        cwd=str(_Path(__file__).resolve().parent),stdin=_sp.DEVNULL,
        capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=150)
    output=result.stdout+'\n'+result.stderr
    if result.returncode or 'ADMIN LIVE v90 REWIZJE: 74 PASS' not in output:
        raise AssertionError('v90 safe versioned OLC recovery FAILED: '+output[-5000:])
    return 74
print(f'ADMIN LIVE v90 REWIZJE: {_v9000_recovery_gate()} checks PASS',flush=True)


# v91: 22 archetype combinations, persistent custom classes and fully validated
# dependency migration with active-player protection through production OLC.
def _v9100_finalization_gate():
    import subprocess as _sp,sys as _sys
    from pathlib import Path as _Path
    for mod,marker in (
        ('validation.v9100_custom_archetypes','V91 CUSTOM ARCHETYPES: 98 PASS'),
        ('validation.v9100_quest_id_migration','V91 QUEST ID MIGRATION: 47 PASS'),
    ):
        r=_sp.run([_sys.executable,'-u','-m',mod],
            cwd=str(_Path(__file__).resolve().parent),stdin=_sp.DEVNULL,
            capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
        output=r.stdout+'\n'+r.stderr
        if r.returncode or marker not in output:
            raise AssertionError('v91 gate failed '+mod+': '+output[-4500:])
        print(r.stdout.strip(),flush=True)
    return 145
print(f'ADMIN LIVE v91.00.0: {_v9100_finalization_gate()} checks PASS',flush=True)


# v92: test multi-kind quest target migrations in both Windows PREDEPLOY gates.
def _v9200_quest_targets_gate():
    import subprocess as _sp,sys as _sys
    from pathlib import Path as _Path
    pairs=(("validation.v9200_quest_target_bundle","V92 QUEST TARGET BUNDLE: 60 PASS"),
           ("validation.v9200_structured_targets","V92 STRUCTURED TARGETS: 23 PASS"))
    for mod,marker in pairs:
        result=_sp.run([_sys.executable,'-u','-m',mod],
            cwd=str(_Path(__file__).resolve().parent),stdin=_sp.DEVNULL,
            capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
        output=result.stdout+'\n'+result.stderr
        if result.returncode or marker not in output:
            raise AssertionError('v92 quest targets failed '+mod+': '+output[-4000:])
        print(result.stdout.strip(),flush=True)
    return 83
print(f'ADMIN LIVE v92.00.0: {_v9200_quest_targets_gate()} checks PASS',flush=True)


# v93: fail the PREDEPLOY gate when either real OLC feature regresses.
def _v9300_multi_domain_gate():
    import subprocess as _sp, sys as _sys
    from pathlib import Path as _Path
    root=_Path(__file__).resolve().parent
    cases=(("validation.v9300_skill_effect_combos", "V93 SKILL EFFECTS: 42 PASS"),
           ("validation.v9300_quest_repair_combined", "V93 COMBINED QUEST REPAIRS: 41 PASS"))
    for module,marker in cases:
        result=_sp.run([_sys.executable,"-u","-m",module],cwd=str(root),
            stdin=_sp.DEVNULL,capture_output=True,text=True,encoding="utf-8",
            errors="replace",timeout=180)
        output=result.stdout+"\n"+result.stderr
        if result.returncode or marker not in output:
            raise AssertionError("v93: fail "+module+": "+output[-4500:])
        print(result.stdout.strip(),flush=True)
    return 83
print(f'ADMIN LIVE v93.00.0: {_v9300_multi_domain_gate()} checks PASS',flush=True)


# v94: run the integrated DRAFT, publishing-guard and real effect regression
# from the exact candidate copy used by PREDEPLOY.
def _v9400_integrated_gate():
    import subprocess as _sp,sys as _sys
    from pathlib import Path as _Path
    root=_Path(__file__).resolve().parent
    result=_sp.run([_sys.executable,'-u','-m','validation.v9400_final_state_packs'],
        cwd=str(root),stdin=_sp.DEVNULL,capture_output=True,text=True,
        encoding='utf-8',errors='replace',timeout=210)
    report=result.stdout+'\n'+result.stderr
    if result.returncode or 'V94 FULL QUESTS AND EFFECTS: 73 PASS' not in report:
        raise AssertionError('v94 integrated regression failed: '+report[-5000:])
    print(result.stdout.strip(),flush=True)
    return 73
print(f'ADMIN LIVE v94.00.0: {_v9400_integrated_gate()} checks PASS',flush=True)

# v95: transactional character progression and real engine passive presets.
def _v9500_gate():
    import subprocess as _sp, sys as _sys
    from pathlib import Path as _Path
    root=_Path(__file__).resolve().parent
    r=_sp.run([_sys.executable,'-u','-m','validation.v9500_progress_and_passives'],
        cwd=str(root),stdin=_sp.DEVNULL,capture_output=True,text=True,
        encoding='utf-8',errors='replace',timeout=150)
    output=r.stdout+'\n'+r.stderr
    if r.returncode or 'V95 PROGRESSION AND CUSTOM PASSIVES: 65 PASS' not in output:
        raise AssertionError('v95 new features: '+output[-5000:])
    print(r.stdout.strip(),flush=True)
    return 65
print(f'ADMIN LIVE v95.00.0: {_v9500_gate()} checks PASS',flush=True)


# v96: check actual transactional changes, offline access, bank and rollback.
def _v9600_gate():
    import subprocess as _sp, sys as _sys
    from pathlib import Path as _Path
    r=_sp.run([_sys.executable,'-u','-m','validation.v9600_mastery_and_expbank'],
        cwd=str(_Path(__file__).resolve().parent),stdin=_sp.DEVNULL,
        capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=150)
    output=r.stdout+'\n'+r.stderr
    if r.returncode or 'V96 OFFLINE CLASS/SKILL PROGRESSION + BANK AUDIT: 54 PASS' not in output:
        raise AssertionError('v96 mastery/bank validation failed: '+output[-5000:])
    print(r.stdout.strip(),flush=True)
    return 54
print(f'ADMIN LIVE v96.00.0: {_v9600_gate()} checks PASS',flush=True)

# v97: multi-character offline stat and protected-item repairs, native UOSS profile cloning.
def _v9700_big_gate():
    import subprocess as _sp, sys as _sys
    from pathlib import Path as _Path
    proc=_sp.run([_sys.executable,'-u','-m','validation.v9700_large_admin_update'],
        cwd=str(_Path(__file__).resolve().parent),stdin=_sp.DEVNULL,
        capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
    output=proc.stdout+'\n'+proc.stderr
    if proc.returncode or 'V97 LARGE ADMIN UPDATE: 120 PASS' not in output:
        raise AssertionError('v97 full Admin Live regression failed: '+output[-5000:])
    print(proc.stdout.strip(),flush=True)
    return 120
print(f'ADMIN LIVE v97.00.0: {_v9700_big_gate()} checks PASS',flush=True)


# v96.00.2: guard against collisions between legacy and current Admin Live
# subcommands.  Run detached from the live game and fail if any route regresses.
def _v9602_legacy_gate():
    import subprocess as _sp, sys as _sys
    from pathlib import Path as _Path
    result=_sp.run([_sys.executable,'-u','-m','validation.v9602_legacy_admin_live_commands'],
        cwd=str(_Path(__file__).resolve().parent),stdin=_sp.DEVNULL,
        capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=150)
    output=result.stdout+'\n'+result.stderr
    if result.returncode or 'ADMIN LIVE v96.00.2 HISTORICAL ROUTING: 18 PASS' not in output:
        raise AssertionError('v96.00.2 historical command routing failed: '+output[-4500:])
    print(result.stdout.strip(),flush=True)
    return 18
print(f'ADMIN LIVE v96.00.2: {_v9602_legacy_gate()} checks PASS',flush=True)


# v96.00.3: validate all 60 stage names, current candidate and adequate audit
# deadlines without removing any gameplay or SQLite regression.
from validation.v9603_predeploy_runtime import run as _v9603_release_gate
print(f'WINDOWS PREDEPLOY v96.00.3: {_v9603_release_gate()} checks PASS',flush=True)


# v98: 3 integrated changes, online ACL, OLC revision and offline SQLite CAS.
def _v9800_three_features_gate():
    import subprocess as _sp, sys as _sys
    from pathlib import Path as _Path
    r=_sp.run([_sys.executable,'-u','-m','validation.v9800_three_features'],
        cwd=str(_Path(__file__).resolve().parent), stdin=_sp.DEVNULL,
        capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
    output=r.stdout+'\n'+r.stderr
    if r.returncode or 'V98 THREE MAJOR FEATURES: 72 PASS' not in output:
        raise AssertionError('v98 integrated regression failed: '+output[-5000:])
    print(r.stdout.strip(),flush=True)
    return 72
print(f'ADMIN LIVE v98.00.0: {_v9800_three_features_gate()} checks PASS',flush=True)

# v99: mandatory five-feature Admin Live regression for candidate release.
def _v9900_five_features_gate():
    import subprocess as _sp, sys as _sys
    from pathlib import Path as _Path
    r=_sp.run([_sys.executable,'-u','-m','validation.v9900_five_features'],
        cwd=str(_Path(__file__).resolve().parent), stdin=_sp.DEVNULL,
        capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
    output=r.stdout+'\n'+r.stderr
    if r.returncode or 'V99 FIVE FEATURES: 52 PASS' not in output:
        raise AssertionError('v99 five-feature regression failed: '+output[-5000:])
    print(r.stdout.strip(),flush=True)
    return 52
print(f'ADMIN LIVE v99.00.0: {_v9900_five_features_gate()} checks PASS',flush=True)

# v100: five-domain guarded update; must pass on Windows before deployment.
def _v10000_admin_live_gate():
    import subprocess as _sp, sys as _sys
    from pathlib import Path as _Path
    result=_sp.run([_sys.executable,'-u','-m','validation.v10000_admin_live_ultimate'],
        cwd=str(_Path(__file__).resolve().parent),stdin=_sp.DEVNULL,
        capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
    message=result.stdout+'\n'+result.stderr
    if result.returncode or 'ADMIN LIVE v100: 63 checks PASS' not in message:
        raise AssertionError('Admin Live v100 regression FAILED: '+message[-5000:])
    print(result.stdout.strip(),flush=True)
    return 63
print(f'ADMIN LIVE v100.00.0: {_v10000_admin_live_gate()} checks PASS',flush=True)

# v101: mandatory three-area regression for Windows PREDEPLOY 60/60 PLUS.
def _v10100_three_gaps_gate():
    import subprocess as _sp,sys as _sys
    from pathlib import Path as _Path
    result=_sp.run([_sys.executable,'-u','-m','validation.v10100_three_gaps'],
        cwd=str(_Path(__file__).resolve().parent),stdin=_sp.DEVNULL,
        capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
    output=result.stdout+'\n'+result.stderr
    if result.returncode or 'ADMIN LIVE v101: 59 checks PASS' not in output:
        raise AssertionError('Admin Live v101 regression FAILED: '+output[-5000:])
    print(result.stdout.strip(),flush=True)
    return 59
print(f'ADMIN LIVE v101.00.0: {_v10100_three_gaps_gate()} checks PASS',flush=True)

# v102: arena tunnel, OLC conditional effects and read-only Admin Live truth audit.
def _v10200_admin_live_gate():
    import subprocess as _sp,sys as _sys
    from pathlib import Path as _Path
    result=_sp.run([_sys.executable,'-u','-m','validation.v10200_admin_live_final'],
        cwd=str(_Path(__file__).resolve().parent),stdin=_sp.DEVNULL,
        capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
    output=result.stdout+'\n'+result.stderr
    if result.returncode or 'ADMIN LIVE v102: 52 checks PASS' not in output:
        raise AssertionError('Admin Live v102 regression FAILED: '+output[-5000:])
    print(result.stdout.strip(),flush=True)
    return 52
print(f'ADMIN LIVE v102.00.0: {_v10200_admin_live_gate()} checks PASS',flush=True)
