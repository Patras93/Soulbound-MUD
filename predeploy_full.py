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
        import server
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
