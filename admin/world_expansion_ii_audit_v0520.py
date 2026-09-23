# -*- coding: utf-8 -*-
"""Soulbound v0.52.0 - World Expansion II release audit."""
from __future__ import annotations

from collections import deque

from data.catalogs import ROOMS, NPCS, QUESTS, MOB_TEMPLATES
from systems.content_registry import MOB_SPAWNS
from world.world_expansion_ii import WORLD_EXPANSION_II_STATE


def _w2_reachable(start="square"):
    seen = set()
    todo = deque([start])
    while todo:
        rid = todo.popleft()
        if rid in seen or rid not in ROOMS:
            continue
        seen.add(rid)
        for dest in ROOMS[rid].get("exits", {}).values():
            if dest not in seen:
                todo.append(dest)
    return seen


def world_expansion_ii_audit_v0520():
    errors = []
    state = WORLD_EXPANSION_II_STATE
    reachable = _w2_reachable()

    if state.get("capital_count") != 1:
        errors.append(f"capital={state.get('capital_count')}, expected 1")
    if state.get("village_count") != 3:
        errors.append(f"villages={state.get('village_count')}, expected 3")
    if state.get("settlement_count") != 4:
        errors.append(f"settlements={state.get('settlement_count')}, expected 4")
    if state.get("hunting_zone_count") != 10:
        errors.append(f"hunting zones={state.get('hunting_zone_count')}, expected 10")
    if int(state.get("room_count", 0)) < 150:
        errors.append(f"new rooms={state.get('room_count')}, expected at least 150")
    if int(state.get("mob_template_count", 0)) < 40:
        errors.append(f"new mobs={state.get('mob_template_count')}, expected at least 40")
    if int(state.get("quest_count", 0)) != 20:
        errors.append(f"new quests={state.get('quest_count')}, expected 20")
    if int(state.get("npc_count", 0)) != 10:
        errors.append(f"new NPCs={state.get('npc_count')}, expected 10")

    for label, rid in state.get("settlements", {}).items():
        if rid not in ROOMS:
            errors.append(f"missing settlement hub: {label}->{rid}")
        elif rid not in reachable:
            errors.append(f"unreachable settlement hub: {label}->{rid}")

    for zone, spec in state.get("hunting_zones", {}).items():
        rooms = tuple(state.get("zone_rooms", {}).get(zone, ()))
        mobs = tuple(state.get("zone_mobs", {}).get(zone, ()))
        boss = state.get("zone_bosses", {}).get(zone)
        if len(rooms) != 8:
            errors.append(f"{zone}: room count {len(rooms)} != 8")
        if len(mobs) != 3:
            errors.append(f"{zone}: normal mob count {len(mobs)} != 3")
        if not boss or boss not in MOB_TEMPLATES:
            errors.append(f"{zone}: missing boss {boss}")
        for rid in rooms:
            if rid not in ROOMS:
                errors.append(f"{zone}: missing room {rid}")
            elif rid not in reachable:
                errors.append(f"{zone}: unreachable room {rid}")
        for mid in mobs:
            if mid not in MOB_TEMPLATES:
                errors.append(f"{zone}: missing mob {mid}")
        if int(spec.get("stage", 0)) <= 0:
            errors.append(f"{zone}: invalid stage {spec.get('stage')}")

    new_room_ids = tuple(state.get("room_ids", ()))
    if len(new_room_ids) != len(set(new_room_ids)):
        errors.append("duplicate room ids in World Expansion II state")

    for rid in new_room_ids:
        room = ROOMS.get(rid)
        if not room:
            continue
        for direction, dest in room.get("exits", {}).items():
            if dest not in ROOMS:
                errors.append(f"broken exit {rid}:{direction}->{dest}")

    giver_names = {NPCS[nid].get("name") for nid in state.get("npc_ids", ()) if nid in NPCS}
    for nid in state.get("npc_ids", ()):
        npc = NPCS.get(nid)
        if not npc:
            errors.append(f"missing NPC {nid}")
            continue
        if npc.get("room") not in ROOMS:
            errors.append(f"NPC room missing {nid}->{npc.get('room')}")
        elif npc.get("room") not in reachable:
            errors.append(f"NPC unreachable {nid}->{npc.get('room')}")

    for qid in state.get("quest_ids", ()):
        q = QUESTS.get(qid)
        if not q:
            errors.append(f"missing quest {qid}")
            continue
        if q.get("giver") not in giver_names:
            errors.append(f"quest giver missing {qid}:{q.get('giver')}")
        target = q.get("target")
        target_found = any(
            target == mob.get("quest_target") or target in tuple(mob.get("quest_targets") or ())
            for mob in MOB_TEMPLATES.values()
        )
        if not target_found:
            errors.append(f"quest target unavailable {qid}:{target}")

    spawn_rooms = {rid for rid, _ in MOB_SPAWNS}
    for zone, rooms in state.get("zone_rooms", {}).items():
        missing = [rid for rid in rooms if rid not in spawn_rooms]
        if missing:
            errors.append(f"{zone}: rooms without mobs: {', '.join(missing)}")

    return {
        "version": "0.52.0",
        "continent": state.get("continent"),
        "capital_count": int(state.get("capital_count", 0)),
        "village_count": int(state.get("village_count", 0)),
        "settlement_count": int(state.get("settlement_count", 0)),
        "hunting_zone_count": int(state.get("hunting_zone_count", 0)),
        "new_room_count": int(state.get("room_count", 0)),
        "new_mob_count": int(state.get("mob_template_count", 0)),
        "new_npc_count": int(state.get("npc_count", 0)),
        "new_quest_count": int(state.get("quest_count", 0)),
        "reachable_new_rooms": sum(1 for rid in new_room_ids if rid in reachable),
        "error_count": len(errors),
        "errors": errors,
    }


WORLD_EXPANSION_II_AUDIT_V0520 = world_expansion_ii_audit_v0520()
if WORLD_EXPANSION_II_AUDIT_V0520["error_count"]:
    raise RuntimeError(
        "World Expansion II Audit v0.52.0 failed: "
        + "; ".join(WORLD_EXPANSION_II_AUDIT_V0520["errors"][:100])
    )

__all__ = ["world_expansion_ii_audit_v0520", "WORLD_EXPANSION_II_AUDIT_V0520"]
