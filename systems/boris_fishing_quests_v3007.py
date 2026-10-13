# -*- coding: utf-8 -*-
"""v3.00.7: Borys offers independent species, mixed-catch and discovery contracts.

All progress is credited by existing ResourceGatheredEvent and persisted in SQLite.
Catalog additions never edit previous quest definitions or character data.
"""
from __future__ import annotations

from config.balance import QUEST_REPEAT_COOLDOWN_SECONDS
from data.catalog_mutations import catalog_assign
from core.progression_resources import (
    RIVER_FISH_ATLAS, LAKE_FISH_ATLAS, SEA_FISH_ATLAS, OCEAN_FISH_ATLAS,
)

# Independent water-body quests come FIRST, so the original river assignment
# is not the only biome visible at the NPC. Each uses the existing fishing
# ResourceGatheredEvent.secondary_category == fish_<habitat>.
BORIS_WATERS_V3007 = (
    ("river", "Ryby rzeczne", 1, 20),
    ("lake", "Ryby jeziorne", 1, 20),
    ("sea", "Ryby morskie", 1, 20),
    ("ocean", "Ryby oceaniczne", 1, 20),
)

# A mix of common specimens, predators, magical fish and endgame catches.
# (ecosystem, recommended fishing stage, fish item_id, required new catches)
BORIS_SPECIES_V3007 = (
    ("river", 1, "river_bleak", 12),
    ("river", 5, "stone_loach", 10),
    ("river", 30, "brown_trout", 7),
    ("river", 50, "river_taimen", 5),
    ("river", 110, "spirit_grayling", 4),
    ("river", 150, "bloodfin_salmon", 3),
    ("river", 175, "star_river_eel", 2),
    ("river", 200, "eternal_river_dragon", 1),
    ("lake", 1, "lake_gudgeon", 12),
    ("lake", 8, "lake_smelt", 10),
    ("lake", 35, "golden_tench", 7),
    ("lake", 55, "deepwater_pike", 5),
    ("lake", 110, "moon_carp", 4),
    ("lake", 150, "astral_pike", 3),
    ("lake", 175, "mirror_sturgeon", 2),
    ("lake", 200, "eternal_lake_serpent", 1),
    ("sea", 1, "sand_eel", 12),
    ("sea", 10, "garfish", 10),
    ("sea", 35, "bluefish", 7),
    ("sea", 55, "conger_eel", 5),
    ("sea", 110, "storm_herring", 4),
    ("sea", 150, "abyss_conger", 3),
    ("sea", 175, "void_sole", 2),
    ("sea", 200, "eternal_sea_drake", 1),
    ("ocean", 1, "flying_fish", 12),
    ("ocean", 15, "bonito", 10),
    ("ocean", 30, "yellowfin_tuna", 7),
    ("ocean", 50, "king_mackerel", 5),
    ("ocean", 120, "celestial_swordfish", 4),
    ("ocean", 150, "astral_sunfish", 3),
    ("ocean", 180, "void_marlin", 2),
    ("ocean", 200, "world_leviathan", 1),
)

# (quest slug, title, recommended stage, {fish_id: required new catches})
BORIS_SETS_V3007 = (
    ("river_market", "Kosz rzecznych przysmaków", 5,
     {"river_bleak": 5, "stone_loach": 4}),
    ("lake_market", "Świeży zestaw jeziorny", 8,
     {"lake_gudgeon": 5, "lake_smelt": 4}),
    ("harbor_market", "Poranny połów portowy", 15,
     {"sand_eel": 5, "garfish": 4}),
    ("blue_water", "Ławica z błękitnych wód", 30,
     {"flying_fish": 5, "bonito": 4, "yellowfin_tuna": 2}),
    ("chef_favorites", "Wybór mistrza kuchni", 55,
     {"brown_trout": 3, "golden_tench": 3, "bluefish": 3}),
    ("predators", "Łowcy drapieżników", 110,
     {"river_taimen": 3, "deepwater_pike": 3, "conger_eel": 3}),
    ("astral_fish", "Astralne łuski", 150,
     {"bloodfin_salmon": 2, "astral_pike": 2, "abyss_conger": 2}),
    ("legendary_four", "Cztery legendarne wody", 200,
     {"eternal_river_dragon": 1, "eternal_lake_serpent": 1,
      "eternal_sea_drake": 1, "world_leviathan": 1}),
)

BORIS_DISCOVERY_V3007 = ((3, 1), (6, 10), (12, 50), (20, 125))
BORIS_QUEST_IDS_V3007 = ()


def install_boris_quests_v3007(quests, npcs, items):
    """Adds quests only; leaves old quests, identities and database schema alone."""
    global BORIS_QUEST_IDS_V3007
    npc = npcs["fisher_tomas"]
    habitats = {
        "river": (RIVER_FISH_ATLAS, "rzeki"),
        "lake": (LAKE_FISH_ATLAS, "jeziora"),
        "sea": (SEA_FISH_ATLAS, "morza"),
        "ocean": (OCEAN_FISH_ATLAS, "oceanu"),
    }
    all_species = set().union(*(atlas for atlas, _label in habitats.values()))
    new_ids = []

    def register(qid, data):
        if qid in quests:
            raise ValueError(f"Zdublowane zlecenie Borysa: {qid}")
        if int(data.get("needed", 0)) < 1:
            raise ValueError(f"Nieprawidłowy cel Borysa: {qid}")
        catalog_assign(data, "QUESTS", quests, (qid,))
        new_ids.append(qid)

    def reward(stage, multiplier=1):
        # No flat rewards: harder specimens / combinations pay substantially more.
        prof_xp = int((2400 + stage * 165) * multiplier)
        tool_xp = int((2200 + stage * 145) * multiplier)
        silver = int((2600 + stage * 460) * multiplier)
        return dict(
            reward_profession="Wędkarstwo", reward_profession_xp=prof_xp,
            reward_tool_type="fishing", reward_tool_xp=tool_xp,
            reward_silver=silver, reward_gold=0, reward_mithril=0,
            reward_items={}, repeatable=True,
            repeat_cooldown=QUEST_REPEAT_COOLDOWN_SECONDS,
        )

    # Four basic, separately repeatable categories: river, lake, sea, ocean.
    # No level requirements: novice players can accept any of them immediately.
    for habitat, title, stage, count in BORIS_WATERS_V3007:
        register(f"boris_waters_{habitat}", dict(
            name=f"Borys — {title}", giver=npc["name"],
            kind="collect_category", target=f"fish_{habitat}", needed=count,
            event_progress_only=True,
            recommended_profession_level=stage,
            description=f"Złów {count} ryb w wodach {habitats[habitat][1]} po przyjęciu zadania. "
                        "Zachowaj ryby do oddania. Zadanie odnawia się co godzinę.",
            **reward(stage),
        ))

    for habitat, stage, fish_id, count in BORIS_SPECIES_V3007:
        atlas, water = habitats[habitat]
        if fish_id not in atlas or fish_id not in items:
            raise ValueError(f"Nieistniejący lub niedostępny gatunek: {fish_id}")
        label = items[fish_id]["name"]
        register(f"boris_species_{fish_id}", dict(
            name=f"Borys — {label}", giver=npc["name"],
            kind="collect_resource", track_resource_progress=True,
            event_progress_only=True, target=fish_id, needed=count,
            recommended_profession_level=stage,
            description=(f"Złów {count} szt. gatunku {label} w wodach {water} "
                         "po przyjęciu zadania. Ryby muszą pozostać w siatce "
                         "lub ekwipunku do oddania."),
            **reward(stage),
        ))

    for slug, title, stage, requirements in BORIS_SETS_V3007:
        missing = set(requirements) - all_species
        if missing or any(item_id not in items for item_id in requirements):
            raise ValueError(f"Brak ryb do zestawu {slug}: {missing}")
        needed = sum(requirements.values())
        targets = ", ".join(f"{items[fid]['name']} x{qty}" for fid, qty in requirements.items())
        register(f"boris_set_{slug}", dict(
            name=f"Borys — {title}", giver=npc["name"],
            kind="collect_resource_set", resource_targets=dict(requirements),
            event_progress_only=True, target="fish", needed=needed,
            recommended_profession_level=stage,
            description=f"Złów po przyjęciu zadania zestaw: {targets}. "
                        "Zachowaj złowione ryby do odbioru nagrody.",
            **reward(stage, 1.55),
        ))

    for count, stage in BORIS_DISCOVERY_V3007:
        register(f"boris_discovery_{count}", dict(
            name=f"Borys — Kolekcjoner {count} gatunków", giver=npc["name"],
            kind="collect_distinct_category", target="fish", needed=count,
            event_progress_only=True, recommended_profession_level=stage,
            description=(f"Złów {count} RÓŻNYCH gatunków ryb po przyjęciu zadania "
                         "(dowolne dostępne łowiska). Zachowaj po jednej sztuce "
                         "każdego zaliczonego gatunku do oddania."),
            **reward(stage, 1.7),
        ))

    # Borys already has 'fisher_30_fish'; add the new list without replacing it.
    previous = tuple(npc.get("specialist_quests") or ())
    catalog_assign(previous + tuple(new_ids), "NPCS", npcs,
                   ("fisher_tomas", "specialist_quests"))
    catalog_assign(
        "Przynieś 30 dowolnych ryb albo wybierz questy rzeczne, jeziorne, "
        "morskie, oceaniczne oraz na konkretne gatunki, mieszane skrzynie "
        "i kolekcje różnych ryb. "
        "Zlecenia odnawiają się osobno co godzinę. Wpisz quest list Borys. "
        "Podstawową Wędkę kupisz u mnie: list albo shop.",
        "NPCS", npcs, ("fisher_tomas", "dialogue"),
    )
    BORIS_QUEST_IDS_V3007 = tuple(new_ids)
    return BORIS_QUEST_IDS_V3007
