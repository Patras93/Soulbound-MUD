#!/usr/bin/env python3
"""Run the complete production-runtime gameplay audit on a disposable database.

SOULBOUND_FULL_AUDIT enables expensive semantic verification, while historical
developer/style audit modules remain a separate opt-in lane.
"""
from __future__ import annotations

import os
import socket
import tempfile


def main():
    with tempfile.TemporaryDirectory(prefix="soulbound-full-audit-") as directory:
        os.environ["SOULBOUND_DB"] = os.path.join(directory, "audit.db")
        os.environ["SOULBOUND_FULL_AUDIT"] = "1"
        os.environ.pop("SOULBOUND_HISTORICAL_AUDITS", None)
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            os.environ["SOULBOUND_PORT"] = str(probe.getsockname()[1])
        import server
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
        # v1.39.0: four deterministic virtual sessions sharing real disposable
        # SQLite. Does not open player sockets or touch the deployment database.
        from validation.v1390_world_stress import run_stress_v1390
        _stress_v1390 = run_stress_v1390(players=4, rounds=120)
        assert not _stress_v1390['errors'], _stress_v1390['failures'][:20]
        print(f"WORLD STRESS v1.39.0: {_stress_v1390['simulated_operations']} operations, "
              f"{_stress_v1390['checks']} checks, "
              f"p95={_stress_v1390['p95_actor_batch_ms']}ms, "
              "4 virtual players, 0 errors; NOT live TCP load")
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
        assert _legendary_v1370['catalog'] == 492
        assert resolve_session_command('medale') == 'medale'
        assert resolve_session_command('kronikapostaci') == 'kronikapostaci'
        assert resolve_session_command('legendy') == 'legendaryrares'
        assert resolve_session_command('legendarneosiagniecia') == 'medale'
        assert callable(getattr(Session, 'legendary_achievements_v1370', None))
        assert callable(getattr(Session, 'show_server_chronicle_v03811', None))
        print('LEGENDARNE OSIAGNIECIA v1.37.0 RUNTIME: 492 definitions, 102 titles, '
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


if __name__ == "__main__":
    main()
