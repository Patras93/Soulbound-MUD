# -*- coding: utf-8 -*-
"""Soulbound v0.56.0 - living taverns and hourly quests for otherwise idle NPCs.

This module runs after the world expansions/runtime progression have populated the
shared catalogs.  It adds innkeepers to the eight non-capital postal settlements,
gives every new innkeeper three hourly quests, and finally guarantees that every
NPC which still has no quest receives one safe hourly errand.
"""
from __future__ import annotations

import hashlib
import math
import re

from core.generator_core import axis_gain, quest_currency_for_stage

from data.catalogs import ITEMS, MOB_TEMPLATES, NPCS, QUESTS, ROOMS
from data.catalog_mutations import catalog_assign
import systems.content_registry as content_registry

V0560_VERSION = "0.56.0"
V0560_HOURLY_COOLDOWN = 60 * 60

# Existing inns already placed by World Expansion I/II.
V0560_TAVERNS = {
    "birch": {
        "room": "birch_inn", "zone": "Brzozowy Trakt",
        "tavern": "Karczma Pod Białą Korą", "npc_id": "innkeeper_mirael",
        "npc": "Karczmarka Mirael", "categories": ("wood", "herb"), "enemy": "bandit",
    },
    "iron": {
        "room": "iron_inn", "zone": "Żelazne Bramy",
        "tavern": "Karczma Pod Młotem", "npc_id": "innkeeper_hrod",
        "npc": "Karczmarz Hrod", "categories": ("ore", "herb"), "enemy": "bandit",
    },
    "ash": {
        "room": "ash_inn", "zone": "Twierdza Popiołu",
        "tavern": "Gospoda Ostatniego Ognia", "npc_id": "innkeeper_vesna",
        "npc": "Karczmarka Vesna", "categories": ("ore", "herb"), "enemy": "bandit",
    },
    "fog": {
        "room": "fog_inn", "zone": "Port Mglistych Wysp",
        "tavern": "Karczma Pod Mglistą Latarnią", "npc_id": "innkeeper_nilo",
        "npc": "Karczmarz Nilo", "categories": ("fish", "herb"), "enemy": "bandit",
    },
    "silver": {
        "room": "silver_crown_inn", "zone": "Srebrna Korona",
        "tavern": "Gospoda Czterech Szlaków", "npc_id": "innkeeper_celene",
        "npc": "Karczmarka Celene", "categories": ("fish", "herb"), "enemy": "bandit",
    },
    "green": {
        "room": "green_shore_inn", "zone": "Zielony Brzeg",
        "tavern": "Karczma Nad Zieloną Wodą", "npc_id": "innkeeper_joran",
        "npc": "Karczmarz Joran", "categories": ("fish", "wood"), "enemy": "bandit",
    },
    "stone": {
        "room": "stone_watch_inn", "zone": "Kamienna Straż",
        "tavern": "Gospoda Pod Tarczą", "npc_id": "innkeeper_runa",
        "npc": "Karczmarka Runa", "categories": ("ore", "wood"), "enemy": "bandit",
    },
    "quiet": {
        "room": "quiet_haven_inn", "zone": "Cicha Przystań",
        "tavern": "Gospoda Cichego Dzwonu", "npc_id": "innkeeper_tavin",
        "npc": "Karczmarz Tavin", "categories": ("fish", "herb"), "enemy": "bandit",
    },
}

_CATEGORY_INFO = {
    "fish": ("ryb", "Wędkarstwo", "fishing"),
    "ore": ("rud", "Górnictwo", "mining"),
    "wood": ("sztuk drewna", "Drwalstwo", "woodcutting"),
    "herb": ("ziół", "Zielarstwo", "herbalism"),
}

# Conservative town stage hints.  They only scale the fixed hourly rewards;
# they do not gate acceptance, in keeping with Soulbound's no-global-level-gate rule.
_TOWN_STAGE = {
    "Brzozowy Trakt": 35,
    "Żelazne Bramy": 75,
    "Twierdza Popiołu": 150,
    "Port Mglistych Wysp": 115,
    "Srebrna Korona": 180,
    "Zielony Brzeg": 55,
    "Kamienna Straż": 140,
    "Cicha Przystań": 200,
}


def _safe_id(value: str) -> str:
    text = re.sub(r"[^a-z0-9_]+", "_", str(value).casefold())
    return text.strip("_") or "npc"


def _add_tavern_network():
    created_npcs = []
    created_quests = []
    for key, spec in V0560_TAVERNS.items():
        room_id = spec["room"]
        if room_id not in ROOMS:
            continue
        stage = int(_TOWN_STAGE.get(spec["zone"], 50))
        qids = []
        for idx, category in enumerate(spec["categories"], 1):
            label, profession, tool_type = _CATEGORY_INFO[category]
            qid = f"v0560_tavern_{key}_{category}"
            needed = 8
            quest = {
                "name": f"{spec['tavern']}: Zapasy {idx}",
                "giver": spec["npc"],
                "kind": "collect_category",
                "target": category,
                "needed": needed,
                "description": (
                    f"Zdobądź {needed} {label} dla {spec['tavern']} i wróć do {spec['npc']}. "
                    "Zlecenie odnawia się niezależnie co godzinę."
                ),
                "generator_level": stage,
                "reward_profession": profession,
                "reward_profession_xp": max(350, stage * 7),
                "reward_tool_type": tool_type,
                "reward_tool_xp": max(300, stage * 5),
                "character_xp_reward": max(25, int(axis_gain("character", stage, 1.75))),
                "reward_silver": quest_currency_for_stage(stage, math.sqrt(needed), True, qid),
                "reward_gold": 0,
                "reward_mithril": 0,
                "reward_items": {},
                "repeatable": True,
                "repeat_cooldown": V0560_HOURLY_COOLDOWN,
                "v0560_tavern_hourly": True,
            }
            catalog_assign(quest, "QUESTS", QUESTS, (qid,))
            qids.append(qid); created_quests.append(qid)

        kill_qid = f"v0560_tavern_{key}_security"
        kill_needed = 8
        kill_quest = {
            "name": f"{spec['tavern']}: Bezpieczna droga",
            "giver": spec["npc"],
            "kind": "kill",
            "target": spec["enemy"],
            "needed": kill_needed,
            "description": (
                f"Pokonaj {kill_needed} bandytów zagrażających podróżnym i dostawom do {spec['tavern']}, "
                f"a następnie wróć do {spec['npc']}. Zlecenie odnawia się co godzinę."
            ),
            "generator_level": stage,
            "reward_stat_progress": max(60, stage * 3),
            "reward_soul_xp": max(250, stage * 16),
            "character_xp_reward": max(25, int(axis_gain("character", stage, 2.0))),
            "reward_silver": quest_currency_for_stage(stage, math.sqrt(kill_needed), True, kill_qid),
            "reward_gold": 0,
            "reward_mithril": 0,
            "reward_items": {},
            "repeatable": True,
            "repeat_cooldown": V0560_HOURLY_COOLDOWN,
            "v0560_tavern_hourly": True,
        }
        catalog_assign(kill_quest, "QUESTS", QUESTS, (kill_qid,))
        qids.append(kill_qid); created_quests.append(kill_qid)

        npc = {
            "name": spec["npc"],
            "room": room_id,
            "dialogue": (
                f"Prowadzę {spec['tavern']}. Mam trzy niezależne zlecenia dla podróżnych; "
                "każde odnawia się po 60 minutach od ukończenia."
            ),
            "quest": qids[0],
            "quest_chain": tuple(qids[1:]),
            "v0560_tavern_keeper": True,
        }
        catalog_assign(npc, "NPCS", NPCS, (spec["npc_id"],))
        created_npcs.append(spec["npc_id"])
    return tuple(created_npcs), tuple(created_quests)


def _npc_explicit_quest_ids(npc):
    ids = []
    for key in ("quest", "quest_chain", "specialist_quests", "quests"):
        value = npc.get(key)
        if isinstance(value, str):
            ids.append(value)
        elif value:
            ids.extend(value)
    return tuple(qid for qid in ids if qid in QUESTS)


def _npc_has_any_quest(npc):
    if _npc_explicit_quest_ids(npc):
        return True
    giver = str(npc.get("name") or "").strip().casefold()
    if not giver:
        return False
    return any(str(q.get("giver") or "").strip().casefold() == giver for q in QUESTS.values())


def _stable_index_v0712(identity, count):
    count = max(1, int(count))
    raw = hashlib.sha256(str(identity).encode("utf-8")).digest()
    return int.from_bytes(raw[:8], "big") % count


def _choose_hourly_partner(source_id, source):
    """Choose a varied, preferably local partner instead of alphabetic-first.

    v0.71.2: the old policy sorted all candidates and always took row zero.  In
    dense zones this caused dozens of unrelated errands to converge on the same
    NPC (notably Lyra/Ilyra-like first names).  We now choose deterministically
    *within the best locality tier*, so the result is stable across restarts but
    distributed among NPCs from the same zone.
    """
    source_room = str(source.get("room") or "")
    source_zone = str((ROOMS.get(source_room) or {}).get("zone") or "")
    same_zone_other_room = []
    same_room = []
    global_candidates = []
    for npc_id, npc in NPCS.items():
        if npc_id == source_id or not npc.get("room"):
            continue
        target_room = str(npc.get("room") or "")
        row = (str(npc_id), npc)
        global_candidates.append(row)
        if target_room == source_room:
            same_room.append(row)
        elif source_zone and str((ROOMS.get(target_room) or {}).get("zone") or "") == source_zone:
            same_zone_other_room.append(row)

    for tier_name, candidates in (
        ("zone", same_zone_other_room),
        ("room", same_room),
        ("world", global_candidates),
    ):
        if not candidates:
            continue
        candidates = sorted(candidates, key=lambda row: row[0])
        idx = _stable_index_v0712(f"hourly-partner:{tier_name}:{source_id}", len(candidates))
        return candidates[idx]
    return None, None


def _choose_hourly_kill_target_v0712(source_id, source):
    """Pick the nearest sensible ordinary mob reachable from the NPC.

    v0.71.2 deliberately ignores training dummies, bosses and instance-only
    scripted targets.  A short BFS keeps patrols local without forcing every
    town to have a spawn in the exact same zone.
    """
    source_room = str(source.get("room") or "")
    if source_room not in ROOMS:
        return None

    mobs_by_room = {}
    for room_id, mob_id in tuple(getattr(content_registry, "MOB_SPAWNS", ()) or ()):
        mob = MOB_TEMPLATES.get(str(mob_id)) or {}
        if not mob:
            continue
        rank = str(mob.get("rank") or mob.get("mob_rank") or "normal").casefold()
        mob_name = str(mob.get("name") or "").casefold()
        mob_key = str(mob_id).casefold()
        if rank in {"world_boss", "boss"} or mob.get("crypt_boss") or mob.get("tower_boss"):
            continue
        if "dummy" in mob_key or "manekin" in mob_name:
            continue
        mobs_by_room.setdefault(str(room_id), set()).add(str(mob_id))

    seen = {source_room}
    frontier = [source_room]
    for distance in range(0, 9):
        candidates = sorted({mob_id for room_id in frontier for mob_id in mobs_by_room.get(room_id, ())})
        if candidates:
            idx = _stable_index_v0712(f"hourly-kill:{source_id}:distance:{distance}", len(candidates))
            return candidates[idx]
        next_frontier = []
        for room_id in frontier:
            exits = (ROOMS.get(room_id) or {}).get("exits") or {}
            for target_room in exits.values():
                target_room = str(target_room or "")
                if target_room in ROOMS and target_room not in seen:
                    seen.add(target_room)
                    next_frontier.append(target_room)
        if not next_frontier:
            break
        frontier = next_frontier
    return None


def _hourly_character_xp_v0712(stage, intensity):
    # Never allow the old 1-XP fallback.  Scale with the same Character Level
    # curve as the rest of Generator Core so late-game errands remain relevant.
    return max(25, int(axis_gain("character", stage, intensity)))


def _hourly_collect_category_v0712(source_id):
    categories = tuple(sorted(_CATEGORY_INFO))
    return categories[_stable_index_v0712(f"hourly-resource:{source_id}", len(categories))]


def _add_hourly_quests_for_idle_npcs():
    created = []
    covered = []
    for npc_id, npc in list(NPCS.items()):
        if _npc_has_any_quest(npc):
            continue

        room = ROOMS.get(str(npc.get("room") or ""), {})
        stage = max(1, int(room.get("generator_level", room.get("recommended_mastery", 1)) or 1))
        stage = min(400, stage)
        qid = f"v0560_hourly_npc_{_safe_id(npc_id)}"
        giver = str(npc.get("name") or npc_id)
        target_id, target = _choose_hourly_partner(npc_id, npc)
        variant = ("talk", "deliver", "collect", "kill")[_stable_index_v0712(f"hourly-kind:{npc_id}", 4)]
        kill_target = _choose_hourly_kill_target_v0712(npc_id, npc) if variant == "kill" else None

        # If a locality cannot support the initially selected objective, fall
        # back to gathering rather than creating a cross-world nonsensical kill.
        if variant in {"talk", "deliver"} and (not target_id or not target):
            variant = "collect"
        if variant == "kill" and not kill_target:
            variant = "collect"

        quest = {
            "giver": giver,
            "generator_level": stage,
            "reward_gold": 0,
            "reward_mithril": 0,
            "reward_items": {},
            "repeatable": True,
            "repeat_cooldown": V0560_HOURLY_COOLDOWN,
            "v0560_generated_hourly": True,
            "v0560_source_npc": npc_id,
            "v0712_hourly_kind": variant,
        }

        if variant == "talk":
            quest.update({
                "name": f"Godzinne zlecenie: Lokalne wieści od {giver}",
                "kind": "talk_npc",
                "target_npc": target_id,
                "needed": 1,
                "description": (
                    f"Porozmawiaj z NPC: {target.get('name', target_id)} i wróć z wiadomościami. "
                    "Zlecenie odnawia się po 60 minutach od ukończenia."
                ),
                "character_xp_reward": _hourly_character_xp_v0712(stage, 1.25),
                "reward_silver": quest_currency_for_stage(stage, 1.0, True, qid),
            })
        elif variant == "deliver":
            item_id = f"v0712_hourly_parcel_{_safe_id(npc_id)}"
            if item_id not in ITEMS:
                catalog_assign({
                    "name": f"Zapieczętowana przesyłka od {giver}",
                    "type": "quest",
                    "price": None,
                    "desc": f"Godzinna przesyłka od {giver} dla {target.get('name', target_id)}.",
                    "v0712_hourly_delivery": True,
                }, "ITEMS", ITEMS, (item_id,))
            quest.update({
                "name": f"Godzinne zlecenie: Przesyłka od {giver}",
                "kind": "deliver_npc",
                "target_npc": target_id,
                "quest_item": item_id,
                "accept_items": {item_id: 1},
                "needed": 1,
                "description": (
                    f"Dostarcz zapieczętowaną przesyłkę do NPC: {target.get('name', target_id)}. "
                    "Zlecenie odnawia się po 60 minutach od ukończenia."
                ),
                "character_xp_reward": _hourly_character_xp_v0712(stage, 1.50),
                "reward_silver": quest_currency_for_stage(stage, 1.25, True, qid),
            })
        elif variant == "kill":
            needed = 5 + _stable_index_v0712(f"hourly-kill-count:{npc_id}", 4)
            mob_name = str((MOB_TEMPLATES.get(kill_target) or {}).get("name") or kill_target)
            quest.update({
                "name": f"Godzinne zlecenie: Patrol dla {giver}",
                "kind": "kill",
                "target": kill_target,
                "needed": needed,
                "description": (
                    f"Pokonaj {needed} przeciwników: {mob_name}, a potem wróć do {giver}. "
                    "Zlecenie odnawia się po 60 minutach od ukończenia."
                ),
                "character_xp_reward": _hourly_character_xp_v0712(stage, 2.0),
                "reward_stat_progress": max(20, int(axis_gain("stat", stage, 1.25))),
                "reward_soul_xp": max(50, int(axis_gain("soul", stage, 1.50))),
                "reward_silver": quest_currency_for_stage(stage, math.sqrt(needed), True, qid),
            })
        else:
            category = _hourly_collect_category_v0712(npc_id)
            label, profession, tool_type = _CATEGORY_INFO[category]
            needed = 5 + _stable_index_v0712(f"hourly-collect-count:{npc_id}", 5)
            quest.update({
                "name": f"Godzinne zlecenie: Zaopatrzenie dla {giver}",
                "kind": "collect_category",
                "target": category,
                "needed": needed,
                "description": (
                    f"Zdobądź {needed} {label} dla {giver}. "
                    "Zlecenie odnawia się po 60 minutach od ukończenia."
                ),
                "reward_profession": profession,
                "reward_profession_xp": max(100, int(axis_gain("profession", stage, 1.50))),
                "reward_tool_type": tool_type,
                "reward_tool_xp": max(80, int(axis_gain("tool", stage, 1.25))),
                "character_xp_reward": max(25, int(axis_gain("character", stage, 1.75))),
                "reward_silver": quest_currency_for_stage(stage, math.sqrt(needed), True, qid),
            })

        catalog_assign(quest, "QUESTS", QUESTS, (qid,))
        catalog_assign(qid, "NPCS", NPCS, (npc_id, "quest"))
        created.append(qid)
        covered.append(npc_id)
    return tuple(created), tuple(covered)


V0560_TAVERN_NPC_IDS, V0560_TAVERN_QUEST_IDS = _add_tavern_network()
V0560_GENERATED_HOURLY_IDS = ()
V0560_GENERATED_NPC_IDS = ()
V0560_ALL_HOURLY_IDS = tuple(V0560_TAVERN_QUEST_IDS)
V0560_LIVING_NPCS_STATE = {}


def _refresh_living_npcs_state():
    global V0560_ALL_HOURLY_IDS, V0560_LIVING_NPCS_STATE
    V0560_ALL_HOURLY_IDS = tuple(dict.fromkeys(V0560_TAVERN_QUEST_IDS + V0560_GENERATED_HOURLY_IDS))
    old_hourlies = tuple(getattr(content_registry, "HOURLY_QUEST_IDS", ()) or ())
    content_registry.HOURLY_QUEST_IDS = tuple(dict.fromkeys(old_hourlies + V0560_ALL_HOURLY_IDS))
    V0560_LIVING_NPCS_STATE = {
        "tavern_count": len(V0560_TAVERN_NPC_IDS),
        "tavern_hourly_count": len(V0560_TAVERN_QUEST_IDS),
        "generated_hourly_count": len(V0560_GENERATED_HOURLY_IDS),
        "generated_npc_count": len(V0560_GENERATED_NPC_IDS),
        "npc_count": len(NPCS),
        "npc_without_quest_count": sum(1 for npc in NPCS.values() if not _npc_has_any_quest(npc)),
    }
    return dict(V0560_LIVING_NPCS_STATE)


def ensure_hourly_quests_for_idle_npcs():
    """Idempotently cover NPCs added after the initial world bootstrap.

    Some legacy/runtime layers still append NPCs late in the manifest.  Running
    this reconciliation again is safe: NPCs already covered by any quest are
    skipped, while newly-added NPCs receive the same varied hourly quest policy.
    """
    global V0560_GENERATED_HOURLY_IDS, V0560_GENERATED_NPC_IDS
    new_ids, new_npcs = _add_hourly_quests_for_idle_npcs()
    if new_ids:
        V0560_GENERATED_HOURLY_IDS = tuple(dict.fromkeys(V0560_GENERATED_HOURLY_IDS + tuple(new_ids)))
    if new_npcs:
        V0560_GENERATED_NPC_IDS = tuple(dict.fromkeys(V0560_GENERATED_NPC_IDS + tuple(new_npcs)))
    state = _refresh_living_npcs_state()
    return {
        "new_hourly_ids": tuple(new_ids),
        "new_npc_ids": tuple(new_npcs),
        "state": state,
    }


# Initial pass after world expansion/runtime progression. A second reconciliation
# runs near the end of the runtime manifest for NPCs created by later legacy layers.
ensure_hourly_quests_for_idle_npcs()

__all__ = [
    "V0560_VERSION", "V0560_HOURLY_COOLDOWN", "V0560_TAVERNS",
    "V0560_TAVERN_NPC_IDS", "V0560_TAVERN_QUEST_IDS",
    "V0560_GENERATED_HOURLY_IDS", "V0560_GENERATED_NPC_IDS",
    "V0560_ALL_HOURLY_IDS", "V0560_LIVING_NPCS_STATE",
    "ensure_hourly_quests_for_idle_npcs",
]
