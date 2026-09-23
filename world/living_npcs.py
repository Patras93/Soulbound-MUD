# -*- coding: utf-8 -*-
"""Soulbound v0.56.0 - living taverns and hourly quests for otherwise idle NPCs.

This module runs after the world expansions/runtime progression have populated the
shared catalogs.  It adds innkeepers to the eight non-capital postal settlements,
gives every new innkeeper three hourly quests, and finally guarantees that every
NPC which still has no quest receives one safe hourly errand.
"""
from __future__ import annotations

import math
import re

from core.generator_core import quest_currency_for_stage

from data.catalogs import NPCS, QUESTS, ROOMS
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


def _choose_hourly_partner(source_id, source):
    source_room = str(source.get("room") or "")
    source_zone = str((ROOMS.get(source_room) or {}).get("zone") or "")
    candidates = []
    for npc_id, npc in NPCS.items():
        if npc_id == source_id or not npc.get("room"):
            continue
        target_room = str(npc.get("room") or "")
        same_room = target_room == source_room
        same_zone = bool(source_zone) and str((ROOMS.get(target_room) or {}).get("zone") or "") == source_zone
        score = 0 if same_room else (1 if same_zone else 2)
        candidates.append((score, str(npc.get("name") or npc_id).casefold(), npc_id, npc))
    if not candidates:
        return None, None
    candidates.sort(key=lambda row: (row[0], row[1], row[2]))
    return candidates[0][2], candidates[0][3]


def _add_hourly_quests_for_idle_npcs():
    created = []
    covered = []
    for npc_id, npc in list(NPCS.items()):
        if _npc_has_any_quest(npc):
            continue
        target_id, target = _choose_hourly_partner(npc_id, npc)
        if not target_id or not target:
            continue
        room = ROOMS.get(str(npc.get("room") or ""), {})
        stage = max(1, int(room.get("generator_level", room.get("recommended_mastery", 1)) or 1))
        qid = f"v0560_hourly_npc_{_safe_id(npc_id)}"
        quest = {
            "name": f"Godzinne zlecenie: Wieści od {npc.get('name', npc_id)}",
            "giver": npc.get("name", npc_id),
            "kind": "talk_npc",
            "target_npc": target_id,
            "needed": 1,
            "description": (
                f"Porozmawiaj z NPC: {target.get('name', target_id)}. "
                "To krótkie zlecenie odnawia się po 60 minutach od ukończenia."
            ),
            "generator_level": stage,
            "reward_silver": quest_currency_for_stage(stage, 1.0, True, qid),
            "reward_gold": 0,
            "reward_mithril": 0,
            "reward_items": {},
            "repeatable": True,
            "repeat_cooldown": V0560_HOURLY_COOLDOWN,
            "v0560_generated_hourly": True,
            "v0560_source_npc": npc_id,
        }
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
    skipped, while newly-added NPCs receive the same hourly talk quest policy.
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
