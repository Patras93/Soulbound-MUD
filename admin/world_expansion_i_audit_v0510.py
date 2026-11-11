# -*- coding: utf-8 -*-
"""Soulbound v0.51.0 - World Expansion I release audit."""
from __future__ import annotations

from collections import deque

from data.catalogs import ROOMS, NPCS, QUESTS, MOB_TEMPLATES
from systems.content_registry import MOB_SPAWNS
from world.world_expansion_i import WORLD_EXPANSION_I_STATE


def _reachable(start="square"):
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


def world_expansion_i_audit_v0510():
    errors = []
    state = WORLD_EXPANSION_I_STATE
    reachable = _reachable()

    if state.get("settlement_count") != 4:
        errors.append(f"settlements={state.get('settlement_count')}, expected 4")
    if state.get("hunting_zone_count") != 8:
        errors.append(f"hunting zones={state.get('hunting_zone_count')}, expected 8")
    if int(state.get("room_count", 0)) < 120:
        errors.append(f"new rooms={state.get('room_count')}, expected at least 120")
    if int(state.get("mob_template_count", 0)) < 32:
        errors.append(f"new mobs={state.get('mob_template_count')}, expected at least 32")
    if int(state.get("quest_count", 0)) != 16:
        errors.append(f"new quests={state.get('quest_count')}, expected 16")
    if int(state.get("npc_count", 0)) != 8:
        errors.append(f"new NPCs={state.get('npc_count')}, expected 8")

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

    # Every new room exit must resolve to a real room.
    for rid in state.get("room_ids", ()):
        room = ROOMS.get(rid)
        if not room:
            continue
        for direction, dest in room.get("exits", {}).items():
            if dest not in ROOMS:
                errors.append(f"broken exit {rid}:{direction}->{dest}")

    # New NPCs and quests are internally complete.
    giver_names = {NPCS[nid].get("name") for nid in state.get("npc_ids", ()) if nid in NPCS}
    for nid in state.get("npc_ids", ()):
        npc = NPCS.get(nid)
        if not npc:
            errors.append(f"missing NPC {nid}")
            continue
        if npc.get("room") not in ROOMS:
            errors.append(f"NPC room missing {nid}->{npc.get('room')}")
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
        "version": "0.51.0",
        "settlement_count": int(state.get("settlement_count", 0)),
        "hunting_zone_count": int(state.get("hunting_zone_count", 0)),
        "new_room_count": int(state.get("room_count", 0)),
        "new_mob_count": int(state.get("mob_template_count", 0)),
        "new_npc_count": int(state.get("npc_count", 0)),
        "new_quest_count": int(state.get("quest_count", 0)),
        "reachable_new_rooms": sum(1 for rid in state.get("room_ids", ()) if rid in reachable),
        "error_count": len(errors),
        "errors": errors,
    }


WORLD_EXPANSION_I_AUDIT_V0510 = world_expansion_i_audit_v0510()
if WORLD_EXPANSION_I_AUDIT_V0510["error_count"]:
    raise RuntimeError(
        "World Expansion I Audit v0.51.0 failed: "
        + "; ".join(WORLD_EXPANSION_I_AUDIT_V0510["errors"][:100])
    )

__all__ = ["world_expansion_i_audit_v0510", "WORLD_EXPANSION_I_AUDIT_V0510"]
