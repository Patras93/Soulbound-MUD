# -*- coding: utf-8 -*-
"""Soulbound v3.31.3: additive, action-backed paths for all 14 professions.

These quests never overwrite old IDs, balances or saved SQLite rows. New
work orders form a prerequisite ladder per profession and are repeatable
after the existing hourly cooldown.
No level hard-locks are introduced; min_profession_level is an informative
milestone, as in the existing quest-offer system.
"""
from __future__ import annotations

from config.balance import QUEST_REPEAT_COOLDOWN_SECONDS
from data.catalog_mutations import catalog_assign
from systems.profession_quest_expansion import PROFESSION_QUEST_SPECS_V0700

# Beginner milestones: real actions, all available from reachable mentors.
BEGINNER_STAGES = (
    (1, 3, 1500, 1000, 1600, "Pierwsza praktyka"),
    (3, 4, 2000, 1400, 2200, "Samodzielna praca"),
    (6, 5, 2700, 1800, 2800, "Warsztatowe podstawy"),
    (10, 6, 3500, 2400, 3600, "Sprawdzian ucznia"),
    (15, 7, 4400, 3000, 4600, "Nowa wprawa"),
    (20, 8, 5600, 3900, 6000, "Zlecenie czeladnika"),
    (30, 10, 7200, 4800, 7800, "Rzetelne rzemiosło"),
    (40, 12, 9000, 6100, 9600, "Pierwsza mistrzowska próba"),
)

# Four professions previously had only 25 associated quests and just ten
# repeatables each. Add a durable path through level 800, without replacing
# their old one-shot journey, ranks or five-times-higher XP requirements.
UNDERREPRESENTED = frozenset(("Krawiectwo", "Garbarstwo", "Stolarstwo", "Zaklinanie"))
CONTINUATION_LEVELS = (
    60, 80, 100, 120, 140, 160, 180, 220, 260, 300, 340,
    380, 420, 460, 500, 540, 580, 620, 660, 700, 740, 800,
)

# Unique names per profession and milestone, while sharing the same event
# engine as existing mastery orders; descriptions promise only real actions.
IDENTITIES = {
    "Wędkarstwo": ("Ścieżka Rybaka", "połów i selekcja ryb"),
    "Górnictwo": ("Ścieżka Górnika", "wydobycie rud i minerałów"),
    "Drwalstwo": ("Ścieżka Drwala", "pozyskanie drewna"),
    "Kowalstwo": ("Ścieżka Kowala", "pracę przy kuźni"),
    "Gotowanie": ("Ścieżka Kucharza", "przygotowanie potraw"),
    "Zielarstwo": ("Ścieżka Zielarki", "zbieranie ziół"),
    "Alchemia": ("Ścieżka Alchemika", "warzenie mikstur"),
    "Jubilerstwo": ("Ścieżka Jubilera", "wykonywanie biżuterii"),
    "Krawiectwo": ("Ścieżka Krawca", "szycie i przygotowanie tkanin"),
    "Garbarstwo": ("Ścieżka Garbarza", "garbowanie i obróbkę skór"),
    "Stolarstwo": ("Ścieżka Stolarza", "obróbkę drewna i pracę stolarską"),
    "Zaklinanie": ("Ścieżka Zaklinacza", "wykonywanie zaklęć rzemieślniczych"),
    "Archeologia": ("Ścieżka Archeologa", "badanie stanowisk i wykopaliska"),
    "Kartografia": ("Ścieżka Kartografa", "pomiary i dokumentowanie terenu"),
}
CONTINUATION_THEMES = (
    "Rzemieślniczy szlak", "Praca bez pośpiechu", "Precyzyjny warsztat",
    "Zlecenie osady", "Próba zręczności", "Warsztat kupiecki",
    "Zlecenie wędrowców", "Praca dla strażników", "Dawna technika",
    "Zamówienie gildii", "Dzieło przy mistrzu", "Wyprawowy warsztat",
    "Rytm wielkiej pracowni", "Rzemiosło dalekich krain",
    "Zadanie arcymistrza", "Sztuka precyzji", "Wielki kontrakt",
    "Dziedzictwo pracowni", "Mistrzowska seria", "Próba wytrwałości",
    "Dzieło pokoleń", "Warsztat bez granic",
)

QUEST_IDS_BY_PROFESSION = {}
ADDED_IDS = []


def install(quests, npcs):
    """Register 112 beginner and 88 follow-on quests exactly once at boot."""
    if ADDED_IDS:
        raise RuntimeError("v3.31.3 profession quests installed twice")
    if set(IDENTITIES) != {name for name, *_ in PROFESSION_QUEST_SPECS_V0700}:
        raise RuntimeError("v3.31.3: profession roster changed")
    for profession, tool_type, npc_id, _ in PROFESSION_QUEST_SPECS_V0700:
        if npc_id not in npcs:
            raise RuntimeError(f"v3.31.3 missing master NPC: {npc_id}")
        npc = npcs[npc_id]
        giver = str(npc.get("name") or npc_id)
        theme, activity = IDENTITIES[profession]
        novice = []
        advanced = []
        previous_qid = None
        for level, needed, prof_xp, tool_xp, silver, stage_title in BEGINNER_STAGES:
            qid = f"v3313_apprentice_{tool_type}_{level}"
            if qid in quests:
                raise RuntimeError(f"v3.31.3 duplicate quest: {qid}")
            quest = {
                "name": f"{theme}: {stage_title}",
                "giver": giver,
                "kind": "profession_action", "target": profession,
                "needed": needed,
                "description": (
                    f"Praktyczne zlecenie profesji {profession} (etap {level}). "
                    f"Po przyjęciu wykonaj {needed} nowych rzeczywistych czynności: {activity}. "
                    "Liczą się wyłącznie akcje wykonane po przyjęciu. "
                    "Zlecenie odnawia się po godzinie od ukończenia."
                ),
                "required_profession": profession,
                "min_profession_level": level,
                "generator_level": level,
                "specialist_tool_type": tool_type,
                "reward_profession": profession, "reward_profession_xp": prof_xp,
                "reward_tool_type": tool_type, "reward_tool_xp": tool_xp,
                "reward_silver": silver, "reward_gold": 0, "reward_mithril": 0,
                "reward_items": {}, "repeatable": True,
                "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
                "v3313_apprentice": True,
            }
            if previous_qid:
                quest["requires_quest"] = previous_qid
            previous_qid = qid
            catalog_assign(quest, "QUESTS", quests, (qid,))
            novice.append(qid)
            ADDED_IDS.append(qid)
        if profession in UNDERREPRESENTED:
            for level, title in zip(CONTINUATION_LEVELS, CONTINUATION_THEMES, strict=True):
                qid = f"v3313_practice_{tool_type}_{level}"
                if qid in quests:
                    raise RuntimeError(f"v3.31.3 duplicate quest: {qid}")
                needed = 12 + level // 35
                prof_xp = 2200 + int(26 * (level ** 1.19))
                tool_xp = int(prof_xp * 0.7)
                quest = {
                    "name": f"{theme}: {title}",
                    "giver": giver,
                    "kind": "profession_action", "target": profession,
                    "needed": needed,
                    "description": (
                        f"Powtarzalna próba {profession}, etap {level}: wykonaj "
                        f"{needed} nowych czynności ({activity}) po przyjęciu zlecenia. "
                        "Nie wymaga resetu profesji ani ponownej nauki narzędzia. "
                        "Zlecenie odnawia się po godzinie od ukończenia."
                    ),
                    "required_profession": profession,
                    "min_profession_level": level,
                    "generator_level": level,
                    "specialist_tool_type": tool_type,
                    "reward_profession": profession, "reward_profession_xp": prof_xp,
                    "reward_tool_type": tool_type, "reward_tool_xp": tool_xp,
                    "reward_silver": 2500 + 110 * level,
                    "reward_gold": 0, "reward_mithril": 0,
                    "reward_items": {}, "repeatable": True,
                    "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
                    "v3313_continuation": True,
                }
                quest["requires_quest"] = previous_qid
                previous_qid = qid
                catalog_assign(quest, "QUESTS", quests, (qid,))
                advanced.append(qid)
                ADDED_IDS.append(qid)
        # Preserve the original starter in the first menu slot. New novice
        # tasks come next and can be accepted using existing `przyjmij 1`.
        current = list(npc.get("specialist_quests") or ())
        old_starter = [qid for qid in current if quests.get(qid, {}).get("starter_quest")]
        rest = [qid for qid in current if qid not in old_starter]
        catalog_assign(tuple(old_starter + novice + rest + advanced),
                       "NPCS", npcs, (npc_id, "specialist_quests"))
        QUEST_IDS_BY_PROFESSION[profession] = tuple(novice + advanced)
    if len(ADDED_IDS) != 200:
        raise RuntimeError(f"v3.31.3 expected 200 new profession quests, got {len(ADDED_IDS)}")
    return {"added_quests": len(ADDED_IDS), "professions": len(QUEST_IDS_BY_PROFESSION),
            "beginner": len(BEGINNER_STAGES)*len(QUEST_IDS_BY_PROFESSION),
            "continuation": len(ADDED_IDS)-len(BEGINNER_STAGES)*len(QUEST_IDS_BY_PROFESSION)}
