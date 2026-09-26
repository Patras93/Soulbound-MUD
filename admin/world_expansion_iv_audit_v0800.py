# -*- coding: utf-8 -*-
"""Soulbound v0.80.0 - Archipelag Pękniętej Gwiazdy audit."""
from __future__ import annotations

from collections import deque

from data.catalogs import ROOMS, NPCS, ITEMS, QUESTS, MOB_TEMPLATES
from systems.content_registry import MOB_SPAWNS
from world.world_expansion_iv import (
    WORLD_EXPANSION_IV_STATE, STORY_QUEST_IDS_V0800, SIDE_QUEST_IDS_V0800,
)


def _v0800_reachable(start, target):
    if start not in ROOMS or target not in ROOMS:
        return False
    seen = {start}; queue = deque([start])
    while queue:
        rid = queue.popleft()
        if rid == target:
            return True
        for nxt in (ROOMS[rid].get("exits") or {}).values():
            if nxt in ROOMS and nxt not in seen:
                seen.add(nxt); queue.append(nxt)
    return False


def world_expansion_iv_audit_v0800():
    errors = []
    state = WORLD_EXPANSION_IV_STATE
    if state.get("room_count", 0) < 35:
        errors.append(f"new rooms={state.get('room_count')}, expected >=35")
    if state.get("zone_count") != 5:
        errors.append(f"zones={state.get('zone_count')}, expected 5")
    if state.get("story_quest_count") != 12 or len(STORY_QUEST_IDS_V0800) != 12:
        errors.append(f"story quests={len(STORY_QUEST_IDS_V0800)}, expected 12")
    if state.get("side_quest_count") != 5 or len(SIDE_QUEST_IDS_V0800) != 5:
        errors.append(f"side quests={len(SIDE_QUEST_IDS_V0800)}, expected 5")
    if state.get("mob_template_count", 0) < 15:
        errors.append(f"new mobs={state.get('mob_template_count')}, expected >=15")
    if state.get("npc_count", 0) < 6:
        errors.append(f"new NPCs={state.get('npc_count')}, expected >=6")
    if not _v0800_reachable("square", "v0800_harbor_square"):
        errors.append("archipelago hub is not reachable from Miasto Dusz")
    if not _v0800_reachable("v0800_harbor_square", "v0800_heart_06"):
        errors.append("final story room is not reachable from archipelago hub")

    previous = None
    for index, qid in enumerate(STORY_QUEST_IDS_V0800, 1):
        q = QUESTS.get(qid)
        if not q:
            errors.append(f"missing story quest {qid}")
            continue
        if q.get("repeatable"):
            errors.append(f"{qid}: story quest must not be repeatable")
        if not q.get("v0800_story"):
            errors.append(f"{qid}: missing story marker")
        if previous and q.get("requires_quest") != previous:
            errors.append(f"{qid}: broken chain, expected {previous}")
        if index == 1 and int(q.get("required_soul_tier", 0) or 0) != 10:
            errors.append("first story quest must require Soul Tier 10")
        previous = qid

    captain = NPCS.get("v0800_captain_seris") or {}
    attached = (captain.get("quest"),) + tuple(captain.get("quest_chain") or ())
    if tuple(attached) != tuple(STORY_QUEST_IDS_V0800):
        errors.append("Kapitan Seris does not expose the complete story chain")

    final_q = QUESTS.get(STORY_QUEST_IDS_V0800[-1]) or {}
    if int((final_q.get("reward_items") or {}).get("v0800_broken_star_compass", 0) or 0) != 1:
        errors.append("final story reward does not grant Kompas Pękniętej Gwiazdy")
    relic = ITEMS.get("v0800_broken_star_compass") or {}
    if relic.get("slot") != "relic" or relic.get("rarity") != "legendary":
        errors.append("final relic has invalid slot/rarity")

    for zone, boss_id in (state.get("zone_bosses") or {}).items():
        if boss_id not in MOB_TEMPLATES:
            errors.append(f"{zone}: missing boss template {boss_id}")
            continue
        if not any(mid == boss_id for _rid, mid in MOB_SPAWNS):
            errors.append(f"{zone}: boss {boss_id} has no spawn")

    return {
        "version": "0.80.0",
        "error_count": len(errors),
        "errors": errors,
        "new_rooms": state.get("room_count", 0),
        "new_mobs": state.get("mob_template_count", 0),
        "new_npcs": state.get("npc_count", 0),
        "story_quests": len(STORY_QUEST_IDS_V0800),
        "side_quests": len(SIDE_QUEST_IDS_V0800),
        "zones": state.get("zone_count", 0),
    }


WORLD_EXPANSION_IV_AUDIT_V0800 = world_expansion_iv_audit_v0800()
if WORLD_EXPANSION_IV_AUDIT_V0800["error_count"]:
    raise RuntimeError(
        "World Expansion IV Audit v0.80.0 failed: "
        + "; ".join(WORLD_EXPANSION_IV_AUDIT_V0800["errors"][:100])
    )

__all__ = ["world_expansion_iv_audit_v0800", "WORLD_EXPANSION_IV_AUDIT_V0800"]
