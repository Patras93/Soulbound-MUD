"""Soulbound v4.00.1: authored world expansion implementation.

Public entry points remain available from world.expansions.
"""

from data import catalog_mutations as _catalog_mut
# v0.45.0: explicit imports; no compatibility-runtime injection.
from core.bootstrap_economy_professions import QUEST_REPEAT_COOLDOWN_SECONDS
from core.classes_skills import ORE_ATLAS_LEVELS, ORE_MINE_FLOOR_MINIMUMS
from core.mines_threat import CHARACTER_BOUND_TOOL_IDS, EXP_AREAS, GUIDE_DESTINATION_ALIASES, TOOL_SHOP_ROOMS
from core.progression_resources import (
    FISH_ATLAS_ALL,
    FISH_RESOURCE_IDS,
    HERB_ATLAS_ALL,
    HERB_RESOURCE_IDS,
    ORE_ATLAS_ALL,
    ORE_RESOURCE_IDS,
    RIVER_FISHING_ROOMS,
    WOOD_ATLAS_ALL,
    WOOD_RESOURCE_IDS,
)
from systems.content_registry import HELP_TOPICS, HELP_TOPIC_ALIASES, MOB_DESCRIPTIONS
from systems.dungeons_regions import (
    FISHING_ROOMS,
    GIANT_FORTRESS_BOSS_FLOORS,
    GIANT_FORTRESS_BOSS_MECHANICS,
    GIANT_FORTRESS_BOSS_NAMES,
    GIANT_FORTRESS_MAX_FLOOR,
    HERBALISM_ROOMS,
    ITEMS,
    MOB_SPAWNS,
    MOB_TEMPLATES,
    NPCS,
    QUESTS,
    RARE_TROLL_VARIANTS,
    ROOMS,
    WOODCUTTING_ROOMS,
    _register_elite_variants,
    _register_rare_variants,
    giant_fortress_floor_id,
)
from systems.equipment_crafting import (
    FISH_STORAGE_IDS,
    MINING_STORAGE_IDS,
    ORE_STORAGE_IDS,
    SHOPS,
    SHOP_SELLERS,
)
from systems.items_resources import HERB_STORAGE_IDS, WOOD_STORAGE_IDS


def build_mountain_crafting_expansion():
    # ========================================================
    # ROOMS AND NPC HUBS
    # ========================================================
    _catalog_mut.catalog_update_path('ROOMS', ROOMS, ("mountain_guard_house", "exits"), {
        "east": "mountain_forge",
        "west": "hunter_lodge",
    })
    _catalog_mut.catalog_update_path('ROOMS', ROOMS, ("mountain_inn", "exits"), {
        "north": "mountain_market",
        "east": "alpine_herbalist_hut",
    })
    _catalog_mut.catalog_assign("giant_fortress_gate", 'ROOMS', ROOMS, ("mountain_village", "exits", "up"))

    _catalog_mut.catalog_assign({
        "zone": "Wioska Górska",
        "name": "Górska Kuźnia",
        "desc": (
            "Ciężki młot uderza o kowadło, a półki "
            "wypełniają sztabki metalu i pancerze."
        ),
        "exits": {
            "west": "mountain_guard_house",
        },
    }, 'ROOMS', ROOMS, ("mountain_forge",))
    _catalog_mut.catalog_assign({
        "zone": "Wioska Górska",
        "name": "Chata Łowcy Potworów",
        "desc": (
            "Na ścianach wiszą trofea z trolli i bestii "
            "zamieszkujących wysokie góry."
        ),
        "exits": {
            "east": "mountain_guard_house",
        },
    }, 'ROOMS', ROOMS, ("hunter_lodge",))
    _catalog_mut.catalog_assign({
        "zone": "Wioska Górska",
        "name": "Górski Targ Minerałów",
        "desc": (
            "Handlarze skupują rudy przynoszone z kopalń "
            "i przełęczy."
        ),
        "exits": {
            "south": "mountain_inn",
        },
    }, 'ROOMS', ROOMS, ("mountain_market",))
    _catalog_mut.catalog_assign({
        "zone": "Wioska Górska",
        "name": "Chata Zielarki Alpejskiej",
        "desc": (
            "Suszone zioła wiszą pod sufitem. Zielarka "
            "prowadzi badania nad roślinami z osobnych łąk."
        ),
        "exits": {
            "west": "mountain_inn",
        },
    }, 'ROOMS', ROOMS, ("alpine_herbalist_hut",))

    # ========================================================
    # GIANT FORTRESS 1-50
    # ========================================================
    _catalog_mut.catalog_assign({
        "zone": "Twierdza Gigantów",
        "name": "Brama Twierdzy Gigantów",
        "desc": (
            "Monumentalna kamienna brama prowadzi do "
            "pięćdziesięciopoziomowej twierdzy."
        ),
        "exits": {
            "down": "mountain_village",
            "up": giant_fortress_floor_id(1),
        },
    }, 'ROOMS', ROOMS, ("giant_fortress_gate",))

    boss_text = {
        10: "Co trzecią odpowiedź używa Miażdżenia Giganta.",
        20: "Co trzecią odpowiedź wyzwala magiczny Promień Cyklopa.",
        30: "Co czwartą odpowiedź rozpoczyna Burzę Głazów.",
        40: "Zmienia typ obrażeń i co trzecią odpowiedź przywołuje Grom Gigantów.",
        50: "Poniżej połowy HP wchodzi w królewską furię; co trzecią odpowiedź używa Królewskiego Trzęsienia.",
    }

    fortress_regular_ids = []
    for floor in range(
        1, GIANT_FORTRESS_MAX_FLOOR + 1
    ):
        room_id = giant_fortress_floor_id(floor)
        exits = {}
        if floor == 1:
            exits["down"] = "giant_fortress_gate"
        else:
            exits["down"] = giant_fortress_floor_id(
                floor - 1
            )
        if floor < GIANT_FORTRESS_MAX_FLOOR:
            exits["up"] = giant_fortress_floor_id(
                floor + 1
            )

        _catalog_mut.catalog_assign({
            "zone": "Twierdza Gigantów",
            "name": (
                f"Twierdza Gigantów - poziom {floor}"
            ),
            "desc": (
                "Kamienny poziom twierdzy jest zbudowany "
                "dla istot kilkukrotnie większych od człowieka."
            ),
            "exits": exits,
        }, 'ROOMS', ROOMS, (room_id,))

        mob_id = f"giant_fortress_mob_{floor}"
        if floor % 3 == 1:
            mob_name = "Ogr Miotacz Głazów"
        elif floor % 3 == 2:
            mob_name = "Cyklop Strażnik"
        else:
            mob_name = "Górski Gigant"

        _catalog_mut.catalog_assign({
            "name": f"{mob_name}, poziom {floor}",
            "max_hp": 450 + floor * 55,
            "damage": 18 + floor * 2,
            "damage_type": (
                "magic"
                if floor % 5 == 0
                else "physical"
            ),
            "silver": 80 + floor * 12,
            "gold": max(0, floor // 10),
            "mithril": 0,
            "stat_reward": 70 + floor * 5,
            "class_xp_reward": 1200 + floor * 140,
            "soul_reward": 300 + floor * 45,
            "drops": {
                "iron_ore": 0.08,
                "silver_ore": (
                    0.08 if floor >= 15 else 0.0
                ),
                "gold_ore": (
                    0.06 if floor >= 30 else 0.0
                ),
            },
            "quest_target": None,
            "elite_eligible": True,
            "giant_fortress_floor": floor,
            "corpse_equipment_pool": [
                "iron_guard",
                "iron_gauntlets",
                "iron_leggings",
                "iron_boots",
            ],
            "corpse_equipment_guaranteed": 1,
        }, 'MOB_TEMPLATES', MOB_TEMPLATES, (mob_id,))
        fortress_regular_ids.append(mob_id)

        MOB_SPAWNS.extend([
            (room_id, mob_id),
            (room_id, mob_id),
        ])

        if floor in GIANT_FORTRESS_BOSS_FLOORS:
            boss_id = (
                f"giant_fortress_boss_{floor}"
            )
            _catalog_mut.catalog_assign({
                "name": GIANT_FORTRESS_BOSS_NAMES[
                    floor
                ],
                "max_hp": 5000 + floor * 300,
                "damage": 45 + floor * 3,
                "damage_type": "physical",
                "silver": 1000 + floor * 40,
                "gold": 3 + floor // 10,
                "mithril": 0,
                "stat_reward": 350 + floor * 8,
                "class_xp_reward": (
                    6000 + floor * 400
                ),
                "soul_reward": (
                    1400 + floor * 100
                ),
                "drops": {
                    "soul_elixir": 0.20,
                    "soul_shard": 0.60,
                },
                "quest_target": None,
                "world_boss": True,
                "giant_fortress_boss": True,
                "giant_fortress_floor": floor,
                "boss_mechanic": (
                    GIANT_FORTRESS_BOSS_MECHANICS[
                        floor
                    ]
                ),
                "boss_mechanic_text": boss_text[
                    floor
                ],
                "corpse_equipment_pool": [
                    "iron_helmet",
                    "iron_guard",
                    "iron_gauntlets",
                    "iron_leggings",
                    "iron_boots",
                    "forge_charm",
                ],
                "corpse_equipment_guaranteed": 2,
            }, 'MOB_TEMPLATES', MOB_TEMPLATES, (boss_id,))
            MOB_SPAWNS.append(
                (room_id, boss_id)
            )

    # ========================================================
    # RARE TROLLS + ELITE ELIGIBILITY
    # ========================================================
    _catalog_mut.catalog_assign({
        "name": "Skradziona Skrzynia Rudy",
        "type": "quest",
        "price": None,
        "desc": (
            "Skrzynia rudy skradziona mieszkańcom "
            "Wioski Górskiej przez trolle."
        ),
    }, 'ITEMS', ITEMS, ("stolen_mountain_ore",))

    base_troll_specs = {
        "albino_troll": (
            "Albinos Troll", 360, 26, "physical",
        ),
        "crystal_troll": (
            "Kryształowy Troll", 410, 30, "magic",
        ),
        "ancient_troll": (
            "Pradawny Troll", 560, 36, "physical",
        ),
        "runic_troll": (
            "Troll Runiczny", 470, 34, "magic",
        ),
    }
    for troll_id, (
        name, hp, damage, damage_type
    ) in base_troll_specs.items():
        _catalog_mut.catalog_assign({
            "name": name,
            "max_hp": hp,
            "damage": damage,
            "damage_type": damage_type,
            "silver": 180,
            "gold": 2,
            "mithril": 0,
            "stat_reward": 140,
            "class_xp_reward": 2400,
            "soul_reward": 600,
            "drops": {
                "stolen_mountain_ore": 0.35,
                "soul_shard": 0.12,
            },
            "quest_target": "mountain_troll",
            "quest_targets": (
                "mountain_patrol_threat",
            ),
            "rare_troll": True,
            "elite_eligible": True,
            "corpse_equipment_pool": [
                "iron_guard",
                "iron_gauntlets",
                "iron_boots",
            ],
            "corpse_equipment_guaranteed": 1,
        }, 'MOB_TEMPLATES', MOB_TEMPLATES, (troll_id,))

    for troll_id in (
        "mountain_troll",
        "troll_brute",
        "troll_shaman",
    ):
        template = MOB_TEMPLATES[troll_id]
        template["elite_eligible"] = True
        template.setdefault(
            "drops", {}
        )["stolen_mountain_ore"] = 0.30
        targets = list(
            template.get("quest_targets") or ()
        )
        if "mountain_patrol_threat" not in targets:
            targets.append(
                "mountain_patrol_threat"
            )
        if troll_id == "troll_shaman":
            targets.append("troll_shaman")
        template["quest_targets"] = tuple(
            dict.fromkeys(targets)
        )

    _catalog_mut.catalog_setdefault_path('MOB_TEMPLATES', MOB_TEMPLATES, ("troll_king",), 
        "drops", {}
    )["stolen_mountain_ore"] = 1.0
    _catalog_mut.catalog_assign(("troll_king",), 'MOB_TEMPLATES', MOB_TEMPLATES, ("troll_king", "quest_targets"))

    elite_bases = list(
        fortress_regular_ids
    ) + [
        "mountain_troll",
        "troll_brute",
        "troll_shaman",
        *RARE_TROLL_VARIANTS,
    ]
    _register_elite_variants(elite_bases)

    # ========================================================
    # MOUNTAIN COMBAT QUESTS
    # ========================================================
    _catalog_mut.catalog_assign({
        "name": "Patrol Górskiego Szlaku",
        "giver": "Strażnik Górski Eryk",
        "kind": "kill",
        "target": "mountain_patrol_threat",
        "needed": 8,
        "description": (
            "Pokonaj 8 trolli lub innych trollowych "
            "zagrożeń na szlaku i w jaskini."
        ),
        "requires_quest": "mountain_troll_hunt",
        "reward_stat_progress": 180,
        "reward_silver": 420,
        "reward_gold": 1,
        "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": 60 * 60,
    }, 'QUESTS', QUESTS, ("mountain_trail_patrol",))
    _catalog_mut.catalog_assign({
        "name": "Polowanie na Trolli Szamanów",
        "giver": "Łowca Potworów Ragna",
        "kind": "kill",
        "target": "troll_shaman",
        "needed": 5,
        "description": (
            "Pokonaj 5 Trolli Szamanów w Jaskini Trolli."
        ),
        "reward_stat_progress": 220,
        "reward_silver": 550,
        "reward_gold": 2,
        "reward_mithril": 0,
        "reward_items": {
            "healing_potion": 2,
        },
        "repeatable": True,
        "repeat_cooldown": 60 * 60,
    }, 'QUESTS', QUESTS, ("troll_shaman_hunt",))
    _catalog_mut.catalog_assign({
        "name": "Polowanie na Króla Trolli",
        "giver": "Łowca Potworów Ragna",
        "kind": "kill",
        "target": "troll_king",
        "needed": 1,
        "description": (
            "Pokonaj Króla Trolli Gruma w najgłębszej "
            "komorze Jaskini Trolli."
        ),
        "requires_quest": "troll_shaman_hunt",
        "reward_stat_progress": 400,
        "reward_silver": 1000,
        "reward_gold": 5,
        "reward_mithril": 0,
        "reward_items": {
            "soul_elixir": 1,
        },
        "repeatable": True,
        "repeat_cooldown": 60 * 60,
    }, 'QUESTS', QUESTS, ("troll_king_hunt",))
    _catalog_mut.catalog_assign({
        "name": "Skradzione Skrzynie Rudy",
        "giver": "Magazynier Borin",
        "kind": "collect",
        "target": "stolen_mountain_ore",
        "needed": 10,
        "progress_label": "skrzyń rudy",
        "description": (
            "Odzyskaj 10 Skradzionych Skrzyń Rudy z trolli na Górskim Szlaku "
            "i w Jaskini Trolli, a następnie wróć do Magazyniera Borina "
            "na placu Wioski Górskiej. Zadanie odnawia się co 60 minut."
        ),
        "reward_stat_progress": 180,
        "reward_silver": 450,
        "reward_gold": 1,
        "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    }, 'QUESTS', QUESTS, ("stolen_mountain_ores",))

    _catalog_mut.catalog_assign({
        "name": "Magazynier Borin",
        "room": "mountain_village",
        "dialogue": (
            "Trolle napadają na transporty rudy i wynoszą całe skrzynie. "
            "Odzyskaj 10 Skradzionych Skrzyń Rudy. To zlecenie mogę wystawić "
            "ponownie co godzinę."
        ),
        "quest": "stolen_mountain_ores",
    }, 'NPCS', NPCS, ("mountain_ore_storekeeper_borin",))

    _catalog_mut.catalog_assign((
        "mountain_troll_hunt",
        "mountain_trail_patrol",
    ), 'NPCS', NPCS, ("mountain_guard_eryk", "quest_chain"))
    _catalog_mut.catalog_assign({
        "name": "Łowca Potworów Ragna",
        "room": "hunter_lodge",
        "dialogue": (
            "Poluję na najgroźniejsze trolle. "
            "Najpierw szamani, potem ich król."
        ),
        "quest_chain": (
            "troll_shaman_hunt",
            "troll_king_hunt",
        ),
    }, 'NPCS', NPCS, ("mountain_monster_hunter",))

    # ========================================================
    # BLACKSMITH QUESTS 1-200
    # ========================================================
    smith_specs = (
        (1, "smith_iron_head", 3, "Żelazne Hełmy"),
        (15, "smith_iron_body", 2, "Żelazne Pancerze"),
        (30, "smith_silver_head", 3, "Srebrne Hełmy"),
        (45, "smith_gold_hands", 3, "Złote Rękawice"),
        (60, "smith_gold_legs", 2, "Złote Nogawice"),
        (75, "smith_gold_charm", 2, "Złote Talizmany"),
        (90, "smith_gold_body", 2, "Złote Pancerze"),
        (100, "smith_cobalt_head", 3, "Kobaltowe Hełmy"),
        (120, "smith_runic_body", 2, "Runiczne Pancerze"),
        (140, "smith_dragonsteel_hands", 2, "Rękawice Smoczej Stali"),
        (160, "smith_astral_legs", 2, "Astralne Nogawice"),
        (180, "smith_void_body", 2, "Pancerze Pustki"),
    )
    smith_chain = []
    previous = None
    for number, (
        level, target, needed, label
    ) in enumerate(smith_specs, 1):
        qid = f"mountain_smith_{level}"
        quest = {
            "name": (
                f"Zlecenie Górskiego Kowala {number}: "
                f"{label}"
            ),
            "giver": "Kowal Górski Brok",
            "kind": "collect",
            "track_craft_progress": True,
            "target": target,
            "needed": needed,
            "description": (
                f"Wykuj {needed} sztuk: "
                f"{ITEMS[target]['name']}."
            ),
            "specialist_tool_type": "crafting",
            "min_tool_level": level,
            "required_profession": "Kowalstwo",
            "min_profession_level": level,
            "reward_profession": "Kowalstwo",
            "reward_profession_xp": (
                500 + number * 350
            ),
            "reward_tool_type": "crafting",
            "reward_tool_xp": (
                450 + number * 320
            ),
            "reward_silver": (
                150 + number * 70
            ),
            "reward_gold": max(
                0, number // 3
            ),
            "reward_mithril": 0,
            "reward_items": {},
            "repeatable": True,
            "repeat_cooldown": (
                QUEST_REPEAT_COOLDOWN_SECONDS
            ),
        }
        if previous:
            quest["requires_quest"] = previous
        _catalog_mut.catalog_assign(quest, 'QUESTS', QUESTS, (qid,))
        smith_chain.append(qid)
        previous = qid

    eternium_targets = tuple(
        f"smith_eternium_{slot}"
        for slot in (
            "head", "body", "hands",
            "legs", "feet", "charm",
        )
    )
    _catalog_mut.catalog_assign({
        "name": (
            "Zlecenie Górskiego Kowala 13: "
            "Pełny Zestaw Eternium"
        ),
        "giver": "Kowal Górski Brok",
        "kind": "craft_set",
        "track_craft_progress": True,
        "targets": eternium_targets,
        "needed": len(eternium_targets),
        "description": (
            "Wykuj po jednym z sześciu elementów "
            "pełnego Zestawu Eternium."
        ),
        "specialist_tool_type": "crafting",
        "min_tool_level": 200,
        "required_profession": "Kowalstwo",
        "min_profession_level": 200,
        "requires_quest": previous,
        "reward_profession": "Kowalstwo",
        "reward_profession_xp": 9000,
        "reward_tool_type": "crafting",
        "reward_tool_xp": 8500,
        "reward_silver": 1800,
        "reward_gold": 8,
        "reward_mithril": 1,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": (
            QUEST_REPEAT_COOLDOWN_SECONDS
        ),
    }, 'QUESTS', QUESTS, ("mountain_smith_200",))
    smith_chain.append("mountain_smith_200")

    _catalog_mut.catalog_assign({
        "name": "Kowal Górski Brok",
        "room": "mountain_forge",
        "dialogue": (
            "Kowalstwo poznaje się po pracy. "
            "Mam trzynaście zleceń od levelu 1 do 200."
        ),
        "specialist_tool_type": "crafting",
        "specialist_topic": "kowalstwo",
        "specialist_recipes": "receptury kowalstwo",
        "specialist_quests": tuple(
            smith_chain
        ),
    }, 'NPCS', NPCS, ("mountain_blacksmith_brok",))

    # ========================================================
    # COOKING QUESTS 1-200
    # ========================================================
    marcel_base = QUESTS["marcel_cooking_order"]
    marcel_base.update({
        "name": "Zlecenie Marcela I: Pieczona Ryba Rzeczna",
        "track_craft_progress": True,
        "requires_quest": None,
    })

    cooking_specs = (
        ("marcel_cook_15", 15, "river_fish_stew", 3, "Gulasze Rzeczne"),
        ("marcel_cook_30", 30, "lake_fish_stew", 3, "Potrawki Jeziorowe"),
        ("marcel_cook_45", 45, "silver_trout_soup", 3, "Zupy ze Srebrnego Pstrąga"),
        ("marcel_cook_60", 60, "lake_fisher_pie", 3, "Zapiekanki Jeziornego Rybaka"),
        ("marcel_cook_75", 75, "spiced_mackerel", 3, "Makrele Korzenne"),
        ("marcel_cook_90", 90, "salmon_herb_plate", 3, "Łososie z Ziołami"),
    )
    cooking_chain = ["marcel_cooking_order"]
    previous = "marcel_cooking_order"
    for index, (
        qid, level, target, needed, label
    ) in enumerate(cooking_specs, 2):
        _catalog_mut.catalog_assign({
            "name": (
                f"Zlecenie Marcela {index}: {label}"
            ),
            "giver": "Kucharz Marcel",
            "kind": "collect",
            "track_craft_progress": True,
            "target": target,
            "needed": needed,
            "description": (
                f"Przygotuj {needed} sztuk: "
                f"{ITEMS[target]['name']}."
            ),
            "specialist_tool_type": "cooking",
            "min_tool_level": level,
            "requires_quest": previous,
            "reward_tool_type": "cooking",
            "reward_tool_xp": (
                500 + index * 250
            ),
            "reward_silver": (
                120 + index * 60
            ),
            "reward_gold": max(
                0, index // 4
            ),
            "reward_mithril": 0,
            "reward_items": {},
            "repeatable": True,
            "repeat_cooldown": (
                QUEST_REPEAT_COOLDOWN_SECONDS
            ),
        }, 'QUESTS', QUESTS, (qid,))
        cooking_chain.append(qid)
        previous = qid

    advanced = QUESTS[
        "marcel_cooking_order_advanced"
    ]
    advanced.update({
        "name": "Zlecenie Marcela VIII: Runiczny Półmisek",
        "track_craft_progress": True,
        "requires_quest": previous,
        "needed": 2,
    })
    cooking_chain.append(
        "marcel_cooking_order_advanced"
    )
    previous = "marcel_cooking_order_advanced"

    high_cooking = (
        ("marcel_cook_120", 120, "dragon_ocean_stew", 2, "Smocze Potrawki"),
        ("marcel_cook_140", 140, "abyss_fish_steak", 2, "Steki Otchłani"),
        ("marcel_cook_160", 160, "storm_marlin_feast", 2, "Uczty Marlina Burzy"),
        ("marcel_cook_180", 180, "leviathan_banquet", 1, "Uczta Lewiatana"),
    )
    for index, (
        qid, level, target, needed, label
    ) in enumerate(high_cooking, 9):
        _catalog_mut.catalog_assign({
            "name": (
                f"Zlecenie Marcela {index}: {label}"
            ),
            "giver": "Kucharz Marcel",
            "kind": "collect",
            "track_craft_progress": True,
            "target": target,
            "needed": needed,
            "description": (
                f"Przygotuj {needed} sztuk: "
                f"{ITEMS[target]['name']}."
            ),
            "specialist_tool_type": "cooking",
            "min_tool_level": level,
            "requires_quest": previous,
            "reward_tool_type": "cooking",
            "reward_tool_xp": (
                2200 + index * 300
            ),
            "reward_silver": (
                400 + index * 70
            ),
            "reward_gold": max(
                1, index // 3
            ),
            "reward_mithril": 0,
            "reward_items": {},
            "repeatable": True,
            "repeat_cooldown": (
                QUEST_REPEAT_COOLDOWN_SECONDS
            ),
        }, 'QUESTS', QUESTS, (qid,))
        cooking_chain.append(qid)
        previous = qid

    master = QUESTS[
        "marcel_cooking_order_master"
    ]
    master.update({
        "name": "Zlecenie Marcela XIII: Wieczna Uczta",
        "track_craft_progress": True,
        "requires_quest": previous,
    })
    cooking_chain.append(
        "marcel_cooking_order_master"
    )
    _catalog_mut.catalog_assign(tuple(cooking_chain), 'NPCS', NPCS, ("specialist_cooking", "specialist_quests"))

    # ========================================================
    # HERBALISM SPECIFIC MEADOW QUESTS
    # ========================================================
    herb_specs = (
        (
            "alpine_lavender",
            35,
            "lavender",
            10,
            "Lawenda dla Gór",
        ),
        (
            "alpine_ginseng",
            50,
            "ginseng",
            8,
            "Korzeń Żeń-szenia",
        ),
        (
            "alpine_moonflower",
            70,
            "moonflower",
            5,
            "Księżycowe Kwiaty",
        ),
    )
    herb_chain = []
    previous = None
    for qid, level, target, needed, label in herb_specs:
        quest = {
            "name": label,
            "giver": "Zielarka Alpejska Ira",
            "kind": "collect_resource",
            "track_resource_progress": True,
            "target": target,
            "needed": needed,
            "description": (
                f"Zbierz na osobnej łące {needed} sztuk: "
                f"{ITEMS[target]['name']}."
            ),
            "specialist_tool_type": "herbalism",
            "min_tool_level": level,
            "reward_profession": "Zielarstwo",
            "reward_profession_xp": 900 + level * 8,
            "reward_tool_type": "herbalism",
            "reward_tool_xp": 800 + level * 7,
            "reward_silver": 250 + level * 3,
            "reward_gold": max(0, level // 50),
            "reward_mithril": 0,
            "reward_items": {},
            "repeatable": True,
            "repeat_cooldown": (
                QUEST_REPEAT_COOLDOWN_SECONDS
            ),
        }
        if previous:
            quest["requires_quest"] = previous
        _catalog_mut.catalog_assign(quest, 'QUESTS', QUESTS, (qid,))
        herb_chain.append(qid)
        previous = qid

    _catalog_mut.catalog_assign({
        "name": "Zielarka Alpejska Ira",
        "room": "alpine_herbalist_hut",
        "dialogue": (
            "Każda łąka ma własne zioło. "
            "Przynoś mi konkretne rośliny, nie losową mieszankę."
        ),
        "specialist_tool_type": "herbalism",
        "specialist_topic": "zielarstwo",
        "specialist_quests": tuple(
            herb_chain
        ),
    }, 'NPCS', NPCS, ("alpine_herbalist_ira",))

    # ========================================================
    # MINING SPECIFIC ORE QUESTS
    # ========================================================
    ore_specs = (
        (1, "copper_ore", 20),
        (15, "iron_ore", 15),
        (30, "silver_ore", 12),
        (45, "gold_ore", 10),
        (100, "cobalt_ore", 8),
        (120, "runestone_ore", 7),
        (140, "dragonsteel_ore", 6),
        (160, "astral_ore", 5),
        (180, "void_ore", 4),
        (200, "eternium_ore", 3),
    )
    mining_chain = []
    previous = None
    for level, target, needed in ore_specs:
        qid = f"dagna_ore_{level}"
        _catalog_mut.catalog_assign({
            "name": (
                f"Zlecenie Dagny: "
                f"{ITEMS[target]['name']}"
            ),
            "giver": "Handlarka Minerałów Dagna",
            "kind": "collect_resource",
            "track_resource_progress": True,
            "target": target,
            "needed": needed,
            "description": (
                f"Wydobądź {needed} sztuk: "
                f"{ITEMS[target]['name']}."
            ),
            "specialist_tool_type": "mining",
            "min_tool_level": level,
            "requires_quest": previous,
            "reward_profession": "Górnictwo",
            "reward_profession_xp": (
                600 + level * 12
            ),
            "reward_tool_type": "mining",
            "reward_tool_xp": (
                550 + level * 10
            ),
            "reward_silver": (
                160 + level * 5
            ),
            "reward_gold": max(
                0, level // 50
            ),
            "reward_mithril": (
                1 if level == 200 else 0
            ),
            "reward_items": {},
            "repeatable": True,
            "repeat_cooldown": (
                QUEST_REPEAT_COOLDOWN_SECONDS
            ),
        }, 'QUESTS', QUESTS, (qid,))
        mining_chain.append(qid)
        previous = qid

    _catalog_mut.catalog_assign({
        "name": "Handlarka Minerałów Dagna",
        "room": "mountain_market",
        "dialogue": (
            "Płacę za konkretne rudy od miedzi aż po Eternium. "
            "Skradzionymi skrzyniami zajmuje się Magazynier Borin na placu Wioski Górskiej."
        ),
        "specialist_tool_type": "mining",
        "specialist_topic": "gornictwo",
        "specialist_quests": tuple(
            mining_chain
        ),
    }, 'NPCS', NPCS, ("mountain_mineral_trader_dagna",))

    # ========================================================
    # FISHING SPECIFIC + RARE VARIANT QUESTS
    # ========================================================
    fishing_specs = (
        (1, "river_carp", 20, "Karp Rzeczny"),
        (30, "silver_trout", 4, "Srebrny Pstrąg"),
        (60, "golden_trout", 3, "Złoty Pstrąg"),
        (80, "tuna", 3, "Tuńczyk"),
        (
            100,
            "rare_fish_golden__silver_trout",
            3,
            "Złoty Okaz Pstrąga",
        ),
        (140, "abyss_tuna", 2, "Tuńczyk Otchłani"),
        (180, "moon_leviathan", 1, "Księżycowy Lewiatan"),
        (
            200,
            "rare_fish_ancient__tuna",
            1,
            "Pradawny Tuńczyk",
        ),
    )
    fishing_chain = []
    previous = None
    for index, (
        level, target, needed, label
    ) in enumerate(fishing_specs, 1):
        qid = f"neris_fish_{level}"
        quest = {
            "name": (
                f"Zlecenie Neris {index}: {label}"
            ),
            "giver": "Mistrz Wędkarstwa Neris",
            "kind": "collect_resource",
            "track_resource_progress": True,
            "target": target,
            "needed": needed,
            "description": (
                f"Złów {needed} sztuk: "
                f"{ITEMS[target]['name']}."
            ),
            "specialist_tool_type": "fishing",
            "min_tool_level": level,
            "reward_profession": "Wędkarstwo",
            "reward_profession_xp": (
                650 + level * 10
            ),
            "reward_tool_type": "fishing",
            "reward_tool_xp": (
                600 + level * 9
            ),
            "reward_silver": (
                150 + level * 4
            ),
            "reward_gold": max(
                0, level // 50
            ),
            "reward_mithril": (
                1 if level == 200 else 0
            ),
            "reward_items": {},
            "repeatable": True,
            "repeat_cooldown": (
                QUEST_REPEAT_COOLDOWN_SECONDS
            ),
        }
        if previous:
            quest["requires_quest"] = previous
        _catalog_mut.catalog_assign(quest, 'QUESTS', QUESTS, (qid,))
        fishing_chain.append(qid)
        previous = qid

    _catalog_mut.catalog_assign(tuple(fishing_chain), 'NPCS', NPCS, ("specialist_fishing", "specialist_quests"))

    # ========================================================
    # SHOPS / SALES / GUIDE
    # ========================================================
    _catalog_mut.catalog_assign([
        "crafting_hammer",
    ], 'SHOPS', SHOPS, ("mountain_forge",))
    _catalog_mut.catalog_assign([
        "herbalist_sickle",
        "alchemy_mortar",
    ], 'SHOPS', SHOPS, ("alpine_herbalist_hut",))

