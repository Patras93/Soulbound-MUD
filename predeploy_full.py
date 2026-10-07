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
        try:
            ns = vars(server)
            full = ns["FULL_GAME_PREDEPLOY_AUDIT_V0336"]
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
                if not server.world.ensure_runtime_room(chosen_room):
                    chest_errors.append(
                        f"{kind} {floor}: World.ensure_runtime_room failed"
                    )
                    continue

                boss_rooms = []
                for mob in server.world.mobs.values():
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
