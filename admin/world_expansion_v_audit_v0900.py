"""Full-release integrity audit for v0.90.0 world content."""
from __future__ import annotations

from data.catalogs import ROOMS, NPCS, ITEMS, QUESTS, MOB_TEMPLATES
from systems.content_registry import MOB_SPAWNS
from world.world_expansion_v import WORLD_EXPANSION_V_STATE


def world_expansion_v_audit_v0900():
    errors = []
    state = WORLD_EXPANSION_V_STATE
    levels = state["catacomb_levels"]
    if set(levels) != {1, 2, 3} or any(len(rooms) != 24 for rooms in levels.values()):
        errors.append("catacombs must have three 24-room levels")
    dungeons = state["archipelago_dungeons"]
    if len(dungeons) != 3 or any(len(rooms) != 40 for rooms in dungeons.values()):
        errors.append("archipelago must have three 40-room dungeons")
    if len(state["archipelago_story_quests"]) != 12:
        errors.append("archipelago story must have 12 quests")
    if state["cities_2_count"] != len(state["cities_2_rooms"]):
        errors.append("Cities 2.0 count differs from city registry")
    if len(state["cities_2_quests"]) != state["cities_2_count"]:
        errors.append("Cities 2.0 quest coverage differs from city registry")
    for group in (*levels.values(), *dungeons.values(), *state["cities_2_rooms"].values()):
        for rid in group:
            if rid not in ROOMS:
                errors.append(f"missing room {rid}")
    for qid in (*state["archipelago_story_quests"], *(qid for ids in state["cities_2_quests"].values() for qid in ids)):
        if qid not in QUESTS:
            errors.append(f"missing quest {qid}")
    for rid, mid in MOB_SPAWNS:
        if rid in ROOMS and ROOMS[rid].get("v0900_expansion") and mid not in MOB_TEMPLATES:
            errors.append(f"missing spawn template {mid} in {rid}")
    return {"version": "0.90.0", "error_count": len(errors), "errors": errors,
            "new_rooms": state["new_rooms"], "new_mobs": state["new_mobs"],
            "new_npcs": state["new_npcs"], "new_quests": state["new_quests"]}


WORLD_EXPANSION_V_AUDIT_V0900 = world_expansion_v_audit_v0900()
if WORLD_EXPANSION_V_AUDIT_V0900["error_count"]:
    raise RuntimeError("World Expansion V audit failed: " + "; ".join(WORLD_EXPANSION_V_AUDIT_V0900["errors"][:30]))

__all__ = ("world_expansion_v_audit_v0900", "WORLD_EXPANSION_V_AUDIT_V0900")
