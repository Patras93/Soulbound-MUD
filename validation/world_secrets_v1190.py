# -*- coding: utf-8 -*-
"""Version 1.19.0: read-only audit of existing maps and new generated secrets."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import ast

from world.world_secrets_v1190 import (
    secret_room_id_v1190, secret_room_identity_v1190, world_secret_roll_v1190,
)


def audit_world_secrets_v1190(runtime=True):
    checks, errors = 0, []

    def check(value, label):
        nonlocal checks
        checks += 1
        if not value:
            errors.append(str(label))

    for kind in ("crypt", "mythic_crypt", "astral", "mythic_astral", "giant",
                 "mine", "crystal_mine", "sunken_grotto", "ancient_forest",
                 "alchemy_garden", "magitek"):
        for role in ("chamber", "archive"):
            rid = secret_room_id_v1190(kind, 1017, role)
            check(secret_room_identity_v1190(rid) == (role, kind, 1017), f"room identity {kind}/{role}")
    for invalid in ("", "v1190_chamber_crypt_0", "v1190_archive__1", "v1190_chamber_crypt_abc", "evil"):
        check(secret_room_identity_v1190(invalid) is None, f"invalid room identity {invalid}")
    dates = [date(2026, 10, 8) + timedelta(days=i) for i in range(100)]
    rare_count = sum(world_secret_roll_v1190("v1190_archive_crypt_17", d) for d in dates)
    check(5 <= rare_count <= 50, "rare encounter uncommon, not impossible")
    check(all(world_secret_roll_v1190("v1190_archive_crypt_17", d) ==
              world_secret_roll_v1190("v1190_archive_crypt_17", d) for d in dates), "daily event deterministic")
    root = Path(__file__).resolve().parents[1]
    for relative, phrase in (
        ("player/session_mixins/perception_maps.py", "world_secrets_command_v1190"),
        ("player/session_mixins/collection_loot_records.py", "Skarbiec jest strzeżony"),
        ("player/session_mixins/movement.py", "Najpierw go pokonaj"),
        ("world/world_state.py", "create_world_secret_rooms_v1190"),
        ("world/generation_systems.py", "sekret wydarzenie"),
    ):
        body = (root / relative).read_text(encoding="utf8")
        ast.parse(body, filename=relative)
        check(phrase in body, f"wiring {relative}")
    from config.command_aliases import COMMAND_ALIAS_DEFINITIONS
    for alias in ("sekret", "secret", "tajemnica"):
        check(COMMAND_ALIAS_DEFINITIONS.get(alias) == "instancesecret", f"alias {alias}")

    if runtime:
        import server
        world = server.World()
        for kind, desc in server.INSTANCE_MAP_DEFS.items():
            # Magitek procedural floor generation mutates global NPC/mob
            # name catalogs. Its live chamber is checked in an isolated smoke
            # test, to keep later full-audit snapshots free of generated names.
            if kind == "magitek":
                check(secret_room_identity_v1190(secret_room_id_v1190(kind, 17)) ==
                      ("chamber", kind, 17), "magitek room identity")
                continue
            floor = server.instance_secret_floors(kind, int(desc.get("min_floor", 1)))[0]
            parent = {
                "crypt": server.crypt_floor_id, "mythic_crypt": server.mythic_crypt_floor_id,
                "astral": server.astral_floor_id, "mythic_astral": server.mythic_astral_floor_id,
                "giant": server.giant_fortress_floor_id, "mine": server.mine_floor_id,
                "magitek": server.magitek_floor_id,
            }.get(kind)
            parent_id = parent(floor) if parent else server.profession_dungeon_room_id(kind, floor)
            chamber = secret_room_id_v1190(kind, floor)
            archive = secret_room_id_v1190(kind, floor, "archive")
            check(world.ensure_runtime_room(chamber), f"create chamber {kind}")
            check(world.ensure_runtime_room(archive), f"create archive {kind}")
            chamber_room = server.ROOMS.get(chamber, {})
            archive_room = server.ROOMS.get(archive, {})
            check(chamber_room.get("exits") == {"down": parent_id, "east": archive}, f"chamber routes {kind}")
            check(archive_room.get("exits") == {"west": chamber, "down": parent_id}, f"archive returns to same floor {kind}")
            check(server.TREASURE_CHESTS.get(chamber, {}).get("respawn") == 86400, f"guarded chest {kind}")
            check(chamber not in server.TREASURE_CHESTS or archive not in server.TREASURE_CHESTS, f"no extra chest in archive {kind}")
            npcs = [npc for npc in server.NPCS.values() if npc.get("room") == archive]
            check(len(npcs) == 1, f"hidden NPC {kind}")
            mob_rows = world.room_mobs(chamber)
            check(len(mob_rows) == 1, f"guard spawned {kind}")
            for mob in mob_rows:
                template = server.MOB_TEMPLATES.get(mob.template_id, {})
                check(bool(template.get("v1190_secret_guard")), f"named guard {kind}")
                check(bool(template.get("mini_boss") and template.get("stationary_mob")), f"passive fixed miniboss {kind}")
            check(world.ensure_runtime_room(chamber) and len(world.room_mobs(chamber)) == 1,
                  f"idempotent re-entry {kind}")
        frontier_ids = server.v0140_surface_secret_room_ids()
        check(bool(frontier_ids), "frontier secrets retained")
        if frontier_ids:
            info = server.v0140_surface_secret_info(frontier_ids[0])
            hidden_room = info["hidden_room"]
            check(world.ensure_runtime_room(hidden_room), "surface chamber exists")
            check(any(npc.get("room") == hidden_room for npc in server.NPCS.values()), "surface mysterious NPC")
            check(hidden_room in server.TREASURE_CHESTS, "old surface chest preserved")
        check(all("trap" not in str(room).lower() and "pułapk" not in str(room).lower()
                  for room_id, room in server.ROOMS.items() if str(room_id).startswith("v1190_")), "no trap mechanics")
    return {"checks": checks, "error_count": len(errors), "errors": errors}


if __name__ == "__main__":
    result = audit_world_secrets_v1190()
    print(result)
    if result["error_count"]:
        raise SystemExit(1)
