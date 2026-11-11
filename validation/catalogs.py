# -*- coding: utf-8 -*-
"""Focused catalog validators used before deploy and while repairing content."""
from __future__ import annotations


def validate_catalogs(*, items, rooms, npcs, quests, mobs, shops, craft_recipes, alchemy_recipes):
    errors = []

    for name, catalog in (
        ("ITEMS", items), ("ROOMS", rooms), ("NPCS", npcs), ("QUESTS", quests),
        ("MOB_TEMPLATES", mobs), ("SHOPS", shops), ("CRAFT_RECIPES", craft_recipes),
        ("ALCHEMY_RECIPES", alchemy_recipes),
    ):
        if not isinstance(catalog, dict) or not catalog:
            errors.append(f"{name} is not a non-empty dict")

    for item_id, item in items.items():
        if not isinstance(item, dict):
            errors.append(f"item {item_id}: definition is not dict")
        elif not str(item.get("name", "")).strip():
            errors.append(f"item {item_id}: missing name")

    for mob_id, mob in mobs.items():
        if not isinstance(mob, dict):
            errors.append(f"mob {mob_id}: definition is not dict")
            continue
        if not str(mob.get("name", "")).strip():
            errors.append(f"mob {mob_id}: missing name")
        drops = mob.get("drops") or {}
        if isinstance(drops, dict):
            for item_id in drops:
                if item_id not in items:
                    errors.append(f"mob {mob_id}: missing drop item {item_id}")

    for quest_id, quest in quests.items():
        if not isinstance(quest, dict):
            errors.append(f"quest {quest_id}: definition is not dict")
            continue
        if not str(quest.get("name", "")).strip():
            errors.append(f"quest {quest_id}: missing name")
        for item_id in (quest.get("reward_items") or {}):
            if item_id not in items:
                errors.append(f"quest {quest_id}: missing reward item {item_id}")

    # Only validate exits that are concrete strings. Procedural placeholders are
    # intentionally left to the exhaustive world validator.
    for room_id, room in rooms.items():
        exits = room.get("exits") or {} if isinstance(room, dict) else {}
        if not isinstance(exits, dict):
            errors.append(f"room {room_id}: exits is not dict")
            continue
        dynamic_prefixes = (
            "prof_", "mine_floor_", "crypt_floor_", "magitek_floor_",
            "astral_floor_", "mythic_crypt_floor_", "mythic_astral_floor_",
            "giant_fortress_", "v0130_frontier_", "v018_endless_", "v020_mega_",
        )
        for direction, target in exits.items():
            if (
                isinstance(target, str) and target and target not in rooms
                and not target.startswith(dynamic_prefixes)
            ):
                errors.append(f"room {room_id}: {direction} -> missing room {target}")

    return {
        "error_count": len(errors),
        "errors": errors,
        "counts": {
            "items": len(items), "rooms": len(rooms), "npcs": len(npcs),
            "quests": len(quests), "mobs": len(mobs), "shops": len(shops),
            "craft_recipes": len(craft_recipes), "alchemy_recipes": len(alchemy_recipes),
        },
    }
