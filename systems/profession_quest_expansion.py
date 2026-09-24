# -*- coding: utf-8 -*-
"""Soulbound v0.70.0 - large profession quest expansion.

Adds four repeatable mastery contracts for every one of the twelve professions.
Progress counts real profession actions performed after accepting a contract.
"""
from __future__ import annotations

from config.balance import QUEST_REPEAT_COOLDOWN_SECONDS
from data.quests import QUESTS
from data.npcs import NPCS
from data.catalog_mutations import catalog_assign

PROFESSION_QUEST_EXPANSION_VERSION = "0.71.0"

# profession, tool type, specialist npc, short action wording
PROFESSION_QUEST_SPECS_V0700 = (
    ("Wędkarstwo", "fishing", "specialist_fishing", "wykonuj połowy"),
    ("Górnictwo", "mining", "specialist_mining", "wydobywaj surowce"),
    ("Drwalstwo", "woodcutting", "specialist_woodcutting", "pozyskuj drewno"),
    ("Kowalstwo", "crafting", "specialist_crafting", "pracuj przy kuźni i rzemiośle"),
    ("Gotowanie", "cooking", "specialist_cooking", "przygotowuj potrawy"),
    ("Zielarstwo", "herbalism", "specialist_herbalism", "zbieraj zioła"),
    ("Alchemia", "alchemy", "specialist_alchemy", "warz mikstury i eliksiry"),
    ("Jubilerstwo", "jewelcrafting", "jeweler_mirella", "twórz biżuterię"),
    ("Krawiectwo", "tailoring", "tailor_lysa", "wykonuj prace krawieckie"),
    ("Garbarstwo", "leatherworking", "leatherworker_soren", "obrabiaj skóry i wykonuj wyroby"),
    ("Stolarstwo", "carpentry", "carpenter_edric", "wykonuj prace stolarskie"),
    ("Zaklinanie", "enchanting", "guild_quartermaster_arcane", "wykonuj zaklęcia rzemieślnicze"),
)

# min profession level, actions, reward profession XP, reward tool XP, silver
PROFESSION_QUEST_STAGES_V0700 = (
    (50, 10, 1400, 900, 2500),
    (150, 15, 4200, 2800, 9000),
    (300, 20, 10500, 7000, 25000),
    (500, 25, 26000, 17000, 60000),
)

PROFESSION_QUEST_IDS_V0700 = []
PROFESSION_QUEST_IDS_BY_PROFESSION_V0700 = {}


def _slug(text):
    table = str.maketrans("ąćęłńóśżźĄĆĘŁŃÓŚŻŹ", "acelnoszzACELNOSZZ")
    return "".join(ch for ch in str(text).translate(table).lower() if ch.isalnum() or ch == "_")


for profession, tool_type, npc_id, action_text in PROFESSION_QUEST_SPECS_V0700:
    if npc_id not in NPCS:
        raise RuntimeError(f"v0.70.0 missing profession specialist NPC: {npc_id}")
    npc = NPCS[npc_id]
    giver = str(npc.get("name") or npc_id)
    existing = list(npc.get("specialist_quests") or ())
    generated = []
    for stage_no, (min_level, needed, prof_xp, tool_xp, silver) in enumerate(PROFESSION_QUEST_STAGES_V0700, 1):
        quest_id = f"v0700_prof_{_slug(tool_type)}_{min_level}"
        if quest_id in QUESTS:
            raise RuntimeError(f"v0.70.0 duplicate profession quest id: {quest_id}")
        title = (
            f"Mistrzostwo {profession} {stage_no}: "
            f"Próba poziomu {min_level}"
        )
        quest = {
            "name": title,
            "giver": giver,
            "kind": "profession_action",
            "target": profession,
            "needed": int(needed),
            "description": (
                f"Po przyjęciu zadania wykonaj {needed} rzeczywistych akcji profesji {profession}: "
                f"{action_text}. Liczą się wyłącznie nowe akcje wykonane po przyjęciu questa."
            ),
            "required_profession": profession,
            "min_profession_level": int(min_level),
            "specialist_tool_type": tool_type,
            "reward_profession": profession,
            "reward_profession_xp": int(prof_xp),
            "reward_tool_type": tool_type,
            "reward_tool_xp": int(tool_xp),
            "reward_silver": int(silver),
            "reward_gold": 0,
            "reward_mithril": 0,
            "reward_items": {},
            "repeatable": True,
            "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
            "v0700_profession_contract": True,
        }
        catalog_assign(quest, "QUESTS", QUESTS, (quest_id,))
        generated.append(quest_id)
        PROFESSION_QUEST_IDS_V0700.append(quest_id)
    catalog_assign(tuple(existing + generated), "NPCS", NPCS, (npc_id, "specialist_quests"))
    # Zaklinanie previously used the arcane quartermaster only as a shopkeeper.
    if npc_id == "guild_quartermaster_arcane":
        catalog_assign("enchanting", "NPCS", NPCS, (npc_id, "specialist_tool_type"))
        catalog_assign("zaklinanie", "NPCS", NPCS, (npc_id, "specialist_topic"))
    PROFESSION_QUEST_IDS_BY_PROFESSION_V0700[profession] = tuple(generated)

PROFESSION_QUEST_EXPANSION_METRICS_V0700 = {
    "version": PROFESSION_QUEST_EXPANSION_VERSION,
    "profession_count": len(PROFESSION_QUEST_SPECS_V0700),
    "quests_per_profession": len(PROFESSION_QUEST_STAGES_V0700),
    "quest_count": len(PROFESSION_QUEST_IDS_V0700),
}


# v0.70.1 - beginner coverage for professions that historically had no level 1-10 quest.
# The runtime is checked first, so existing beginner quests are never duplicated.
BEGINNER_PROFESSION_QUEST_SPECS_V0701 = (
    ("Krawiectwo", "tailoring", "tailor_lysa", "wykonaj 3 prace krawieckie"),
    ("Garbarstwo", "leatherworking", "leatherworker_soren", "wykonaj 3 prace garbarskie"),
    ("Stolarstwo", "carpentry", "carpenter_edric", "wykonaj 3 prace stolarskie"),
    ("Zaklinanie", "enchanting", "guild_quartermaster_arcane", "wykonaj 3 zaklęcia rzemieślnicze"),
)
BEGINNER_PROFESSION_QUEST_IDS_V0701 = []
BEGINNER_PROFESSION_QUEST_SKIPPED_V0701 = []


def _has_beginner_profession_quest_v0701(profession):
    for quest in QUESTS.values():
        quest_profession = quest.get("required_profession") or quest.get("reward_profession")
        if quest_profession != profession:
            continue
        if int(quest.get("min_profession_level", 1) or 1) <= 10:
            return True
    return False


for profession, tool_type, npc_id, action_text in BEGINNER_PROFESSION_QUEST_SPECS_V0701:
    if _has_beginner_profession_quest_v0701(profession):
        BEGINNER_PROFESSION_QUEST_SKIPPED_V0701.append(profession)
        continue
    if npc_id not in NPCS:
        raise RuntimeError(f"v0.70.1 missing beginner profession NPC: {npc_id}")
    npc = NPCS[npc_id]
    giver = str(npc.get("name") or npc_id)
    quest_id = f"v0701_beginner_{tool_type}"
    if quest_id in QUESTS:
        raise RuntimeError(f"v0.70.1 duplicate beginner profession quest id: {quest_id}")
    quest = {
        "name": f"Pierwsze kroki: {profession}",
        "giver": giver,
        "kind": "profession_action",
        "target": profession,
        "needed": 3,
        "description": (
            f"Rozpocznij naukę profesji {profession}: {action_text}. "
            "Liczą się wyłącznie nowe akcje wykonane po przyjęciu zadania."
        ),
        "required_profession": profession,
        "min_profession_level": 1,
        "generator_level": 1,
        "specialist_tool_type": tool_type,
        "reward_profession": profession,
        "reward_profession_xp": 300,
        "reward_tool_type": tool_type,
        "reward_tool_xp": 200,
        "reward_silver": 1500,
        "reward_gold": 0,
        "reward_mithril": 0,
        "reward_items": {},
        "repeatable": False,
        "starter_quest": True,
        "v0701_beginner_profession": True,
    }
    catalog_assign(quest, "QUESTS", QUESTS, (quest_id,))
    current = list(npc.get("specialist_quests") or ())
    catalog_assign(tuple([quest_id] + current), "NPCS", NPCS, (npc_id, "specialist_quests"))
    BEGINNER_PROFESSION_QUEST_IDS_V0701.append(quest_id)

BEGINNER_PROFESSION_QUEST_METRICS_V0701 = {
    "version": "0.70.1",
    "added": len(BEGINNER_PROFESSION_QUEST_IDS_V0701),
    "skipped_existing": tuple(BEGINNER_PROFESSION_QUEST_SKIPPED_V0701),
}


# v0.71.0 - pełniejsze, jednorazowe ścieżki rozwoju profesji 1-600.
# Istniejące kontrakty v0.70.0 na 50/150/300/500 pozostają powtarzalne i
# niezależne; poniższe etapy wypełniają duże luki między nimi.
PROFESSION_JOURNEY_STAGES_V0710 = (
    # min level, actions, profession XP, tool XP, silver
    (25, 6, 700, 450, 1500),
    (75, 8, 1800, 1100, 3500),
    (100, 10, 2700, 1700, 5000),
    (200, 12, 6200, 4000, 12000),
    (250, 14, 8400, 5400, 17000),
    (350, 16, 13500, 8800, 30000),
    (400, 18, 17500, 11500, 40000),
    (450, 20, 22500, 14800, 50000),
    (550, 24, 35000, 22500, 75000),
    (600, 30, 50000, 32000, 100000),
)

PROFESSION_JOURNEY_QUEST_IDS_V0710 = []
PROFESSION_JOURNEY_IDS_BY_PROFESSION_V0710 = {}

for profession, tool_type, npc_id, action_text in PROFESSION_QUEST_SPECS_V0700:
    npc = NPCS[npc_id]
    giver = str(npc.get("name") or npc_id)
    current = list(npc.get("specialist_quests") or ())
    generated = []
    previous_journey_id = None
    for stage_no, (min_level, needed, prof_xp, tool_xp, silver) in enumerate(PROFESSION_JOURNEY_STAGES_V0710, 1):
        quest_id = f"v0710_journey_{_slug(tool_type)}_{min_level}"
        if quest_id in QUESTS:
            raise RuntimeError(f"v0.71.0 duplicate profession journey quest id: {quest_id}")
        quest = {
            "name": f"Droga Mistrza {profession}: etap {stage_no} — poziom {min_level}",
            "giver": giver,
            "kind": "profession_action",
            "target": profession,
            "needed": int(needed),
            "description": (
                f"Rozwiń profesję {profession} na kolejnym etapie mistrzostwa. "
                f"Po przyjęciu zadania wykonaj {needed} rzeczywistych akcji: {action_text}. "
                "Liczą się tylko nowe akcje wykonane po przyjęciu zadania."
            ),
            "required_profession": profession,
            "min_profession_level": int(min_level),
            "specialist_tool_type": tool_type,
            "reward_profession": profession,
            "reward_profession_xp": int(prof_xp),
            "reward_tool_type": tool_type,
            "reward_tool_xp": int(tool_xp),
            "reward_silver": int(silver),
            "reward_gold": 0,
            "reward_mithril": 0,
            "reward_items": {},
            "repeatable": False,
            "v0710_profession_journey": True,
        }
        if previous_journey_id:
            quest["requires_quest"] = previous_journey_id
        catalog_assign(quest, "QUESTS", QUESTS, (quest_id,))
        generated.append(quest_id)
        PROFESSION_JOURNEY_QUEST_IDS_V0710.append(quest_id)
        previous_journey_id = quest_id
    catalog_assign(tuple(current + generated), "NPCS", NPCS, (npc_id, "specialist_quests"))
    PROFESSION_JOURNEY_IDS_BY_PROFESSION_V0710[profession] = tuple(generated)

PROFESSION_JOURNEY_METRICS_V0710 = {
    "version": "0.71.0",
    "profession_count": len(PROFESSION_QUEST_SPECS_V0700),
    "stages_per_profession": len(PROFESSION_JOURNEY_STAGES_V0710),
    "quest_count": len(PROFESSION_JOURNEY_QUEST_IDS_V0710),
}
