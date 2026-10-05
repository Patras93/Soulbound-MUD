# -*- coding: utf-8 -*-
"""Soulbound v0.36.11 - Troll Shaman Quest Density.

The repeatable Troll Shaman quest requires 5 kills. Older generic quest-density
logic could leave only three concurrent ordinary troll_shaman spawns, all in a
single room. This layer makes the authored Jaskinia Trolli layout match the
quest requirement. v1.12.8 also keeps the troll quest line's stat progression
meaningful against the modern long-term level curve.
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

# v1.12.8: stat progression had fallen far behind character progression.
# These are intentional per-stat rewards, not a shared pool: completing one
# quest grants the listed amount separately to each of the six base stats.
# manual_stat_progress is read before Generator Core reward fields, keeping
# these authored values stable across future numeric regeneration.
V1128_TROLL_QUEST_STAT_REWARDS = {
    "mountain_troll_hunt": 15_000,
    "mountain_trail_patrol": 15_000,
    "stolen_mountain_ores": 15_000,
    "troll_shaman_hunt": 18_000,
    "deep_troll_clearance": 20_000,
    "troll_king_hunt": 25_000,
}
V1128_TROLL_QUEST_STAT_REPAIRS = {}
for _quest_id, _stat_reward in V1128_TROLL_QUEST_STAT_REWARDS.items():
    _quest = QUESTS.get(_quest_id)
    if not isinstance(_quest, dict):
        continue
    _catalog_mut.catalog_assign(
        int(_stat_reward), 'QUESTS', QUESTS, (_quest_id, "manual_stat_progress")
    )
    _catalog_mut.catalog_assign(
        int(_stat_reward), 'QUESTS', QUESTS, (_quest_id, "reward_stat_progress")
    )
    V1128_TROLL_QUEST_STAT_REPAIRS[_quest_id] = int(_stat_reward)

HELP_TOPICS.setdefault("questy", []).append(
    "v0.36.11: Polowanie na Trolli Szamanów ma 8 równoczesnych zwykłych Trolli Szamanów rozmieszczonych w kilku komorach Jaskini Trolli; quest nadal wymaga 5 zabójstw."
)
HELP_TOPICS.setdefault("trolle", []).append(
    "Polowanie na Trolli Szamanów: szukaj ich w Jaskini Trolli, szczególnie w Galerii Szamanów; v0.36.11 utrzymuje 8 równoczesnych spawnów dla celu 5 zabójstw."
)
HELP_TOPICS.setdefault("trolle", []).append(
    "v1.12.8: trollowe zlecenia dają od 15000 EXP do każdej z sześciu statystyk osobno; Polowanie na Trolli Szamanów daje 18000, Wojenny Szlak Trolli 20000, a Król Trolli 25000 do każdej statystyki."
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


def troll_quest_stat_rewards_audit_v1128():
    errors = []
    for quest_id, expected in V1128_TROLL_QUEST_STAT_REWARDS.items():
        quest = QUESTS.get(quest_id)
        # mountain_troll_hunt is legacy-authored outside this module; all IDs are
        # expected in the assembled runtime, but report absence clearly.
        if not isinstance(quest, dict):
            errors.append(f"missing troll quest: {quest_id}")
            continue
        manual = int(quest.get("manual_stat_progress", 0) or 0)
        visible = int(quest.get("reward_stat_progress", 0) or 0)
        if manual != expected:
            errors.append(f"{quest_id}: manual stat reward {manual}, expected {expected}")
        if visible != expected:
            errors.append(f"{quest_id}: visible stat reward {visible}, expected {expected}")
    return {
        "version": "1.12.8",
        "quests_checked": len(V1128_TROLL_QUEST_STAT_REWARDS),
        "minimum_per_stat": min(V1128_TROLL_QUEST_STAT_REWARDS.values()),
        "error_count": len(errors),
        "errors": errors,
    }


TROLL_QUEST_STAT_REWARDS_AUDIT_V1128 = troll_quest_stat_rewards_audit_v1128()
if TROLL_QUEST_STAT_REWARDS_AUDIT_V1128["error_count"]:
    raise RuntimeError(
        "Troll Quest Stat Rewards Audit v1.12.8 failed: "
        + "; ".join(TROLL_QUEST_STAT_REWARDS_AUDIT_V1128["errors"][:100])
    )


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
