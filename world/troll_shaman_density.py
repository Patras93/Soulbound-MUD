# -*- coding: utf-8 -*-
"""Soulbound v0.36.11 - Troll Shaman Quest Density.

The repeatable Troll Shaman quest requires 5 kills. Older generic quest-density
logic could leave only three concurrent ordinary troll_shaman spawns, all in a
single room. This layer makes the authored Jaskinia Trolli layout match the
quest requirement without changing the quest target or reward.
"""
from data import catalog_mutations as _catalog_mut
from data.mobs import MOB_TEMPLATES
from data.quests import QUESTS
from data.rooms import ROOMS
from systems.content_registry import MOB_SPAWNS
from world.equipment_help import HELP_TOPICS, HELP_TOPIC_ALIASES

_V03611_TROLL_SHAMAN_LAYOUT = [
    ("troll_cave_2", "troll_shaman"),
    ("troll_cave_3", "troll_shaman"),
    ("troll_cave_3", "troll_shaman"),
    ("troll_underground_river", "troll_shaman"),
    ("troll_shaman_gallery", "troll_shaman"),
    ("troll_shaman_gallery", "troll_shaman"),
    ("troll_shaman_gallery", "troll_shaman"),
    ("troll_nursery", "troll_shaman"),
]

# Normalize only the ordinary quest target. Deep/endgame shaman variants keep
# their own IDs and are intentionally untouched.
MOB_SPAWNS[:] = [
    (room_id, mob_id)
    for room_id, mob_id in MOB_SPAWNS
    if mob_id != "troll_shaman"
]
MOB_SPAWNS.extend(_V03611_TROLL_SHAMAN_LAYOUT)

# Keep the quest text explicit about the denser cave population.
if isinstance(QUESTS.get("troll_shaman_hunt"), dict):
    _catalog_mut.catalog_assign("Pokonaj 5 Trolli Szamanów w Jaskini Trolli. "
        "Szamani występują w kilku komorach jaskini jednocześnie.", 'QUESTS', QUESTS, ("troll_shaman_hunt", "description"))

HELP_TOPICS.setdefault("questy", []).append(
    "v0.36.11: Polowanie na Trolli Szamanów ma 8 równoczesnych zwykłych Trolli Szamanów rozmieszczonych w kilku komorach Jaskini Trolli; quest nadal wymaga 5 zabójstw."
)
HELP_TOPICS.setdefault("trolle", []).append(
    "Polowanie na Trolli Szamanów: szukaj ich w Jaskini Trolli, szczególnie w Galerii Szamanów; v0.36.11 utrzymuje 8 równoczesnych spawnów dla celu 5 zabójstw."
)
HELP_TOPIC_ALIASES.update({
    "troll szaman": "trolle",
    "trolle szamani": "trolle",
    "szamani trolli": "trolle",
    "troll shaman": "trolle",
})


def troll_shaman_density_audit_v03611():
    errors = []
    quest = QUESTS.get("troll_shaman_hunt") or {}
    if quest.get("kind") != "kill":
        errors.append("troll_shaman_hunt is not a kill quest")
    if str(quest.get("target")) != "troll_shaman":
        errors.append(f"quest target={quest.get('target')!r}, expected troll_shaman")
    if int(quest.get("needed", 0) or 0) != 5:
        errors.append(f"quest needed={quest.get('needed')!r}, expected 5")

    spawns = [(r, m) for r, m in MOB_SPAWNS if m == "troll_shaman"]
    rooms = [r for r, _ in spawns]
    if len(spawns) < 8:
        errors.append(f"only {len(spawns)} ordinary troll_shaman spawns; expected at least 8")
    if len(set(rooms)) < 4:
        errors.append(f"troll_shaman spawns use only {len(set(rooms))} rooms; expected at least 4")
    if rooms.count("troll_shaman_gallery") < 3:
        errors.append("Troll Shaman Gallery should contain at least 3 ordinary shamans")
    bad_rooms = [rid for rid in set(rooms) if str((ROOMS.get(rid) or {}).get("zone")) != "Jaskinia Trolli"]
    if bad_rooms:
        errors.append("ordinary troll_shaman outside Jaskinia Trolli: " + ", ".join(sorted(bad_rooms)))
    if "troll_shaman" not in MOB_TEMPLATES:
        errors.append("missing troll_shaman template")

    return {
        "version": "0.36.11",
        "quest_needed": int(quest.get("needed", 0) or 0),
        "spawn_count": len(spawns),
        "room_count": len(set(rooms)),
        "rooms": sorted(set(rooms)),
        "error_count": len(errors),
        "errors": errors,
    }


TROLL_SHAMAN_DENSITY_AUDIT_V03611 = troll_shaman_density_audit_v03611()
if TROLL_SHAMAN_DENSITY_AUDIT_V03611["error_count"]:
    raise RuntimeError(
        "Troll Shaman Density Audit v0.36.11 failed: "
        + "; ".join(TROLL_SHAMAN_DENSITY_AUDIT_V03611["errors"][:100])
    )

LATEST_CHANGES_TITLE = "Soulbound v0.36.11 - More Troll Shamans"
LATEST_CHANGES = [
    "Polowanie na Trolli Szamanów nadal wymaga 5 zabójstw.",
    "Zwiększono liczbę zwykłych Trolli Szamanów do 8 równoczesnych spawnów.",
    "Szamani są rozmieszczeni w kilku komorach Jaskini Trolli, zamiast skupiać się wyłącznie w jednym miejscu.",
    "Galeria Szamanów ma 3 równoczesnych zwykłych Trolli Szamanów.",
]
