def build_mountain_crafting_expansion():
    # ========================================================
    # ROOMS AND NPC HUBS
    # ========================================================
    ROOMS["mountain_guard_house"]["exits"].update({
        "east": "mountain_forge",
        "west": "hunter_lodge",
    })
    ROOMS["mountain_inn"]["exits"].update({
        "north": "mountain_market",
        "east": "alpine_herbalist_hut",
    })
    ROOMS["mountain_village"]["exits"]["up"] = (
        "giant_fortress_gate"
    )

    ROOMS["mountain_forge"] = {
        "zone": "Wioska Górska",
        "name": "Górska Kuźnia",
        "desc": (
            "Ciężki młot uderza o kowadło, a półki "
            "wypełniają sztabki metalu i pancerze."
        ),
        "exits": {
            "west": "mountain_guard_house",
        },
    }
    ROOMS["hunter_lodge"] = {
        "zone": "Wioska Górska",
        "name": "Chata Łowcy Potworów",
        "desc": (
            "Na ścianach wiszą trofea z trolli i bestii "
            "zamieszkujących wysokie góry."
        ),
        "exits": {
            "east": "mountain_guard_house",
        },
    }
    ROOMS["mountain_market"] = {
        "zone": "Wioska Górska",
        "name": "Górski Targ Minerałów",
        "desc": (
            "Handlarze skupują rudy przynoszone z kopalń "
            "i przełęczy."
        ),
        "exits": {
            "south": "mountain_inn",
        },
    }
    ROOMS["alpine_herbalist_hut"] = {
        "zone": "Wioska Górska",
        "name": "Chata Zielarki Alpejskiej",
        "desc": (
            "Suszone zioła wiszą pod sufitem. Zielarka "
            "prowadzi badania nad roślinami z osobnych łąk."
        ),
        "exits": {
            "west": "mountain_inn",
        },
    }

    # ========================================================
    # GIANT FORTRESS 1-50
    # ========================================================
    ROOMS["giant_fortress_gate"] = {
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
    }

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

        ROOMS[room_id] = {
            "zone": "Twierdza Gigantów",
            "name": (
                f"Twierdza Gigantów - poziom {floor}"
            ),
            "desc": (
                "Kamienny poziom twierdzy jest zbudowany "
                "dla istot kilkukrotnie większych od człowieka."
            ),
            "exits": exits,
        }

        mob_id = f"giant_fortress_mob_{floor}"
        if floor % 3 == 1:
            mob_name = "Ogr Miotacz Głazów"
        elif floor % 3 == 2:
            mob_name = "Cyklop Strażnik"
        else:
            mob_name = "Górski Gigant"

        MOB_TEMPLATES[mob_id] = {
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
        }
        fortress_regular_ids.append(mob_id)

        MOB_SPAWNS.extend([
            (room_id, mob_id),
            (room_id, mob_id),
        ])

        if floor in GIANT_FORTRESS_BOSS_FLOORS:
            boss_id = (
                f"giant_fortress_boss_{floor}"
            )
            MOB_TEMPLATES[boss_id] = {
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
            }
            MOB_SPAWNS.append(
                (room_id, boss_id)
            )

    # ========================================================
    # RARE TROLLS + ELITE ELIGIBILITY
    # ========================================================
    ITEMS["stolen_mountain_ore"] = {
        "name": "Skradziona Skrzynia Rudy",
        "type": "quest",
        "price": None,
        "desc": (
            "Skrzynia rudy skradziona mieszkańcom "
            "Wioski Górskiej przez trolle."
        ),
    }

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
        MOB_TEMPLATES[troll_id] = {
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
        }

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

    MOB_TEMPLATES["troll_king"].setdefault(
        "drops", {}
    )["stolen_mountain_ore"] = 1.0
    MOB_TEMPLATES["troll_king"][
        "quest_targets"
    ] = ("troll_king",)

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
    QUESTS["mountain_trail_patrol"] = {
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
    }
    QUESTS["troll_shaman_hunt"] = {
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
    }
    QUESTS["troll_king_hunt"] = {
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
    }
    QUESTS["stolen_mountain_ores"] = {
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
    }

    NPCS["mountain_ore_storekeeper_borin"] = {
        "name": "Magazynier Borin",
        "room": "mountain_village",
        "dialogue": (
            "Trolle napadają na transporty rudy i wynoszą całe skrzynie. "
            "Odzyskaj 10 Skradzionych Skrzyń Rudy. To zlecenie mogę wystawić "
            "ponownie co godzinę."
        ),
        "quest": "stolen_mountain_ores",
    }

    NPCS["mountain_guard_eryk"][
        "quest_chain"
    ] = (
        "mountain_troll_hunt",
        "mountain_trail_patrol",
    )
    NPCS["mountain_monster_hunter"] = {
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
    }

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
        QUESTS[qid] = quest
        smith_chain.append(qid)
        previous = qid

    eternium_targets = tuple(
        f"smith_eternium_{slot}"
        for slot in (
            "head", "body", "hands",
            "legs", "feet", "charm",
        )
    )
    QUESTS["mountain_smith_200"] = {
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
    }
    smith_chain.append("mountain_smith_200")

    NPCS["mountain_blacksmith_brok"] = {
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
    }

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
        QUESTS[qid] = {
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
        }
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
        QUESTS[qid] = {
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
        }
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
    NPCS["specialist_cooking"][
        "specialist_quests"
    ] = tuple(cooking_chain)

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
        QUESTS[qid] = quest
        herb_chain.append(qid)
        previous = qid

    NPCS["alpine_herbalist_ira"] = {
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
    }

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
        QUESTS[qid] = {
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
        }
        mining_chain.append(qid)
        previous = qid

    NPCS["mountain_mineral_trader_dagna"] = {
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
    }

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
        QUESTS[qid] = quest
        fishing_chain.append(qid)
        previous = qid

    NPCS["specialist_fishing"][
        "specialist_quests"
    ] = tuple(fishing_chain)

    # ========================================================
    # SHOPS / SALES / GUIDE
    # ========================================================
    SHOPS["mountain_forge"] = [
        "crafting_hammer",
    ]
    SHOPS["alpine_herbalist_hut"] = [
        "herbalist_sickle",
        "alchemy_mortar",
    ]

    

def build_world_expansion_i():
    global EXP_AREAS

    # ========================================================
    # LOGICZNY PODZIAŁ ISTNIEJĄCYCH SPECJALISTÓW
    # Sprzedawcy podstawowych narzędzi zostają w swoich punktach,
    # a mistrzowie profesji dostają osobne miejsca nauki.
    # ========================================================
    ROOMS["fish_market"]["exits"]["west"] = "fishing_school"
    ROOMS["fishing_school"] = {
        "zone": "Miasto Dusz",
        "name": "Szkoła Wędkarstwa",
        "desc": (
            "Cicha sala nad Targiem Rybnym. Na ścianach wiszą mapy "
            "łowisk i stare wędki mistrzów. Tutaj uczy Neris."
        ),
        "exits": {"east": "fish_market"},
    }

    ROOMS["cave_entrance"]["exits"]["east"] = "miners_guild"
    ROOMS["miners_guild"] = {
        "zone": "Podziemia",
        "name": "Gildia Górników",
        "desc": (
            "Kamienna izba przy wejściu do kopalni. Kordan prowadzi "
            "tu szkolenie z Górnictwa, z dala od sklepu Torena."
        ),
        "exits": {"west": "cave_entrance"},
    }

    ROOMS["lumberjack_camp"]["exits"]["north"] = "forester_lodge"
    ROOMS["forester_lodge"] = {
        "zone": "Dzicz",
        "name": "Leśniczówka",
        "desc": (
            "Drewniana leśniczówka stoi na skraju Gaju Szeptów. "
            "Mistrz Drwalstwa Oren uczy tutaj pracy z rzadkim drewnem."
        ),
        "exits": {"south": "lumberjack_camp"},
    }

    ROOMS["herbalist_hut"]["exits"]["west"] = "herbalism_garden"
    ROOMS["herbalist_hut"]["exits"]["east"] = "alchemy_lab"
    ROOMS["herbalism_garden"] = {
        "zone": "Dzicz",
        "name": "Ogród Zielarski",
        "desc": (
            "Uporządkowane grządki otaczają mały drewniany pawilon. "
            "Mistrzyni Sena prowadzi tu naukę Zielarstwa."
        ),
        "exits": {"east": "herbalist_hut"},
    }
    ROOMS["alchemy_lab"] = {
        "zone": "Dzicz",
        "name": "Laboratorium Alchemiczne",
        "desc": (
            "Kamienne stoły, retorty i moździerze wypełniają osobne "
            "laboratorium. Orin prowadzi tutaj Alchemię i swoje zlecenia."
        ),
        "exits": {"west": "herbalist_hut"},
    }

    ROOMS["forge"]["exits"]["north"] = "crafting_workshop"
    ROOMS["crafting_workshop"] = {
        "zone": "Miasto Dusz",
        "name": "Warsztat Rzemieślniczy",
        "desc": (
            "Za Kuźnią Dusz działa osobny warsztat precyzyjnego "
            "rzemiosła. Haldor prowadzi tu zlecenia Kowalstwa i Rzemiosła."
        ),
        "exits": {"south": "forge"},
    }

    NPCS["specialist_fishing"]["room"] = "fishing_school"
    NPCS["specialist_mining"]["room"] = "miners_guild"
    NPCS["specialist_woodcutting"]["room"] = "forester_lodge"
    NPCS["specialist_herbalism"]["room"] = "herbalism_garden"
    NPCS["specialist_alchemy"]["room"] = "alchemy_lab"
    NPCS["specialist_crafting"]["room"] = "crafting_workshop"

    # ========================================================
    # DZICZ — NOWY PÓŁNOCNY REGION
    # ========================================================
    ROOMS["crossroads"]["exits"]["north"] = "wild_frontier"
    ROOMS["wild_frontier"] = {
        "zone": "Dzicz",
        "name": "Skraj Północnej Dziczy",
        "desc": (
            "Stary trakt znika pod trawą. Dalej rozchodzą się ścieżki "
            "do zarośli, opuszczonych gospodarstw i obozu łowców."
        ),
        "exits": {
            "south": "crossroads",
            "north": "hunter_clearing",
            "west": "thorn_scrub",
            "east": "abandoned_farm",
        },
    }
    ROOMS["hunter_clearing"] = {
        "zone": "Dzicz",
        "name": "Polana Łowców",
        "desc": (
            "Bezpieczna polana służy jako mały terenowy hub. "
            "Łowcy naprawiają tu sprzęt i obserwują ruch bestii."
        ),
        "exits": {
            "south": "wild_frontier",
            "north": "burnt_fields",
        },
    }
    ROOMS["thorn_scrub"] = {
        "zone": "Dzicz",
        "name": "Cierniste Zarośla",
        "desc": (
            "Gęste kolczaste krzewy tworzą naturalny labirynt. "
            "Między nimi słychać warczenie dzikich bestii."
        ),
        "exits": {
            "east": "wild_frontier",
            "north": "beast_den",
        },
    }
    ROOMS["abandoned_farm"] = {
        "zone": "Dzicz",
        "name": "Opuszczona Farma",
        "desc": (
            "Zawalone zabudowania przypominają o dawnych osadnikach. "
            "Ślady zwierząt prowadzą na północ."
        ),
        "exits": {
            "west": "wild_frontier",
            "north": "broken_shrine",
        },
    }
    ROOMS["burnt_fields"] = {
        "zone": "Dzicz",
        "name": "Spalone Pola",
        "desc": (
            "Czarna ziemia i zwęglone pnie ciągną się ku kamiennemu "
            "wąwozowi. W popiele żerują agresywne stworzenia."
        ),
        "exits": {
            "south": "hunter_clearing",
            "north": "stone_ravine",
        },
    }
    ROOMS["stone_ravine"] = {
        "zone": "Dzicz",
        "name": "Kamienny Wąwóz",
        "desc": (
            "Wąwóz przecina północną Dzicz. Boczne przejście prowadzi "
            "do legowiska największej bestii regionu."
        ),
        "exits": {
            "south": "burnt_fields",
            "west": "beast_den",
        },
    }
    ROOMS["broken_shrine"] = {
        "zone": "Dzicz",
        "name": "Pęknięta Kapliczka",
        "desc": (
            "Dawna kapliczka została rozbita przez korzenie i pazury. "
            "Na zachodzie leży wejście do legowiska bestii."
        ),
        "exits": {
            "south": "abandoned_farm",
            "west": "beast_den",
        },
    }
    ROOMS["beast_den"] = {
        "zone": "Dzicz",
        "name": "Legowisko Rogatego Króla",
        "desc": (
            "W skalnej niecce leżą kości i połamane rogi. "
            "To terytorium największego drapieżnika północnej Dziczy."
        ),
        "exits": {
            "south": "thorn_scrub",
            "east": "stone_ravine",
            "north": "broken_shrine",
        },
    }

    # ========================================================
    # GÓRY — NIŻSZE STOKI, LÓD, SZCZYT I STARA KOPALNIA
    # ========================================================
    ROOMS["mountain_pass"]["exits"]["north"] = "mountain_lower_slopes"
    ROOMS["mountain_lower_slopes"] = {
        "zone": "Góry",
        "name": "Niższe Stoki",
        "desc": (
            "Kamienista ścieżka odchodzi od głównej przełęczy. "
            "Wyżej słychać wiatr uderzający o skalne półki."
        ),
        "exits": {
            "south": "mountain_pass",
            "north": "wind_shelf",
            "west": "goat_trail",
        },
    }
    ROOMS["goat_trail"] = {
        "zone": "Góry",
        "name": "Szlak Kozic",
        "desc": (
            "Wąska ścieżka prowadzi nad urwiskiem do dawnej "
            "krasnoludzkiej kopalni."
        ),
        "exits": {
            "east": "mountain_lower_slopes",
            "west": "dwarf_mine_entrance",
        },
    }
    ROOMS["dwarf_mine_entrance"] = {
        "zone": "Góry",
        "name": "Wejście do Starej Kopalni Krasnoludów",
        "desc": (
            "Zardzewiała brama stoi otwarta. To opuszczone wyrobisko "
            "jest częścią terenu Gór, a nie Kopalni Głębinowej."
        ),
        "exits": {
            "east": "goat_trail",
            "north": "abandoned_dwarf_hall",
        },
    }
    ROOMS["abandoned_dwarf_hall"] = {
        "zone": "Góry",
        "name": "Opuszczona Hala Krasnoludów",
        "desc": (
            "Kamienne filary podtrzymują strop dawnej hali wydobywczej. "
            "Dziś mieszkają tu górskie bestie."
        ),
        "exits": {"south": "dwarf_mine_entrance"},
    }
    ROOMS["wind_shelf"] = {
        "zone": "Góry",
        "name": "Wietrzna Półka",
        "desc": (
            "Silny wiatr niemal zrzuca z wąskiej skalnej półki. "
            "Stąd droga rozdziela się ku lodowej przełęczy i obozowi."
        ),
        "exits": {
            "south": "mountain_lower_slopes",
            "north": "ice_pass",
            "east": "summit_camp",
        },
    }
    ROOMS["ice_pass"] = {
        "zone": "Góry",
        "name": "Lodowa Przełęcz",
        "desc": (
            "Śnieg skrzypi pod stopami, a oblodzone skały prowadzą "
            "na Szczyt Burzy."
        ),
        "exits": {
            "south": "wind_shelf",
            "north": "storm_summit",
        },
    }
    ROOMS["summit_camp"] = {
        "zone": "Góry",
        "name": "Obóz Szczytowy",
        "desc": (
            "Mały obóz badaczy i zwiadowców osłania kamienny mur. "
            "To bezpieczny hub wysokich Gór."
        ),
        "exits": {
            "west": "wind_shelf",
            "east": "lava_fissure",
            "north": "storm_summit",
        },
    }
    ROOMS["lava_fissure"] = {
        "zone": "Góry",
        "name": "Szczelina Lawowa",
        "desc": (
            "Gorące powietrze wydobywa się z głębokiej szczeliny. "
            "Kamienie mają tu czerwony połysk."
        ),
        "exits": {"west": "summit_camp"},
    }
    ROOMS["storm_summit"] = {
        "zone": "Góry",
        "name": "Szczyt Burzy",
        "desc": (
            "Najwyższy punkt szlaku tonie w chmurach i błyskawicach. "
            "Ogromny drapieżnik krąży nad szczytem."
        ),
        "exits": {
            "south": "ice_pass",
            "west": "summit_camp",
        },
    }

    # ========================================================
    # JASKINIA TROLLI — BOCZNE GŁĘBOKIE KOMORY
    # ========================================================
    ROOMS["troll_cave_2"]["exits"]["north"] = "troll_fungus_cavern"
    ROOMS["troll_cave_3"]["exits"]["south"] = "troll_war_camp"

    ROOMS["troll_fungus_cavern"] = {
        "zone": "Jaskinia Trolli",
        "name": "Grota Grzybów",
        "desc": (
            "Olbrzymie blade grzyby rosną na wilgotnej skale. "
            "Ślady trolli prowadzą ku podziemnej rzece."
        ),
        "exits": {
            "south": "troll_cave_2",
            "east": "troll_underground_river",
        },
    }
    ROOMS["troll_underground_river"] = {
        "zone": "Jaskinia Trolli",
        "name": "Podziemna Rzeka Trolli",
        "desc": (
            "Ciemna rzeka przecina jaskinię. Prymitywne kładki "
            "prowadzą do sal szamanów i do dołu kości."
        ),
        "exits": {
            "west": "troll_fungus_cavern",
            "north": "troll_shaman_gallery",
            "south": "troll_bone_pit",
        },
    }
    ROOMS["troll_shaman_gallery"] = {
        "zone": "Jaskinia Trolli",
        "name": "Galeria Szamanów",
        "desc": (
            "Ściany pokrywają malunki i kościane amulety. "
            "Szamani trolli odprawiają tu rytuały."
        ),
        "exits": {
            "south": "troll_underground_river",
            "east": "troll_nursery",
        },
    }
    ROOMS["troll_nursery"] = {
        "zone": "Jaskinia Trolli",
        "name": "Gniazdo Trolli",
        "desc": (
            "Ciepła komora jest pełna skór, kości i zapasów. "
            "Dalej znajdują się zagrody jeńców."
        ),
        "exits": {
            "west": "troll_shaman_gallery",
            "south": "troll_slave_pens",
        },
    }
    ROOMS["troll_slave_pens"] = {
        "zone": "Jaskinia Trolli",
        "name": "Zagrody Jeńców",
        "desc": (
            "Puste drewniane klatki stoją pod ścianami. "
            "Na wschodzie widać skarbiec plemienia."
        ),
        "exits": {
            "north": "troll_nursery",
            "east": "troll_treasure_vault",
        },
    }
    ROOMS["troll_treasure_vault"] = {
        "zone": "Jaskinia Trolli",
        "name": "Skarbiec Trolli",
        "desc": (
            "Skrzynie, metal i łupy z karawan leżą w wielkim nieładzie. "
            "Na południu słychać wojenne bębny."
        ),
        "exits": {
            "west": "troll_slave_pens",
            "south": "troll_deep_war_camp",
        },
    }
    ROOMS["troll_bone_pit"] = {
        "zone": "Jaskinia Trolli",
        "name": "Dół Kości",
        "desc": (
            "Głęboka komora jest wypełniona kośćmi zwierząt i wojowników. "
            "Wschodni tunel prowadzi do wojennego obozu."
        ),
        "exits": {
            "north": "troll_underground_river",
            "east": "troll_deep_war_camp",
        },
    }
    ROOMS["troll_deep_war_camp"] = {
        "zone": "Jaskinia Trolli",
        "name": "Głęboki Obóz Wojenny",
        "desc": (
            "Uzbrojone trolle ćwiczą tu przed wyprawami na powierzchnię. "
            "Południowy korytarz prowadzi do pradawnego ołtarza."
        ),
        "exits": {
            "north": "troll_treasure_vault",
            "west": "troll_bone_pit",
            "south": "troll_altar",
        },
    }
    ROOMS["troll_altar"] = {
        "zone": "Jaskinia Trolli",
        "name": "Pradawny Ołtarz Trolli",
        "desc": (
            "Kamienny ołtarz nosi ślady setek rytuałów. "
            "Najpotężniejszy wojownik głębin strzeże tego miejsca."
        ),
        "exits": {"north": "troll_deep_war_camp"},
    }

    # ========================================================
    # BAGNA — NOWY TEREN
    # ========================================================
    ROOMS["deep_grove"]["exits"]["south"] = "swamp_boardwalk"
    ROOMS["swamp_boardwalk"] = {
        "zone": "Bagna",
        "name": "Groble Czarnego Bagna",
        "desc": (
            "Drewniane pomosty prowadzą nad ciemną wodą. "
            "Na wschodzie znajduje się posterunek łowców bagien."
        ),
        "exits": {
            "north": "deep_grove",
            "south": "reed_mire",
            "east": "swamp_hunter_post",
        },
    }
    ROOMS["swamp_hunter_post"] = {
        "zone": "Bagna",
        "name": "Posterunek Łowców Bagien",
        "desc": (
            "Sucha platforma służy jako bezpieczny hub wypraw na Bagna."
        ),
        "exits": {"west": "swamp_boardwalk"},
    }
    ROOMS["reed_mire"] = {
        "zone": "Bagna",
        "name": "Trzcinowe Mokradła",
        "desc": (
            "Wysokie trzciny zasłaniają ścieżki. Woda sięga do kolan."
        ),
        "exits": {
            "north": "swamp_boardwalk",
            "east": "blackwater_pool",
            "west": "fungal_bog",
            "south": "poison_fen",
        },
    }
    ROOMS["blackwater_pool"] = {
        "zone": "Bagna",
        "name": "Czarne Rozlewisko",
        "desc": (
            "Nieruchoma czarna woda odbija tylko fragmenty nieba. "
            "Na wschodzie stoi chata bagiennej zielarki."
        ),
        "exits": {
            "west": "reed_mire",
            "east": "swamp_witch_hut",
            "south": "drowned_ruins",
        },
    }
    ROOMS["swamp_witch_hut"] = {
        "zone": "Bagna",
        "name": "Chata Bagiennej Zielarki",
        "desc": (
            "Chata stoi na grubych palach. Suszą się tu zioła "
            "i składniki znajdowane tylko na mokradłach."
        ),
        "exits": {"west": "blackwater_pool"},
    }
    ROOMS["fungal_bog"] = {
        "zone": "Bagna",
        "name": "Grzybowe Torfowisko",
        "desc": (
            "Mokry torf porastają wielkie grzyby i blade mchy."
        ),
        "exits": {
            "east": "reed_mire",
            "south": "serpent_nest",
        },
    }
    ROOMS["serpent_nest"] = {
        "zone": "Bagna",
        "name": "Gniazdo Bagiennych Węży",
        "desc": (
            "W korzeniach starych drzew wiją się ślady wielkich gadów."
        ),
        "exits": {"north": "fungal_bog"},
    }
    ROOMS["poison_fen"] = {
        "zone": "Bagna",
        "name": "Trujące Mokradło",
        "desc": (
            "Zielonkawa mgła unosi się nad wodą. Kamienna ścieżka "
            "prowadzi do zatopionej kapliczki."
        ),
        "exits": {
            "north": "reed_mire",
            "east": "sunken_swamp_shrine",
        },
    }
    ROOMS["sunken_swamp_shrine"] = {
        "zone": "Bagna",
        "name": "Zatopiona Kapliczka Bagien",
        "desc": (
            "Połowa starej świątyni zniknęła pod wodą. "
            "Na wschodzie leżą zatopione ruiny."
        ),
        "exits": {
            "west": "poison_fen",
            "east": "drowned_ruins",
        },
    }
    ROOMS["drowned_ruins"] = {
        "zone": "Bagna",
        "name": "Zatopione Ruiny",
        "desc": (
            "Kamienne mury wystają z czarnej wody. "
            "Na południu pulsuje serce mokradeł."
        ),
        "exits": {
            "north": "blackwater_pool",
            "west": "sunken_swamp_shrine",
            "south": "bog_heart",
        },
    }
    ROOMS["bog_heart"] = {
        "zone": "Bagna",
        "name": "Serce Czarnego Bagna",
        "desc": (
            "Głęboka sadzawka otoczona martwymi drzewami jest legowiskiem "
            "Hydry Czarnego Bagna."
        ),
        "exits": {"north": "drowned_ruins"},
    }

    # Bagna są logicznym wysokopoziomowym terenem Zielarstwa.
    HERBALISM_ROOMS.update({
        "swamp_boardwalk", "reed_mire", "blackwater_pool",
        "swamp_witch_hut", "fungal_bog", "serpent_nest",
        "poison_fen", "sunken_swamp_shrine", "drowned_ruins",
    })

    # ========================================================
    # PUSTYNIA — NOWY TEREN
    # ========================================================
    ROOMS["ruined_watchtower"]["exits"]["north"] = "dry_canyon"
    ROOMS["dry_canyon"] = {
        "zone": "Pustynia",
        "name": "Suchy Kanion",
        "desc": (
            "Kamienny kanion prowadzi z zielonych ziem ku pustyni."
        ),
        "exits": {
            "south": "ruined_watchtower",
            "north": "desert_gate",
        },
    }
    ROOMS["desert_gate"] = {
        "zone": "Pustynia",
        "name": "Brama Pustyni",
        "desc": (
            "Dwa kamienne filary oznaczają początek Wielkiej Pustyni. "
            "Na wschodzie stoi obóz karawan."
        ),
        "exits": {
            "south": "dry_canyon",
            "north": "desert_dunes",
            "east": "caravan_camp",
        },
    }
    ROOMS["caravan_camp"] = {
        "zone": "Pustynia",
        "name": "Obóz Karawan",
        "desc": (
            "Namioty, studnia i zwierzęta juczne tworzą bezpieczny "
            "hub podróżników."
        ),
        "exits": {
            "west": "desert_gate",
            "east": "desert_oasis",
        },
    }
    ROOMS["desert_oasis"] = {
        "zone": "Pustynia",
        "name": "Oaza Siedmiu Palm",
        "desc": (
            "Źródło i palmy dają chwilę odpoczynku. "
            "Na północy zaczynają się piaskowcowe ruiny."
        ),
        "exits": {
            "west": "caravan_camp",
            "north": "sandstone_ruins",
        },
    }
    ROOMS["desert_dunes"] = {
        "zone": "Pustynia",
        "name": "Morze Wydm",
        "desc": (
            "Wydmy ciągną się aż po horyzont. "
            "Na zachodzie leży Kotlina Skorpionów."
        ),
        "exits": {
            "south": "desert_gate",
            "north": "glass_flats",
            "west": "scorpion_basin",
        },
    }
    ROOMS["scorpion_basin"] = {
        "zone": "Pustynia",
        "name": "Kotlina Skorpionów",
        "desc": (
            "Kamienista niecka jest pełna nor wielkich pustynnych skorpionów."
        ),
        "exits": {"east": "desert_dunes"},
    }
    ROOMS["glass_flats"] = {
        "zone": "Pustynia",
        "name": "Szklane Równiny",
        "desc": (
            "Piasek stopił się kiedyś w czarne szkło. "
            "Wschodni szlak prowadzi do Świątyni Słońca."
        ),
        "exits": {
            "south": "desert_dunes",
            "east": "sun_temple",
        },
    }
    ROOMS["sandstone_ruins"] = {
        "zone": "Pustynia",
        "name": "Piaskowcowe Ruiny",
        "desc": (
            "Ruiny dawnego miasta otaczają zejście do zasypanej świątyni."
        ),
        "exits": {
            "south": "desert_oasis",
            "north": "buried_temple",
        },
    }
    ROOMS["buried_temple"] = {
        "zone": "Pustynia",
        "name": "Zasypana Świątynia",
        "desc": (
            "Piasek wdziera się przez pęknięty strop. "
            "Na północy znajduje się główne sanktuarium."
        ),
        "exits": {
            "south": "sandstone_ruins",
            "north": "sun_temple",
        },
    }
    ROOMS["sun_temple"] = {
        "zone": "Pustynia",
        "name": "Świątynia Płonącego Słońca",
        "desc": (
            "Złote symbole świecą na ścianach. "
            "Pradawny Strażnik Słońca nie opuszcza sanktuarium."
        ),
        "exits": {
            "south": "buried_temple",
            "west": "glass_flats",
        },
    }

    # ========================================================
    # NOWE NPC — KAŻDY W LOGICZNYM HUBIE
    # ========================================================
    NPCS["wild_ranger_elda"] = {
        "name": "Łowczyni Elda",
        "room": "hunter_clearing",
        "dialogue": (
            "Północna Dzicz robi się coraz bardziej niebezpieczna. "
            "Potrzebuję kogoś do ograniczenia liczby bestii."
        ),
        "quest": "wild_frontier_hunt",
    }
    NPCS["wild_cartographer_ivo"] = {
        "name": "Kartograf Ivo",
        "room": "hunter_clearing",
        "dialogue": (
            "Rysuję nowe ścieżki Dziczy. Polana jest naszym punktem "
            "orientacyjnym, a Legowisko Rogatego Króla końcem szlaku."
        ),
        "quest": None,
    }
    NPCS["mountain_scout_harek"] = {
        "name": "Zwiadowca Harek",
        "room": "summit_camp",
        "dialogue": (
            "Wysokie stoki pełne są drapieżników. "
            "Oczyść szlak między obozem a Szczytem Burzy."
        ),
        "quest": "high_mountain_patrol",
    }
    NPCS["troll_scholar_yorna"] = {
        "name": "Badaczka Trolli Yorna",
        "room": "troll_fungus_cavern",
        "dialogue": (
            "Głębsze komory są częścią całej osady trolli, "
            "nie tylko drogą do Króla. Zbadaj i oczyść ich wojenny szlak."
        ),
        "quest": "deep_troll_clearance",
    }
    NPCS["swamp_hunter_varg"] = {
        "name": "Łowca Bagien Varg",
        "room": "swamp_hunter_post",
        "dialogue": (
            "Mokradła są pełne gadów i stworzeń z czarnej wody. "
            "Trzymaj się pomostów, dopóki nie poznasz terenu."
        ),
        "quest": "swamp_purge",
    }
    NPCS["swamp_herbalist_nela"] = {
        "name": "Bagienna Zielarka Nela",
        "room": "swamp_witch_hut",
        "dialogue": (
            "Na bagnach rosną najmocniejsze zioła Dziczy. "
            "Możesz tu korzystać z Zielarstwa, ale uważaj na bestie."
        ),
        "quest": None,
    }
    NPCS["caravan_master_samir"] = {
        "name": "Mistrz Karawan Samir",
        "room": "caravan_camp",
        "dialogue": (
            "Karawany tracą ludzi na wydmach. Oczyść szlak między "
            "Bramą Pustyni, oazą i ruinami."
        ),
        "quest": "desert_patrol",
    }
    NPCS["desert_scholar_amina"] = {
        "name": "Badaczka Amina",
        "room": "sandstone_ruins",
        "dialogue": (
            "Te ruiny są starsze niż Miasto Dusz. "
            "Świątynia Słońca na północy wciąż jest aktywna."
        ),
        "quest": None,
    }

    # ========================================================
    # QUESTY TERENOWE
    # ========================================================
    QUESTS["wild_frontier_hunt"] = {
        "name": "Bestie Północnej Dziczy",
        "giver": "Łowczyni Elda",
        "kind": "kill",
        "target": "world_exp_wild_beast",
        "needed": 12,
        "description": (
            "Pokonaj 12 bestii Północnej Dziczy i wróć do Eldy."
        ),
        "reward_stat_progress": 320,
        "reward_silver": 850,
        "reward_gold": 2,
        "reward_mithril": 0,
        "reward_items": {"healing_potion": 3},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    }
    QUESTS["high_mountain_patrol"] = {
        "name": "Patrol Wysokich Gór",
        "giver": "Zwiadowca Harek",
        "kind": "kill",
        "target": "world_exp_mountain_threat",
        "needed": 10,
        "description": (
            "Pokonaj 10 stworzeń na wysokich stokach i wróć do Harka."
        ),
        "reward_stat_progress": 430,
        "reward_silver": 1100,
        "reward_gold": 3,
        "reward_mithril": 0,
        "reward_items": {"greater_healing_potion": 2},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    }
    QUESTS["deep_troll_clearance"] = {
        "name": "Wojenny Szlak Trolli",
        "giver": "Badaczka Trolli Yorna",
        "kind": "kill",
        "target": "world_exp_troll_depths",
        "needed": 12,
        "description": (
            "Pokonaj 12 trolli z głębokich komór i wróć do Yorny."
        ),
        "reward_stat_progress": 500,
        "reward_silver": 1350,
        "reward_gold": 4,
        "reward_mithril": 0,
        "reward_items": {"soul_shard": 2},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    }
    QUESTS["swamp_purge"] = {
        "name": "Oczyszczanie Czarnego Bagna",
        "giver": "Łowca Bagien Varg",
        "kind": "kill",
        "target": "world_exp_swamp_threat",
        "needed": 12,
        "description": (
            "Pokonaj 12 stworzeń Czarnego Bagna i wróć do Varga."
        ),
        "reward_stat_progress": 560,
        "reward_silver": 1600,
        "reward_gold": 5,
        "reward_mithril": 0,
        "reward_items": {"greater_healing_potion": 2},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    }
    QUESTS["desert_patrol"] = {
        "name": "Bezpieczny Szlak Karawan",
        "giver": "Mistrz Karawan Samir",
        "kind": "kill",
        "target": "world_exp_desert_threat",
        "needed": 12,
        "description": (
            "Pokonaj 12 zagrożeń Wielkiej Pustyni i wróć do Samira."
        ),
        "reward_stat_progress": 680,
        "reward_silver": 1900,
        "reward_gold": 6,
        "reward_mithril": 0,
        "reward_items": {"soul_elixir": 1},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    }

    # ========================================================
    # MOBY I BOSSOWIE NOWYCH TERENÓW
    # max_hp jest bazowe; globalne x2 zostanie nałożone później.
    # ========================================================
    expansion_mobs = {
        "wild_thorn_wolf": {
            "name": "Wilk Cierniowy",
            "max_hp": 150, "damage": 14, "damage_type": "physical",
            "silver": 45, "gold": 0, "mithril": 0,
            "stat_reward": 55, "class_xp_reward": 850, "soul_reward": 180,
            "drops": {"healing_potion": 0.06},
            "quest_target": "world_exp_wild_beast",
        },
        "wild_ash_boar": {
            "name": "Popielny Dzik",
            "max_hp": 190, "damage": 17, "damage_type": "physical",
            "silver": 55, "gold": 0, "mithril": 0,
            "stat_reward": 65, "class_xp_reward": 980, "soul_reward": 215,
            "drops": {"iron_ore": 0.08},
            "quest_target": "world_exp_wild_beast",
        },
        "wild_horned_king": {
            "name": "Rogaty Król Dziczy",
            "max_hp": 1500, "damage": 32, "damage_type": "physical",
            "silver": 600, "gold": 2, "mithril": 0,
            "stat_reward": 260, "class_xp_reward": 4800, "soul_reward": 1100,
            "drops": {"soul_shard": 0.55},
            "quest_target": "world_exp_wild_beast",
            "world_boss": True,
        },
        "mountain_harpy": {
            "name": "Harpia Szczytowa",
            "max_hp": 300, "damage": 25, "damage_type": "physical",
            "silver": 90, "gold": 1, "mithril": 0,
            "stat_reward": 90, "class_xp_reward": 1550, "soul_reward": 390,
            "drops": {"silver_ore": 0.08},
            "quest_target": "world_exp_mountain_threat",
        },
        "mountain_ice_wolf": {
            "name": "Lodowy Wilk",
            "max_hp": 360, "damage": 29, "damage_type": "magic",
            "silver": 105, "gold": 1, "mithril": 0,
            "stat_reward": 100, "class_xp_reward": 1750, "soul_reward": 430,
            "drops": {"gold_ore": 0.05},
            "quest_target": "world_exp_mountain_threat",
        },
        "mountain_stone_ram": {
            "name": "Kamienny Tryk",
            "max_hp": 430, "damage": 31, "damage_type": "physical",
            "silver": 115, "gold": 1, "mithril": 0,
            "stat_reward": 110, "class_xp_reward": 1950, "soul_reward": 470,
            "drops": {"cobalt_ore": 0.04},
            "quest_target": "world_exp_mountain_threat",
        },
        "mountain_storm_eagle": {
            "name": "Orzeł Burzy",
            "max_hp": 3200, "damage": 55, "damage_type": "magic",
            "silver": 1200, "gold": 5, "mithril": 0,
            "stat_reward": 480, "class_xp_reward": 9000, "soul_reward": 2400,
            "drops": {"soul_elixir": 0.25, "astral_ore": 0.08},
            "quest_target": "world_exp_mountain_threat",
            "world_boss": True,
        },
        "deep_troll_warrior": {
            "name": "Troll Wojenny",
            "max_hp": 480, "damage": 34, "damage_type": "physical",
            "silver": 125, "gold": 1, "mithril": 0,
            "stat_reward": 120, "class_xp_reward": 2200, "soul_reward": 520,
            "drops": {"iron_ore": 0.10},
            "quest_target": "mountain_troll",
            "quest_targets": ("world_exp_troll_depths",),
        },
        "deep_troll_shaman": {
            "name": "Szaman Głębin Trolli",
            "max_hp": 420, "damage": 37, "damage_type": "magic",
            "silver": 140, "gold": 1, "mithril": 0,
            "stat_reward": 130, "class_xp_reward": 2450, "soul_reward": 570,
            "drops": {"soul_shard": 0.14},
            "quest_target": "mountain_troll",
            "quest_targets": ("world_exp_troll_depths",),
        },
        "deep_troll_warlord": {
            "name": "Wódz Głębin Urrak",
            "max_hp": 4200, "damage": 62, "damage_type": "physical",
            "silver": 1500, "gold": 6, "mithril": 0,
            "stat_reward": 540, "class_xp_reward": 10500, "soul_reward": 2800,
            "drops": {"soul_shard": 0.80, "soul_elixir": 0.20},
            "quest_target": "mountain_troll",
            "quest_targets": ("world_exp_troll_depths",),
            "world_boss": True,
        },
        "swamp_crawler": {
            "name": "Pełzacz Bagienny",
            "max_hp": 380, "damage": 30, "damage_type": "physical",
            "silver": 110, "gold": 1, "mithril": 0,
            "stat_reward": 115, "class_xp_reward": 2100, "soul_reward": 500,
            "drops": {"nightshade": 0.10},
            "quest_target": "world_exp_swamp_threat",
        },
        "swamp_serpent": {
            "name": "Wąż Czarnej Wody",
            "max_hp": 460, "damage": 35, "damage_type": "physical",
            "silver": 130, "gold": 1, "mithril": 0,
            "stat_reward": 130, "class_xp_reward": 2400, "soul_reward": 580,
            "drops": {"mandrake": 0.10},
            "quest_target": "world_exp_swamp_threat",
        },
        "swamp_mire_witch": {
            "name": "Wiedźma Mokradła",
            "max_hp": 520, "damage": 40, "damage_type": "magic",
            "silver": 155, "gold": 1, "mithril": 0,
            "stat_reward": 145, "class_xp_reward": 2750, "soul_reward": 650,
            "drops": {"moonflower": 0.10},
            "quest_target": "world_exp_swamp_threat",
        },
        "swamp_hydra": {
            "name": "Hydra Czarnego Bagna",
            "max_hp": 5200, "damage": 70, "damage_type": "physical",
            "silver": 1800, "gold": 7, "mithril": 0,
            "stat_reward": 620, "class_xp_reward": 12500, "soul_reward": 3400,
            "drops": {"soul_elixir": 0.30, "astral_lotus": 0.15},
            "quest_target": "world_exp_swamp_threat",
            "world_boss": True,
        },
        "desert_raider": {
            "name": "Pustynny Łupieżca",
            "max_hp": 520, "damage": 40, "damage_type": "physical",
            "silver": 170, "gold": 1, "mithril": 0,
            "stat_reward": 150, "class_xp_reward": 2900, "soul_reward": 700,
            "drops": {"gold_ore": 0.08},
            "quest_target": "world_exp_desert_threat",
        },
        "dune_scorpion": {
            "name": "Olbrzymi Skorpion Wydm",
            "max_hp": 610, "damage": 44, "damage_type": "physical",
            "silver": 185, "gold": 1, "mithril": 0,
            "stat_reward": 165, "class_xp_reward": 3200, "soul_reward": 780,
            "drops": {"void_ore": 0.03},
            "quest_target": "world_exp_desert_threat",
        },
        "sand_wraith": {
            "name": "Piaskowy Upiór",
            "max_hp": 560, "damage": 47, "damage_type": "magic",
            "silver": 200, "gold": 2, "mithril": 0,
            "stat_reward": 175, "class_xp_reward": 3450, "soul_reward": 830,
            "drops": {"soul_shard": 0.18},
            "quest_target": "world_exp_desert_threat",
        },
        "sun_guardian": {
            "name": "Pradawny Strażnik Słońca",
            "max_hp": 6800, "damage": 82, "damage_type": "magic",
            "silver": 2400, "gold": 9, "mithril": 0,
            "stat_reward": 760, "class_xp_reward": 15000, "soul_reward": 4200,
            "drops": {"soul_elixir": 0.35, "eternium_ore": 0.05},
            "quest_target": "world_exp_desert_threat",
            "world_boss": True,
        },
    }

    for mob_id, template in expansion_mobs.items():
        template.setdefault("corpse_equipment_pool", [
            "iron_guard", "iron_gauntlets", "forge_charm"
        ])
        template.setdefault("corpse_equipment_guaranteed", 1)
        MOB_TEMPLATES[mob_id] = template

    MOB_SPAWNS.extend([
        # Dzicz
        ("wild_frontier", "wild_thorn_wolf"),
        ("thorn_scrub", "wild_thorn_wolf"),
        ("thorn_scrub", "wild_ash_boar"),
        ("abandoned_farm", "wild_ash_boar"),
        ("burnt_fields", "wild_ash_boar"),
        ("stone_ravine", "wild_thorn_wolf"),
        ("broken_shrine", "wild_ash_boar"),
        ("beast_den", "wild_horned_king"),

        # Góry
        ("mountain_lower_slopes", "mountain_stone_ram"),
        ("goat_trail", "mountain_stone_ram"),
        ("abandoned_dwarf_hall", "mountain_ice_wolf"),
        ("wind_shelf", "mountain_harpy"),
        ("ice_pass", "mountain_ice_wolf"),
        ("lava_fissure", "mountain_stone_ram"),
        ("storm_summit", "mountain_storm_eagle"),

        # Jaskinia Trolli
        ("troll_fungus_cavern", "deep_troll_warrior"),
        ("troll_underground_river", "deep_troll_warrior"),
        ("troll_shaman_gallery", "deep_troll_shaman"),
        ("troll_nursery", "deep_troll_warrior"),
        ("troll_slave_pens", "deep_troll_warrior"),
        ("troll_treasure_vault", "deep_troll_shaman"),
        ("troll_bone_pit", "deep_troll_warrior"),
        ("troll_deep_war_camp", "deep_troll_warrior"),
        ("troll_deep_war_camp", "deep_troll_shaman"),
        ("troll_altar", "deep_troll_warlord"),

        # Bagna
        ("reed_mire", "swamp_crawler"),
        ("blackwater_pool", "swamp_serpent"),
        ("fungal_bog", "swamp_crawler"),
        ("serpent_nest", "swamp_serpent"),
        ("poison_fen", "swamp_mire_witch"),
        ("sunken_swamp_shrine", "swamp_mire_witch"),
        ("drowned_ruins", "swamp_crawler"),
        ("bog_heart", "swamp_hydra"),

        # Pustynia
        ("desert_gate", "desert_raider"),
        ("desert_dunes", "dune_scorpion"),
        ("scorpion_basin", "dune_scorpion"),
        ("glass_flats", "sand_wraith"),
        ("sandstone_ruins", "desert_raider"),
        ("buried_temple", "sand_wraith"),
        ("sun_temple", "sun_guardian"),
    ])

    # ========================================================
    # GUIDE / NPC ALIASES
    # ========================================================
    
    # ========================================================
    # EXPOWISKA
    # ========================================================
    for area in EXP_AREAS:
        if area["id"] == "dzicz":
            area["soul_max"] = 65
            area["description"] = (
                "Dzicz obejmuje teraz także Północną Dzicz, "
                "Cierniste Zarośla, Spalone Pola, Kamienny Wąwóz "
                "i Legowisko Rogatego Króla."
            )
        elif area["id"] == "trolle":
            area["soul_max"] = 120
            area["description"] = (
                "Góry obejmują Niższe Stoki, starą kopalnię krasnoludów, "
                "Lodową Przełęcz i Szczyt Burzy. Jaskinia Trolli ma teraz "
                "rozbudowane głębokie komory i wojenny obóz."
            )

    EXP_AREAS = EXP_AREAS + (
        {
            "id": "bagna",
            "name": "Czarne Bagna",
            "aliases": (
                "bagna", "czarne bagno", "mokradla", "mokradła",
                "hydra",
            ),
            "soul_min": 40,
            "soul_max": 100,
            "difficulty": "średnia do trudnej",
            "guide": "bagna",
            "enemies": (
                "Pełzacze Bagienne, Węże Czarnej Wody, "
                "Wiedźmy Mokradła i Hydra Czarnego Bagna"
            ),
            "description": (
                "Rozległy teren mokradeł z hubem łowców, "
                "Zielarstwem i bossem świata na końcu."
            ),
            "note": (
                "Bagna są dobrym terenem dla Zielarstwa, ale głębsze "
                "lokacje są znacznie groźniejsze od wejścia."
            ),
        },
        {
            "id": "pustynia",
            "name": "Wielka Pustynia",
            "aliases": (
                "pustynia", "wydmy", "karawany", "swiatynia slonca",
                "świątynia słońca",
            ),
            "soul_min": 70,
            "soul_max": 140,
            "difficulty": "trudna",
            "guide": "pustynia",
            "enemies": (
                "Pustynni Łupieżcy, Olbrzymie Skorpiony Wydm, "
                "Piaskowe Upiory i Pradawny Strażnik Słońca"
            ),
            "description": (
                "Duży region z obozem karawan, oazą, ruinami, "
                "Zasypaną Świątynią i bossem świata."
            ),
            "note": (
                "Obóz Karawan jest głównym bezpiecznym hubem Pustyni."
            ),
        },
    )

    # ========================================================
    # HELP
    # ========================================================
    HELP_TOPICS["world_expansion_i"] = [
        "World Expansion I rozbudowuje Dzicz, Góry i Jaskinię Trolli oraz dodaje Bagna i Pustynię.",
        "Dodano ponad 40 nowych lokacji i kilka nowych terenowych hubów.",
        "Północna Dzicz zaczyna się na północ od Rozdroża.",
        "Wysokie Góry odchodzą na północ od Górskiej Przełęczy.",
        "Głębokie komory Jaskini Trolli odchodzą od istniejących tuneli.",
        "Czarne Bagna zaczynają się na południe od Głębi Gaju.",
        "Wielka Pustynia zaczyna się na północ od Ruin Strażnicy.",
        "Nowe tereny mają własne moby, bossów świata, NPC i questy.",
        "Specjaliści profesji zostali rozdzieleni do osobnych logicznych pomieszczeń.",
        "Neris: Szkoła Wędkarstwa.",
        "Kordan: Gildia Górników.",
        "Oren: Leśniczówka.",
        "Sena: Ogród Zielarski.",
        "Orin: Laboratorium Alchemiczne.",
        "Haldor: Warsztat Rzemieślniczy.",
        "Sprzedawcy podstawowych narzędzi pozostają w swoich dotychczasowych miejscach.",
        "Kilof nadal sprzedaje wyłącznie Górnik Toren.",
        "Komendy prowadz i expowiska obejmują nowe regiony.",
    ]



def build_world_expansion_ii():
    """Six explorable areas plus location-bound profession field quests."""
    global EXP_AREAS

    # ========================================================
    # UNIQUE FIELD RESOURCES — ONLY FROM SPECIFIC NEW ROOMS
    # ========================================================
    field_items = {
        "field_grave_moss": {
            "name": "Mech Nagrobny", "type": "resource", "price": None,
            "resource_category": "herb", "sell_silver": 22,
            "desc": "Zioło rosnące wyłącznie na starych nagrobkach Cmentarza.",
        },
        "field_void_thorn": {
            "name": "Cierń Pustki", "type": "resource", "price": None,
            "resource_category": "herb", "sell_silver": 38,
            "desc": "Skażona roślina występująca tylko w Ruinach Kultystów.",
        },
        "field_ironbark_root": {
            "name": "Korzeń Żelaznokory", "type": "resource", "price": None,
            "resource_category": "wood", "sell_silver": 34,
            "desc": "Twardy korzeń pozyskiwany tylko w Legowisku Bestii.",
        },
        "field_tomb_silver": {
            "name": "Srebro Grobowe", "type": "resource", "price": None,
            "resource_category": "ore", "sell_silver": 45,
            "desc": "Ciemne srebro z głębszych warstw Kopalni Głębinowej, dostępne od poziomu 80.",
        },
        "field_blind_sewer_eel": {
            "name": "Ślepy Węgorz Kanałowy", "type": "resource", "price": None,
            "resource_category": "fish", "sell_silver": 28,
            "desc": "Rzadka ryba żyjąca tylko w podziemnym kanale pod Miastem Dusz.",
        },
        "field_frost_crystal_ore": {
            "name": "Ruda Lodowego Kryształu", "type": "resource", "price": None,
            "resource_category": "ore", "sell_silver": 60,
            "desc": "Lodowy minerał z Kopalni Głębinowej, dostępny od poziomu 100.",
        },
    }
    ITEMS.update(field_items)
    HERB_STORAGE_IDS.update({"field_grave_moss", "field_void_thorn"})
    WOOD_STORAGE_IDS.add("field_ironbark_root")
    ORE_STORAGE_IDS.update({"field_tomb_silver", "field_frost_crystal_ore"})
    MINING_STORAGE_IDS.update({"field_tomb_silver", "field_frost_crystal_ore"})
    FISH_STORAGE_IDS.add("field_blind_sewer_eel")
    # v0.8.72: terenowe zasoby są pełnoprawną częścią atlasów/codexu,
    # nie tylko specjalistycznych sakw.
    HERB_RESOURCE_IDS.update({"field_grave_moss", "field_void_thorn"})
    WOOD_RESOURCE_IDS.add("field_ironbark_root")
    ORE_RESOURCE_IDS.update({"field_tomb_silver", "field_frost_crystal_ore"})
    FISH_RESOURCE_IDS.add("field_blind_sewer_eel")
    HERB_ATLAS_ALL.update({"field_grave_moss", "field_void_thorn"})
    WOOD_ATLAS_ALL.add("field_ironbark_root")
    ORE_ATLAS_ALL.update({"field_tomb_silver", "field_frost_crystal_ore"})
    FISH_ATLAS_ALL.add("field_blind_sewer_eel")
    # Minimalne wymagania narzędzia zgodne ze specjalistycznymi questami.
    ORE_ATLAS_LEVELS.update({"field_tomb_silver": 80, "field_frost_crystal_ore": 100})
    ORE_MINE_FLOOR_MINIMUMS.update({"field_tomb_silver": 80, "field_frost_crystal_ore": 100})

    # ========================================================
    # 1. STARY CMENTARZ — expansion of the existing Graveyard
    # ========================================================
    ROOMS["graveyard"]["zone"] = "Stary Cmentarz"
    ROOMS["graveyard"]["exits"].update({"north": "cemetery_ossuary_path", "east": "necropolis_gate"})
    ROOMS.update({
        "cemetery_ossuary_path": {"zone":"Stary Cmentarz","name":"Aleja Ossuariów","desc":"Popękane kapliczki i kamienne ossuaria stoją po obu stronach wąskiej alei.","exits":{"south":"graveyard","north":"cemetery_fallen_chapel","west":"cemetery_moon_garden"}},
        "cemetery_moon_garden": {"zone":"Stary Cmentarz","name":"Ogród Księżycowego Mchu","desc":"Wilgotne nagrobki porasta Mech Nagrobny. To terenowe miejsce Zielarstwa.","exits":{"east":"cemetery_ossuary_path","north":"cemetery_bone_field"}},
        "cemetery_fallen_chapel": {"zone":"Stary Cmentarz","name":"Zawalona Kaplica","desc":"Dach kaplicy runął, odsłaniając stare krypty i zbezczeszczony ołtarz.","exits":{"south":"cemetery_ossuary_path","north":"cemetery_bell_tower"}},
        "cemetery_bone_field": {"zone":"Stary Cmentarz","name":"Pole Kości","desc":"Płytkie groby zostały rozkopane, a kości tworzą białe pasma wśród ziemi.","exits":{"south":"cemetery_moon_garden","east":"cemetery_bell_tower"}},
        "cemetery_bell_tower": {"zone":"Stary Cmentarz","name":"Wieża Martwego Dzwonu","desc":"Pęknięty dzwon porusza się bez wiatru. Dalej znajduje się grobowiec grabarza.","exits":{"south":"cemetery_fallen_chapel","west":"cemetery_bone_field","north":"cemetery_keeper_tomb"}},
        "cemetery_keeper_tomb": {"zone":"Stary Cmentarz","name":"Grobowiec Strażnika Cmentarza","desc":"Kamienny sarkofag stoi pośrodku komory. Spoczynek Strażnika dawno został przerwany.","exits":{"south":"cemetery_bell_tower"}},
    })
    HERBALISM_ROOMS.add("cemetery_moon_garden")

    # ========================================================
    # 2. RUINY KULTYSTÓW
    # ========================================================
    ROOMS["ruined_watchtower"]["exits"]["north"] = "cult_ruins_gate"
    ROOMS.update({
        "cult_ruins_gate": {"zone":"Ruiny Kultystów","name":"Brama Ruin Kultystów","desc":"Czarne symbole pokrywają resztki kamiennej bramy. Dalej prowadzi zarośnięty dziedziniec.","exits":{"south":"ruined_watchtower","north":"cult_ruins_courtyard"}},
        "cult_ruins_courtyard": {"zone":"Ruiny Kultystów","name":"Zbezczeszczony Dziedziniec","desc":"Rozbite posągi otaczają krąg wypalonej ziemi.","exits":{"south":"cult_ruins_gate","north":"cult_ruins_cloister","east":"cult_ruins_overgrown_garden"}},
        "cult_ruins_overgrown_garden": {"zone":"Ruiny Kultystów","name":"Ogród Cierni Pustki","desc":"Czarne pnącza rodzą Cierń Pustki. To terenowe miejsce Zielarstwa.","exits":{"west":"cult_ruins_courtyard","north":"cult_ruins_library"}},
        "cult_ruins_cloister": {"zone":"Ruiny Kultystów","name":"Krużganek Szeptów","desc":"Każdy krok odbija się szeptem, którego nie wypowiada żaden żywy człowiek.","exits":{"south":"cult_ruins_courtyard","north":"cult_ruins_ritual_hall"}},
        "cult_ruins_library": {"zone":"Ruiny Kultystów","name":"Spalona Biblioteka Kultu","desc":"Zwęglone księgi i metalowe tablice leżą między zawalonymi regałami.","exits":{"south":"cult_ruins_overgrown_garden","west":"cult_ruins_ritual_hall"}},
        "cult_ruins_ritual_hall": {"zone":"Ruiny Kultystów","name":"Sala Rytuałów","desc":"Runy tworzą koncentryczne kręgi wokół kamiennego ołtarza.","exits":{"south":"cult_ruins_cloister","east":"cult_ruins_library","north":"cult_ruins_sanctum"}},
        "cult_ruins_sanctum": {"zone":"Ruiny Kultystów","name":"Sanktuarium Pustki","desc":"Najgłębsza część ruin. Tutaj Arcykultysta podtrzymuje pęknięcie Pustki.","exits":{"south":"cult_ruins_ritual_hall"}},
    })
    HERBALISM_ROOMS.add("cult_ruins_overgrown_garden")

    # ========================================================
    # 3. LEGOWISKO BESTII — deeper branch from Beast Den
    # ========================================================
    ROOMS["beast_den"]["exits"]["west"] = "beast_lair_mouth"
    ROOMS.update({
        "beast_lair_mouth": {"zone":"Legowisko Bestii","name":"Szczelina Legowiska Bestii","desc":"Pazury wyżłobiły głębokie ślady w skale. Z wnętrza dochodzi ciężki oddech.","exits":{"east":"beast_den","west":"beast_lair_tracks"}},
        "beast_lair_tracks": {"zone":"Legowisko Bestii","name":"Korytarz Tropów","desc":"Błoto jest pełne nakładających się śladów łap i kopyt.","exits":{"east":"beast_lair_mouth","west":"beast_lair_root_cavern","north":"beast_lair_bone_nest"}},
        "beast_lair_root_cavern": {"zone":"Legowisko Bestii","name":"Grota Żelaznokory","desc":"Pradawne korzenie przebijają strop. Można tu pozyskać Korzeń Żelaznokory.","exits":{"east":"beast_lair_tracks","north":"beast_lair_hunting_ground"}},
        "beast_lair_bone_nest": {"zone":"Legowisko Bestii","name":"Kościane Gniazdo","desc":"Wielkie gniazdo zbudowano z gałęzi, futer i kości.","exits":{"south":"beast_lair_tracks","west":"beast_lair_hunting_ground"}},
        "beast_lair_hunting_ground": {"zone":"Legowisko Bestii","name":"Podziemne Łowisko","desc":"Szeroka jaskinia jest naturalną areną polowań drapieżników.","exits":{"south":"beast_lair_root_cavern","east":"beast_lair_bone_nest","north":"beast_lair_alpha_den"}},
        "beast_lair_alpha_den": {"zone":"Legowisko Bestii","name":"Nora Pradawnego Alfa","desc":"Najgłębsza nora jest pełna świeżych śladów i połamanych rogów. Tu mieszka Pradawny Alfa.","exits":{"south":"beast_lair_hunting_ground"}},
    })
    WOODCUTTING_ROOMS.add("beast_lair_root_cavern")

    # ========================================================
    # 4. NEKROPOLIA
    # ========================================================
    ROOMS.update({
        "necropolis_gate": {"zone":"Nekropolia","name":"Brama Nekropolii","desc":"Olbrzymie kamienne wrota prowadzą do miasta grobowców.","exits":{"west":"graveyard","east":"necropolis_procession"}},
        "necropolis_procession": {"zone":"Nekropolia","name":"Aleja Procesyjna","desc":"Posągi bez twarzy stoją wzdłuż drogi prowadzącej między mauzoleami.","exits":{"west":"necropolis_gate","east":"necropolis_quarry","north":"necropolis_catacombs"}},
        "necropolis_quarry": {"zone":"Nekropolia","name":"Grobowy Kamieniołom","desc":"Dawny kamieniołom Nekropolii. Wydobycie przeniesiono do Kopalni Głębinowej; miejsce pozostało częścią regionu i questów.","exits":{"west":"necropolis_procession","north":"necropolis_silent_square"}},
        "necropolis_catacombs": {"zone":"Nekropolia","name":"Katakumby Bezimiennych","desc":"Niskie tunele są wypełnione setkami zapieczętowanych nisz.","exits":{"south":"necropolis_procession","east":"necropolis_silent_square"}},
        "necropolis_silent_square": {"zone":"Nekropolia","name":"Plac Ciszy","desc":"Centralny plac Nekropolii otaczają cztery monumentalne grobowce.","exits":{"south":"necropolis_quarry","west":"necropolis_catacombs","north":"necropolis_royal_tombs"}},
        "necropolis_royal_tombs": {"zone":"Nekropolia","name":"Królewskie Grobowce","desc":"Złote inskrypcje mówią o dynastii, której imię zostało wymazane.","exits":{"south":"necropolis_silent_square","north":"necropolis_throne"}},
        "necropolis_throne": {"zone":"Nekropolia","name":"Tron Umarłego Króla","desc":"Kamienny tron stoi przed otwartym sarkofagiem. Umarły Król powrócił do swej sali.","exits":{"south":"necropolis_royal_tombs"}},
    })

    # ========================================================
    # 5. KANAŁY POD MIASTEM
    # ========================================================
    ROOMS["south_street"]["exits"]["down"] = "sewer_entrance"
    ROOMS.update({
        "sewer_entrance": {"zone":"Kanały Pod Miastem","name":"Krata Kanałów","desc":"Kamienne schody schodzą pod ulicę do wilgotnych kanałów.","exits":{"up":"south_street","down":"sewer_runoff"}},
        "sewer_runoff": {"zone":"Kanały Pod Miastem","name":"Kanał Odpływowy","desc":"Brudna woda płynie płytkim korytem między kamiennymi ścianami.","exits":{"up":"sewer_entrance","east":"sewer_rat_nest","south":"sewer_black_channel"}},
        "sewer_rat_nest": {"zone":"Kanały Pod Miastem","name":"Gniazdo Szczurów","desc":"Resztki skrzyń i tkanin tworzą ogromne gniazdo pod fundamentami.","exits":{"west":"sewer_runoff","south":"sewer_smuggler_den"}},
        "sewer_black_channel": {"zone":"Kanały Pod Miastem","name":"Czarny Kanał","desc":"Głęboki kanał jest jedynym siedliskiem Ślepego Węgorza Kanałowego.","exits":{"north":"sewer_runoff","east":"sewer_smuggler_den"}},
        "sewer_smuggler_den": {"zone":"Kanały Pod Miastem","name":"Kryjówka Przemytników","desc":"Puste beczki i fałszywe skrzynie zdradzają dawną trasę przemytników.","exits":{"north":"sewer_rat_nest","west":"sewer_black_channel","south":"sewer_flooded_vault"}},
        "sewer_flooded_vault": {"zone":"Kanały Pod Miastem","name":"Zalana Komora","desc":"Woda sięga kolan, a na dnie widać stare monety i kości.","exits":{"north":"sewer_smuggler_den","east":"sewer_cistern"}},
        "sewer_cistern": {"zone":"Kanały Pod Miastem","name":"Stara Cysterna","desc":"Wielka podziemna cysterna jest legowiskiem czegoś znacznie większego niż szczur.","exits":{"west":"sewer_flooded_vault"}},
    })
    RIVER_FISHING_ROOMS.add("sewer_black_channel")
    FISHING_ROOMS.add("sewer_black_channel")

    # ========================================================
    # 6. LODOWE JASKINIE
    # ========================================================
    ROOMS["ice_pass"]["exits"]["east"] = "ice_cave_mouth"
    ROOMS.update({
        "ice_cave_mouth": {"zone":"Lodowe Jaskinie","name":"Wejście do Lodowych Jaskiń","desc":"Szczelina w lodzie prowadzi do błękitnych tuneli pod górą.","exits":{"west":"ice_pass","east":"ice_cave_blue_tunnel"}},
        "ice_cave_blue_tunnel": {"zone":"Lodowe Jaskinie","name":"Błękitny Tunel","desc":"Światło odbija się w tysiącach drobnych kryształów lodu.","exits":{"west":"ice_cave_mouth","east":"ice_cave_frozen_lake","north":"ice_cave_crystal_chamber"}},
        "ice_cave_crystal_chamber": {"zone":"Lodowe Jaskinie","name":"Komnata Lodowego Kryształu","desc":"Komnata lodowych kryształów. Wydobycie przeniesiono do Kopalni Głębinowej; komnata pozostała miejscem eksploracji i walki.","exits":{"south":"ice_cave_blue_tunnel","east":"ice_cave_glacier裂"}},
        "ice_cave_frozen_lake": {"zone":"Lodowe Jaskinie","name":"Zamarznięte Jezioro","desc":"Gruby lód przykrywa czarną wodę. Coś porusza się pod powierzchnią.","exits":{"west":"ice_cave_blue_tunnel","north":"ice_cave_glacier裂"}},
        "ice_cave_glacier裂": {"zone":"Lodowe Jaskinie","name":"Szczelina Lodowca","desc":"Wąska rozpadlina prowadzi do najstarszej części jaskiń.","exits":{"west":"ice_cave_crystal_chamber","south":"ice_cave_frozen_lake","north":"ice_cave_ancient_hall"}},
        "ice_cave_ancient_hall": {"zone":"Lodowe Jaskinie","name":"Pradawna Sala Lodu","desc":"Naturalne kolumny lodu przypominają salę tronową.","exits":{"south":"ice_cave_glacier裂","north":"ice_cave_dragon_nest"}},
        "ice_cave_dragon_nest": {"zone":"Lodowe Jaskinie","name":"Gniazdo Lodowego Smoka","desc":"Ogromne ślady pazurów otaczają gniazdo wykute w wiecznym lodzie.","exits":{"south":"ice_cave_ancient_hall"}},
    })

    # ========================================================
    # MOBS — 6 AREAS, REGULARS + ELITES + BOSSES
    # ========================================================
    MOB_TEMPLATES.update({
        # Cemetery
        "cemetery_restless_dead":{"name":"Niespokojny Zmarły","max_hp":260,"damage":22,"damage_type":"physical","silver":55,"gold":0,"mithril":0,"stat_reward":70,"class_xp_reward":850,"soul_reward":520,"drops":{"soul_shard":0.25},"quest_target":None},
        "cemetery_grave_hound":{"name":"Grobowy Ogar","max_hp":320,"damage":26,"damage_type":"physical","silver":65,"gold":0,"mithril":0,"stat_reward":82,"class_xp_reward":1000,"soul_reward":610,"drops":{"wolf_fang":0.45},"quest_target":None},
        "cemetery_bone_collector":{"name":"Zbieracz Kości","max_hp":410,"damage":31,"damage_type":"magic","silver":80,"gold":1,"mithril":0,"stat_reward":95,"class_xp_reward":1250,"soul_reward":750,"drops":{"soul_shard":0.45},"quest_target":None},
        "cemetery_bell_wraith":{"name":"Upiór Martwego Dzwonu","max_hp":540,"damage":38,"damage_type":"magic","silver":95,"gold":1,"mithril":0,"stat_reward":115,"class_xp_reward":1550,"soul_reward":930,"drops":{"soul_shard":0.60},"quest_target":None},
        "cemetery_keeper":{"name":"Nieumarły Strażnik Cmentarza","max_hp":1300,"damage":55,"damage_type":"physical","silver":250,"gold":3,"mithril":0,"stat_reward":180,"class_xp_reward":3300,"soul_reward":1900,"drops":{"soul_elixir":0.18},"quest_target":None,"boss_mechanic":"cemetery_keeper","world_boss":True},
        # Cult ruins
        "cult_acolyte":{"name":"Akolita Pustki","max_hp":520,"damage":41,"damage_type":"magic","silver":100,"gold":1,"mithril":0,"stat_reward":120,"class_xp_reward":1750,"soul_reward":1050,"drops":{"soul_shard":0.45},"quest_target":None},
        "cult_blade":{"name":"Ostrze Kultu","max_hp":610,"damage":47,"damage_type":"physical","silver":115,"gold":1,"mithril":0,"stat_reward":135,"class_xp_reward":2050,"soul_reward":1220,"drops":{"soul_shard":0.40},"quest_target":None},
        "cult_void_seer":{"name":"Wieszcz Pustki","max_hp":700,"damage":53,"damage_type":"magic","silver":130,"gold":2,"mithril":0,"stat_reward":150,"class_xp_reward":2350,"soul_reward":1450,"drops":{"soul_elixir":0.10},"quest_target":None},
        "cult_ritual_guard":{"name":"Strażnik Rytuału","max_hp":850,"damage":61,"damage_type":"physical","silver":150,"gold":2,"mithril":0,"stat_reward":165,"class_xp_reward":2750,"soul_reward":1700,"drops":{"soul_shard":0.70},"quest_target":None},
        "cult_archon":{"name":"Arcykultysta Otchłani","max_hp":2400,"damage":82,"damage_type":"magic","silver":350,"gold":6,"mithril":0,"stat_reward":260,"class_xp_reward":6000,"soul_reward":4200,"drops":{"soul_elixir":0.30},"quest_target":None,"boss_mechanic":"void_archon","world_boss":True},
        # Beast lair
        "beast_cave_stalker":{"name":"Jaskiniowy Tropiciel","max_hp":430,"damage":36,"damage_type":"physical","silver":75,"gold":1,"mithril":0,"stat_reward":105,"class_xp_reward":1450,"soul_reward":880,"drops":{"wolf_fang":0.55},"quest_target":None},
        "beast_ironhide_boar":{"name":"Dzik Żelaznoskóry","max_hp":650,"damage":45,"damage_type":"physical","silver":90,"gold":1,"mithril":0,"stat_reward":125,"class_xp_reward":1800,"soul_reward":1100,"drops":{},"quest_target":None},
        "beast_root_bear":{"name":"Niedźwiedź Korzeni","max_hp":780,"damage":52,"damage_type":"physical","silver":105,"gold":1,"mithril":0,"stat_reward":140,"class_xp_reward":2200,"soul_reward":1350,"drops":{},"quest_target":None},
        "beast_bone_mane":{"name":"Kościanogrzywy Drapieżnik","max_hp":920,"damage":60,"damage_type":"physical","silver":125,"gold":2,"mithril":0,"stat_reward":160,"class_xp_reward":2600,"soul_reward":1600,"drops":{"soul_shard":0.35},"quest_target":None},
        "beast_ancient_alpha":{"name":"Pradawny Alfa Bestii","max_hp":2800,"damage":88,"damage_type":"physical","silver":320,"gold":5,"mithril":0,"stat_reward":275,"class_xp_reward":6500,"soul_reward":4500,"drops":{"soul_elixir":0.22},"quest_target":None,"boss_mechanic":"ancient_alpha","world_boss":True},
        # Necropolis
        "necro_tomb_guard":{"name":"Strażnik Grobowca","max_hp":820,"damage":58,"damage_type":"physical","silver":130,"gold":2,"mithril":0,"stat_reward":165,"class_xp_reward":2800,"soul_reward":1750,"drops":{"soul_shard":0.55},"quest_target":None},
        "necro_mourning_spirit":{"name":"Duch Żałobnika","max_hp":760,"damage":62,"damage_type":"magic","silver":140,"gold":2,"mithril":0,"stat_reward":175,"class_xp_reward":3000,"soul_reward":1900,"drops":{"soul_shard":0.65},"quest_target":None},
        "necro_bone_knight":{"name":"Kościany Rycerz","max_hp":1050,"damage":72,"damage_type":"physical","silver":165,"gold":3,"mithril":0,"stat_reward":195,"class_xp_reward":3500,"soul_reward":2250,"drops":{},"quest_target":None},
        "necro_royal_lich":{"name":"Królewski Licz","max_hp":1250,"damage":78,"damage_type":"magic","silver":185,"gold":3,"mithril":0,"stat_reward":210,"class_xp_reward":3900,"soul_reward":2550,"drops":{"soul_elixir":0.12},"quest_target":None},
        "necro_dead_king":{"name":"Umarły Król Nekropolii","max_hp":4200,"damage":105,"damage_type":"magic","silver":450,"gold":9,"mithril":1,"stat_reward":340,"class_xp_reward":9000,"soul_reward":7000,"drops":{"soul_elixir":0.38},"quest_target":None,"boss_mechanic":"dead_king","world_boss":True},
        # Sewers
        "sewer_plague_rat":{"name":"Szczur Zarazy","max_hp":210,"damage":19,"damage_type":"physical","silver":40,"gold":0,"mithril":0,"stat_reward":60,"class_xp_reward":700,"soul_reward":410,"drops":{},"quest_target":None},
        "sewer_slime":{"name":"Szlam Kanałowy","max_hp":290,"damage":23,"damage_type":"magic","silver":48,"gold":0,"mithril":0,"stat_reward":72,"class_xp_reward":850,"soul_reward":500,"drops":{},"quest_target":None},
        "sewer_smuggler":{"name":"Przemytnik Kanałów","max_hp":360,"damage":28,"damage_type":"physical","silver":70,"gold":1,"mithril":0,"stat_reward":85,"class_xp_reward":1050,"soul_reward":640,"drops":{},"quest_target":None},
        "sewer_mutant":{"name":"Mutant z Cysterny","max_hp":500,"damage":35,"damage_type":"physical","silver":85,"gold":1,"mithril":0,"stat_reward":100,"class_xp_reward":1350,"soul_reward":820,"drops":{"soul_shard":0.25},"quest_target":None},
        "sewer_king":{"name":"Król Podmiejskich Kanałów","max_hp":1500,"damage":58,"damage_type":"physical","silver":260,"gold":3,"mithril":0,"stat_reward":190,"class_xp_reward":3600,"soul_reward":2200,"drops":{"soul_elixir":0.15},"quest_target":None,"boss_mechanic":"sewer_king","world_boss":True},
        # Ice caves
        "ice_fang_wolf":{"name":"Wilk Lodowego Kła","max_hp":700,"damage":52,"damage_type":"physical","silver":110,"gold":1,"mithril":0,"stat_reward":145,"class_xp_reward":2350,"soul_reward":1450,"drops":{"wolf_fang":0.70},"quest_target":None},
        "ice_crystal_golem":{"name":"Golem Lodowego Kryształu","max_hp":980,"damage":60,"damage_type":"magic","silver":135,"gold":2,"mithril":0,"stat_reward":170,"class_xp_reward":2900,"soul_reward":1850,"drops":{"soul_shard":0.50},"quest_target":None},
        "ice_wraith":{"name":"Upiór Szronu","max_hp":860,"damage":65,"damage_type":"magic","silver":145,"gold":2,"mithril":0,"stat_reward":180,"class_xp_reward":3150,"soul_reward":2050,"drops":{"soul_shard":0.65},"quest_target":None},
        "ice_glacier_guard":{"name":"Strażnik Lodowca","max_hp":1200,"damage":74,"damage_type":"physical","silver":170,"gold":3,"mithril":0,"stat_reward":205,"class_xp_reward":3700,"soul_reward":2450,"drops":{},"quest_target":None},
        "ice_dragon":{"name":"Pradawny Lodowy Smok","max_hp":5000,"damage":118,"damage_type":"magic","silver":520,"gold":10,"mithril":1,"stat_reward":380,"class_xp_reward":10500,"soul_reward":8200,"drops":{"soul_elixir":0.42},"quest_target":None,"boss_mechanic":"ice_dragon","world_boss":True},
    })

    MOB_SPAWNS.extend([
        ("graveyard","cemetery_restless_dead"),("cemetery_ossuary_path","cemetery_restless_dead"),("cemetery_moon_garden","cemetery_grave_hound"),("cemetery_fallen_chapel","cemetery_bone_collector"),("cemetery_bone_field","cemetery_grave_hound"),("cemetery_bell_tower","cemetery_bell_wraith"),("cemetery_keeper_tomb","cemetery_keeper"),
        ("cult_ruins_gate","cult_acolyte"),("cult_ruins_courtyard","cult_blade"),("cult_ruins_overgrown_garden","cult_acolyte"),("cult_ruins_cloister","cult_void_seer"),("cult_ruins_library","cult_void_seer"),("cult_ruins_ritual_hall","cult_ritual_guard"),("cult_ruins_sanctum","cult_archon"),
        ("beast_lair_mouth","beast_cave_stalker"),("beast_lair_tracks","beast_cave_stalker"),("beast_lair_root_cavern","beast_ironhide_boar"),("beast_lair_bone_nest","beast_bone_mane"),("beast_lair_hunting_ground","beast_root_bear"),("beast_lair_alpha_den","beast_ancient_alpha"),
        ("necropolis_gate","necro_tomb_guard"),("necropolis_procession","necro_tomb_guard"),("necropolis_quarry","necro_bone_knight"),("necropolis_catacombs","necro_mourning_spirit"),("necropolis_silent_square","necro_bone_knight"),("necropolis_royal_tombs","necro_royal_lich"),("necropolis_throne","necro_dead_king"),
        ("sewer_runoff","sewer_plague_rat"),("sewer_rat_nest","sewer_plague_rat"),("sewer_black_channel","sewer_slime"),("sewer_smuggler_den","sewer_smuggler"),("sewer_flooded_vault","sewer_mutant"),("sewer_cistern","sewer_king"),
        ("ice_cave_mouth","ice_fang_wolf"),("ice_cave_blue_tunnel","ice_fang_wolf"),("ice_cave_crystal_chamber","ice_crystal_golem"),("ice_cave_frozen_lake","ice_wraith"),("ice_cave_glacier裂","ice_glacier_guard"),("ice_cave_ancient_hall","ice_wraith"),("ice_cave_dragon_nest","ice_dragon"),
    ])

    # ========================================================
    # FIELD PROFESSION QUESTS
    # ========================================================
    QUESTS.update({
        "field_grave_moss": {"name":"Terenowe Zielarstwo: Mech Nagrobny","giver":"Mistrzyni Zielarstwa Sena","kind":"collect_resource","target":"field_grave_moss","needed":8,"description":"Zbierz 8 sztuk Mchu Nagrobnego wyłącznie w Ogrodzie Księżycowego Mchu na Starym Cmentarzu. Postęp zaczyna od 0/8 i rośnie przy każdym nowym zbiorze po przyjęciu questa.","progress_label":"Mech Nagrobny","specialist_tool_type":"herbalism","min_tool_level":20,"reward_profession":"Zielarstwo","reward_profession_xp":1400,"reward_tool_type":"herbalism","reward_tool_xp":1100,"reward_silver":260,"reward_gold":1,"reward_mithril":0,"reward_items":{},"repeatable":True,"repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS},
        "field_void_thorn": {"name":"Terenowe Zielarstwo: Cierń Pustki","giver":"Mistrzyni Zielarstwa Sena","kind":"collect_resource","target":"field_void_thorn","needed":8,"description":"Zbierz 8 Cierni Pustki wyłącznie w Ogrodzie Cierni Pustki w Ruinach Kultystów.","specialist_tool_type":"herbalism","min_tool_level":60,"reward_profession":"Zielarstwo","reward_profession_xp":2400,"reward_tool_type":"herbalism","reward_tool_xp":1900,"reward_silver":420,"reward_gold":2,"reward_mithril":0,"reward_items":{},"repeatable":True,"repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS},
        "field_ironbark_root": {"name":"Terenowe Drwalstwo: Korzeń Żelaznokory","giver":"Mistrz Drwalstwa Oren","kind":"collect_resource","target":"field_ironbark_root","needed":8,"description":"Pozyskaj 8 Korzeni Żelaznokory wyłącznie w Grocie Żelaznokory w Legowisku Bestii.","specialist_tool_type":"woodcutting","min_tool_level":40,"reward_profession":"Drwalstwo","reward_profession_xp":1900,"reward_tool_type":"woodcutting","reward_tool_xp":1500,"reward_silver":330,"reward_gold":1,"reward_mithril":0,"reward_items":{},"repeatable":True,"repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS},
        "field_tomb_silver": {"name":"Głębinowe Górnictwo: Srebro Grobowe","giver":"Mistrz Górnictwa Kordan","kind":"collect_resource","target":"field_tomb_silver","needed":10,"description":"Wydobądź 10 Srebra Grobowego w Kopalni Głębinowej od poziomu 80.","specialist_tool_type":"mining","min_tool_level":80,"reward_profession":"Górnictwo","reward_profession_xp":3200,"reward_tool_type":"mining","reward_tool_xp":2600,"reward_silver":600,"reward_gold":3,"reward_mithril":0,"reward_items":{},"repeatable":True,"repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS},
        "field_blind_sewer_eel": {"name":"Terenowe Wędkarstwo: Ślepy Węgorz","giver":"Mistrz Wędkarstwa Neris","kind":"collect_resource","target":"field_blind_sewer_eel","needed":6,"description":"Złów 6 Ślepych Węgorzy Kanałowych wyłącznie w Czarnym Kanale pod Miastem Dusz.","specialist_tool_type":"fishing","min_tool_level":30,"reward_profession":"Wędkarstwo","reward_profession_xp":1600,"reward_tool_type":"fishing","reward_tool_xp":1300,"reward_silver":300,"reward_gold":1,"reward_mithril":0,"reward_items":{},"repeatable":True,"repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS},
        "field_frost_crystal_ore": {"name":"Głębinowe Górnictwo: Lodowy Kryształ","giver":"Mistrz Górnictwa Kordan","kind":"collect_resource","target":"field_frost_crystal_ore","needed":10,"description":"Wydobądź 10 Rudy Lodowego Kryształu w Kopalni Głębinowej od poziomu 100.","specialist_tool_type":"mining","min_tool_level":100,"reward_profession":"Górnictwo","reward_profession_xp":4200,"reward_tool_type":"mining","reward_tool_xp":3500,"reward_silver":800,"reward_gold":4,"reward_mithril":0,"reward_items":{},"repeatable":True,"repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS},
    })

    # Specialists list these field quests when spoken to.
    NPCS["specialist_herbalism"]["specialist_quests"] = tuple(NPCS["specialist_herbalism"].get("specialist_quests", ())) + ("field_grave_moss","field_void_thorn")
    NPCS["specialist_woodcutting"]["specialist_quests"] = tuple(NPCS["specialist_woodcutting"].get("specialist_quests", ())) + ("field_ironbark_root",)
    NPCS["specialist_mining"]["specialist_quests"] = tuple(NPCS["specialist_mining"].get("specialist_quests", ())) + ("field_tomb_silver","field_frost_crystal_ore")
    NPCS["specialist_fishing"]["specialist_quests"] = tuple(NPCS["specialist_fishing"].get("specialist_quests", ())) + ("field_blind_sewer_eel",)

    # ========================================================
    # GUIDE — only entrances; interior remains exploration-only
    # ========================================================
    GUIDE_DESTINATION_ALIASES.update({
        "cmentarz":"graveyard","stary cmentarz":"graveyard","cemetery":"graveyard",
        "ruiny kultystow":"cult_ruins_gate","ruiny kultu":"cult_ruins_gate","cultist ruins":"cult_ruins_gate",
        "legowisko bestii":"beast_lair_mouth","beast lair":"beast_lair_mouth",
        "nekropolia":"necropolis_gate","necropolis":"necropolis_gate",
        "kanaly":"sewer_entrance","kanaly pod miastem":"sewer_entrance","sewers":"sewer_entrance","city sewers":"sewer_entrance",
        "lodowe jaskinie":"ice_cave_mouth","lodowa jaskinia":"ice_cave_mouth","ice caves":"ice_cave_mouth","ice cave":"ice_cave_mouth",
    })

    # ========================================================
    # EXP AREAS
    # ========================================================
    EXP_AREAS = EXP_AREAS + (
        {"id":"cmentarz","name":"Stary Cmentarz","aliases":("cmentarz","stary cmentarz","cemetery"),"soul_min":15,"soul_max":45,"difficulty":"łatwa do średniej","guide":"cmentarz","enemies":"Niespokojni Zmarli, Grobowe Ogary, Zbieracze Kości, Upiory Dzwonu i Nieumarły Strażnik Cmentarza","description":"Rozbudowany cmentarz z alejami, kaplicą, polem kości, miejscem Zielarstwa i bossem na końcu.","note":"Mech Nagrobny można zebrać tylko w Ogrodzie Księżycowego Mchu."},
        {"id":"ruiny_kultystow","name":"Ruiny Kultystów","aliases":("ruiny kultystow","ruiny kultu","cultist ruins"),"soul_min":40,"soul_max":80,"difficulty":"średnia do trudnej","guide":"ruiny kultystow","enemies":"Akolici Pustki, Ostrza Kultu, Wieszcze Pustki, Strażnicy Rytuału i Arcykultysta Otchłani","description":"Zniszczony kompleks kultu z ogrodem skażonych roślin, biblioteką i sanktuarium.","note":"Cierń Pustki występuje tylko w Ogrodzie Cierni Pustki."},
        {"id":"legowisko_bestii","name":"Legowisko Bestii","aliases":("legowisko bestii","beast lair"),"soul_min":35,"soul_max":75,"difficulty":"średnia","guide":"legowisko bestii","enemies":"Jaskiniowe Tropiciele, Dziki Żelaznoskóre, Niedźwiedzie Korzeni, Kościanogrzywe Drapieżniki i Pradawny Alfa","description":"Podziemne legowisko drapieżników z bocznymi norami, terenem Drwalstwa i bossem alfa.","note":"Korzeń Żelaznokory pozyskuje się tylko w Grocie Żelaznokory."},
        {"id":"nekropolia","name":"Nekropolia","aliases":("nekropolia","necropolis"),"soul_min":70,"soul_max":125,"difficulty":"trudna","guide":"nekropolia","enemies":"Strażnicy Grobowców, Duchy Żałobników, Kościani Rycerze, Królewscy Licze i Umarły Król","description":"Miasto grobowców za Starym Cmentarzem, z katakumbami, kamieniołomem i królewską częścią.","note":"Srebro Grobowe wydobywa się w Kopalni Głębinowej od poziomu 80; kamieniołom jest miejscem eksploracji."},
        {"id":"kanaly","name":"Kanały Pod Miastem","aliases":("kanaly","kanaly pod miastem","sewers","city sewers"),"soul_min":10,"soul_max":45,"difficulty":"łatwa do średniej","guide":"kanaly","enemies":"Szczury Zarazy, Szlamy Kanałowe, Przemytnicy, Mutanci i Król Podmiejskich Kanałów","description":"Podziemna sieć pod Miastem Dusz z kanałem, kryjówką przemytników i starą cysterną.","note":"Ślepy Węgorz Kanałowy żyje tylko w Czarnym Kanale."},
        {"id":"lodowe_jaskinie","name":"Lodowe Jaskinie","aliases":("lodowe jaskinie","lodowa jaskinia","ice caves","ice cave"),"soul_min":60,"soul_max":115,"difficulty":"trudna","guide":"lodowe jaskinie","enemies":"Wilki Lodowego Kła, Golemy Lodowego Kryształu, Upiory Szronu, Strażnicy Lodowca i Pradawny Lodowy Smok","description":"Rozległe jaskinie odchodzące od Lodowej Przełęczy, z kryształową komnatą i gniazdem smoka.","note":"Rudę Lodowego Kryształu wydobywa się w Kopalni Głębinowej od poziomu 100; komnata jest miejscem eksploracji i walki."},
    )

    HELP_TOPICS["world_expansion_ii"] = [
        "World Expansion II dodaje 6 rozbudowanych expowisk: Stary Cmentarz, Ruiny Kultystów, Legowisko Bestii, Nekropolię, Kanały Pod Miastem i Lodowe Jaskinie.",
        "Każdy obszar ma własne pokoje, zwykłe moby, mocniejsze moby i bossa na końcu.",
        "prowadz / guide / walk prowadzi tylko przed wejście; wnętrze trzeba eksplorować samodzielnie.",
        "Dodano terenowe questy profesyjne z unikalnymi surowcami możliwymi do zdobycia tylko w konkretnym miejscu.",
        "Sena: Mech Nagrobny ze Starego Cmentarza i Cierń Pustki z Ruin Kultystów.",
        "Oren: Korzeń Żelaznokory z Legowiska Bestii.",
        "Kordan: wszystkie rudy, w tym Srebro Grobowe i Rudę Lodowego Kryształu, wydobywa się w Kopalni Głębinowej.",
        "Neris: Ślepy Węgorz Kanałowy z Kanałów Pod Miastem.",
    ]
    HELP_TOPICS["questy_profesji_teren"] = HELP_TOPICS["world_expansion_ii"]

def build_high_end_mob_pack():
    """
    High-End Mob Pack.
    Nie dodaje levelu ani XP postaci.
    Ogromne nagrody dotyczą wyłącznie Soul XP i Class Mastery XP.
    Najtrudniejsze moby są w osobnych odnogach, aby nie blokować
    zwykłego przechodzenia regionów.
    """

    # ========================================================
    # 5 ODDZIELNYCH ODNÓG WYZWANIA
    # ========================================================
    ROOMS["beast_den"]["exits"]["down"] = "wild_ancient_path"
    ROOMS["wild_ancient_path"] = {
        "zone": "Dzicz",
        "name": "Pradawny Szlak Bestii",
        "desc": (
            "To odgałęzienie Północnej Dziczy jest przeznaczone dla "
            "bardzo mocnych postaci. Zwykłe bestie tutaj nie przetrwały."
        ),
        "exits": {
            "up": "beast_den",
            "north": "wild_primal_hollow",
        },
    }
    ROOMS["wild_primal_hollow"] = {
        "zone": "Dzicz",
        "name": "Pradawna Kotlina Dziczy",
        "desc": (
            "W kotlinie żyje coś znacznie potężniejszego od Rogatego Króla. "
            "To teren wyzwania, nie zwykła ścieżka fabularna."
        ),
        "exits": {"south": "wild_ancient_path"},
    }

    ROOMS["storm_summit"]["exits"]["up"] = "mountain_tempest_path"
    ROOMS["mountain_tempest_path"] = {
        "zone": "Góry",
        "name": "Ścieżka Wiecznej Burzy",
        "desc": (
            "Błyskawice uderzają bez przerwy. Przeciwnicy tutaj mają "
            "ogromne HP i mocne kontrataki."
        ),
        "exits": {
            "down": "storm_summit",
            "north": "mountain_tempest_sanctum",
        },
    }
    ROOMS["mountain_tempest_sanctum"] = {
        "zone": "Góry",
        "name": "Sanktuarium Wiecznej Burzy",
        "desc": (
            "Kamienny krąg na samym szczycie. To miejsce jednego z "
            "najpotężniejszych przeciwników otwartego świata."
        ),
        "exits": {"south": "mountain_tempest_path"},
    }

    ROOMS["troll_altar"]["exits"]["down"] = "troll_abyss"
    ROOMS["troll_abyss"] = {
        "zone": "Jaskinia Trolli",
        "name": "Otchłań Trolli",
        "desc": (
            "Niżej żyją stare, wojenne kasty trolli. Ich wytrzymałość "
            "jest wielokrotnie większa od zwykłych trolli."
        ),
        "exits": {
            "up": "troll_altar",
            "south": "troll_abyss_throne",
        },
    }
    ROOMS["troll_abyss_throne"] = {
        "zone": "Jaskinia Trolli",
        "name": "Tron Pierwszego Wodza",
        "desc": (
            "Pradawny kamienny tron stoi w ogromnej pieczarze. "
            "To końcowe wyzwanie głębin Jaskini Trolli."
        ),
        "exits": {"north": "troll_abyss"},
    }

    ROOMS["bog_heart"]["exits"]["down"] = "swamp_rotten_depths"
    ROOMS["swamp_rotten_depths"] = {
        "zone": "Bagna",
        "name": "Gnijące Głębie Bagna",
        "desc": (
            "Pod powierzchnią mokradeł pulsują stare korzenie. "
            "Moby tej odnogi są przeznaczone dla endgame."
        ),
        "exits": {
            "up": "bog_heart",
            "south": "swamp_primordial_pool",
        },
    }
    ROOMS["swamp_primordial_pool"] = {
        "zone": "Bagna",
        "name": "Pradawne Rozlewisko",
        "desc": (
            "Czarna woda nie porusza się nawet przy silnym wietrze. "
            "To legowisko pierwotnej hydry."
        ),
        "exits": {"north": "swamp_rotten_depths"},
    }

    ROOMS["sun_temple"]["exits"]["down"] = "desert_sun_tomb"
    ROOMS["desert_sun_tomb"] = {
        "zone": "Pustynia",
        "name": "Grobowiec Słońca",
        "desc": (
            "Ukryta część świątyni zaczyna prawdziwy endgame Pustyni. "
            "Tutejsi strażnicy mają setki tysięcy punktów życia."
        ),
        "exits": {
            "up": "sun_temple",
            "north": "desert_solar_sanctum",
        },
    }
    ROOMS["desert_solar_sanctum"] = {
        "zone": "Pustynia",
        "name": "Sanktuarium Wiecznego Słońca",
        "desc": (
            "Oślepiające sanktuarium skrywa najpotężniejsze otwarte "
            "wyzwanie tego pakietu."
        ),
        "exits": {"south": "desert_sun_tomb"},
    }

    # ========================================================
    # ENDGAME ELITY + BOSSOWIE
    # max_hp jest wartością bazową; globalne x2 jest nakładane później.
    # ========================================================
    mobs = {
        # Dzicz — wejście do wysokiego endgame.
        "end_wild_ancient_mauler": {
            "name": "Pradawny Rozpruwacz Dziczy",
            "max_hp": 60000,
            "damage": 210,
            "damage_type": "physical",
            "silver": 10000, "gold": 20, "mithril": 0,
            "stat_reward": 4500,
            "class_xp_reward": 150000,
            "soul_reward": 100000,
            "drops": {"soul_shard": 0.65, "soul_elixir": 0.12},
            "quest_target": None,
        },
        "end_wild_spirit_behemoth": {
            "name": "Duchowy Behemot Dziczy",
            "max_hp": 100000,
            "damage": 270,
            "damage_type": "magic",
            "silver": 14000, "gold": 30, "mithril": 0,
            "stat_reward": 6000,
            "class_xp_reward": 300000,
            "soul_reward": 250000,
            "drops": {"soul_shard": 0.80, "cut_gem_diamond": 0.05},
            "quest_target": None,
        },
        "end_wild_primal_avatar": {
            "name": "Pierwotny Avatar Dziczy",
            "max_hp": 250000,
            "damage": 430,
            "damage_type": "physical",
            "silver": 35000, "gold": 75, "mithril": 1,
            "stat_reward": 12000,
            "class_xp_reward": 1500000,
            "soul_reward": 1000000,
            "drops": {"soul_elixir": 0.60, "cut_gem_soul_topaz": 0.12},
            "quest_target": None,
            "world_boss": True,
        },

        # Góry.
        "end_mountain_ice_colossus": {
            "name": "Lodowy Kolos Szczytu",
            "max_hp": 125000,
            "damage": 360,
            "damage_type": "physical",
            "silver": 18000, "gold": 40, "mithril": 0,
            "stat_reward": 7500,
            "class_xp_reward": 450000,
            "soul_reward": 350000,
            "drops": {"cobalt_ore": 0.25, "cut_gem_sapphire": 0.06},
            "quest_target": None,
        },
        "end_mountain_storm_elemental": {
            "name": "Żywiołak Wiecznej Burzy",
            "max_hp": 190000,
            "damage": 480,
            "damage_type": "magic",
            "silver": 24000, "gold": 55, "mithril": 0,
            "stat_reward": 9000,
            "class_xp_reward": 750000,
            "soul_reward": 600000,
            "drops": {"astral_ore": 0.14, "cut_gem_astral_crystal": 0.05},
            "quest_target": None,
        },
        "end_mountain_tempest_titan": {
            "name": "Tytan Wiecznej Burzy",
            "max_hp": 600000,
            "damage": 760,
            "damage_type": "magic",
            "silver": 65000, "gold": 150, "mithril": 1,
            "stat_reward": 18000,
            "class_xp_reward": 3000000,
            "soul_reward": 2000000,
            "drops": {"soul_elixir": 0.75, "cut_gem_astral_crystal": 0.14},
            "quest_target": None,
            "world_boss": True,
        },

        # Jaskinia Trolli.
        "end_troll_juggernaut": {
            "name": "Troll Juggernaut Głębin",
            "max_hp": 160000,
            "damage": 430,
            "damage_type": "physical",
            "silver": 22000, "gold": 50, "mithril": 0,
            "stat_reward": 8500,
            "class_xp_reward": 600000,
            "soul_reward": 450000,
            "drops": {"soul_shard": 0.85, "dragonsteel_ore": 0.12},
            "quest_target": None,
        },
        "end_troll_ancestral_shaman": {
            "name": "Pradawny Szaman Trolli",
            "max_hp": 230000,
            "damage": 540,
            "damage_type": "magic",
            "silver": 28000, "gold": 65, "mithril": 0,
            "stat_reward": 10500,
            "class_xp_reward": 1000000,
            "soul_reward": 800000,
            "drops": {"soul_elixir": 0.30, "cut_gem_dragon_garnet": 0.08},
            "quest_target": None,
        },
        "end_troll_first_warlord": {
            "name": "Pierwszy Wódz Trolli Grommar",
            "max_hp": 750000,
            "damage": 860,
            "damage_type": "physical",
            "silver": 85000, "gold": 190, "mithril": 2,
            "stat_reward": 22000,
            "class_xp_reward": 4000000,
            "soul_reward": 3000000,
            "drops": {"soul_elixir": 0.80, "cut_gem_dragon_garnet": 0.16},
            "quest_target": None,
            "world_boss": True,
        },

        # Bagna.
        "end_swamp_plague_colossus": {
            "name": "Kolos Zarazy",
            "max_hp": 210000,
            "damage": 500,
            "damage_type": "physical",
            "silver": 26000, "gold": 60, "mithril": 0,
            "stat_reward": 10000,
            "class_xp_reward": 800000,
            "soul_reward": 650000,
            "drops": {"void_lotus": 0.18, "cut_gem_amethyst": 0.07},
            "quest_target": None,
        },
        "end_swamp_rotten_oracle": {
            "name": "Wyrocznia Gnijących Głębin",
            "max_hp": 300000,
            "damage": 620,
            "damage_type": "magic",
            "silver": 34000, "gold": 80, "mithril": 0,
            "stat_reward": 12500,
            "class_xp_reward": 1200000,
            "soul_reward": 950000,
            "drops": {"void_lotus": 0.25, "cut_gem_void_onyx": 0.08},
            "quest_target": None,
        },
        "end_swamp_primordial_hydra": {
            "name": "Pierwotna Hydra Bagna",
            "max_hp": 1000000,
            "damage": 980,
            "damage_type": "physical",
            "silver": 110000, "gold": 250, "mithril": 2,
            "stat_reward": 27000,
            "class_xp_reward": 7000000,
            "soul_reward": 5000000,
            "drops": {"soul_elixir": 0.90, "cut_gem_void_onyx": 0.20},
            "quest_target": None,
            "world_boss": True,
        },

        # Pustynia — najwyższy poziom pakietu.
        "end_desert_glass_colossus": {
            "name": "Szklany Kolos Pustyni",
            "max_hp": 350000,
            "damage": 650,
            "damage_type": "physical",
            "silver": 40000, "gold": 95, "mithril": 0,
            "stat_reward": 13500,
            "class_xp_reward": 1400000,
            "soul_reward": 1000000,
            "drops": {"void_ore": 0.20, "cut_gem_void_onyx": 0.07},
            "quest_target": None,
        },
        "end_desert_solar_revenant": {
            "name": "Słoneczny Revenant",
            "max_hp": 475000,
            "damage": 780,
            "damage_type": "magic",
            "silver": 52000, "gold": 120, "mithril": 1,
            "stat_reward": 16000,
            "class_xp_reward": 2200000,
            "soul_reward": 1800000,
            "drops": {"eternium_ore": 0.06, "cut_gem_eternium_prism": 0.06},
            "quest_target": None,
        },
        "end_desert_eternal_sun": {
            "name": "Awatar Wiecznego Słońca",
            "max_hp": 1500000,
            "damage": 1200,
            "damage_type": "magic",
            "silver": 160000, "gold": 400, "mithril": 3,
            "stat_reward": 35000,
            "class_xp_reward": 10000000,
            "soul_reward": 8000000,
            "drops": {"soul_elixir": 1.0, "cut_gem_eternium_prism": 0.25},
            "quest_target": None,
            "world_boss": True,
        },
    }

    corpse_pool = [
        "iron_helmet", "iron_guard", "iron_gauntlets",
        "iron_leggings", "iron_boots", "forge_charm",
    ]
    for mob_id, template in mobs.items():
        template.setdefault("corpse_equipment_pool", corpse_pool)
        template.setdefault(
            "corpse_equipment_guaranteed",
            3 if template.get("world_boss") else 2,
        )
        template["high_end_mob"] = True
        MOB_TEMPLATES[mob_id] = template

    MOB_SPAWNS.extend([
        ("wild_ancient_path", "end_wild_ancient_mauler"),
        ("wild_ancient_path", "end_wild_spirit_behemoth"),
        ("wild_primal_hollow", "end_wild_primal_avatar"),

        ("mountain_tempest_path", "end_mountain_ice_colossus"),
        ("mountain_tempest_path", "end_mountain_storm_elemental"),
        ("mountain_tempest_sanctum", "end_mountain_tempest_titan"),

        ("troll_abyss", "end_troll_juggernaut"),
        ("troll_abyss", "end_troll_ancestral_shaman"),
        ("troll_abyss_throne", "end_troll_first_warlord"),

        ("swamp_rotten_depths", "end_swamp_plague_colossus"),
        ("swamp_rotten_depths", "end_swamp_rotten_oracle"),
        ("swamp_primordial_pool", "end_swamp_primordial_hydra"),

        ("desert_sun_tomb", "end_desert_glass_colossus"),
        ("desert_sun_tomb", "end_desert_solar_revenant"),
        ("desert_solar_sanctum", "end_desert_eternal_sun"),
    ])

    
    HELP_TOPICS["high_end_moby"] = [
        "High-End Mob Pack dodaje 15 bardzo trudnych elit i bossów.",
        "Nie istnieje XP postaci. Ogromne nagrody to Soul XP i Class Mastery XP.",
        "Elity dają od 100 tysięcy do 1,8 miliona Soul XP.",
        "Bossowie dają od 1 miliona do 8 milionów Soul XP.",
        "Class Mastery XP sięga od 150 tysięcy do 10 milionów.",
        "Przeciwnicy mają bardzo wysokie HP i obrażenia, więc nagrody nie są darmową farmą.",
        "Najtrudniejsze moby są w osobnych odnogach Dziczy, Gór, Jaskini Trolli, Bagien i Pustyni.",
        "Zwykłe ścieżki regionów pozostają przechodnie bez walki z tymi mobami.",
        "Użyj consider <mob>, żeby ocenić zagrożenie przed atakiem.",
        "Wysokie wyzwania mają sens po rozwinięciu statystyk, Soul, Class Mastery, EQ i socketów.",
        "Awatar Wiecznego Słońca jest najmocniejszym bossem tego pakietu: po globalnym skalowaniu ma 3 miliony HP.",
    ]


def configure_profession_tool_sellers():
    # v0.8.8: wszystkie narzędzia profesji są przypisane do postaci.
    for _bound_tool_id in CHARACTER_BOUND_TOOL_IDS:
        if _bound_tool_id in ITEMS:
            ITEMS[_bound_tool_id]["character_bound"] = True

    """
    Każde narzędzie jest sprzedawane tylko przez NPC dokładnie
    związany z daną profesją. Narzędzia są usuwane ze wszystkich
    innych sklepów przed przypisaniem docelowych sprzedawców.
    """

    # Osobna kuchnia dla Kucharza Marcela, żeby Karczmarz
    # nie sprzedawał narzędzia profesji Gotowanie.
    ROOMS["inn"]["exits"]["east"] = "blue_flame_kitchen"
    ROOMS["blue_flame_kitchen"] = {
        "zone": "Miasto Dusz",
        "name": "Kuchnia Błękitnego Płomienia",
        "desc": (
            "Gorąca kuchnia pełna garnków, pieców i stołów roboczych. "
            "Kucharz Marcel prowadzi tutaj Gotowanie i jako jedyny "
            "sprzedaje Nóż Kucharski."
        ),
        "exits": {"west": "inn"},
    }
    NPCS["specialist_cooking"]["room"] = "blue_flame_kitchen"

    profession_tools = {
        "fishing_rod": ("fish_market", "fisher_tomas"),
        "pickaxe": ("cave_entrance", "miner_toren"),
        "saw": ("forester_lodge", "specialist_woodcutting"),
        "crafting_hammer": (
            "crafting_workshop",
            "specialist_crafting",
        ),
        "chef_knife": (
            "blue_flame_kitchen",
            "specialist_cooking",
        ),
        "herbalist_sickle": (
            "herbalism_garden",
            "specialist_herbalism",
        ),
        "alchemy_mortar": (
            "alchemy_lab",
            "specialist_alchemy",
        ),
        "jeweler_pliers": (
            "jeweler_workshop",
            "jeweler_mirella",
        ),
    }

    tool_ids = set(profession_tools)

    # Usuń wszystkie narzędzia z dotychczasowych sklepów.
    for room_id in list(SHOPS):
        SHOPS[room_id] = [
            item_id
            for item_id in SHOPS[room_id]
            if item_id not in tool_ids
        ]
        if not SHOPS[room_id]:
            SHOPS.pop(room_id, None)

    # Dodaj każde narzędzie dokładnie raz.
    for item_id, (room_id, seller_id) in profession_tools.items():
        SHOPS.setdefault(room_id, [])
        if item_id not in SHOPS[room_id]:
            SHOPS[room_id].append(item_id)
        SHOP_SELLERS[room_id] = seller_id
        TOOL_SHOP_ROOMS[item_id] = room_id

        npc = NPCS.get(seller_id)
        if npc is not None:
            npc["shopkeeper"] = True

    # Stare sklepy zachowują sprzedawcę tylko dla swoich innych towarów.
    SHOP_SELLERS["inn"] = "innkeeper"
    SHOP_SELLERS["forge"] = "doran"

    # Przejrzyste opisy NPC.
    NPCS["fisher_tomas"]["shopkeeper"] = True
    NPCS["fisher_tomas"]["dialogue"] = (
        "Jeśli chcesz zacząć Wędkarstwo, kupisz u mnie podstawową Wędkę. "
        "Przynieś mi także trzydzieści dowolnych ryb, a wynagrodzę twoją pracę. "
        "Wpisz list albo shop, aby zobaczyć ofertę."
    )
    NPCS["specialist_fishing"]["dialogue"] = (
        "Jestem Mistrzem Wędkarstwa Neris. Uczę rozwoju Wędki, Tierów "
        "i łowisk wysokiego levelu. Podstawową Wędkę kupisz u Rybaka Borysa na Targu Rybnym."
    )
    NPCS["miner_toren"]["dialogue"] = (
        "Dobra ruda nie wydobędzie się sama. "
        "Tylko u mnie kupisz Kilof do Górnictwa. "
        "Wpisz list albo shop, aby zobaczyć ofertę."
    )
    NPCS["specialist_woodcutting"]["dialogue"] = (
        "Jestem Mistrzem Drwalstwa. Tylko u mnie kupisz Piłę. "
        "Uczę pracy z drewnem od levelu 1 do 400."
    )
    NPCS["specialist_crafting"]["dialogue"] = (
        "Prowadzę Rzemiosło i Kowalstwo. "
        "Tylko u mnie kupisz Młot Rzemieślniczy."
    )
    NPCS["specialist_cooking"]["dialogue"] = (
        "Jestem Kucharzem Błękitnego Płomienia. "
        "Tylko u mnie kupisz Nóż Kucharski i uczysz się Gotowania."
    )
    NPCS["specialist_herbalism"]["dialogue"] = (
        "Jestem Mistrzynią Zielarstwa. "
        "Tylko u mnie kupisz Sierp Zielarski."
    )
    NPCS["specialist_alchemy"]["dialogue"] = (
        "Jestem Mistrzem Alchemii. "
        "Tylko u mnie kupisz Moździerz Alchemiczny."
    )
    NPCS["jeweler_mirella"]["dialogue"] = (
        "Prowadzę Jubilerstwo od levelu 1 do 400. "
        "Tylko u mnie kupisz Szczypce Jubilerskie."
    )

    
    HELP_TOPICS["sprzedawcy_narzedzi"] = [
        "Każde narzędzie kupisz tylko u NPC dokładnie związanego z jego profesją.",
        "Wędka: Rybak Borys na Targu Rybnym.",
        "Kilof: Górnik Toren przy Wejściu do Kryształowej Jaskini.",
        "Piła: Mistrz Drwalstwa Oren w Leśniczówce.",
        "Młot Rzemieślniczy: Mistrz Rzemiosła Haldor w Warsztacie Rzemieślniczym.",
        "Nóż Kucharski: Kucharz Marcel w Kuchni Błękitnego Płomienia.",
        "Sierp Zielarski: Mistrzyni Zielarstwa Sena w Ogrodzie Zielarskim.",
        "Moździerz Alchemiczny: Mistrz Alchemii Orin w Laboratorium Alchemicznym.",
        "Szczypce Jubilerskie: Jubilerka Mirella w Pracowni Jubilerskiej.",
        "Żaden z tych przedmiotów nie jest sprzedawany w zwykłym sklepie innej profesji.",
    ]

def configure_v0800_help_info():
    HELP_TOPICS["informacje"] = [
        "W v0.8.0 najważniejsze komendy informacyjne mają dwa poziomy szczegółowości.",
        "Bez dopisku info dostajesz szybki stan, wygodny pod NVDA.",
        "Z dopiskiem info dostajesz pełny opis mechaniki, progów i dalszego celu.",
        "dusza - szybki stan Broni Duszy.",
        "dusza info - pełne Soul XP, Tiery, Próby Broni Duszy, progi i następny cel.",
        "staty - szybkie statystyki bojowe.",
        "staty info - statystyki bazowe, bonusy EQ, pasywy, sety i sposób rozwoju.",
        "profesje - szybkie levele i rangi profesji.",
        "profesje info - XP, akcje, następne rangi oraz narzędzia i sprzedawcy.",
        "narzedzia - szybki stan narzędzi.",
        "narzedzia info - XP, Tier, bonus, czas akcji i właściwy sprzedawca.",
        "eq - szybka lista założonego wyposażenia.",
        "eq info - pełne bonusy, obrona, sety, sockety i efektywne statystyki.",
        "kodeksklasowy <klasa> - skille, wymagana Biegłość, nauczyciel, cena i status odblokowania.",
        "help informacje - ten przewodnik.",
    ]
    HELP_TOPIC_ALIASES.update({
        "info": "informacje",
        "informacja": "informacje",
        "informacje": "informacje",
        "komendy info": "informacje",
    })

def configure_v081_help_info():
    HELP_TOPICS["sety_klasowe"] = [
        "Każda z 12 klas ma pełny zestaw 8 części: głowa, korpus, dłonie, nogi, stopy, talizman, pierścień i naszyjnik.",
        "Klasowe EQ ma Tiery Biegłości 1, 10, 20, 30 i dalej co 10 aż do 400; każdy próg daje mocniejszy pełny zestaw.",
        "Każda część klasowego EQ ma dwie podstawowe statystyki archetypu: klasy fizyczne dostają Siłę i Kondycję, a klasy magiczne Inteligencję i Siłę Woli.",
        "W klasach magicznych Inteligencja jest statystyką odpowiadającą mocy/mądrości magicznej; gra nie tworzy osobnej siódmej statystyki Mądrość.",
        "Sklep klasowy pokazuje najlepszy Tier odblokowany przez Biegłość danej klasy; wyższy Tier wymaga tej Biegłości także przy zakładaniu.",
        "Próg 2 części daje klasowy bonus do statystyk.",
        "Próg 4 części zwiększa wszystkie obrażenia.",
        "Próg 6 części zwiększa obronę fizyczną i magiczną.",
        "Próg 8 części zwiększa maksymalne HP, a klasom magicznym także Manę.",
        "Wartości są różne dla każdej klasy, np. Berserker i Czarownik mają bardziej ofensywne sety, a Strażnik bardziej defensywny.",
        "Bonus liczy się tylko dla aktywnej klasy.",
        "Komenda sety pokazuje aktywne sety.",
        "Komenda sety info pokazuje wszystkie 12 zestawów i progi 2/4/6/8.",
        "Komenda sety <klasa> pokazuje konkretny zestaw.",
        "eq info i staty info pokazują aktywne bonusy setów klasowych.",
    ]
    HELP_TOPICS["teren_info"] = [
        "teren info <nazwa> pokazuje zbiorcze informacje o regionie.",
        "Przykład: teren info bagna, teren info góry, teren info pustynia.",
        "Informacje obejmują liczbę lokacji, orientacyjny zakres Soul, trudność, NPC, questy, bossów, przeciwników, profesje i dojście.",
        "Dane są zbierane z faktycznego świata gry, NPC, spawnów i expowisk.",
        "expowiska <nazwa> nadal służy do szczegółów expienia.",
        "mapa nadal pokazuje strukturę lokacji.",
        "prowadz <teren> prowadzi do wybranego regionu.",
    ]
    HELP_TOPIC_ALIASES.update({
        "sety": "sety_klasowe",
        "sety klasowe": "sety_klasowe",
        "set klasowy": "sety_klasowe",
        "class sets": "sety_klasowe",
        "teren": "teren_info",
        "teren info": "teren_info",
        "region": "teren_info",
        "region info": "teren_info",
    })
    HELP_TOPICS["informacje"].extend([
        "sety / sety info - aktywne i pełne bonusy zestawów klasowych 2/4/6/8.",
        "teren info <nazwa> - region, Soul, NPC, questy, bossowie, profesje i dojście.",
    ])

    # Uaktualnienie starszych opisów po rozwoju profesji i narzędzi.
    if "profesje" in HELP_TOPICS:
        HELP_TOPICS["profesje"].append(
            "Aktualne profesje 1-400: Wędkarstwo, Górnictwo, Drwalstwo, Zielarstwo, Gotowanie, Alchemia, Kowalstwo i Jubilerstwo. Każda ma własny poziom; odpowiadające narzędzie rozwija się osobno."
        )
    if "ekwipunek" in HELP_TOPICS:
        HELP_TOPICS["ekwipunek"].append(
            "Wyposażenie klasowe ma teraz aktywne progi zestawu 2/4/6/8. Użyj sety info."
        )

def build_paid_training_guild_expansion():
    """v0.8.9: płatna nauka i 12 osobnych sal klasowych."""

    class_rooms = {
        "teacher_warrior": (
            "guild_warrior_chamber", "Sala Wojownika",
            "guild_martial_hall",
            "Sala tarcz, mieczy i ciężkich manekinów. Mistrz Garran szkoli tu wyłącznie Wojowników.",
        ),
        "teacher_berserker": (
            "guild_berserker_chamber", "Sala Berserkera",
            "guild_martial_hall",
            "Wzmocnione ściany i ciężkie cele pozwalają ćwiczyć furię bez narażania całej Gildii.",
        ),
        "teacher_monk": (
            "guild_monk_chamber", "Sala Mnicha",
            "guild_body_hall",
            "Cicha sala oddechu, równowagi i walki wręcz. Mistrz Shen prowadzi tu trening Mnichów.",
        ),
        "teacher_guardian": (
            "guild_guardian_chamber", "Bastion Strażnika",
            "guild_body_hall",
            "Ciężkie tarcze i stanowiska obronne tworzą salę przeznaczoną wyłącznie dla tanków Strażników.",
        ),
        "teacher_rogue": (
            "guild_rogue_chamber", "Sala Łotrzyka",
            "guild_shadow_gallery",
            "Wąskie przejścia, zamki i cele precyzyjne służą treningowi Łotrzyków.",
        ),
        "teacher_hunter": (
            "guild_hunter_chamber", "Sala Łowcy",
            "guild_shadow_gallery",
            "Długi tor strzelecki i ruchome cele pozwalają Łowcom trenować bez przeszkadzania Łotrzykom.",
        ),
        "teacher_mage": (
            "guild_mage_chamber", "Komnata Maga",
            "guild_arcane_chamber",
            "Runy izolują energię Arkanów. Arcymag Vaelis szkoli tu tylko Magów.",
        ),
        "teacher_psion": (
            "guild_psion_chamber", "Komnata Psionika",
            "guild_arcane_chamber",
            "Wyciszona komnata skupienia chroni innych przed niekontrolowaną energią umysłu.",
        ),
        "teacher_necromancer": (
            "guild_necromancer_chamber", "Komnata Nekromanty",
            "guild_dark_chamber",
            "Pieczęcie ochronne otaczają salę pracy z energią śmierci. Morwen szkoli tu Nekromantów.",
        ),
        "teacher_warlock": (
            "guild_warlock_chamber", "Komnata Czarownika",
            "guild_dark_chamber",
            "Osobna sala Otchłani pozwala Czarownikom trenować bez zakłócania nauki Nekromantów.",
        ),
        "teacher_priest": (
            "guild_priest_chamber", "Kaplica Kapłana",
            "guild_sanctuary",
            "Jasna kaplica leczenia i ochrony. Mistrz Aureon prowadzi tu naukę Kapłanów.",
        ),
        "teacher_druid": (
            "guild_druid_chamber", "Gaj Druida",
            "guild_sanctuary",
            "Żywe rośliny i kamienny krąg tworzą osobny gaj treningowy dla Druidów.",
        ),
    }

    # Każda dotychczasowa sala pary staje się hubem z dwoma wyjściami.
    room_links = {
        "guild_martial_hall": (
            ("north", "guild_warrior_chamber"),
            ("west", "guild_berserker_chamber"),
        ),
        "guild_body_hall": (
            ("north", "guild_monk_chamber"),
            ("east", "guild_guardian_chamber"),
        ),
        "guild_shadow_gallery": (
            ("north", "guild_rogue_chamber"),
            ("east", "guild_hunter_chamber"),
        ),
        "guild_arcane_chamber": (
            ("north", "guild_mage_chamber"),
            ("south", "guild_psion_chamber"),
        ),
        "guild_dark_chamber": (
            ("north", "guild_necromancer_chamber"),
            ("east", "guild_warlock_chamber"),
        ),
        "guild_sanctuary": (
            ("south", "guild_priest_chamber"),
            ("west", "guild_druid_chamber"),
        ),
    }
    for hub, links in room_links.items():
        for direction, target in links:
            ROOMS[hub]["exits"][direction] = target

    # Return direction is deliberately simple for screen-reader navigation.
    return_direction = {
        "guild_martial_hall": "south",
        "guild_body_hall": "west",
        "guild_shadow_gallery": "down",
        "guild_arcane_chamber": "west",
        "guild_dark_chamber": "west",
        "guild_sanctuary": "up",
    }

    for teacher_id, (room_id, room_name, hub, desc) in class_rooms.items():
        ROOMS[room_id] = {
            "zone": "Gildia Dusz",
            "name": room_name,
            "desc": desc,
            "exits": {return_direction[hub]: hub},
        }
        NPCS[teacher_id]["room"] = room_id
        NPCS[teacher_id]["dialogue"] += (
            " Nauka umiejętności jest płatna. Cena rośnie wraz z wymaganą Biegłością klasy skilla."
        )

    
    HELP_TOPICS["nauka"] = [
        "Nauka umiejętności klasowych u nauczycieli Gildii Dusz jest płatna.",
        "Cena zależy od Biegłości klasy wymaganej przez konkretną umiejętność.",
        "Skille kosztują wspólną walutę; późniejsze skille kosztują coraz więcej.",
        "Nauczyciel zawsze podaje cenę przed nauką.",
        "Komendy: learn <numer>, learn <skill>, naucz <numer>, naucz <umiejętność>.",
        "Pieniądze są pobierane dopiero po sprawdzeniu aktywnej klasy, wymaganej Biegłości i tego, czy skill nie jest już znany.",
        "Każda z 12 klas ma teraz własną salę i własnego nauczyciela.",
        "Wpisz teachers albo nauczyciele, aby usłyszeć dokładne lokacje.",
    ]


# ============================================================
# v0.8.19 - Forest, Wolves & Quest Balance Expansion
# ============================================================
def build_forest_wolves_and_quest_balance():
    """Rozbudowuje Las Szeptów i poprawia trzy istniejące questy."""
    global EXP_AREAS

    # --------------------------------------------------------
    # Las Szeptów: osobne, większe expowisko po Głębi Gaju.
    # --------------------------------------------------------
    ROOMS["deep_grove"]["exits"]["west"] = "forest_edge"
    ROOMS.update({
        "forest_edge": {
            "zone": "Las Szeptów", "name": "Skraj Lasu Szeptów",
            "desc": (
                "Drzewa rosną tu znacznie gęściej niż w Gaju Szeptów. "
                "Między korzeniami widać liczne ślady wilczych łap."
            ),
            "exits": {"east": "deep_grove", "west": "forest_birch_path", "north": "forest_wolf_trail"},
        },
        "forest_birch_path": {
            "zone": "Las Szeptów", "name": "Brzozowy Trakt",
            "desc": "Wąski trakt przecina jasny zagajnik. Wycie odbija się między białymi pniami.",
            "exits": {"east": "forest_edge", "west": "forest_stream", "north": "forest_old_oaks"},
        },
        "forest_wolf_trail": {
            "zone": "Las Szeptów", "name": "Wilczy Trakt",
            "desc": "Ziemię pokrywają świeże tropy całej watahy. Szlak prowadzi ku ciemniejszej części lasu.",
            "exits": {"south": "forest_edge", "north": "forest_moon_glade", "west": "forest_old_oaks"},
        },
        "forest_old_oaks": {
            "zone": "Las Szeptów", "name": "Krąg Starych Dębów",
            "desc": "Pradawne dęby tworzą naturalny krąg. Między korzeniami leżą kości zwierzyny.",
            "exits": {"south": "forest_birch_path", "east": "forest_wolf_trail", "north": "forest_fallen_tree"},
        },
        "forest_stream": {
            "zone": "Las Szeptów", "name": "Cichy Strumień",
            "desc": "Zimna woda płynie pod korzeniami. Na błotnistym brzegu odciśnięte są wilcze łapy.",
            "exits": {"east": "forest_birch_path", "north": "forest_moss_hollow"},
        },
        "forest_moss_hollow": {
            "zone": "Las Szeptów", "name": "Omszała Kotlina",
            "desc": "Miękki mech tłumi kroki. Niskie warczenie dochodzi z kilku kierunków jednocześnie.",
            "exits": {"south": "forest_stream", "east": "forest_fallen_tree", "north": "forest_wolf_den"},
        },
        "forest_fallen_tree": {
            "zone": "Las Szeptów", "name": "Powalony Olbrzym",
            "desc": "Ogromny przewrócony pień dzieli las na dwie ścieżki. Pod korzeniami kryją się drapieżniki.",
            "exits": {"south": "forest_old_oaks", "west": "forest_moss_hollow", "east": "forest_moon_glade"},
        },
        "forest_moon_glade": {
            "zone": "Las Szeptów", "name": "Księżycowa Polana",
            "desc": "Nawet w dzień polanę spowija srebrzysta poświata. Watahy zbierają się tutaj przed polowaniem.",
            "exits": {"south": "forest_wolf_trail", "west": "forest_fallen_tree", "north": "forest_alpha_hollow"},
        },
        "forest_wolf_den": {
            "zone": "Las Szeptów", "name": "Wilcza Nora",
            "desc": "Między głazami znajduje się rozległa nora pełna sierści, kości i świeżych tropów.",
            "exits": {"south": "forest_moss_hollow", "east": "forest_alpha_hollow"},
        },
        "forest_alpha_hollow": {
            "zone": "Las Szeptów", "name": "Kotlina Wilczej Watahy",
            "desc": "Najgłębsza część lasu. Dziesiątki śladów zbiegają się przy kamiennym wyniesieniu przywódcy watahy.",
            "exits": {"south": "forest_moon_glade", "west": "forest_wolf_den"},
        },
    })

    # --------------------------------------------------------
    # Nowe odmiany wilków. Wszystkie zaliczają quest Cienie w gaju.
    # --------------------------------------------------------
    MOB_TEMPLATES["shadow_wolf_stalker"] = {
        "name": "Tropiciel Cienia", "max_hp": 95, "damage": 11, "damage_type": "physical",
        "silver": 34, "gold": 0, "mithril": 0,
        "stat_reward": 36, "soul_reward": 175,
        "drops": {"wolf_fang": 0.55, "healing_potion": 0.05},
        "quest_target": "shadow_wolf",
    }
    MOB_TEMPLATES["shadow_wolf_howler"] = {
        "name": "Wyjący Wilk Cienia", "max_hp": 125, "damage": 14, "damage_type": "physical",
        "silver": 46, "gold": 0, "mithril": 0,
        "stat_reward": 44, "soul_reward": 220,
        "drops": {"wolf_fang": 0.65, "mana_potion": 0.04},
        "quest_target": "shadow_wolf",
    }
    MOB_TEMPLATES["shadow_wolf_pack_leader"] = {
        "name": "Przywódca Watahy Cienia", "max_hp": 320, "damage": 22, "damage_type": "physical",
        "silver": 150, "gold": 1, "mithril": 0,
        "stat_reward": 120, "class_xp_reward": 1000, "soul_reward": 700,
        "drops": {"wolf_fang": 1.0, "soul_shard": 0.35, "soul_elixir": 0.08},
        "quest_target": "shadow_wolf",
        "mini_boss": True, "respawn_seconds": 180,
        "boss_mechanic_text": (
            "Mini-boss wilczej watahy. Jest znacznie mocniejszy od zwykłych Wilków Cienia."
        ),
    }
    MOB_DESCRIPTIONS.update({
        "shadow_wolf_stalker": "Szybszy Wilk Cienia, który poluje na skraju watahy.",
        "shadow_wolf_howler": "Silniejszy Wilk Cienia. Jego wycie przyciąga uwagę całej watahy.",
        "shadow_wolf_pack_leader": "Największy wilk Lasu Szeptów i przywódca miejscowej watahy.",
    })

    # W lesie ma być wyraźnie więcej wilków niż w starym Gaju Szeptów.
    forest_spawns = (
        ("forest_edge", "shadow_wolf"), ("forest_edge", "shadow_wolf"),
        ("forest_birch_path", "shadow_wolf"), ("forest_birch_path", "shadow_wolf_stalker"),
        ("forest_wolf_trail", "shadow_wolf"), ("forest_wolf_trail", "shadow_wolf"),
        ("forest_wolf_trail", "shadow_wolf_stalker"),
        ("forest_old_oaks", "shadow_wolf_stalker"), ("forest_old_oaks", "shadow_wolf_howler"),
        ("forest_stream", "shadow_wolf"), ("forest_stream", "shadow_wolf"),
        ("forest_moss_hollow", "shadow_wolf"), ("forest_moss_hollow", "shadow_wolf_stalker"),
        ("forest_fallen_tree", "shadow_wolf_stalker"), ("forest_fallen_tree", "shadow_wolf_howler"),
        ("forest_moon_glade", "shadow_wolf"), ("forest_moon_glade", "shadow_wolf_stalker"),
        ("forest_moon_glade", "shadow_wolf_howler"),
        ("forest_wolf_den", "shadow_wolf"), ("forest_wolf_den", "shadow_wolf"),
        ("forest_wolf_den", "shadow_wolf_stalker"), ("forest_wolf_den", "shadow_wolf_howler"),
        ("forest_alpha_hollow", "shadow_wolf"), ("forest_alpha_hollow", "shadow_wolf_stalker"),
        ("forest_alpha_hollow", "shadow_wolf_pack_leader"),
    )
    MOB_SPAWNS.extend(forest_spawns)

    GUIDE_DESTINATION_ALIASES.update({
        "las": "forest_edge",
        "las szeptow": "forest_edge",
        "las szeptów": "forest_edge",
        "forest": "forest_edge",
        "whisper forest": "forest_edge",
        "wilczy trakt": "forest_edge",
        "wilcza nora": "forest_edge",
        "wataha wilkow": "forest_edge",
        "wataha wilków": "forest_edge",
    })

    EXP_AREAS = EXP_AREAS + ({
        "id": "whisper_forest",
        "name": "Las Szeptów",
        "aliases": (
            "las", "las szeptow", "las szeptów", "wilki", "wilcza nora",
            "forest", "whisper forest",
        ),
        "soul_min": 10,
        "soul_max": 45,
        "difficulty": "łatwa do średniej",
        "guide": "las szeptow",
        "enemies": (
            "Wilki Cienia, Tropiciele Cienia, Wyjące Wilki Cienia, "
            "elitarne i rare warianty oraz Przywódca Watahy Cienia"
        ),
        "description": (
            "Duży leśny obszar za Głębią Gaju. Dziesięć nowych miejsc tworzy "
            "sieć ścieżek, polan i wilczych nor z gęstymi watahami."
        ),
        "note": (
            "Prowadzenie zatrzymuje na Skraju Lasu Szeptów. Wnętrze trzeba odkryć samodzielnie."
        ),
    },)

    # --------------------------------------------------------
    # Quest goblinów: 20 zabitych i powtarzalny co godzinę.
    # --------------------------------------------------------
    if "goblin_problem" in QUESTS:
        QUESTS["goblin_problem"]["needed"] = 20
        QUESTS["goblin_problem"]["repeatable"] = True
        QUESTS["goblin_problem"]["repeat_cooldown"] = QUEST_REPEAT_COOLDOWN_SECONDS
        QUESTS["goblin_problem"]["description"] = (
            "Pokonaj 20 goblinów w ruinach, obozie i Jaskiniach Goblinów. "
            "Po ukończeniu zadanie można ponownie przyjąć po 60 minutach."
        )
        if "captain_arven" in NPCS:
            NPCS["captain_arven"]["dialogue"] = (
                "Gobliny zajęły starą strażnicę i wciąż wracają. "
                "Zabij 20 goblinów. To zlecenie mogę wystawić ponownie co godzinę."
            )

    # --------------------------------------------------------
    # Cienie w Gaju: powtarzalne co godzinę.
    # --------------------------------------------------------
    if "shadow_wolves" in QUESTS:
        QUESTS["shadow_wolves"]["repeatable"] = True
        QUESTS["shadow_wolves"]["repeat_cooldown"] = QUEST_REPEAT_COOLDOWN_SECONDS
        QUESTS["shadow_wolves"]["description"] = (
            "Pokonaj 2 Wilki Cienia w Gaju Szeptów lub Lesie Szeptów. "
            "Po ukończeniu zadanie można ponownie przyjąć po 60 minutach."
        )
        if "mira" in NPCS:
            NPCS["mira"]["dialogue"] = (
                "Wilki Cienia zakłócają równowagę gaju. Ich obecność jest coraz silniejsza. "
                "Zlecenie Cienie w Gaju mogę ponownie wystawić co godzinę."
            )

    # --------------------------------------------------------
    # Główny quest trolli: powtarzalny co godzinę.
    # --------------------------------------------------------
    if "mountain_troll_hunt" in QUESTS:
        QUESTS["mountain_troll_hunt"]["repeatable"] = True
        QUESTS["mountain_troll_hunt"]["repeat_cooldown"] = QUEST_REPEAT_COOLDOWN_SECONDS
        QUESTS["mountain_troll_hunt"]["description"] = (
            "Pokonaj 12 trolli w Jaskini Trolli i wróć do Strażnika Górskiego Eryka "
            "w Wiosce Górskiej. Po ukończeniu zadanie można ponownie przyjąć po 60 minutach."
        )
        if "mountain_guard_eryk" in NPCS:
            NPCS["mountain_guard_eryk"]["dialogue"] = (
                "Trolle z południowej jaskini coraz częściej schodzą pod samą wioskę. "
                "Potrzebujemy kogoś, kto przerzedzi ich szeregi. "
                "Zlecenie Plaga Trolli mogę wystawić ponownie co godzinę."
            )


REGIONAL_SET_BONUSES = {
    "cultist": {"name":"Set Kultystów Pustki", "hp":1.08, "damage":1.18, "defense":1.12},
    "necropolis": {"name":"Set Umarłego Króla", "hp":1.12, "damage":1.14, "defense":1.18},
    "ice_caves": {"name":"Set Wiecznego Lodu", "hp":1.10, "damage":1.16, "defense":1.16},
}

TREASURE_CHEST_RARITIES = {
    "common": ("Zwykła", 62),
    "rare": ("Rzadka", 25),
    "epic": ("Epicka", 10),
    "legendary": ("Legendarna", 3),
}
TREASURE_CHESTS = {}


def build_elite_rare_named_loot_expansion():
    # --------------------------------------------------------
    # Regional sets: 3 x 6 pieces, thresholds 2/4/6.
    # --------------------------------------------------------
    slots = (
        ("head","Hełm"),("body","Pancerz"),("hands","Rękawice"),
        ("legs","Nogawice"),("feet","Buty"),("charm","Talizman"),
    )
    set_specs = {
        "cultist": ("Kultysty Pustki", 8, "intelligence", 4),
        "necropolis": ("Umarłego Króla", 10, "willpower", 5),
        "ice_caves": ("Wiecznego Lodu", 11, "constitution", 5),
    }
    regional_items = {}
    for set_id, (label, defense_base, affix, amount) in set_specs.items():
        ids=[]
        for idx,(slot,slot_name) in enumerate(slots):
            item_id=f"regional_{set_id}_{slot}"
            defense=max(1, defense_base + idx//2)
            ITEMS[item_id]={
                "name":f"{slot_name} {label}", "type":"armor", "slot":slot,
                "defense":defense, "price":None, "rarity":"epic", "rarity_name":"Epicki",
                "affix":affix, "affix_amount":amount,
                "regional_set":set_id,
                "desc":(
                    f"Część regionalnego zestawu {REGIONAL_SET_BONUSES[set_id]['name']}. "
                    f"Obrona +{defense}. Bonus statystyki +{amount}. "
                    "Progi: 2 części HP/Mana, 4 części obrażenia, 6 części obrona."
                ),
            }
            ids.append(item_id)
        regional_items[set_id]=ids

    # --------------------------------------------------------
    # Named boss loot.
    # --------------------------------------------------------
    named = {
        "cemetery_keeper_lantern": {"name":"Latarnia Strażnika Cmentarza","type":"armor","slot":"charm","defense":7,"price":None,"rarity":"legendary","rarity_name":"Legendarny","affix":"willpower","affix_amount":5,"desc":"Unikalna latarnia Strażnika Cmentarza. Obrona +7, Siła Woli +5."},
        "void_archon_ring": {"name":"Pierścień Arcykultysty Otchłani","type":"armor","slot":"ring","defense":6,"price":None,"rarity":"legendary","rarity_name":"Legendarny","affix":"intelligence","affix_amount":6,"sockets":2,"desc":"Unikalny pierścień Arcykultysty. Obrona +6, Inteligencja +6, 2 gniazda."},
        "primal_alpha_necklace": {"name":"Naszyjnik Pradawnego Alfa","type":"armor","slot":"necklace","defense":7,"price":None,"rarity":"legendary","rarity_name":"Legendarny","affix":"strength","affix_amount":6,"sockets":2,"desc":"Kły Pradawnego Alfa oprawione w naszyjnik. Obrona +7, Siła +6, 2 gniazda."},
        "dead_king_seal": {"name":"Pieczęć Umarłego Króla","type":"armor","slot":"ring","defense":9,"price":None,"rarity":"legendary","rarity_name":"Legendarny","affix":"willpower","affix_amount":7,"sockets":3,"desc":"Pierścień Umarłego Króla Nekropolii. Obrona +9, Siła Woli +7, 3 gniazda."},
        "cistern_king_chain": {"name":"Łańcuch Króla Cysterny","type":"armor","slot":"necklace","defense":6,"price":None,"rarity":"legendary","rarity_name":"Legendarny","affix":"constitution","affix_amount":5,"sockets":2,"desc":"Ciężki łańcuch Króla Podmiejskich Kanałów. Obrona +6, Kondycja +5, 2 gniazda."},
        "eternal_ice_heart": {"name":"Serce Wiecznego Lodu","type":"armor","slot":"charm","defense":11,"price":None,"rarity":"legendary","rarity_name":"Legendarny","affix":"intelligence","affix_amount":8,"desc":"Zamarznięte serce Pradawnego Lodowego Smoka. Obrona +11, Inteligencja +8."},
    }
    ITEMS.update(named)
    for _named_item_id in named:
        ITEMS[_named_item_id]["named_loot"] = True
    boss_named = {
        "cemetery_keeper": ("cemetery_keeper_lantern",0.45),
        "cult_archon": ("void_archon_ring",0.45),
        "beast_ancient_alpha": ("primal_alpha_necklace",0.45),
        "necro_dead_king": ("dead_king_seal",0.45),
        "sewer_king": ("cistern_king_chain",0.45),
        "ice_dragon": ("eternal_ice_heart",0.45),
    }
    for boss_id,(item_id,chance) in boss_named.items():
        if boss_id in MOB_TEMPLATES:
            MOB_TEMPLATES[boss_id].setdefault("drops",{})[item_id]=chance

    # Main regional bosses also yield regional set pieces through corpse loot.
    for boss_id,set_id in (("cult_archon","cultist"),("necro_dead_king","necropolis"),("ice_dragon","ice_caves")):
        t=MOB_TEMPLATES.get(boss_id)
        if t:
            t["corpse_equipment_pool"]=list(regional_items[set_id])
            t["corpse_equipment_guaranteed"]=2

    # --------------------------------------------------------
    # Mini bosses: two in each of 8 exploration areas.
    # --------------------------------------------------------
    mini_specs = [
        ("cemetery_crypt_reaper","Żniwiarz Starej Krypty","cemetery_fallen_chapel",700,46,"magic",2200,1500,None),
        ("cemetery_mourning_knight","Rycerz Martwego Dzwonu","cemetery_bell_tower",900,55,"physical",2800,1900,None),
        ("cult_void_executioner","Egzekutor Pustki","cult_ruins_ritual_hall",1200,70,"physical",3800,2600,"cultist"),
        ("cult_black_oracle","Czarna Wyrocznia","cult_ruins_library",1050,76,"magic",4000,2800,"cultist"),
        ("beast_cave_matriarch","Matriarcha Jaskiniowych Bestii","beast_lair_bone_nest",1400,78,"physical",4300,3000,None),
        ("beast_ironhorn_champion","Żelaznorogi Czempion","beast_lair_hunting_ground",1650,84,"physical",4700,3300,None),
        ("necro_ossuary_champion","Czempion Ossuarium","necropolis_catacombs",2100,92,"physical",6000,4400,"necropolis"),
        ("necro_death_bishop","Biskup Śmierci","necropolis_royal_tombs",1950,98,"magic",6400,4700,"necropolis"),
        ("sewer_plague_broodmother","Matka Zarazy","sewer_rat_nest",850,48,"physical",2500,1700,None),
        ("sewer_smuggler_boss","Mistrz Przemytników","sewer_smuggler_den",1100,58,"physical",3100,2200,None),
        ("ice_crystal_behemoth","Kryształowy Behemot","ice_cave_crystal_chamber",2400,104,"physical",7200,5200,"ice_caves"),
        ("ice_frost_lich","Licz Wiecznego Szronu","ice_cave_ancient_hall",2200,110,"magic",7600,5600,"ice_caves"),
        ("bandit_quartermaster","Kwatermistrz Bandytów","bandit_loot_depot",520,34,"physical",1900,900,None),
        ("bandit_duelist","Bandycki Mistrz Pojedynku","bandit_arena",640,39,"physical",2300,1100,None),
        ("goblin_mushroom_beast","Goblińska Bestia Grzybowa","goblin_fungus_gallery",500,31,"physical",1700,800,None),
        ("goblin_bombmaster","Mistrz Goblińskich Bombiarzy","goblin_bomb_workshop",620,42,"magic",2400,1200,None),
    ]
    for mob_id,name,room,hp,damage,dtype,classxp,soul,set_id in mini_specs:
        t={
            "name":name,"max_hp":hp,"damage":damage,"damage_type":dtype,
            "silver":max(90,hp//5),"gold":max(1,hp//900),"mithril":0,
            "stat_reward":max(100,hp//8),"class_xp_reward":classxp,"soul_reward":soul,
            "drops":{"soul_shard":0.55,"soul_elixir":0.12},"quest_target":None,
            "mini_boss":True,"respawn_seconds":180,
            "boss_mechanic_text":"Mini-boss. Jest wyraźnie mocniejszy od zwykłych przeciwników w tym expowisku.",
            "corpse_equipment_pool":[],"corpse_equipment_guaranteed":0,
        }
        if set_id:
            t["corpse_equipment_pool"]=list(regional_items[set_id])
            t["corpse_equipment_guaranteed"]=1
        MOB_TEMPLATES[mob_id]=t
        MOB_SPAWNS.append((room,mob_id))

    # --------------------------------------------------------
    # Elite + Rare eligibility. Bosses/minibosses excluded.
    # --------------------------------------------------------
    eligible=[]
    for mob_id,t in list(MOB_TEMPLATES.items()):
        if (
            t.get("training_dummy") or t.get("world_boss") or t.get("mini_boss")
            or t.get("crypt_boss") or t.get("astral_boss")
            or t.get("mythic_crypt_boss") or t.get("mythic_astral_boss")
            or t.get("giant_fortress_boss") or "__elite_" in mob_id or mob_id.endswith("__rare")
        ):
            continue
        # Actual spawned ordinary opponents only.
        if any(tid == mob_id for _room,tid in MOB_SPAWNS):
            t["elite_eligible"]=True
            t["rare_eligible"]=True
            eligible.append(mob_id)
    _register_elite_variants(eligible)
    _register_rare_variants(eligible)

    # --------------------------------------------------------
    # Renewable treasure chests. One to two per area.
    # --------------------------------------------------------
    chest_rows = {
        "bandit_loot_depot": ("Skrzynia Łupów Bandytów",900,["healing_potion","soul_shard"],[]),
        "goblin_treasure_burrow": ("Goblińska Skrzynia Skarbów",900,["healing_potion","mana_potion","soul_shard"],[]),
        "ruin_armory": ("Skrzynia Starej Zbrojowni",1200,["healing_potion","mana_potion","soul_shard"],[]),
        "cemetery_bone_field": ("Zapieczętowana Skrzynia Cmentarna",1200,["soul_shard","soul_elixir"],[]),
        "cult_ruins_library": ("Skrzynia Zakazanej Wiedzy",1200,["soul_shard","soul_elixir"],regional_items["cultist"]),
        "cult_ruins_ritual_hall": ("Rytualna Skrzynia Kultystów",1500,["soul_elixir"],regional_items["cultist"]),
        "beast_lair_bone_nest": ("Skrzynia Łowców Bestii",1200,["wolf_fang","soul_shard"],[]),
        "necropolis_catacombs": ("Sarkofag Skarbów Nekropolii",1500,["soul_shard","soul_elixir"],regional_items["necropolis"]),
        "necropolis_royal_tombs": ("Królewska Skrzynia Nekropolii",1800,["soul_elixir"],regional_items["necropolis"]),
        "sewer_flooded_vault": ("Zalana Skrzynia Przemytników",900,["healing_potion","mana_potion","soul_shard"],[]),
        "ice_cave_crystal_chamber": ("Kryształowa Skrzynia Lodu",1500,["soul_shard","soul_elixir"],regional_items["ice_caves"]),
        "ice_cave_ancient_hall": ("Pradawna Skrzynia Lodowa",1800,["soul_elixir"],regional_items["ice_caves"]),
    }
    TREASURE_CHESTS.clear()
    for room,(name,respawn,base_pool,set_pool) in chest_rows.items():
        TREASURE_CHESTS[room]={
            "name":name,"respawn":respawn,"base_pool":tuple(base_pool),"set_pool":tuple(set_pool),
        }


def configure_base_mob_corpse_equipment():
    MOB_TEMPLATES["training_dummy"]["leave_corpse"] = False
    configs={
        "goblin":["leather_vest","lucky_charm"],
        "goblin_brute":["leather_vest","iron_gauntlets","iron_boots"],
        "bandit":["leather_vest","lucky_charm"],
        "bandit_marauder":["leather_vest","iron_gauntlets","iron_boots","lucky_charm"],
        "skeleton":["iron_helmet","iron_gauntlets","iron_boots"],
        "crypt_wraith":["forge_charm","lucky_charm"],
        "crystal_guardian":["iron_guard","iron_leggings","forge_charm"],
    }
    for tid,pool in configs.items():
        MOB_TEMPLATES[tid]["corpse_equipment_pool"]=pool
        MOB_TEMPLATES[tid]["corpse_equipment_guaranteed"]=1


def _corpse_material_tier_by_index(index):
    return CORPSE_MATERIAL_TIERS[max(0, min(len(CORPSE_MATERIAL_TIERS) - 1, int(index)))]


def _dungeon_material_tier_index(template):
    """v0.9.17: wysokie materiały są przede wszystkim nagrodą za lochy/wieże.

    v0.9.19 rozciąga zwykłą Kryptę przez pełne 1-400: materiał zmienia się
    wraz z pasmami Biegłości, a konkretne warianty EQ dochodzą co 10.
    Mityczne warianty zaczynają od wyższego pułapu. Wieża Astralna,
    Twierdza Gigantów i bojowe lochy profesyjne mają własne pasma.
    """
    idx = None

    mythic_crypt = int(template.get("mythic_crypt_floor", 0) or 0)
    if mythic_crypt > 0:
        # 1-20 Runiczny, 21-40 Smocza Stal, 41-60 Astral, 61-80 Pustka, 81+ Eternium.
        idx = 5 + (mythic_crypt - 1) // 20

    mythic_astral = int(template.get("mythic_astral_floor", 0) or 0)
    if mythic_astral > 0:
        idx = max(idx if idx is not None else 0, 5 + (mythic_astral - 1) // 20)

    crypt_floor = int(template.get("crypt_floor", 0) or 0)
    if crypt_floor > 0:
        # v0.9.19: pełna drabinka materiałów jest rozciągnięta przez progresję 1-400.
        # Żelazo 1-39, Stal 40-79, Mithril 80-119, ... Eternium 360+.
        idx = max(idx if idx is not None else 0, crypt_floor // 40)

    astral_floor = int(template.get("astral_floor", 0) or 0)
    if astral_floor > 0:
        # Wieża startuje na 100, więc zaczyna już od Kobaltu i kończy na Eternium.
        idx = max(idx if idx is not None else 0, 4 + max(0, astral_floor - 100) // 20)

    giant_floor = int(template.get("giant_fortress_floor", 0) or 0)
    if giant_floor > 0:
        # Twierdza rozwija materiały szybciej niż zwykły świat.
        idx = max(idx if idx is not None else 0, 1 + (giant_floor - 1) // 10)

    prof_floor = int(template.get("profession_dungeon_floor", 0) or 0)
    prof_name = str(template.get("profession_dungeon") or "")
    if prof_floor > 0 and prof_name and prof_name != "crystal_mine":
        # Bojowe lochy profesyjne: co 4 poziomy następny materiał.
        idx = max(idx if idx is not None else 0, (prof_floor - 1) // 4)

    if idx is None:
        return None

    return max(0, min(len(CORPSE_MATERIAL_TIERS) - 1, idx))


def corpse_material_tier_for_template(template):
    """Dobiera materiał z pierwszeństwem progresji lochu, potem siły moba."""
    dungeon_idx = _dungeon_material_tier_index(template)
    if dungeon_idx is not None:
        return _corpse_material_tier_by_index(dungeon_idx)

    score = int(template.get("max_hp", 1)) + int(template.get("damage", 1)) * 8
    selected_idx = 0
    for idx, tier in enumerate(CORPSE_MATERIAL_TIERS):
        if score >= int(tier["min_score"]):
            selected_idx = idx
        else:
            break

    # Zwykły świat daje głównie niższe materiały. Wysokie materiały mają
    # być kojarzone z Kryptami, Wieżami i Lochami; boss świata może dojść
    # maksymalnie do Runicznego, zwykły mob do Kobaltu.
    world_cap = 5 if bool(template.get("world_boss") or template.get("mini_boss")) else 4
    return _corpse_material_tier_by_index(min(selected_idx, world_cap))


CLASS_DROP_MASTERY_BY_MATERIAL = {
    key: levels[0] for key, levels in CORPSE_MATERIAL_MASTERY_BANDS.items()
}


def class_equipment_drop_mastery_for_template(template):
    # Nieskończone Krypty są źródłem EQ 201-400. Zwykły świat nadal
    # korzysta z materiałów i starego capu 200, więc nie zalewamy mapy
    # nowym endgameowym sprzętem.
    crypt_floor = int(template.get("crypt_floor", 0) or 0)
    if crypt_floor > 0:
        return class_equipment_unlocked_tier(min(400, crypt_floor))
    mythic_floor = int(template.get("mythic_crypt_floor", 0) or 0)
    if mythic_floor > 0:
        return class_equipment_unlocked_tier(min(400, 100 + mythic_floor // 2))
    material = corpse_material_tier_for_template(template)["key"]
    wanted = CLASS_DROP_MASTERY_BY_MATERIAL.get(material, 1)
    return class_equipment_unlocked_tier(wanted)


def class_equipment_drop_chance(template):
    """Rzadki dodatkowy drop klasowego EQ, bez gwarancji na zwykłych mobach."""
    boss = bool(
        template.get("world_boss")
        or template.get("mini_boss")
        or template.get("crypt_boss")
        or template.get("astral_boss")
        or template.get("mythic_crypt_boss")
        or template.get("mythic_astral_boss")
        or template.get("boss_mechanic")
    )
    elite = bool(
        template.get("elite_affix")
        or template.get("rare_variant")
        or template.get("rare_troll")
    )
    if boss:
        return 0.35
    if elite:
        return 0.18
    return 0.07


def class_equipment_drop_pool(template):
    mastery = class_equipment_drop_mastery_for_template(template)
    pool = []
    for class_name in CLASS_EQUIPMENT_SETS:
        pool.extend(
            CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER
            .get(class_name, {})
            .get(mastery, ())
        )
    return tuple(pool)


def _is_equipment_progression_boss(template):
    return bool(
        template.get("world_boss")
        or template.get("mini_boss")
        or template.get("crypt_boss")
        or template.get("astral_boss")
        or template.get("mythic_crypt_boss")
        or template.get("mythic_astral_boss")
        or template.get("giant_fortress_boss")
        or template.get("boss_mechanic")
    )


def corpse_material_tier_for_mastery_v0919(mastery):
    mastery = max(1, min(400, int(mastery or 1)))
    selected = CORPSE_MATERIAL_TIERS[0]
    for tier in CORPSE_MATERIAL_TIERS:
        levels = CORPSE_MATERIAL_MASTERY_BANDS[tier["key"]]
        if int(levels[0]) <= mastery:
            selected = tier
        else:
            break
    return selected


def equipment_progression_mastery_for_template_v0919(template):
    """Maksymalny próg Biegłości EQ sensowny dla źródła dropu."""
    mastery = None
    crypt_floor = int(template.get("crypt_floor", 0) or 0)
    mythic_crypt = int(template.get("mythic_crypt_floor", 0) or 0)
    astral_floor = int(template.get("astral_floor", 0) or 0)
    mythic_astral = int(template.get("mythic_astral_floor", 0) or 0)
    giant_floor = int(template.get("giant_fortress_floor", 0) or 0)
    prof_floor = int(template.get("profession_dungeon_floor", 0) or 0)
    prof_name = str(template.get("profession_dungeon") or "")

    if crypt_floor > 0:
        mastery = min(400, max(1, crypt_floor))
    elif mythic_crypt > 0:
        mastery = min(400, 200 + max(0, mythic_crypt - 1) * 2)
    elif mythic_astral > 0:
        mastery = min(400, 200 + max(0, mythic_astral - 1) * 2)
    elif astral_floor > 0:
        mastery = min(400, 160 + max(0, astral_floor - 100) * 2)
    elif giant_floor > 0:
        mastery = min(400, 40 + max(0, giant_floor - 1) * 4)
    elif prof_floor > 0 and prof_name and prof_name != "crystal_mine":
        mastery = min(400, 1 if prof_floor <= 1 else (prof_floor - 1) * 10)

    if mastery is None:
        material = corpse_material_tier_for_template(template)["key"]
        mastery = CORPSE_MATERIAL_REQUIRED_MASTERY.get(material, 1)

    # Boss daje dostęp do następnego progu +10, a nie skok o cały materiał.
    if _is_equipment_progression_boss(template):
        mastery = min(400, mastery + 10)
    return class_equipment_unlocked_tier(mastery)


def configure_material_corpse_equipment():
    for template_id, template in MOB_TEMPLATES.items():
        if template.get("leave_corpse", True) is False:
            continue
        base_tier = corpse_material_tier_for_template(template)
        target_mastery = equipment_progression_mastery_for_template_v0919(template)
        tier = corpse_material_tier_for_mastery_v0919(target_mastery)
        # Nigdy nie obniżamy materiału wyliczonego z siły/typu źródła.
        if list(CORPSE_MATERIAL_TIER_BY_KEY).index(base_tier["key"]) > list(CORPSE_MATERIAL_TIER_BY_KEY).index(tier["key"]):
            tier = base_tier
        candidates = [
            item_id
            for item_id in CORPSE_MATERIAL_ITEM_IDS[tier["key"]]
            if int(ITEMS[item_id].get("required_mastery", 1) or 1) <= target_mastery
        ]
        if not candidates:
            # Aspiracyjny materiał nigdy nie może wyzerować dropu. Wybieramy
            # najniższy wariant tej rodziny, który gracz będzie mógł zachować.
            candidates = [
                min(
                    CORPSE_MATERIAL_ITEM_IDS[tier["key"]],
                    key=lambda item_id: int(ITEMS[item_id].get("required_mastery", 1) or 1),
                )
            ]
        template["corpse_material_tier"] = tier["key"]
        template["corpse_material_pool"] = list(candidates)
        template["corpse_material_mastery_cap"] = target_mastery

        special = bool(
            template.get("elite_affix")
            or template.get("rare_variant")
            or template.get("rare_troll")
            or _is_equipment_progression_boss(template)
        )
        template["corpse_material_guaranteed"] = 2 if special else 1

build_crypt_200_floors()
build_crypt_loot_variants()
build_astral_tower()
build_mythic_endgame()
# v0.9.12: ręcznie przygotowane piętro 200 prowadzi dalej do części proceduralnej.
ROOMS[crypt_floor_id(CRYPT_PREGENERATED_MAX_FLOOR)]["exits"]["down"] = crypt_floor_id(CRYPT_PREGENERATED_MAX_FLOOR + 1)
ROOMS[mythic_crypt_floor_id(MYTHIC_MAX_FLOOR)]["exits"]["down"] = mythic_crypt_floor_id(MYTHIC_MAX_FLOOR + 1)
build_profession_dungeons()
for _prof_dungeon in ("sunken_grotto", "ancient_forest", "alchemy_garden"):
    for _prof_floor in range(1, PROF_DUNGEON_MAX_FLOOR + 1):
        MOB_SPAWNS.extend(profession_dungeon_combat_pack(_prof_dungeon, _prof_floor))
build_mountain_region_and_herb_meadows()
build_mountain_crafting_expansion()

# v0.9.13: dawne ostatnie piętra prowadzą dalej do części proceduralnej.
ROOMS[astral_floor_id(ASTRAL_MAX_FLOOR)]["exits"]["up"] = astral_floor_id(ASTRAL_MAX_FLOOR + 1)
ROOMS[mythic_astral_floor_id(MYTHIC_MAX_FLOOR)]["exits"]["up"] = mythic_astral_floor_id(MYTHIC_MAX_FLOOR + 1)
ROOMS[giant_fortress_floor_id(GIANT_FORTRESS_MAX_FLOOR)]["exits"]["up"] = giant_fortress_floor_id(GIANT_FORTRESS_MAX_FLOOR + 1)
ROOMS[mine_floor_id(MINE_PREGENERATED_MAX_FLOOR)]["exits"]["down"] = mine_floor_id(MINE_PREGENERATED_MAX_FLOOR + 1)
ROOMS[profession_dungeon_room_id("crystal_mine", PROF_DUNGEON_MAX_FLOOR)]["exits"]["down"] = profession_dungeon_room_id("crystal_mine", PROF_DUNGEON_MAX_FLOOR + 1)
ROOMS[profession_dungeon_room_id("sunken_grotto", PROF_DUNGEON_MAX_FLOOR)]["exits"]["down"] = profession_dungeon_room_id("sunken_grotto", PROF_DUNGEON_MAX_FLOOR + 1)
ROOMS[profession_dungeon_room_id("ancient_forest", PROF_DUNGEON_MAX_FLOOR)]["exits"]["south"] = profession_dungeon_room_id("ancient_forest", PROF_DUNGEON_MAX_FLOOR + 1)
ROOMS[profession_dungeon_room_id("alchemy_garden", PROF_DUNGEON_MAX_FLOOR)]["exits"]["east"] = profession_dungeon_room_id("alchemy_garden", PROF_DUNGEON_MAX_FLOOR + 1)

build_world_expansion_i()
build_high_end_mob_pack()
build_world_expansion_ii()

# v0.25.1 — UNIFIED DEEP MINE
# Jedyna aktywna kopalnia to Kopalnia Głębinowa. Wszystkie historyczne
# rejestracje MINING_ROOMS poza jej wejściem i mine_floor_N są usuwane.
def v0251_enforce_single_mine():
    MINING_ROOMS.intersection_update(UNIFIED_DEEP_MINE_STATIC_ROOMS | MINING_DEPTH_ROOMS)

v0251_enforce_single_mine()
validate_complete_resource_atlases()
build_forest_wolves_and_quest_balance()
build_elite_rare_named_loot_expansion()

# v0.9.18: każde EQ ma próg Biegłości. Mocne, przekazywalne przedmioty nie
# mogą omijać progresji tylko dlatego, że nie są przypisane do konkretnej klasy.
def configure_equipment_mastery_requirements_v0918():
    blacksmith_mastery = {
        str(tier["key"]): max(1, min(CLASS_MASTERY_MAX_LEVEL, int(tier["profession_level"])))
        for tier in BLACKSMITH_TIERS
    }

    # Regionalne zestawy i unikatowe dropy bossów istniały przed globalnym
    # systemem wymagań EQ. W v0.9.18 dostają realne progi Biegłości, aby
    # przekazanie przedmiotu nowej postaci nie omijało progresji.
    regional_mastery = {
        "cultist": 40,
        "necropolis": 70,
        "ice_caves": 60,
    }
    named_mastery = {
        "bandit_chief_signet": 10,
        "goblin_king_crown": 20,
        "shadow_alpha_fang": 20,
        "ruin_warden_plate": 30,
        "crystal_lord_core": 40,
        "cemetery_keeper_lantern": 15,
        "void_archon_ring": 40,
        "primal_alpha_necklace": 35,
        "dead_king_seal": 70,
        "cistern_king_chain": 10,
        "eternal_ice_heart": 60,
        "troll_king_tusk": 40,
    }

    recipe_mastery = {}
    for recipe_table in (CRAFT_RECIPES, JEWELCRAFT_RECIPES):
        for recipe in recipe_table.values():
            output = recipe.get("output")
            if not output or ITEMS.get(output, {}).get("type") != "armor":
                continue
            req = max(
                1,
                int(recipe.get("min_profession_level", 0) or 0),
                int(recipe.get("min_tool_level", 0) or 0),
            )
            recipe_mastery[output] = max(recipe_mastery.get(output, 1), req)

    configured = 0
    for item_id, item in ITEMS.items():
        if item.get("type") != "armor":
            continue
        required_class = item.get("required_class")
        if required_class:
            item["required_mastery"] = max(1, int(item.get("required_mastery", 1) or 1))
            configured += 1
            continue

        requirement = max(1, int(item.get("required_mastery", 1) or 1))

        material = item.get("corpse_material")
        if material in CORPSE_MATERIAL_REQUIRED_MASTERY:
            requirement = max(requirement, CORPSE_MATERIAL_REQUIRED_MASTERY[material])

        crypt_tier = int(item.get("crypt_set_tier", 0) or 0)
        if crypt_tier > 0:
            requirement = max(requirement, min(400, crypt_tier * 10))

        astral_tier = int(item.get("astral_set_tier", 0) or 0)
        if astral_tier > 0:
            requirement = max(requirement, min(400, 90 + astral_tier * 10))

        astral_floor = int(item.get("astral_relic_floor", 0) or 0)
        if astral_floor > 0:
            requirement = max(requirement, min(400, astral_floor))

        crypt_boss_floor = int(item.get("boss_relic_floor", 0) or 0)
        if crypt_boss_floor > 0:
            requirement = max(requirement, min(400, crypt_boss_floor))

        regional_set = str(item.get("regional_set") or "")
        if regional_set in regional_mastery:
            requirement = max(requirement, regional_mastery[regional_set])

        if item_id in named_mastery:
            requirement = max(requirement, named_mastery[item_id])

        blacksmith_material = str(item.get("blacksmith_material") or "")
        if blacksmith_material in blacksmith_mastery:
            requirement = max(requirement, blacksmith_mastery[blacksmith_material])

        jewel_level = int(item.get("jewelcraft_level", 0) or 0)
        if jewel_level > 0:
            requirement = max(requirement, min(400, jewel_level))

        if item_id in recipe_mastery:
            requirement = max(requirement, min(400, recipe_mastery[item_id]))

        item["required_mastery"] = max(1, min(CLASS_MASTERY_MAX_LEVEL, requirement))
        item["mastery_requirement_scope"] = "active_class"
        marker = f"Wymaga Biegłości aktywnej klasy {item['required_mastery']}."
        desc = str(item.get("desc") or "").strip()
        if "Wymaga Biegłości aktywnej klasy" not in desc:
            item["desc"] = (desc + " " + marker).strip()
        configured += 1
    return configured

V0918_EQUIPMENT_MASTERY_CONFIGURED = configure_equipment_mastery_requirements_v0918()


# v0.9.19: globalna siatka wymagań EQ. Poziom 1 pozostaje startowy dla
# zgodności save'ów, a wszystkie dalsze progi są dokładnie co 10 Biegłości.
EQUIPMENT_MASTERY_LEVELS_V0919 = (1,) + tuple(range(10, 401, 10))


def normalize_equipment_mastery_v0919(value):
    value = max(1, min(400, int(value or 1)))
    if value <= 1:
        return 1
    return min(400, ((value + 9) // 10) * 10)


def normalize_all_equipment_mastery_v0919():
    changed = 0
    for item in ITEMS.values():
        if item.get("type") != "armor":
            continue
        before = int(item.get("required_mastery", 1) or 1)
        after = normalize_equipment_mastery_v0919(before)
        if after != before:
            changed += 1
        item["required_mastery"] = after
        if not item.get("required_class"):
            item["mastery_requirement_scope"] = "active_class"
        # Usuń stary tekst z nietypowym progiem 15/35 itd. i dopisz prawdę.
        desc = str(item.get("desc") or "")
        desc = re.sub(r"\s*Wymaga Biegłości aktywnej klasy \d+\.?", "", desc).strip()
        if not item.get("required_class"):
            item["desc"] = (desc + f" Wymaga Biegłości aktywnej klasy {after}.").strip()
    return changed


V0919_NORMALIZED_EQUIPMENT_REQUIREMENTS = normalize_all_equipment_mastery_v0919()


def v0919_equipment_progression_audit():
    by_level = {level: {slot: 0 for slot in CLASS_EQUIPMENT_SLOT_DEFS} for level in EQUIPMENT_MASTERY_LEVELS_V0919}
    invalid = []
    for item_id, item in ITEMS.items():
        if item.get("type") != "armor":
            continue
        req = int(item.get("required_mastery", 1) or 1)
        if req not in EQUIPMENT_MASTERY_LEVELS_V0919:
            invalid.append((item_id, req))
            continue
        slot = str(item.get("slot") or "")
        if slot in by_level[req]:
            by_level[req][slot] += 1
    return by_level, invalid


V0919_EQUIPMENT_BY_LEVEL_SLOT, V0919_INVALID_EQUIPMENT_THRESHOLDS = v0919_equipment_progression_audit()

# v0.9.15: minimum trzy zwykłe moby w pokojach głównych lochów/wież.
# Kopalnie są wykluczone. Bossów nie kopiujemy.
DENSE_DUNGEON_ZONES = {
    "Krypta Nieskończona", "Mityczna Krypta",
    "Wieża Astralna", "Mityczna Wieża Astralna",
    "Twierdza Gigantów", "Jaskinia Trolli", "Jaskinie Goblinów",
    "Kanały Pod Miastem", "Lodowe Jaskinie", "Nekropolia",
    "Ruiny Kultystów", "Ruiny Strażnicy",
}
DENSE_ZONE_NAME_POOLS = {
    "Krypta Nieskończona": CRYPT_REGULAR_NAMES,
    "Wieża Astralna": ASTRAL_REGULAR_NAMES,
    "Mityczna Krypta": (
        "Mityczny Kościany Rycerz", "Mityczny Upiór",
        "Mityczny Żniwiarz Grobowca", "Mityczny Strażnik Otchłani",
    ),
    "Mityczna Wieża Astralna": (
        "Mityczny Astralny Strażnik", "Mityczny Rycerz Konstelacji",
        "Mityczne Widmo Nebuli", "Mityczny Herold Gwiezdnej Burzy",
    ),
    "Twierdza Gigantów": (
        "Ogr Miotacz Głazów", "Cyklop Strażnik", "Górski Gigant",
    ),
    "Jaskinia Trolli": (
        "Troll Jaskiniowy", "Troll Skalny", "Trollowy Rozpruwacz", "Troll Szaman",
    ),
    "Jaskinie Goblinów": (
        "Goblin Zwiadowca", "Goblin Łucznik", "Goblin Nożownik", "Goblin Szaman",
    ),
    "Kanały Pod Miastem": (
        "Kanałowy Szczurołak", "Plugawy Topielec", "Zmutowany Szczur", "Kanałowy Rozbójnik",
    ),
    "Lodowe Jaskinie": (
        "Lodowy Wilk", "Mroźny Upiór", "Kryształowy Golem", "Jaskiniowy Yeti",
    ),
    "Nekropolia": (
        "Kościany Wojownik", "Grobowy Upiór", "Nekropolitalny Strażnik", "Przeklęty Akolita",
    ),
    "Ruiny Kultystów": (
        "Kultysta Ostrza", "Kultysta Płomienia", "Przeklęty Wyznawca", "Cień Rytualisty",
    ),
    "Ruiny Strażnicy": (
        "Upadły Strażnik", "Ruiny Łucznik", "Kamienny Wartownik", "Widmo Garnizonu",
    ),
}

def _is_boss_for_density(template):
    return bool(
        template.get("world_boss") or template.get("mini_boss")
        or template.get("crypt_boss") or template.get("astral_boss")
        or template.get("mythic_crypt_boss") or template.get("mythic_astral_boss")
        or template.get("giant_fortress_boss") or template.get("boss_mechanic")
    )

def densify_static_dungeon_spawns():
    # Najpierw usuń stare identyczne duplikaty tego samego archetypu
    # tylko w lochach objętych tym systemem. Zastępujemy je różnymi mobami.
    compact = []
    seen_pairs = set()
    for room_id, template_id in MOB_SPAWNS:
        zone = ROOMS.get(room_id, {}).get("zone")
        pair = (room_id, template_id)
        if zone in DENSE_DUNGEON_ZONES and pair in seen_pairs:
            continue
        compact.append(pair)
        seen_pairs.add(pair)
    MOB_SPAWNS[:] = compact

    room_spawns = {}
    for room_id, template_id in MOB_SPAWNS:
        room_spawns.setdefault(room_id, []).append(template_id)

    additions = []
    for room_id, room in ROOMS.items():
        zone = room.get("zone")
        if zone not in DENSE_DUNGEON_ZONES:
            continue
        # Nigdy nie dotykamy żadnej kopalni.
        if "Kopalnia" in str(zone) or "Kopalnia" in str(room.get("name", "")):
            continue
        existing = room_spawns.get(room_id, [])
        regular = [
            tid for tid in existing
            if tid in MOB_TEMPLATES and not _is_boss_for_density(MOB_TEMPLATES[tid])
        ]
        if not regular:
            continue
        pool = DENSE_ZONE_NAME_POOLS.get(zone, ())
        def _archetype_name(template_id):
            name = str(MOB_TEMPLATES.get(template_id, {}).get("name", template_id))
            name = re.sub(r",\s*(?:poziom|piętro)\s+\d+.*$", "", name, flags=re.I)
            return name.casefold().strip()
        distinct_archetypes = {_archetype_name(tid) for tid in regular}
        needed = max(0, 3 - len(distinct_archetypes))
        available_pool = [
            name for name in pool
            if str(name).casefold().strip() not in distinct_archetypes
        ]
        for n in range(needed):
            base_id = regular[n % len(regular)]
            base = MOB_TEMPLATES[base_id]
            variant_id = f"{base_id}_v915_{n + 2}"
            if variant_id in MOB_TEMPLATES:
                additions.append((room_id, variant_id))
                continue
            variant = dict(base)
            if isinstance(base.get("drops"), dict):
                variant["drops"] = dict(base["drops"])
            if isinstance(base.get("corpse_equipment_pool"), list):
                variant["corpse_equipment_pool"] = list(base["corpse_equipment_pool"])
            if available_pool:
                # Dobieramy nazwę nieobecną jeszcze w tym pokoju.
                chosen = available_pool[n % len(available_pool)]
                floor_match = re.search(r"(\d+)$", room_id)
                floor_text = floor_match.group(1) if floor_match else None
                suffix = f", poziom {floor_text}" if floor_text else ""
                if "Krypta" in zone:
                    suffix = f", piętro {floor_text}" if floor_text else ""
                variant["name"] = f"{chosen}{suffix}"
                distinct_archetypes.add(str(chosen).casefold().strip())
            else:
                variant["name"] = f"{base.get('name', 'Przeciwnik')} — patrol {n + 2}"
            # Lekko różny profil walki, bez zwiększania ekonomii za pojedyncze zabicie.
            if n % 2 == 0:
                variant["damage_type"] = "magic" if base.get("damage_type") == "physical" else "physical"
            variant["dense_dungeon_variant"] = True
            variant["template_id"] = variant_id
            MOB_TEMPLATES[variant_id] = variant
            additions.append((room_id, variant_id))
    MOB_SPAWNS.extend(additions)
    return len(additions)

DENSE_DUNGEON_ADDED_SPAWNS = densify_static_dungeon_spawns()

# ============================================================
# v0.9.12 - CONTENT 201-400: Soul Trials + questy profesyjne
# ============================================================
for _tier in range(21, 41):
    _level = SOUL_TIER_THRESHOLDS[_tier - 1]
    _qid = SOUL_TRIAL_QUEST_IDS[_tier]
    QUESTS[_qid] = {
        "name": f"Próba Broni Duszy: Tier {_tier}",
        "giver": "Kapłan Elor", "kind": "kill",
        "target": f"crypt_boss_{_level}", "needed": 1,
        "description": (
            f"Pokonaj bossa piętra {_level} nieskończonej Krypty i wróć do Kapłana Elora."
        ),
        "required_soul_level": _level, "required_soul_tier": _tier - 1,
        "unlocks_soul_tier": _tier,
        "reward_silver": 2_000 + (_level - 200) * 120,
        "reward_gold": 10 + (_level - 200) // 10,
        "reward_mithril": 0, "reward_items": {},
    }

# v0.26.1 — Soul Trial Balance Pass.
# Tiery 2-7 prowadzą początkującego przez zwykłych przeciwników zamiast
# natychmiast wysyłać go na bossów Krypty. Tiery 8-12 używają bossów
# regionalnych o łagodniejszej krzywej HP. Od Tieru 13 zaczynają się
# właściwe próby mistrzowskie na bossach Krypty, a 21-40 pozostają endgame.
def configure_soul_trials_v0261():
    overrides = {
        2: {
            "target": "temple_rat", "needed": 6,
            "description": "Pokonaj 6 Szczurów Świątynnych w piwnicy Świątyni Odrodzenia i wróć do Kapłana Elora.",
        },
        3: {
            "target": "goblin", "needed": 5,
            "description": "Pokonaj 5 goblinów na starym szlaku lub w ich obozowisku i wróć do Kapłana Elora.",
        },
        4: {
            "target": "skeleton", "needed": 5,
            "description": "Pokonaj 5 Szkieletów Strażników przy wejściu do Krypty i wróć do Kapłana Elora.",
        },
        5: {
            "target": "crypt_wraith", "needed": 5,
            "description": "Pokonaj 5 Upiorów Krypty i wróć do Kapłana Elora. To pierwsza próba przeciw magii nieumarłych.",
        },
        6: {
            "target": "sewer_plague_rat", "needed": 4,
            "description": "Pokonaj 4 Szczury Zarazy w Kanałach Pod Miastem i wróć do Kapłana Elora.",
        },
        7: {
            "target": "cemetery_restless_dead", "needed": 4,
            "description": "Pokonaj 4 Niespokojnych Zmarłych na Starym Cmentarzu i wróć do Kapłana Elora.",
        },
        8: {
            "target": "cemetery_keeper", "needed": 1,
            "description": "Pokonaj Nieumarłego Strażnika Cmentarza i wróć do Kapłana Elora. To pierwsza próba bossowa Broni Duszy.",
        },
        9: {
            "target": "sewer_king", "needed": 1,
            "description": "Pokonaj Króla Podmiejskich Kanałów i wróć do Kapłana Elora.",
        },
        10: {
            "target": "cult_archon", "needed": 1,
            "description": "Pokonaj Arcykultystę Otchłani w Ruinach Kultystów i wróć do Kapłana Elora.",
        },
        11: {
            "target": "beast_ancient_alpha", "needed": 1,
            "description": "Pokonaj Pradawnego Alfę Bestii w Legowisku Bestii i wróć do Kapłana Elora.",
        },
        12: {
            "target": "ice_dragon", "needed": 1,
            "description": "Pokonaj Pradawnego Lodowego Smoka w Lodowych Jaskiniach i wróć do Kapłana Elora.",
        },
    }
    for tier, quest_id in SOUL_TRIAL_QUEST_IDS.items():
        quest = QUESTS.get(quest_id)
        if not quest:
            continue
        quest["trial_band"] = soul_trial_difficulty_band(tier)
        quest["soul_trial_tier"] = int(tier)
        if tier in overrides:
            quest.update(overrides[tier])

    # Teksty sprzed rozszerzenia 201-400 nie mogą nazywać T19/T20 końcem serii.
    q19 = QUESTS.get(SOUL_TRIAL_QUEST_IDS.get(19), {})
    if q19:
        q19["description"] = (
            "Pokonaj Cesarza Upiorów na piętrze 180 Krypty, a następnie wróć do Kapłana Elora. "
            "To końcówka mistrzowskiej części 1-200, ale dalsze Próby trwają do Tieru 40."
        )
    q20 = QUESTS.get(SOUL_TRIAL_QUEST_IDS.get(20), {})
    if q20:
        q20["description"] = (
            "Pokonaj Władcę Dwustu Pięter na kamieniu milowym piętra 200 Krypty i wróć do Kapłana Elora. "
            "Tier 20 zamyka część 1-200; kolejne Próby Tierów 21-40 prowadzą przez progresję 201-400."
        )

configure_soul_trials_v0261()

def _add_profession_400_quest(npc_id, qid, *, level, profession, tool_type, kind, target=None, needed=2, targets=None):
    npc = NPCS.get(npc_id)
    if not npc:
        return
    quest = {
        "name": f"Zlecenie {_PROGRESSION_400_NAMES[level]} ({profession})",
        "giver": npc.get("name", profession),
        "kind": kind, "needed": needed,
        "description": f"Wykonaj zlecenie profesji {profession} na poziomie {level}.",
        "specialist_tool_type": tool_type,
        "required_profession": profession, "min_profession_level": level,
        "reward_profession": profession, "reward_profession_xp": 4_000 + (level - 200) * 20,
        "reward_tool_type": tool_type, "reward_tool_xp": 3_500 + (level - 200) * 18,
        "reward_silver": 100_000_000 + (level - 200) * 250_000,
        "reward_gold": 0, "reward_mithril": 0, "reward_items": {},
        "repeatable": True, "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
        "event_progress_only": True,
    }
    if target is not None:
        quest["target"] = target
    if targets is not None:
        quest["targets"] = tuple(targets)
    if kind == "collect_resource":
        quest["track_resource_progress"] = True
    if kind in ("collect", "craft_set"):
        quest["track_craft_progress"] = True
    QUESTS[qid] = quest
    old = tuple(npc.get("specialist_quests") or ())
    if qid not in old:
        npc["specialist_quests"] = old + (qid,)

for _level in PROGRESSION_400_LEVELS:
    _needed = max(1, 4 - ((_level - 220) // 80))
    _add_profession_400_quest(
        "specialist_fishing", f"fishing_400_{_level}", level=_level,
        profession="Wędkarstwo", tool_type="fishing", kind="collect_resource",
        target=f"fish_400_ocean_{_level}", needed=_needed,
    )
    _add_profession_400_quest(
        "specialist_mining", f"mining_400_{_level}", level=_level,
        profession="Górnictwo", tool_type="mining", kind="collect_resource",
        target=f"ore_400_{_level}", needed=_needed,
    )
    _add_profession_400_quest(
        "specialist_woodcutting", f"wood_400_q_{_level}", level=_level,
        profession="Drwalstwo", tool_type="woodcutting", kind="collect_resource",
        target=f"wood_400_{_level}", needed=_needed,
    )
    _add_profession_400_quest(
        "specialist_herbalism", f"herb_400_q_{_level}", level=_level,
        profession="Zielarstwo", tool_type="herbalism", kind="collect_resource",
        target=f"herb_400_{_level}", needed=_needed,
    )
    _add_profession_400_quest(
        "specialist_cooking", f"cook_400_{_level}", level=_level,
        profession="Gotowanie", tool_type="cooking", kind="collect",
        target=f"feast_400_{_level}", needed=_needed,
    )
    _add_profession_400_quest(
        "specialist_alchemy", f"alchemy_400_{_level}", level=_level,
        profession="Alchemia", tool_type="alchemy", kind="collect",
        target=f"elixir_400_{_level}", needed=_needed,
    )
    _add_profession_400_quest(
        "specialist_crafting", f"craft_400_{_level}", level=_level,
        profession="Kowalstwo", tool_type="crafting", kind="collect",
        target=f"charm_400_{_level}", needed=_needed,
    )
    _add_profession_400_quest(
        "jeweler_mirella", f"jewel_400_{_level}", level=_level,
        profession="Jubilerstwo", tool_type="jewelcrafting", kind="collect",
        target=f"jewel_p400_{_level}_ring", needed=_needed,
    )


# ============================================================
# v0.8.61 - GLOBALNY REBALANS EKONOMII

# Nie tworzymy nowych lokacji ani twardych limitów ryb.
for _rid in ("forest_stream", "troll_underground_river"):
    if _rid in ROOMS:
        RIVER_FISHING_ROOMS.add(_rid)
        FRESHWATER_FISHING_ROOMS.add(_rid)
        FISHING_ROOMS.add(_rid)
for _rid in ("blackwater_pool", "ice_cave_frozen_lake"):
    if _rid in ROOMS:
        LAKE_FISHING_ROOMS.add(_rid)
        FRESHWATER_FISHING_ROOMS.add(_rid)
        FISHING_ROOMS.add(_rid)
configure_profession_tool_sellers()
configure_v0800_help_info()
configure_v081_help_info()
def configure_v0856_help_refresh():
    """Aktualizuje podstawowe pomoce do rzeczywistego stanu v0.8.56."""
    HELP_TOPIC_ALIASES.update({
        "staty": "statystyki", "status": "statystyki", "stats": "statystyki", "stat": "statystyki",
        "hp": "hp", "health": "hp", "zdrowie": "hp", "zycie": "hp", "życie": "hp",
        "score": "score", "wynik": "score", "postac": "score", "postać": "score",
        "dusza": "dusza", "soul": "dusza", "soul info": "dusza",
        "quest": "questy", "quests": "questy", "zadania": "questy",
    })

    HELP_TOPICS["podstawy"] = [
        "Soulbound nie ma levelu postaci. Rozwój odbywa się przez statystyki, Biegłość klas, Soul Level Broni Duszy, EQ i profesje.",
        "Najważniejsze komendy startowe: look, exits, hp, score, staty, dusza, eq, quest, portfel i help.",
        "k <mob> rozpoczyna walkę realtime z dowolnym zabijalnym mobem; con <mob> ocenia go bez walki.",
        "quit zapisuje bieżącą postać i wraca do menu wyboru postaci na tym samym koncie.",
        "help staty, help hp, help score, help dusza i help quest opisują najważniejsze systemy.",
    ]
    HELP_TOPICS["statystyki"] = [
        "staty pokazuje każdą statystykę w osobnym komunikacie NVDA, a potem HP, Manę, obronę i ofensywę.",
        "staty info pokazuje osobno bazę, wartość efektywną oraz bonus EQ/klejnotów dla każdej statystyki.",
        "Sześć statystyk: Siła, Zręczność, Kondycja, Inteligencja, Siła Woli i Charyzma.",
        "Każda z sześciu statystyk ma własny licznik EXP i własny próg. Od v0.19 próg wylicza Global Progression Generator: początek jest szybki, a wymagania rosną mocniej wraz z wartością statystyki. Zdobycie pełnego progu zwiększa tylko tę konkretną statystykę o 1.",
        "Kondycja zwiększa HP każdej klasy. Inteligencja zwiększa Manę każdej klasy.",
        "Zręczność wpływa na szybkość, unik i krytyki. Siła zwiększa fizyczne obrażenia i częściowo skaluje magiczne skille/spelle.",
        "Nie ma ręcznego rozdawania punktów i nie ma levelu postaci.",
    ]
    HELP_TOPICS["hp"] = [
        "hp / zdrowie pokazuje bieżące HP, maksymalne HP, bieżącą Manę i maksymalną Manę.",
        "Wartości są czytane osobno, żeby NVDA nie łączył całego stanu w jeden długi komunikat.",
        "Maksymalne HP wynika głównie z Kondycji, rasy, klasy, EQ i bonusów. Maksymalna Mana wynika głównie z Inteligencji oraz bonusów.",
    ]
    HELP_TOPICS["score"] = [
        "score / wynik to zwarte podsumowanie aktualnej postaci.",
        "Pokazuje rasę, główną i aktywne klasy, Biegłość każdej klasy, Soul Level/Tier, HP, Manę i sześć statystyk.",
        "Pokazuje też wspólny portfel konta, aktualną lokację/strefę oraz dynamiczną ocenę terenu.",
        "score i expowiska pokazują orientacyjną ocenę terenu w historycznej skali 1-400; con i dynamiczny EXP walki używają osobnej bieżącej skali siły 1-400. Żadna z tych ocen nie jest levelem postaci.",
    ]
    HELP_TOPICS["dusza"] = [
        "dusza pokazuje krótki stan Broni Duszy: Soul Level, Tier, Soul XP, moc i następny cel.",
        "dusza info pokazuje pełne progi Tierów 1-40 oraz stan Prób Broni Duszy potrzebnych do dalszej progresji.",
        "Kolejne Tiery do 40 wymagają odpowiedniego Soul Levelu i właściwego odblokowania; progi 1-200 zachowują wcześniejsze Próby, a 201-400 kontynuują progresję endgame.",
        "Soul Level ma zakres 1-400 i rozwija Broń Duszy; nie jest levelem postaci.",
        "Skille/spelle klasowe zachowują stare progi odblokowania do 200, a Biegłość właściwej klasy rozwija się 1-400, nie Soul Level.",
        "Po osiągnięciu progu wpisz quest list Kapłan Elor, przyjmij właściwą Próbę, wykonaj cel, oddaj quest i użyj unlock.",
    ]

    HELP_TOPICS["aoe"] = [
        "Czary i skille obszarowe trafiają wszystkie dostępne cele zgodnie z opisem konkretnej umiejętności.",
        "Historyczne progi Soul zostały zastąpione Biegłością klasy: np. umiejętność z progu 40 wymaga Biegłości 40 danej klasy.",
        "Skille odblokowuje Biegłość właściwej klasy w całym zakresie 1-400: klasyczne progi pozostają do 200, a dalsze odblokowania są w zakresie 220-400.",
        "Pełne szczegóły konkretnego AoE: help <nazwa skilla> albo skill info <nazwa>.",
        "Akcja obszarowa działa w walce realtime i nie tworzy osobnej tury przeciwnika.",
    ]
    HELP_TOPICS["naturalne_naucz"] = [
        "U nauczyciela aktywnej klasy możesz uczyć się skilli naturalną nazwą kategorii.",
        "naucz leczenie, naucz tarcza, naucz unik, naucz drain i naucz dobij wybierają pasujący dostępny skill.",
        "Ofensywne przykłady: naucz ciecie, naucz pocisk, naucz ogien, naucz burza, naucz mlot, naucz strzal.",
        "System bierze pod uwagę tylko skille klasy nauczyciela, przy którym aktualnie stoisz.",
        "Najpierw preferuje skill, którego jeszcze nie znasz, a potem najwyższy dostępny próg Biegłości klasy.",
        "Pełne nazwy i numery skilli nadal działają.",
    ]
    HELP_TOPICS["rozwoj_statystyk"] = list(HELP_TOPICS["statystyki"])
    HELP_TOPICS["soul200"] = [
        "Broń Duszy ma Soul Level 1-400 i 40 Tierów.",
        "Każdy Tier 2-20 ma własną jednorazową Próbę u Kapłana Elora.",
        "Po osiągnięciu wymaganego Soul Levelu wykonaj Próbę, oddaj ją i wpisz unlock.",
        "Soul Level zwiększa moc Broni Duszy i nie odblokowuje skilli klasowych.",
        "Skille klasowe odblokowuje Biegłość klasy 1-400; stare progi 1-200 pozostają w tych samych miejscach, a dalsza linia działa do 400.",
        "Nie ma levelu postaci.",
    ]
    HELP_TOPICS["soul_tier45_krypta200"] = [
        "Broń Duszy ma 20 Tierów na Soul Levelach: 1, 10, 20, 25, 35, 45, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180 i 200.",
        "Każdy Tier 2-20 wymaga własnej jednorazowej Próby Broni Duszy u Kapłana Elora.",
        "Po progu użyj quest list Kapłan Elor, wykonaj Próbę, oddaj zadanie i wpisz unlock.",
        "dusza info pokazuje stan wszystkich 39 Prób (Tier 2-40), ich pasmo trudności oraz następny cel.",
        "Nie ma resetu Soul Levelu, Soul XP ani historycznie ukończonych prób.",
    ]

    if "informacje" in HELP_TOPICS:
        HELP_TOPICS["informacje"] = [
            "Najważniejsze komendy informacyjne są rozdzielone na krótkie i pełne wersje pod NVDA.",
            "hp - bieżące i maksymalne HP oraz Mana, osobno.",
            "score - ogólne podsumowanie postaci i progresji.",
            "staty - każda statystyka osobno; staty info - baza, wartość efektywna, EQ i mechanika.",
            "dusza - szybki stan Broni Duszy; dusza info - Tiery 1-40, wymagania i następny cel.",
            "profesje / profesje info - stan i pełne informacje profesji.",
            "narzedzia / narzedzia info - stan i pełne informacje narzędzi.",
            "eq / eq info - założone EQ oraz pełne bonusy, sockety i sety.",
            "kodeksklasowy <klasa> - skille odblokowywane Biegłością klasy, nauczyciel, cena i status.",
            "help informacje - ten przewodnik.",
        ]

configure_v0856_help_refresh()


def configure_v0856_help_categories():
    """Przywraca ogólne tematy reklamowane przez główny help."""
    HELP_TOPIC_ALIASES.update({
        "professions": "profesje", "profession": "profesje",
        "inventory": "ekwipunek", "equipment": "ekwipunek", "eq": "ekwipunek",
        "mining": "gornictwo", "mine": "gornictwo",
        "woodcutting": "drwalstwo", "wood": "drwalstwo",
        "herbalism": "zielarstwo", "herbs": "zielarstwo",
        "alchemy": "alchemia", "crafting": "rzemioslo", "craft": "rzemioslo",
        "recipes": "receptury", "recipe": "receptury",
        "charisma": "charyzma", "haryzma": "charyzma",
        "party": "druzyny", "druzyna": "druzyny", "drużyna": "druzyny",
        "corpse": "zwloki", "zwloki": "zwloki", "zwłoki": "zwloki",
        "containers": "pojemniki", "container": "pojemniki",
        "shops": "sklepy", "shop": "sklepy", "sklep": "sklepy",
        "sprzedaj": "sklepy", "sell": "sklepy", "kup": "sklepy", "buy": "sklepy",
        "dostarcz": "questy", "deliver": "questy",
        "players": "gracze", "player": "gracze",
        "death": "smierc", "smierc": "smierc", "śmierć": "smierc",
        "races": "rasy", "race": "rasy",
        "abilities": "umiejetnosci", "skills": "umiejetnosci", "umiejętności": "umiejetnosci",
        "skillnames": "nazwy_skilli", "nazwyskilli": "nazwy_skilli",
        "teachers": "nauczyciele", "trainers": "nauczyciele",
        "atlas": "atlas",
    })
    HELP_TOPICS["profesje"] = [
        "Soulbound ma 8 profesji 1-400: Wędkarstwo, Górnictwo, Drwalstwo, Zielarstwo, Gotowanie, Alchemia, Kowalstwo i Jubilerstwo.",
        "Każda profesja ma własny level 1-400. Odpowiadające narzędzie ma osobną progresję 1-400 i służy do odblokowania lepszych surowców oraz bonusów jakości/urobku.",
        "profesje pokazuje szybki stan; profesje info pokazuje XP, rangi i dalszy rozwój.",
        "Narzędzia profesji rozwijają się do 400 i nie mają trwałości.",
        "Zasada v0.8.66: level profesji skraca czas pracy i blokuje receptury/zlecenia/poziomy lochów; level narzędzia odblokowuje lepsze zasoby i zwiększa bonus jakości/urobku.",
        "v0.9.9: przy rozmowie NPC profesyjny informuje o nowym zadaniu, komentuje powrót i stan n/x, a przy przyjęciu mówi osobną kwestię przed startem 0/x.",
        "v0.9.8: przy oddaniu questa NPC komentuje wykonanie i czytelnie wręcza nagrodę; questy profesyjne/rzemieślnicze zawsze mają także nagrodę w walucie.",
        "v0.9.7: NPC profesyjni rozpoznają twoją aktualną rangę. Rozmowa z Borysem, Torenem, Branem, Liorą, Marcelem, Orinem, Haldorem, Mirellą i mistrzami zbieractwa zmienia ton wraz z rangą; jest to wyłącznie prestiż/dialog.",
    ]
    HELP_TOPICS["ekwipunek"] = [
        "inventory / i pokazuje przedmioty w ekwipunku. eq / equipment pokazuje założone wyposażenie.",
        "Od v0.9.11 nowa postać NIE dostaje startowego EQ klasowego. Klasowe wyposażenie zdobywa się w sklepach i jako losowy drop z mobów.",
        "Każda z 12 klas ma 3 różne linie EQ na każdym progu Biegłości; alternatywne linie mają równy budżet mocy, więc wybór jest różnorodnością, nie power creepem.",
        "eq info pokazuje pełne bonusy, sety i sockety.",
        "Materiałowe EQ z ciał występuje jako żelazo, stal, mithril, adamantyt, kobalt, runiczne, smocza stal, astral, Pustka i eternium; konkretne statystyki i właściwości są losowane niezależnie od klasy.",
        "Zręczność z EQ realnie zwiększa szansę na krytyk; inne właściwości mogą wzmacniać obrażenia, obronę, unik, HP albo Manę.",
        "Klasowe EQ ma progi Biegłości 1, 10, 20 i dalej co 10 aż do 400.",
        "Postać może nosić dwa pierścienie i dwa talizmany.",
        "Sprzedawalne nieprzypisane duplikaty można wskazać numerem, np. sprzedaj 2.talizman korzeni.",
    ]
    HELP_TOPICS["atlas"] = [
        "atlas pokazuje gdzie i od jakiego levelu narzędzia odblokowują się ryby, drewno, zioła, rudy i inne surowce.",
        "Przykłady: atlas ryby, atlas drewno, atlas rudy, atlas <nazwa surowca>.",
        "Wpis konkretnego zasobu podaje region/lokację, wymagane narzędzie i minimalny level narzędzia. Szybkość pracy zależy od levelu właściwej profesji.",
    ]
    HELP_TOPICS["gornictwo"] = [
        "Górnictwo ma progresję 1-400; jego level skraca czas kopania do ustalonego minimum. Kilof rozwija się osobno 1-400 i odblokowuje lepsze rudy/żyły oraz bonus urobku.",
        "kop wykonuje pojedyncze wydobycie; kop on i kop off sterują auto-kopaniem.",
        "Kopalnia Głębinowa nie ma końca; ściany mają losową liczbę uderzeń zapisywaną dla postaci. Zasobowa moc głębokości zatrzymuje się na progresji 400.",
        "kop on może wystartować już w ręcznej części Kryształowej Jaskini: automat sam dochodzi w dół do poziomu 1, a potem schodzi po każdym przebiciu ściany.",
        "Rudy progresji 220-400 wymagają jednocześnie odpowiedniego levelu Kilofa i co najmniej odpowiadającego mu poziomu Kopalni Głębinowej.",
        "Po odblokowaniu ruda pozostaje dostępna na wszystkich głębszych piętrach. Starsze rudy stają się rzadsze, ale nie znikają z puli.",
        "atlas rudy pokazuje wymagany level Kilofa i minimalną głębokość dla każdej rudy.",
        "kopalnia / mineinfo pokazuje bieżące piętro, najgłębszy odblokowany poziom, ścianę, auto-kopanie, Górnictwo, Kilof oraz najważniejsze dostępne rudy.",
    ]
    HELP_TOPICS["drwalstwo"] = [
        "Drwalstwo ma progresję 1-400; jego level skraca czas cięcia do ustalonego minimum. Piła rozwija się osobno 1-400 i odblokowuje lepsze drewno oraz bonus urobku.",
        "tnij wykonuje pojedynczą akcję; tnij on i tnij off sterują automatem.",
        "atlas drewno pokazuje wymagany level Piły i miejsca występowania drewna.",
    ]
    HELP_TOPICS["zielarstwo"] = [
        "Zielarstwo ma progresję 1-400; jego level skraca czas zbioru do ustalonego minimum. Sierp rozwija się osobno 1-400 i odblokowuje lepsze zioła oraz bonus urobku.",
        "zbieraj wykonuje pojedynczy zbiór; zbieraj on i zbieraj off sterują automatem.",
        "atlas zioła pokazuje wymagany level Sierpa i miejsca występowania ziół.",
    ]
    HELP_TOPICS["alchemia"] = [
        "Alchemia rozwija się 1-400; jej level skraca czas warzenia do ustalonego minimum i blokuje receptury/zlecenia. Moździerz rozwija się osobno 1-400 i zwiększa Tier/bonus produktu.",
        "alchemia / warz <receptura> tworzy mikstury, jeśli masz wymagany poziom i składniki.",
        "Questy Alchemii u Orina są niezależne; np. Mikstury Many i Mikstury Leczenia mogą być aktywne równocześnie.",
    ]
    HELP_TOPICS["rzemioslo"] = [
        "Crafting metalowy korzysta z Młota Rzemieślniczego 1-400, a jego wymagania i tempo wynikają z profesji Kowalstwo 1-400.",
        "craft / stworz / wytworz <receptura> tworzy przedmiot.",
        "Nie ma trwałości ani zużywania narzędzi.",
    ]
    HELP_TOPICS["receptury"] = [
        "receptury pokazuje dostępne przepisy.",
        "receptury craft, receptury cook, receptury alchemia i receptury jubilerstwo filtrują listę.",
        "Wymagania receptur pokazują level odpowiedniej profesji oraz wymagany Tier właściwego narzędzia. Oba warunki muszą być spełnione.",
    ]
    HELP_TOPICS["charyzma"] = [
        "Charyzma jest szóstą normalną statystyką postaci.",
        "Ma własny niezależny EXP i próg; sprzedaż przyznaje dodatkowy EXP Charyzmy zależny od wartości transakcji.",
        "Wpływa na rabat sklepowy i limit drużyny lidera.",
        "Komendy: charyzma, haryzma, charisma oraz staty info.",
    ]
    HELP_TOPICS["druzyny"] = [
        "załóż drużynę / zaloz druzyne tworzy drużynę. Samo druzyna / party pokazuje jej skład i status osłony.",
        "zaproś <gracz> / zapros <gracz> zaprasza gracza; działa też forma zaproś <gracz> do drużyny oraz druzyna zapros <gracz>.",
        "dołącz / dolacz przyjmuje zaproszenie, odrzuć / odrzuc je odrzuca, a opuść / opusc opuszcza drużynę.",
        "wyrzuć <gracz> / wyrzuc <gracz> usuwa członka. rozwiąż / rozwiaz rozwiązuje drużynę. Te dwie operacje wymagają lidera.",
        "lider <gracz> przekazuje wskazanemu członkowi dowodzenie drużyną.",
        "pc <tekst> to czat drużynowy. wspieraj / assist pomaga członkowi drużyny w jego aktualnej walce.",
        "zasłoń / zaslon albo zasłoń drużynę / zaslon druzyne włącza drużynową osłonę Strażnika. Aktywna klasa Strażnik przejmuje aggro wspólnego przeciwnika od całej drużyny w tej samej lokacji.",
        "zasłoń off / zaslon off wyłącza osłonę. Tank może chronić jeden wspólny cel walki naraz; nie przejmuje zdalnie obrażeń z innych lokacji ani innego równoległego moba.",
        "Guardy, pancerz, redukcja klasowa i Broń Duszy Strażnika działają normalnie na trafienia przejęte przez tankowanie.",
        "Limit drużyny rośnie z Charyzmą lidera.",
    ]
    HELP_TOPICS["zwloki"] = [
        "ciało / zwloki / corpse pokazuje numerowaną listę ciał mobów w aktualnej lokacji.",
        "Przy wielu ciałach użyj selektora 2.cialo / 2.corpse, 3.cialo / 3.corpse itd.",
        "l in corpse / l in 2.corpse / l w 2.cialo pokazuje zawartość bez zabierania.",
        "przeszukaj 2.cialo / loot 2.corpse zabiera całą zawartość konkretnego ciała.",
        "get miecz from 2.corpse / wez miecz z 2.cialo zabiera jeden przedmiot; get all from 2.corpse zabiera wszystko.",
        "Każde ciało przeciwnika może mieć materiałowe EQ dobrane poziomem do siły moba: od żelaza i stali przez mithril i adamantyt aż po eternium. Konkretne statystyki i właściwości części są losowe.",
        "Elity, rzadkie moby i bossowie mogą zostawić dwie części materiałowego EQ, a ich dotychczasowy unikalny loot pozostaje osobno.",
    ]
    HELP_TOPICS["pojemniki"] = [
        "Siatka przechowuje ryby, Sakwa rudy, Stos drewna drewno, a Torba Zielarska zioła.",
        "put / wloz przenosi surowce profesyjne do ich pojemników; take / wyjmij wyciąga zasób.",
        "Szkatułka Rzemieślnicza działa automatycznie: sztabki, deski, materiały craftu i oszlifowane klejnoty jubilerskie wpadają do niej przy zdobyciu i nie wymagają ręcznego przenoszenia.",
        "Receptury automatycznie pobierają materiały ze Szkatułki; sell i sell all nigdy jej nie opróżniają.",
        "Bank Dusz jest osobnym trwałym magazynem konta.",
    ]
    HELP_TOPICS["level"] = [
        "level albo lvl pokazuje Level postaci 1-400, aktualny EXP oraz dokładnie ile EXP brakuje do następnego Levelu.",
        "Level postaci jest osobny od Soul Levelu Broni Duszy; dusza pokazuje progres Broni Duszy.",
    ]
    HELP_TOPICS["xp"] = [
        "xp pokazuje aktualny EXP postaci oraz dokładnie ile brakuje do następnego Levelu postaci.",
        "Na Levelu 400 komenda informuje o osiągniętym maksimum.",
    ]
    HELP_TOPICS["nawigacja_profesje"] = [
        "walk profesje albo prowadz profesje pokazuje wszystkie profesje i miejsca, do których warto iść: mistrzów, sklepy narzędzi, warsztaty i wejścia.",
        "walk profesje <profesja> prowadzi do głównego huba danej profesji, np. walk profesje alchemia.",
        "walk eq pokazuje sklepy z klasowym EQ; walk eq <klasa> prowadzi do właściwego kwatermistrza.",
    ]
    HELP_TOPIC_ALIASES.update({
        "level":"level", "lvl":"level", "xp":"xp",
        "walk profesje":"nawigacja_profesje", "prowadz profesje":"nawigacja_profesje",
        "walk eq":"nawigacja_profesje", "prowadz eq":"nawigacja_profesje",
    })
    HELP_TOPICS["sklepy"] = [
        "shop / sklep / list / lista pokazuje numerowaną ofertę aktualnego sprzedawcy.",
        "shop info <numer> / sklep info <numer> pokazuje pełny opis, statystyki, wymagania, cenę po rabacie i porównanie z założonym EQ przed zakupem.",
        "kup <nazwa> albo kup <numer> kupuje przedmiot; np. kup 9 lub kup 9 3.",
        "sprzedaj <nazwa> sprzedaje dokładnie jedną wolną sztukę przedmiotu z inventory.",
        "EQ możesz wskazać typem zamiast pełnej nazwy: sprzedaj helm, zbroja, rękawice, nogi, buty, pierścień, talizman albo naszyjnik.",
        "Jeśli do typu lub fragmentu pasuje kilka twoich przedmiotów, gra pokazuje numerowaną listę. Potem wpisz sprzedaj <numer>; nic nie jest wybierane losowo.",
        "Założone EQ i Character-Bound są zawsze chronione. Sprzedaż pojedyncza nigdy nie zdejmie ani nie sprzeda założonej sztuki.",
        "sprzedaj inventory sprzedaje hurtowo dozwolone wolne przedmioty. Zasoby profesji sprzedaje się u właściwych fachowców i można używać ich istniejących komend skupu.",
        "Charyzma wpływa na rabat zakupowy i rozwija się również przez sprzedaż.",
    ]
    HELP_TOPICS["gracze"] = [
        "who pokazuje graczy online.",
        "say <tekst> mówi do osób w tej samej lokacji; tell <gracz> <tekst> wysyła wiadomość prywatną.",
        "pc <tekst> wysyła wiadomość do drużyny.",
    ]
    HELP_TOPICS["smierc"] = [
        "Po śmierci postać odradza się w Świątyni Odrodzenia.",
        "Traci 10 procent każdego nominału wspólnego portfela zgodnie z obecną mechaniką śmierci.",
        "Postęp postaci, EQ, questy, Biegłość, Soul i profesje pozostają zapisane.",
    ]
    HELP_TOPICS["rasy"] = [
        "Gra ma 13 ras. Od v0.9.0 każda rasa ma dokładnie 50 bazowych punktów rozdzielonych między Siłę, Zręczność, Kondycję, Inteligencję i Siłę Woli; nie ma rasy z ukrytym większym budżetem startowym.",
        "Rasy różnią się rozkładem tych 50 punktów oraz własnym pasywem, więc nadal mają wyraźne specjalizacje.",
        "Każda z 12 klas dokłada dokładnie 9 własnych punktów startowych; startowa Charyzma bazowa wynosi 10 przed bonusem klasy.",
        "Kreator podaje polecane klasy dla każdej rasy, ale żadna kombinacja rasa-klasa nie jest blokowana.",
        "opis <rasa> pokazuje opis rasy oraz polecane klasy.",
    ]
    HELP_TOPICS["umiejetnosci"] = [
        "Każda z 12 klas ma Biegłość 1-400; istniejące progi odblokowania skilli 1-200 pozostają bez zmian.",
        "Progi umiejętności: 1, 10, 20, 30 i dalej co 10 aż do 400. Każdy próg ma 3 skille/spelle do nauczenia; alternatywy progu współdzielą cooldown wyboru.",
        "skills pokazuje umiejętności aktywnej klasy; kodeksklasowy <klasa> pokazuje pełną progresję.",
        "help <nazwa skilla> albo skill info <nazwa> pokazuje pełną pomoc konkretnej umiejętności.",
        "Soul Level nie odblokowuje skilli klasowych.",
    ]
    HELP_TOPICS["nazwy_skilli"] = [
        "skillnames / nazwyskilli pokazuje nazwy wszystkich skilli/spelli.",
        "help <nazwa skilla> działa dla wszystkich obecnych skilli/spelli, także klas nieaktywnych.",
    ]
    HELP_TOPICS["nauczyciele"] = [
        "teachers / nauczyciele pokazuje nauczycieli klasowych.",
        "Skilla można nauczyć się u nauczyciela właściwej aktywnej klasy po osiągnięciu wymaganej Biegłości.",
        "Koszt nauki może być obniżany przez reputację Gildii klasowej.",
    ]

configure_v0856_help_categories()


def configure_v0917_help():
    HELP_TOPIC_ALIASES.update({
        "przekaz": "przekazywanie_eq", "przekaż": "przekazywanie_eq",
        "daj": "przekazywanie_eq", "give": "przekazywanie_eq",
        "materialy eq": "materialy_eq", "materiały eq": "materialy_eq",
    })
    HELP_TOPICS["przekazywanie_eq"] = [
        "przekaż <gracz> <pełna nazwa EQ> / daj <gracz> <pełna nazwa EQ> przekazuje jedną sztukę wyposażenia.",
        "Odbiorca musi być online i stać w tej samej lokacji.",
        "Założonego EQ nie można przekazać. Najpierw użyj zdejmij <slot>.",
        "Jeśli masz dwie identyczne sztuki, z których jedna jest założona, możesz przekazać tylko wolną sztukę.",
        "Przekazany przedmiot zachowuje dokładnie swoją nazwę, materiał, statystyki, klasę i wymagania. Odbiorca sam decyduje, czy go założyć.",
    ]
    HELP_TOPICS["materialy_eq"] = [
        "Materiałowe EQ występuje jako: Żelazne, Stalowe, Mithrilowe, Adamantytowe, Kobaltowe, Runiczne, ze Smoczej Stali, Astralne, Pustki i Eternium.",
        "Najwyższe materiały po v0.9.17 zdobywa się przede wszystkim w Kryptach, Wieżach, Twierdzy i bojowych Lochach, a nie z przypadkowych zwykłych mobów świata.",
        "Od v0.9.19 zwykła Krypta rozciąga materiały przez pełną progresję 1-400: Żelazo na początku, potem Stal, Mithril, Adamantyt, Kobalt, Runiczny, Smocza Stal, Astral, Pustka i Eternium.",
        "W obrębie jednego materiału istnieją kolejne warianty co 10 Biegłości. Boss daje następny krok +10, zamiast przeskakiwać od razu o cały materiał.",
        "Mityczne Krypty/Wieże zaczynają od wyższych materiałów. Wieża Astralna i Twierdza również mają progresję materiału wraz z piętrem.",
        "Kopalnie pozostają systemem surowców i nie dostały bojowych mobów tylko po to, aby generować EQ.",
    ]
    if "ekwipunek" in HELP_TOPICS:
        HELP_TOPICS["ekwipunek"].extend([
            "Gracz sam wybiera EQ; gra nie zakłada ani nie podmienia najlepszego przedmiotu automatycznie.",
            "przekaż <gracz> <pełna nazwa EQ> pozwala oddać innemu graczowi wolną, niezałożoną sztukę EQ w tej samej lokacji.",
            "Wysokie materiały EQ są głównie nagrodą za Krypty, Wieże, Twierdzę i Lochy; help materiały eq pokazuje progresję.",
        ])

configure_v0917_help()


def configure_v0856_walking_help():
    """v0.8.56: aktualna pomoc ruchu/chodzenia i sprzedawcy Wędki."""
    HELP_TOPIC_ALIASES.update({
        "chodzenie": "nawigacja", "ruch": "nawigacja", "walk movement": "nawigacja",
        "wedka sprzedawca": "wedkarstwo", "wędka sprzedawca": "wedkarstwo",
    })
    HELP_TOPICS["nawigacja"] = [
        "Ruch nie jest natychmiastowym teleportem. Po komendzie kierunku NVDA najpierw mówi, że idziesz, a po krótkim marszu dopiero docierasz do sąsiedniej lokacji.",
        "Kierunki: north/south/east/west/up/down albo skróty n/s/e/w/u/d; działają też polskie nazwy kierunków.",
        "look / l opisuje aktualną lokację; exits mówi dostępne wyjścia; where podaje lokację i strefę.",
        "prowadz <cel> / walk <cel> wykonuje trasę krok po kroku. Do NPC dochodzi dokładnie, a przy zwykłej lokacji ostatni krok wykonujesz sam.",
        "prowadz lista / walk list pokazuje kategorie celów nawigacji.",
        "Nie możesz rozpocząć zwykłego marszu podczas walki realtime; najpierw pokonaj moba albo użyj flee.",
        "Ruch wyłącza aktywne auto-łowienie, auto-kopanie, auto-Drwalstwo i auto-Zielarstwo.",
    ]
    if "podstawy" in HELP_TOPICS:
        HELP_TOPICS["podstawy"].append(
            "Poruszanie jest krokowe: wpisz n/s/e/w/u/d, usłyszysz rozpoczęcie marszu, a potem dotarcie do lokacji. help nawigacja podaje szczegóły."
        )
    if "wedkarstwo" in HELP_TOPICS:
        HELP_TOPICS["wedkarstwo"].append(
            "Podstawową Wędkę kupisz bezpośrednio u Rybaka Borysa na Targu Rybnym; Mistrz Neris uczy dalszego rozwoju Wędkarstwa."
        )

configure_v0856_walking_help()

def configure_v0857_navigation_help():
    """v0.8.57: planowanie trasy i przerywalne prowadzenie pod NVDA."""
    HELP_TOPIC_ALIASES.update({
        "trasa": "nawigacja", "route": "nawigacja", "droga": "nawigacja",
        "prowadz stop": "nawigacja", "prowadz status": "nawigacja",
    })
    HELP_TOPICS["nawigacja"] = [
        "Ruch kierunkowy jest krokowy: NVDA najpierw czyta rozpoczęcie marszu, a po krótkim czasie dotarcie do sąsiedniej lokacji.",
        "Kierunki: north/south/east/west/up/down albo n/s/e/w/u/d; działają też polskie nazwy kierunków.",
        "look / l opisuje bieżącą lokację; exits mówi dostępne wyjścia; exits info dodaje nazwę i strefę za każdym wyjściem; where podaje lokację i strefę.",
        "trasa <cel> / route <cel> planuje drogę bez poruszania postacią. Podaje liczbę przejść, pierwszy krok, skróconą trasę, strefy i szacowany czas.",
        "trasa pełna <cel> czyta każdy krok; trasa krok powtarza najbliższy kierunek do ostatnio zaplanowanego celu.",
        "prowadz <cel> / walk <cel> uruchamia prowadzenie w tle. Do NPC dochodzi dokładnie; przy zwykłej lokacji ostatni krok wykonujesz sam.",
        "Wyjątek dostępności: prowadz kopalnia / walk mine prowadzi bezpośrednio na pierwszy poziom Kopalni Głębinowej, bez ręcznego ostatniego kroku.",
        "prowadz status / walk status podaje cel, pozostałe przejścia i następny krok podczas marszu.",
        "prowadz stop / walk stop natychmiast przerywa automatyczny marsz i zostawia postać w ostatniej osiągniętej lokacji.",
        "Ręczny kierunek lub rozpoczęcie innej aktywności przerywa prowadzenie, aby uniknąć jednoczesnych ruchów.",
        "prowadz lista / walk list pokazuje kategorie celów nawigacji.",
        "Nie możesz rozpocząć ruchu podczas walki realtime; najpierw pokonaj przeciwnika albo użyj flee.",
    ]

configure_v0857_navigation_help()
build_paid_training_guild_expansion()
configure_base_mob_corpse_equipment()
configure_material_corpse_equipment()


# ============================================================
# v0.8.61 - GLOBALNY REBALANS CEN I EKONOMII
# ============================================================
V0861_BASE_SHOP_PRICES_SILVER = {
    "healing_potion": 100,
    "leather_vest": 600,
    "lucky_charm": 750,
    "iron_gauntlets": 900,
    "iron_boots": 900,
    "iron_helmet": 1_200,
    "forge_charm": 1_500,
    "iron_leggings": 1_800,
    "iron_guard": 2_800,
    "fishing_rod": 500,
    "pickaxe": 500,
    "saw": 500,
    "crafting_hammer": 500,
    "chef_knife": 500,
    "herbalist_sickle": 500,
    "alchemy_mortar": 500,
    "jeweler_pliers": 500,
}

V0861_CLASS_TIER_BASE_SILVER = {
    1: 1_000,
    10: 2_500,
    20: 5_000,
    30: 10_000,
    40: 20_000,
    50: 40_000,
    60: 80_000,
    70: 160_000,
    80: 320_000,
    90: 640_000,
    100: 1_250_000,
    110: 2_500_000,
    120: 5_000_000,
    130: 10_000_000,
    140: 20_000_000,
    150: 40_000_000,
    160: 80_000_000,
    170: 160_000_000,
    180: 320_000_000,
    190: 600_000_000,
    200: 900_000_000,
}

# v0.9.12: ceny klasowego EQ 210-400 rosną łagodnie od starego progu 200.
# 200 pozostaje dokładnie 900 000 000 srebra bazowo; każdy kolejny próg
# co 10 Biegłości to +8%, więc EQ 400 jest droższe, ale ekonomia nie eksploduje.
for _mastery in range(210, 401, 10):
    _steps = (_mastery - 200) // 10
    V0861_CLASS_TIER_BASE_SILVER[_mastery] = int(round(900_000_000 * (1.08 ** _steps)))

V0861_CLASS_SLOT_PRICE_FACTOR = {
    "head": 1.00,
    "body": 1.60,
    "hands": 0.85,
    "legs": 1.30,
    "feet": 0.85,
    "charm": 1.10,
    "ring": 1.20,
    "necklace": 1.40,
}

def rebalance_economy_v0861():
    """Ujednolica wszystkie cenniki pod wspólne saldo i nowe nominały."""
    # 1. Podstawowe sklepy i trwałe narzędzia profesji.
    for item_id, price_silver in V0861_BASE_SHOP_PRICES_SILVER.items():
        item = ITEMS.get(item_id)
        if not item:
            continue
        item["price"] = int(price_silver)
        item["currency"] = "silver"

    # 2. Pełne 21 progów klasowego EQ: ceny rosną aż do poziomu mithrilowego.
    for item_id in CLASS_EQUIPMENT_ITEM_IDS:
        item = ITEMS.get(item_id)
        if not item:
            continue
        mastery = max(1, int(item.get("required_mastery", 1) or 1))
        base = V0861_CLASS_TIER_BASE_SILVER.get(mastery)
        if base is None:
            nearest = min(V0861_CLASS_TIER_BASE_SILVER, key=lambda key: abs(key - mastery))
            base = V0861_CLASS_TIER_BASE_SILVER[nearest]
        factor = V0861_CLASS_SLOT_PRICE_FACTOR.get(item.get("slot"), 1.0)
        item["price"] = max(1, int(round(base * factor)))
        item["currency"] = "silver"

    # 3. Skup surowców. Zwykłe srebrne ceny pozostają czytelne,
    #    a drogie surowce w złocie rosną łagodnie. Stary sprzedawalny
    #    mithril nie może dawać 1 000 000 złota za pojedynczy surowiec.
    for item in ITEMS.values():
        old_mithril = int(item.get("sell_mithril", 0) or 0)
        old_gold = int(item.get("sell_gold", 0) or 0)
        if old_mithril > 0:
            # Sprzedawalny przedmiot za dawny 1 mithril daje 100 000 złota,
            # a nie pełny nowy mithril wart 1 000 000 złota.
            item["sell_gold"] = old_gold + old_mithril * 100_000
            item["sell_mithril"] = 0
            continue
        if old_gold > 10:
            if old_gold <= 50:
                new_gold = old_gold * 2
            elif old_gold <= 100:
                new_gold = old_gold * 3
            elif old_gold <= 250:
                new_gold = old_gold * 4
            else:
                new_gold = old_gold * 5
            item["sell_gold"] = int(new_gold)

    # 4. Stare słabe moby nie mogą wypłacać pełnego mithrilu.
    #    Prawdziwy mithril pozostaje u endgame bossów z co najmniej 500k HP.
    for mob_id, mob in MOB_TEMPLATES.items():
        mithril = int(mob.get("mithril", 0) or 0)
        if mithril <= 0:
            continue
        hp = max(1, int(mob.get("max_hp", 1) or 1))
        if hp >= 500_000 or mob_id.startswith("end_") or mob_id.startswith("mythic_"):
            continue
        if hp < 5_000:
            gold_per_legacy_mithril = 250
        elif hp < 25_000:
            gold_per_legacy_mithril = 1_000
        elif hp < 100_000:
            gold_per_legacy_mithril = 5_000
        else:
            gold_per_legacy_mithril = 20_000
        mob["gold"] = int(mob.get("gold", 0) or 0) + mithril * gold_per_legacy_mithril
        mob["mithril"] = 0


rebalance_economy_v0861()


# ============================================================
# v0.8.62 - GLOBALNY REBALANS NAGRÓD QUESTOWYCH
# ============================================================
# Wszystkie nagrody pieniężne są od tej wersji zapisywane wyłącznie jako
# wartość wspólnego salda w najmniejszym nominale (srebro). Złoto i mithril
# pozostają nominałami prezentacji: 1000 srebra = 1 złoto,
# 1 000 000 złota = 1 mithril.
V0862_PROFESSION_QUEST_BASE_SILVER = {
    1: 250,
    5: 400,
    15: 750,
    20: 1_250,
    30: 2_500,
    35: 3_500,
    40: 5_000,
    45: 7_500,
    50: 10_000,
    60: 20_000,
    70: 35_000,
    75: 45_000,
    80: 60_000,
    90: 100_000,
    100: 250_000,
    110: 400_000,
    120: 750_000,
    130: 1_250_000,
    140: 2_000_000,
    150: 3_500_000,
    160: 7_500_000,
    170: 12_500_000,
    180: 25_000_000,
    190: 50_000_000,
    200: 100_000_000,
}
for _level in PROGRESSION_400_LEVELS:
    V0862_PROFESSION_QUEST_BASE_SILVER[_level] = int(
        100_000_000 * (1.0 + 0.75 * ((_level - 200) / 200.0))
    )

V0862_SOUL_TRIAL_REWARD_SILVER = {
    10: 250,
    20: 750,
    25: 1_500,
    35: 3_000,
    45: 6_000,
    60: 15_000,
    70: 30_000,
    80: 50_000,
    90: 80_000,
    100: 150_000,
    110: 300_000,
    120: 600_000,
    130: 1_200_000,
    140: 2_500_000,
    150: 5_000_000,
    160: 10_000_000,
    170: 20_000_000,
    180: 75_000_000,
    200: 500_000_000,
}
for _level in range(210, 401, 10):
    V0862_SOUL_TRIAL_REWARD_SILVER[_level] = int(
        500_000_000 * (1.0 + 0.50 * ((_level - 200) / 200.0))
    )

V0862_FIXED_QUEST_REWARDS_SILVER = {
    # v0.8.73: większa Próba Karpia Rzecznego, 20 sztuk.
    "neris_fish_1": 300,
    # Start i pierwsze okolice.
    "sol_starter_blacksmith_delivery": 75,
    "sol_starter_inn_delivery": 100,
    "sol_starter_guard_delivery": 150,
    "sol_starter_herbalist_delivery": 200,
    "sol_starter_class_teacher": 1_500,
    "temple_rats": 200,
    "goblin_problem": 300,
    "shadow_wolves": 450,
    "bandit_patrol": 1_500,
    "soul_shards": 7_500,
    # Próby profesji wymagające zebrania 30 zasobów.
    "fisher_30_fish": 2_500,
    "herbalist_30_herbs": 2_500,
    "lumberjack_30_wood": 2_500,
    "miner_30_ore": 2_500,
    # Otwarte questy świata bez jawnego poziomu narzędzia/Soul Level.
    "mountain_trail_patrol": 5_000,
    "stolen_mountain_ores": 6_000,
    "troll_shaman_hunt": 12_000,
    "mountain_troll_hunt": 15_000,
    "wild_frontier_hunt": 20_000,
    "high_mountain_patrol": 30_000,
    "deep_troll_clearance": 50_000,
    "troll_king_hunt": 75_000,
    "swamp_purge": 100_000,
    "desert_patrol": 150_000,
}


def v0862_nearest_progression_reward(level):
    level = max(1, int(level or 1))
    keys = sorted(V0862_PROFESSION_QUEST_BASE_SILVER)
    eligible = [key for key in keys if key <= level]
    key = eligible[-1] if eligible else keys[0]
    return V0862_PROFESSION_QUEST_BASE_SILVER[key]


def rebalance_quest_rewards_v0862():
    """Przelicza wszystkie 119 questów na płynną skalę wspólnego salda."""
    for quest_id, quest in QUESTS.items():
        reward = None

        if quest_id in V0862_FIXED_QUEST_REWARDS_SILVER:
            reward = V0862_FIXED_QUEST_REWARDS_SILVER[quest_id]

        soul_level = int(quest.get("required_soul_level", 0) or 0)
        if soul_level:
            reward = V0862_SOUL_TRIAL_REWARD_SILVER.get(
                soul_level,
                v0862_nearest_progression_reward(soul_level),
            )

        tool_level = int(quest.get("min_tool_level", 0) or 0)
        if tool_level:
            reward = v0862_nearest_progression_reward(tool_level)
            kind = quest.get("kind")
            needed = max(1, int(quest.get("needed", 1) or 1))

            # Trudniejsze formy zadania płacą trochę więcej, ale nie tworzą
            # skoków o całe nominały. Liczba wymaganych przedmiotów ma tylko
            # łagodny wpływ, aby powtarzalnych questów nie dało się nadużywać.
            if kind == "craft_set":
                reward = int(reward * 2.5)
            elif kind in ("collect_category", "collect_distinct_category"):
                reward = int(reward * 1.25)
            elif kind == "collect":
                reward = int(reward * 1.10)
            elif kind == "collect_resource":
                reward = int(reward * 1.00)
            elif kind == "kill":
                reward = int(reward * 1.20)

            if needed >= 10:
                reward = int(reward * 1.20)
            elif needed >= 5:
                reward = int(reward * 1.10)

        # Awaryjnie każdy quest, którego nie opisuje jedna z powyższych grup,
        # zachowuje dotychczasową wartość, ale zostaje znormalizowany do
        # jednego salda. W praktyce v0.8.62 obejmuje wprost wszystkie 119.
        if reward is None:
            reward = legacy_currency_to_coins(
                quest.get("reward_silver", 0),
                quest.get("reward_gold", 0),
                quest.get("reward_mithril", 0),
            )

        quest["reward_silver"] = max(0, int(reward))
        quest["reward_gold"] = 0
        quest["reward_mithril"] = 0


rebalance_quest_rewards_v0862()


# v0.8.73: dwa większe questy zbierackie z podniesionymi nagrodami.
if "soul_shards" in QUESTS:
    QUESTS["soul_shards"]["reward_items"] = {"soul_elixir": 2}
if "neris_fish_1" in QUESTS:
    QUESTS["neris_fish_1"]["reward_profession_xp"] = 1200
    QUESTS["neris_fish_1"]["reward_tool_xp"] = 1000


def normalize_profession_requirements_v0866():
    """v0.8.66: bezpośrednie progi questów profesyjnych należą do profesji.

    Historyczne min_tool_level służy wyłącznie do migracji wartości progu.
    Po skopiowaniu próg zostaje usunięty z aktywnych danych questa. Narzędzie
    nadal jest wymagane do wykonania danej akcji i jego level odblokowuje pule
    surowców, ale nie blokuje przyjęcia questa.
    """
    for quest in QUESTS.values():
        tool_type = quest.get("specialist_tool_type")
        profession = (
            quest.get("required_profession")
            or quest.get("reward_profession")
            or profession_for_tool_type(tool_type)
        )
        old_level = int(quest.get("min_tool_level", 0) or 0)
        if profession and old_level:
            quest.setdefault("required_profession", profession)
            quest.setdefault("min_profession_level", old_level)
        if profession:
            quest.pop("min_tool_level", None)


normalize_profession_requirements_v0866()


def normalize_quest_progress_tracking_v0866():
    """v0.8.66: każdy quest zaczyna 0/x i liczy tylko zdarzenia po przyjęciu.

    Zwykłe questy collect, których celem jest wynik receptury, są śledzone
    jako wykonanie craftu. Pozostałe collect rosną dopiero przy nowym
    zdobyciu przedmiotu. Stary zapas nigdy nie daje darmowego postępu.
    """
    crafted_outputs = {
        recipe.get("output")
        for recipes in (CRAFT_RECIPES, ALCHEMY_RECIPES, JEWELCRAFT_RECIPES, COOK_RECIPES)
        for recipe in recipes.values()
        if recipe.get("output")
    }
    for quest in QUESTS.values():
        kind = quest.get("kind")
        if kind == "collect":
            if quest.get("target") in crafted_outputs:
                quest["track_craft_progress"] = True
            quest["event_progress_only"] = True
        elif kind == "collect_resource":
            # Każdy surowcowy quest, także terenowe wyjątki, używa licznika
            # zdarzeń od 0/x zamiast stanu magazynu sprzed przyjęcia.
            quest["track_resource_progress"] = True
            quest["event_progress_only"] = True
        elif kind in (
            "collect_category", "collect_distinct_category", "collect_resource_set",
            "kill", "craft_set", "deliver_npc", "talk_npc", "talk_class_teacher",
            "explore_frontier", "discover_secret", "mini_dungeon", "world_event",
            "legendary_rare", "world_boss",
        ):
            quest["event_progress_only"] = True


normalize_quest_progress_tracking_v0866()


def quest_is_profession_or_crafting_v098(quest):
    """Czy quest należy do ścieżki profesji/rzemiosła i powinien płacić walutą."""
    return bool(
        quest.get("reward_profession")
        or quest.get("reward_tool_type")
        or quest.get("specialist_tool_type")
        or quest.get("required_profession")
        or quest.get("track_craft_progress")
        or quest.get("kind") == "craft_set"
    )


def ensure_profession_quest_currency_v098():
    """v0.9.8: każdy quest profesyjny/rzemieślniczy ma pieniężną wypłatę.

    Istniejące wartości z pełnego rebalance v0.8.62 są autorytatywne i nie są
    zwiększane. Fallback uruchamia się wyłącznie dla definicji z zerową walutą,
    również dla przyszłych questów dopisanych po tej wersji.
    """
    changed = 0
    for quest in QUESTS.values():
        if not quest_is_profession_or_crafting_v098(quest):
            continue
        existing = legacy_currency_to_coins(
            quest.get("reward_silver", 0),
            quest.get("reward_gold", 0),
            quest.get("reward_mithril", 0),
        )
        if existing > 0:
            continue

        level = max(1, int(quest.get("min_profession_level", 1) or 1))
        needed = max(1, int(quest.get("needed", 1) or 1))
        reward = int(v0862_nearest_progression_reward(level))
        kind = quest.get("kind")
        if kind == "craft_set":
            reward = int(reward * 2.5)
        elif kind in ("collect_category", "collect_distinct_category"):
            reward = int(reward * 1.25)
        elif kind == "collect":
            reward = int(reward * 1.10)
        elif kind == "kill":
            reward = int(reward * 1.20)
        if needed >= 10:
            reward = int(reward * 1.20)
        elif needed >= 5:
            reward = int(reward * 1.10)

        quest["reward_silver"] = max(50, reward)
        quest["reward_gold"] = 0
        quest["reward_mithril"] = 0
        changed += 1
    return changed


V098_PROFESSION_QUEST_CURRENCY_REPAIRS = ensure_profession_quest_currency_v098()


def build_independent_specialist_quest_offers():
    """
    v0.8.31: zlecenia profesyjne u jednego specjalisty są niezależne.
    Wymagania poziomu narzędzia/profesji zostają, ale ukończenie poprzedniego
    zlecenia nie jest potrzebne do przyjęcia kolejnego. Fabularne quest_chain
    pozostają nietknięte.
    """
    changed = 0
    for npc in NPCS.values():
        for quest_id in tuple(npc.get("specialist_quests") or ()):
            quest = QUESTS.get(quest_id)
            if not quest:
                continue
            if "requires_quest" in quest:
                quest.pop("requires_quest", None)
                changed += 1
    return changed


INDEPENDENT_SPECIALIST_QUESTS = build_independent_specialist_quest_offers()


# ============================================================
# v0.8.55 - World Stability / topology repairs
# ============================================================
def repair_world_topology_v0855():
    """Naprawia połączenia świata nadpisane przez późniejsze rozszerzenia.

    Kilka builderów poprawnie tworzyło wejścia do nowych terenów, ale kolejne
    rozszerzenia ponownie definiowały słowniki ``exits`` tych samych pokoi.
    W efekcie część świata była odcięta, a Jaskinia Trolli miała jedno wyjście
    prowadzące do nieistniejącej lokacji. Naprawa jest wyłącznie topologiczna
    i nie zmienia danych postaci ani bazy SQLite.
    """
    # Stary, nigdy niezdefiniowany cel mógł spowodować wyjątek przy ruchu.
    if ROOMS.get("troll_cave_3", {}).get("exits", {}).get("south") == "troll_war_camp":
        ROOMS["troll_cave_3"]["exits"].pop("south", None)

    # Pradawny Las: pierwotne wejście ``south`` z Deep Grove zostało zajęte
    # przez Bagna. Zachowujemy oba tereny i dodajemy niezależne zejście.
    if "deep_grove" in ROOMS and profession_dungeon_room_id("ancient_forest", 1) in ROOMS:
        ROOMS["deep_grove"]["exits"]["down"] = profession_dungeon_room_id("ancient_forest", 1)
        if "Wejście do Pradawnego Lasu" not in ROOMS["deep_grove"]["desc"]:
            ROOMS["deep_grove"]["desc"] += " Wejście do Pradawnego Lasu prowadzi w dół, w najgęstszy ostęp."

    # Ogród Alchemika: wschodnie wyjście Zielarki zajęło później laboratorium.
    # Dodajemy osobne północne wejście, nie usuwając laboratorium ani ogrodu ziół.
    if "herbalist_hut" in ROOMS and profession_dungeon_room_id("alchemy_garden", 1) in ROOMS:
        ROOMS["herbalist_hut"]["exits"]["north"] = profession_dungeon_room_id("alchemy_garden", 1)
        if "Ogród Alchemika" not in ROOMS["herbalist_hut"]["desc"]:
            ROOMS["herbalist_hut"]["desc"] += " Na północy znajduje się wejście do Ogrodu Alchemika."

    # Pustynia: północ Ruin Strażnicy została później zajęta przez Ruiny
    # Kultystów. Pustynia pozostaje podłączona osobnym podejściem w górę.
    if "ruined_watchtower" in ROOMS and "dry_canyon" in ROOMS:
        ROOMS["ruined_watchtower"]["exits"]["up"] = "dry_canyon"
        if "Suchy Kanion" not in ROOMS["ruined_watchtower"]["desc"]:
            ROOMS["ruined_watchtower"]["desc"] += " Stroma droga w górę prowadzi do Suchego Kanionu i dalej ku Pustyni."


repair_world_topology_v0855()


def apply_global_mob_hp_multiplier():
    """Zwiększa HP wszystkich mobów i bossów po zbudowaniu całego świata."""
    for template in MOB_TEMPLATES.values():
        base_hp = max(1, int(template.get("max_hp", 1)))
        template["base_max_hp"] = base_hp
        template["max_hp"] = max(
            1,
            int(round(base_hp * GLOBAL_MOB_HP_MULTIPLIER)),
        )

def apply_dungeon_boss_floor_hp():
    """
    Bossowie Krypty i Wieży Astralnej mają dokładnie:
    HP = numer piętra * 1000.
    """
    for floor in CRYPT_BOSS_FLOORS:
        template = MOB_TEMPLATES[f"crypt_boss_{floor}"]
        template["max_hp"] = max(1, int(round(floor * 1000 * crypt_depth_multiplier(floor))))
        template["scaled_boss_hp_rule"] = "floor_x_1000"

    for floor in ASTRAL_BOSS_FLOORS:
        template = MOB_TEMPLATES[f"astral_boss_{floor}"]
        template["max_hp"] = floor * 1000
        template["scaled_boss_hp_rule"] = "floor_x_1000"

    for floor in MYTHIC_BOSS_FLOORS:
        crypt_template = MOB_TEMPLATES[
            f"mythic_crypt_boss_{floor}"
        ]
        crypt_template["max_hp"] = max(1, int(round((300000 + floor * 5000) * crypt_depth_multiplier(floor))))
        crypt_template["scaled_boss_hp_rule"] = (
            "mythic_300k_plus_floor_x_5000"
        )

        astral_template = MOB_TEMPLATES[
            f"mythic_astral_boss_{floor}"
        ]
        astral_template["max_hp"] = 400000 + floor * 6000
        astral_template["scaled_boss_hp_rule"] = (
            "mythic_400k_plus_floor_x_6000"
        )

apply_global_mob_hp_multiplier()
apply_dungeon_boss_floor_hp()
# v0.8.64: materiał ciała musi być liczony z FINALNEGO HP po globalnym
# skalowaniu i regułach bossów, nie z wcześniejszej wartości template.
configure_material_corpse_equipment()

# ============================================================
# v0.9.12 - INFINITE CRYPTS (lazy generation beyond floor 200)
# ============================================================
def _infinite_crypt_economy_floor(floor):
    # Głębia ma zwiększać ryzyko i EXP, nie drukować nieskończonej waluty.
    return min(CRYPT_PREGENERATED_MAX_FLOOR, max(1, int(floor)))

def _configure_dynamic_corpse_material(template):
    base_tier = corpse_material_tier_for_template(template)
    target_mastery = equipment_progression_mastery_for_template_v0919(template)
    tier = corpse_material_tier_for_mastery_v0919(target_mastery)
    if list(CORPSE_MATERIAL_TIER_BY_KEY).index(base_tier["key"]) > list(CORPSE_MATERIAL_TIER_BY_KEY).index(tier["key"]):
        tier = base_tier
    candidates = [
        item_id
        for item_id in CORPSE_MATERIAL_ITEM_IDS[tier["key"]]
        if int(ITEMS[item_id].get("required_mastery", 1) or 1) <= target_mastery
    ]
    if not candidates:
        candidates = [
            min(
                CORPSE_MATERIAL_ITEM_IDS[tier["key"]],
                key=lambda item_id: int(ITEMS[item_id].get("required_mastery", 1) or 1),
            )
        ]
    template["corpse_material_tier"] = tier["key"]
    template["corpse_material_pool"] = list(candidates)
    template["corpse_material_mastery_cap"] = target_mastery
    special = bool(template.get("crypt_boss") or template.get("mythic_crypt_boss"))
    template["corpse_material_guaranteed"] = 2 if special else 1

def _dynamic_regular_mob_pack(room_id, base_id, template, names, floor, floor_word="poziom"):
    spawns = [(room_id, base_id)]
    names = tuple(names or ())
    base_index = (max(1, int(floor)) - 1) % len(names) if names else 0
    for offset in (1, 2):
        variant_id = f"{base_id}_v{offset + 1}"
        variant = dict(template)
        if isinstance(template.get("drops"), dict):
            variant["drops"] = dict(template["drops"])
        if isinstance(template.get("corpse_equipment_pool"), list):
            variant["corpse_equipment_pool"] = list(template["corpse_equipment_pool"])
        if names:
            variant["name"] = f"{names[(base_index + offset) % len(names)]}, {floor_word} {floor}"
        else:
            variant["name"] = f"{template.get('name', 'Przeciwnik')} — wariant {offset + 1}"
        if offset == 1:
            variant["max_hp"] = max(1, int(round(int(template.get("max_hp", 1)) * 1.06)))
            variant["damage_type"] = "magic" if template.get("damage_type") == "physical" else "physical"
        else:
            variant["damage"] = max(1, int(round(int(template.get("damage", 1)) * 1.08)))
        variant["template_id"] = variant_id
        variant["dense_dungeon_variant"] = True
        MOB_TEMPLATES[variant_id] = variant
        _configure_dynamic_corpse_material(variant)
        spawns.append((room_id, variant_id))
    return spawns

def _ensure_dynamic_boss_key(kind, floor):
    key_id = boss_floor_key_id(kind, floor)
    if key_id not in ITEMS:
        ITEMS[key_id] = {
            "name": f"Klucz Bossa {BOSS_CHEST_KIND_NAMES[kind]} {floor}",
            "type": "quest",
            "price": None,
            "boss_chest_key": True,
            "boss_chest_kind": kind,
            "boss_chest_floor": int(floor),
            "desc": (
                f"Jednorazowy klucz z ciała bossa. Otwiera skrzynię na "
                f"piętrze {floor} w: {BOSS_CHEST_KIND_NAMES[kind]}."
            ),
        }
    return key_id

MILESTONE_BOSS_NAMES = {
    "crypt": {
        50: "Strażnik Pięćdziesięciu Grobów",
        100: "Arcywładca Stu Krypt",
    },
    "mythic_crypt": {
        50: "Mityczny Egzekutor Pięćdziesięciu Dusz",
        100: "Mityczny Imperator Stu Otchłani",
    },
    "astral": {
        50: "Strażnik Pięćdziesięciu Gwiazd",
        100: "Imperator Stu Gwiazd",
    },
    "mythic_astral": {
        50: "Mityczny Herold Pięćdziesięciu Sfer",
        100: "Mityczny Suweren Stu Sfer",
    },
    "giant": {
        50: "Król Pięćdziesięciu Olbrzymów",
        100: "Cesarz Stu Tytanów",
    },
}


def milestone_boss_tier(floor):
    floor = max(1, int(floor))
    if floor % 100 == 0:
        return 100
    if floor % 50 == 0:
        return 50
    return 0


def milestone_boss_name(kind, floor, default_name):
    marker = milestone_boss_tier(floor)
    if not marker:
        return default_name
    base = MILESTONE_BOSS_NAMES.get(str(kind), {}).get(marker)
    if not base:
        return default_name
    cycle = max(1, int(floor) // marker)
    return f"{base} — próg {floor}, cykl {cycle}"


def apply_milestone_boss_identity(template, kind, floor):
    marker = milestone_boss_tier(floor)
    if not marker:
        return template
    template["name"] = milestone_boss_name(kind, floor, template.get("name", "Boss"))
    template["milestone_boss"] = True
    template["milestone_boss_50"] = True
    template["milestone_boss_100"] = (marker == 100)
    template["milestone_dungeon_kind"] = str(kind)
    template["milestone_floor"] = int(floor)
    # Jeśli katalog bossów został już zbudowany, dopisujemy lazy-generated bossa.
    catalog = globals().get("BOSS_COLLECTION_CATALOG")
    template_id = template.get("template_id")
    if isinstance(catalog, dict) and template_id:
        catalog[str(template_id)] = template["name"]
    return template


def boss_floor_identity(template):
    checks = (
        ("crypt_boss", "crypt_floor", "crypt"),
        ("mythic_crypt_boss", "mythic_crypt_floor", "mythic_crypt"),
        ("astral_boss", "astral_floor", "astral"),
        ("mythic_astral_boss", "mythic_astral_floor", "mythic_astral"),
        ("giant_fortress_boss", "giant_fortress_floor", "giant"),
    )
    for boss_flag, floor_field, kind in checks:
        if template.get(boss_flag):
            floor = int(template.get(floor_field, 0) or 0)
            if floor >= 10 and floor % 10 == 0:
                return kind, floor
    return None, 0



# ============================================================
# v0.9.21 - INSTANCE MAPS / SECRETS / CHECKPOINT MEMORY
# ============================================================
INSTANCE_MAP_DEFS = {
    "crypt": {"label": "Krypta", "min_floor": 1},
    "mythic_crypt": {"label": "Mityczna Krypta", "min_floor": 1},
    "astral": {"label": "Wieża Astralna", "min_floor": ASTRAL_MIN_FLOOR},
    "mythic_astral": {"label": "Mityczna Wieża Astralna", "min_floor": 1},
    "giant": {"label": "Twierdza Gigantów", "min_floor": 1},
    "mine": {"label": "Kopalnia Głębinowa", "min_floor": 1, "passive_checkpoints": True},
    "crystal_mine": {"label": "Kryształowe Groty", "min_floor": 1, "passive_checkpoints": True},
    "sunken_grotto": {"label": "Zatopiona Grota", "min_floor": 1, "passive_checkpoints": True},
    "ancient_forest": {"label": "Pradawny Las", "min_floor": 1, "passive_checkpoints": True},
    "alchemy_garden": {"label": "Ogród Alchemika", "min_floor": 1, "passive_checkpoints": True},
}
INSTANCE_KIND_ALIASES = {
    "krypta": "crypt", "crypt": "crypt",
    "mitycznakrypta": "mythic_crypt", "mythiccrypt": "mythic_crypt",
    "wieza": "astral", "wiezaastralna": "astral", "astral": "astral", "astraltower": "astral",
    "mitycznawieza": "mythic_astral", "mitycznawiezaastralna": "mythic_astral", "mythicastral": "mythic_astral",
    "twierdza": "giant", "twierdzagigantow": "giant", "giant": "giant", "giantfortress": "giant",
    "kopalnia": "mine", "kopalniaglebinowa": "mine", "deepmine": "mine",
    "kopalniakrysztalow": "mine", "crystalmine": "mine",
    "krysztalowegroty": "crystal_mine", "crystalgrottos": "crystal_mine",
    "zatopionagrota": "sunken_grotto", "sunkengrotto": "sunken_grotto",
    "pradawnylas": "ancient_forest", "ancientforest": "ancient_forest",
    "ogrodalchemika": "alchemy_garden", "alchemygarden": "alchemy_garden",
}
INSTANCE_SECRET_OFFSETS = (16, 36, 66, 86)
INSTANCE_SECRET_TITLES = (
    "Ukryty zapis", "Zapomniana nisza", "Ślad dawnego przejścia", "Sekretna inskrypcja"
)

def instance_room_identity(room_id):
    room_id = str(room_id or "")
    floor = crypt_floor_number(room_id)
    if floor is not None:
        return "crypt", int(floor)
    floor = mythic_crypt_floor_number(room_id)
    if floor is not None:
        return "mythic_crypt", int(floor)
    floor = astral_floor_number(room_id)
    if floor is not None:
        return "astral", int(floor)
    floor = mythic_astral_floor_number(room_id)
    if floor is not None:
        return "mythic_astral", int(floor)
    floor = giant_fortress_floor_number(room_id)
    if floor is not None:
        return "giant", int(floor)
    floor = mine_floor_number(room_id)
    if floor is not None:
        return "mine", int(floor)
    dungeon, floor = profession_dungeon_floor(room_id)
    if dungeon and floor is not None:
        return str(dungeon), int(floor)
    return None, None

def instance_sector_bounds(kind, floor):
    info = INSTANCE_MAP_DEFS[str(kind)]
    minimum = int(info.get("min_floor", 1))
    floor = max(minimum, int(floor))
    start = minimum + ((floor - minimum) // 100) * 100
    return start, start + 99

def instance_secret_floors(kind, floor):
    start, end = instance_sector_bounds(kind, floor)
    return tuple(start + offset for offset in INSTANCE_SECRET_OFFSETS if start + offset <= end)

def instance_secret_index(kind, floor):
    floors = instance_secret_floors(kind, floor)
    try:
        return floors.index(int(floor))
    except ValueError:
        return None

def instance_secret_name(kind, floor):
    index = instance_secret_index(kind, floor)
    if index is None:
        return None
    label = INSTANCE_MAP_DEFS[str(kind)]["label"]
    start, end = instance_sector_bounds(kind, floor)
    return f"{INSTANCE_SECRET_TITLES[index]} — {label}, sektor {start}-{end}, piętro {int(floor)}"

def normalize_instance_kind(value):
    key = normalize_lookup_text(str(value or "")).replace(" ", "")
    return INSTANCE_KIND_ALIASES.get(key)

def legendary_loot_mastery_for_floor(floor):
    floor = max(1, int(floor))
    return min(400, max(50, (floor // 50) * 50))


def _infinite_crypt_boss_profile(floor):
    cycle = (110, 120, 130, 140, 150, 160, 170, 180, 190, 200)
    source = cycle[((int(floor) // 10) - 21) % len(cycle)]
    return (
        milestone_boss_name("crypt", floor, f"Władca Nieskończonej Krypty, piętro {floor}"),
        CRYPT_BOSS_MECHANICS[source],
        CRYPT_BOSS_MECHANIC_TEXT[source],
    )

def _infinite_mythic_boss_profile(floor):
    cycle = ("two_hundred_lord", "void_regen", "astral_reaper", "phantom_emperor", "final_guardian")
    mechanic = cycle[((int(floor) // 10) - 21) % len(cycle)]
    text = {
        "two_hundred_lord": "Mityczna Bariera, druga faza i silny magiczny kontratak co trzecią odpowiedź.",
        "void_regen": "Co czwarty kontratak regeneruje część maksymalnego HP.",
        "astral_reaper": "Boss zmienia fazę fizyczną i magiczną i okresowo wzmacnia cios.",
        "phantom_emperor": "Boss ma Widmowy Unik i okresowo wzmacnia magię.",
        "final_guardian": "Poniżej połowy HP boss staje się znacznie bardziej niebezpieczny.",
    }[mechanic]
    return milestone_boss_name("mythic_crypt", floor, f"Mityczny Władca Nieskończonej Krypty, piętro {floor}"), mechanic, text

def create_infinite_crypt_floor_definition(floor, mythic=False):
    floor = max(1, int(floor))
    mult = crypt_depth_multiplier(floor)
    econ = _infinite_crypt_economy_floor(floor)
    # EQ rośnie do progresji 400, potem ma twardy cap mimo nieskończonej Krypty.
    tier = min(40, max(1, (floor - 1) // 10 + 1))
    if mythic:
        tier = min(40, max(20, 20 + (floor - 1) // 10))
    gear = [f"crypt_t{tier}_{slot}" for slot in CLASS_EQUIPMENT_SLOT_DEFS]
    if mythic:
        room_id = mythic_crypt_floor_id(floor)
        exits = {
            "up": "mythic_crypt_gate" if floor == 1 else mythic_crypt_floor_id(floor - 1),
            "down": mythic_crypt_floor_id(floor + 1),
        }
        note = " Przy pierwszym przejściu mityczny boss blokuje zejście do chwili pokonania." if is_mythic_crypt_boss_floor(floor) else ""
        ROOMS[room_id] = {
            "zone": "Mityczna Krypta",
            "name": f"Mityczna Krypta, piętro {floor}",
            "desc": f"Mityczne piętro {floor}. Próg trudności {crypt_depth_step(floor)}.{note}",
            "exits": exits,
            "procedural_infinite": True,
        }
        regular_id = f"mythic_crypt_mob_{floor}"
        base_hp = max(1, int(round((4000 + floor * 100) * mult)))
        template = {
            "name": f"Mityczny Strażnik Głębi, piętro {floor}",
            "max_hp": max(1, int(round(base_hp * GLOBAL_MOB_HP_MULTIPLIER))),
            "base_max_hp": base_hp,
            "damage": max(1, int(round((120 + floor) * mult))),
            "damage_type": "magic" if floor % 2 else "physical",
            "silver": 800 + econ * 8,
            "gold": 5 + econ // 20,
            "mithril": 0,
            "stat_reward": max(1, int(round((800 + floor * 5) * mult))),
            "class_xp_reward": max(1, int(round((20000 + floor * 300) * mult))),
            "soul_reward": max(1, int(round((4000 + floor * 25) * mult))),
            "drops": {"soul_shard": 0.55},
            "quest_target": None,
            "mythic_crypt_floor": floor,
            "corpse_equipment_pool": list(gear),
            "corpse_equipment_guaranteed": 1,
        }
        MOB_TEMPLATES[regular_id] = template
        _configure_dynamic_corpse_material(template)
        spawns = _dynamic_regular_mob_pack(
            room_id, regular_id, template, MYTHIC_CRYPT_REGULAR_NAMES, floor, "piętro"
        )
        if is_mythic_crypt_boss_floor(floor):
            boss_id = f"mythic_crypt_boss_{floor}"
            bname, mechanic, mechanic_text = _infinite_mythic_boss_profile(floor)
            boss = {
                "name": bname,
                "max_hp": max(1, int(round((300000 + floor * 5000) * mult))),
                "base_max_hp": max(1, int(round((300000 + floor * 5000) * mult / GLOBAL_MOB_HP_MULTIPLIER))),
                "damage": max(1, int(round((240 + floor * 2) * mult))),
                "damage_type": "magic" if floor % 20 else "physical",
                "silver": 8000 + econ * 40,
                "gold": 60 + econ // 5,
                "mithril": 1,
                "stat_reward": max(1, int(round((3000 + floor * 12) * mult))),
                "class_xp_reward": max(1, int(round((60000 + floor * 700) * mult))),
                "soul_reward": max(1, int(round((9000 + floor * 50) * mult))),
                "drops": {"soul_shard": 1.0, "soul_elixir": 0.70},
                "quest_target": None,
                "mythic_crypt_floor": floor,
                "mythic_crypt_boss": True,
                "boss_mechanic": mechanic,
                "boss_mechanic_text": mechanic_text,
                "corpse_equipment_pool": list(gear),
                "corpse_equipment_guaranteed": 3,
            }
            boss["template_id"] = boss_id
            apply_milestone_boss_identity(boss, "mythic_crypt", floor)
            MOB_TEMPLATES[boss_id] = boss
            _configure_dynamic_corpse_material(boss)
            _ensure_dynamic_boss_key("mythic_crypt", floor)
            spawns.append((room_id, boss_id))
        return room_id, spawns

    room_id = crypt_floor_id(floor)
    exits = {
        "up": "crypt_hall" if floor == 1 else crypt_floor_id(floor - 1),
        "down": crypt_floor_id(floor + 1),
    }
    note = " Przy pierwszym przejściu boss tego progu blokuje zejście do chwili pokonania." if is_crypt_boss_floor(floor) else ""
    ROOMS[room_id] = {
        "zone": "Krypta Nieskończona",
        "name": f"Krypta, piętro {floor}",
        "desc": f"Piętro {floor}. Próg trudności {crypt_depth_step(floor)}.{note}",
        "exits": exits,
        "procedural_infinite": True,
    }
    regular_id = f"crypt_floor_mob_{floor}"
    base_hp = max(1, int(round((70 + floor * 9) * mult)))
    template = {
        "name": f"{CRYPT_REGULAR_NAMES[(floor - 1) % len(CRYPT_REGULAR_NAMES)]}, piętro {floor}",
        "max_hp": max(1, int(round(base_hp * GLOBAL_MOB_HP_MULTIPLIER))),
        "base_max_hp": base_hp,
        "damage": max(1, int(round((6 + floor // 3) * mult))),
        "damage_type": "magic" if (floor % 3 == 0 or floor % 4 == 0) else "physical",
        "silver": 8 + econ,
        "gold": 0,
        "mithril": 0,
        "stat_reward": max(1, int(round((20 + floor * 2) * mult))),
        "class_xp_reward": max(1, int(round((450 + floor * 60) * mult))),
        "soul_reward": max(1, int(round((100 + floor * 10) * mult))),
        "drops": {"soul_shard": min(0.30, 0.08 + econ * 0.002)},
        "quest_target": None,
        "crypt_floor": floor,
        "corpse_equipment_pool": gear,
        "corpse_equipment_guaranteed": 1,
    }
    MOB_TEMPLATES[regular_id] = template
    _configure_dynamic_corpse_material(template)
    spawns = _dynamic_regular_mob_pack(
        room_id, regular_id, template, CRYPT_REGULAR_NAMES, floor, "piętro"
    )
    if is_crypt_boss_floor(floor):
        boss_id = f"crypt_boss_{floor}"
        bname, mechanic, mechanic_text = _infinite_crypt_boss_profile(floor)
        boss = {
            "name": bname,
            "max_hp": max(1, int(round(floor * 1000 * mult))),
            "base_max_hp": max(1, int(round(floor * 1000 * mult / GLOBAL_MOB_HP_MULTIPLIER))),
            "damage": max(1, int(round((16 + floor // 2) * mult))),
            "damage_type": "magic" if floor % 20 == 0 else "physical",
            "silver": 300 + econ * 12,
            "gold": 0,
            "mithril": 0,
            "stat_reward": max(1, int(round((350 + floor * 6) * mult))),
            "class_xp_reward": max(1, int(round((3000 + floor * 160) * mult))),
            "soul_reward": max(1, int(round((600 + floor * 20) * mult))),
            "drops": {"soul_shard": 1.0, "soul_elixir": min(0.50, 0.15 + econ * 0.003)},
            "quest_target": None,
            "crypt_floor": floor,
            "crypt_boss": True,
            "boss_mechanic": mechanic,
            "boss_mechanic_text": mechanic_text,
            "corpse_equipment_pool": list(gear),
            "corpse_equipment_guaranteed": 3,
        }
        boss["template_id"] = boss_id
        apply_milestone_boss_identity(boss, "crypt", floor)
        MOB_TEMPLATES[boss_id] = boss
        _configure_dynamic_corpse_material(boss)
        _ensure_dynamic_boss_key("crypt", floor)
        spawns.append((room_id, boss_id))
    return room_id, spawns

# ============================================================
# v0.9.13 - INFINITE DUNGEONS & TOWERS (lazy continuation)
# ============================================================
INFINITE_DUNGEON_STEP_RATE = 0.025

# v0.9.14: proceduralna część nie jest już tylko ciągiem identycznych pokoi.
# Motyw piętra zmienia opis oraz lekko profil HP/obrażeń/EXP. Mnożniki są
# stałe i cykliczne, więc głębokość nie tworzy nowego nieskończonego power creepu.
INFINITE_COMBAT_FLOOR_THEMES = {
    "astral": (
        {"label": "Rezonans Gwiezdny", "desc": "astralne echo wzmacnia magię przeciwników", "hp": 1.00, "damage": 1.06, "xp": 1.05, "damage_type": "magic"},
        {"label": "Galeria Pękniętych Zwierciadeł", "desc": "odbicia wydłużają walkę i wzmacniają strażników", "hp": 1.10, "damage": 1.00, "xp": 1.06, "damage_type": None},
        {"label": "Kanał Gwiezdnego Prądu", "desc": "przeciwnicy uderzają szybciej i mocniej", "hp": 0.97, "damage": 1.12, "xp": 1.08, "damage_type": "magic"},
        {"label": "Krąg Astralnej Straży", "desc": "warstwa obronna wzmacnia cały garnizon", "hp": 1.13, "damage": 1.07, "xp": 1.10, "damage_type": None},
        {"label": "Próba Nieskończonego Astralu", "desc": "na piętrze czeka dodatkowy strażnik próby", "hp": 1.08, "damage": 1.10, "xp": 1.12, "damage_type": None},
    ),
    "mythic_astral": (
        {"label": "Mityczny Rezonans", "desc": "warstwa astralna pulsuje niestabilną magią", "hp": 1.05, "damage": 1.08, "xp": 1.06, "damage_type": "magic"},
        {"label": "Sala Wiecznych Odbić", "desc": "mityczne odbicia wzmacniają wytrzymałość strażników", "hp": 1.12, "damage": 1.03, "xp": 1.08, "damage_type": None},
        {"label": "Pęknięcie Pustki", "desc": "niestabilna energia zwiększa obrażenia", "hp": 1.00, "damage": 1.14, "xp": 1.10, "damage_type": "magic"},
        {"label": "Mityczny Bastion", "desc": "piętro jest silniej bronione niż zwykły odcinek", "hp": 1.15, "damage": 1.08, "xp": 1.11, "damage_type": None},
        {"label": "Próba Mitycznego Suwerena", "desc": "na piętrze pojawia się dodatkowy mityczny strażnik próby", "hp": 1.10, "damage": 1.12, "xp": 1.14, "damage_type": None},
    ),
    "giant": (
        {"label": "Kamienny Garnizon", "desc": "ściany i pancerze wzmacniają wytrzymałość gigantów", "hp": 1.12, "damage": 1.00, "xp": 1.06, "damage_type": "physical"},
        {"label": "Sala Miotaczy", "desc": "garnizon skupia się na ciężkich uderzeniach", "hp": 1.00, "damage": 1.10, "xp": 1.07, "damage_type": "physical"},
        {"label": "Cyklopi Runiczni", "desc": "runiczna energia przeplata obrażenia fizyczne i magiczne", "hp": 1.06, "damage": 1.08, "xp": 1.09, "damage_type": "magic"},
        {"label": "Królewski Bastion", "desc": "elitarna straż otrzymuje dodatkową wytrzymałość", "hp": 1.15, "damage": 1.06, "xp": 1.10, "damage_type": None},
        {"label": "Próba Giganta", "desc": "na piętrze czeka dodatkowy czempion twierdzy", "hp": 1.10, "damage": 1.10, "xp": 1.12, "damage_type": None},
    ),
}

def infinite_combat_floor_theme(kind, floor):
    themes = INFINITE_COMBAT_FLOOR_THEMES[kind]
    # Układ powtarza się co 5 pięter i pozostaje w pełni deterministyczny.
    return themes[(max(1, int(floor)) - 1) % len(themes)]

def _apply_infinite_combat_theme(template, theme):
    hp_mult = float(theme.get("hp", 1.0))
    damage_mult = float(theme.get("damage", 1.0))
    xp_mult = float(theme.get("xp", 1.0))
    template["max_hp"] = max(1, int(round(int(template["max_hp"]) * hp_mult)))
    if "base_max_hp" in template:
        template["base_max_hp"] = max(1, int(round(int(template["base_max_hp"]) * hp_mult)))
    template["damage"] = max(1, int(round(int(template["damage"]) * damage_mult)))
    for key in ("stat_reward", "class_xp_reward", "soul_reward"):
        if key in template:
            template[key] = max(1, int(round(int(template[key]) * xp_mult)))
    if theme.get("damage_type"):
        template["damage_type"] = theme["damage_type"]
    template["infinite_floor_theme"] = theme["label"]
    return template

def _infinite_challenge_template(base_template, kind, floor):
    """Dodatkowy mini-boss na co piątym proceduralnym piętrze bez bossa głównego."""
    challenge = dict(base_template)
    challenge["name"] = f"Czempion Próby: {base_template['name']}"
    challenge["max_hp"] = max(1, int(round(int(base_template["max_hp"]) * 2.35)))
    if "base_max_hp" in challenge:
        challenge["base_max_hp"] = max(1, int(round(int(base_template["base_max_hp"]) * 2.35)))
    challenge["damage"] = max(1, int(round(int(base_template["damage"]) * 1.28)))
    challenge["stat_reward"] = max(1, int(round(int(base_template.get("stat_reward", 1)) * 1.65)))
    challenge["class_xp_reward"] = max(1, int(round(int(base_template.get("class_xp_reward", 1)) * 1.80)))
    challenge["soul_reward"] = max(1, int(round(int(base_template.get("soul_reward", 1)) * 1.80)))
    challenge["mini_boss"] = True
    challenge["elite_eligible"] = False
    challenge["respawn_seconds"] = 180
    challenge["infinite_challenge"] = True
    challenge["elite_base_template"] = base_template.get("template_id")
    drops = dict(base_template.get("drops") or {})
    drops["soul_shard"] = max(0.55, float(drops.get("soul_shard", 0.0)))
    challenge["drops"] = drops
    challenge["corpse_equipment_guaranteed"] = max(2, int(base_template.get("corpse_equipment_guaranteed", 1)))
    return challenge

INFINITE_GATHER_FEATURE_LABELS = {
    "deep_mine": ("Rezonans Skały", "Bogata Komora", "Węzeł Głębinowy"),
    "crystal_mine": ("Rezonans Kryształów", "Komora Echa Kryształów", "Węzeł Energii Kryształowej"),
    "sunken_grotto": ("Prąd Obfitości", "Ławica Głębinowa", "Węzeł Oceaniczny"),
    "ancient_forest": ("Echo Korzeni", "Gęsty Ostęp", "Węzeł Pradawnych Drzew"),
    "alchemy_garden": ("Alchemiczny Rezonans", "Ogród Obfitości", "Węzeł Esencji"),
}

def infinite_gathering_floor_feature(kind, floor, handmade_max):
    """Stałe bonusowe sektory; bonus nie rośnie wraz z nieskończoną głębokością."""
    floor = max(1, int(floor))
    if floor <= int(handmade_max):
        return {"label": "", "desc": "", "quantity_bonus": 0, "xp_mult": 1.0}
    labels = INFINITE_GATHER_FEATURE_LABELS[kind]
    if floor % 10 == 0:
        return {"label": labels[2], "desc": "mistrzowski sektor: +2 do bazowego zbioru i +25 procent XP profesji/narzędzia", "quantity_bonus": 2, "xp_mult": 1.25}
    if floor % 5 == 0:
        return {"label": labels[1], "desc": "bogaty sektor: +1 do bazowego zbioru i +15 procent XP profesji/narzędzia", "quantity_bonus": 1, "xp_mult": 1.15}
    if floor % 3 == 0:
        return {"label": labels[0], "desc": "rezonujący sektor: +10 procent XP profesji/narzędzia", "quantity_bonus": 0, "xp_mult": 1.10}
    return {"label": "", "desc": "", "quantity_bonus": 0, "xp_mult": 1.0}

def infinite_continuation_multiplier(floor, handmade_max):
    """Łagodny wzrost co 10 pięter po końcu ręcznie zaprojektowanej części."""
    floor = max(1, int(floor))
    handmade_max = max(0, int(handmade_max))
    extra_tens = max(0, (floor - handmade_max) // 10)
    return 1.0 + INFINITE_DUNGEON_STEP_RATE * extra_tens

def _capped_dungeon_economy_floor(floor):
    # Waluta, surowce i gear zatrzymują ekonomiczną moc na progresji 400.
    return min(400, max(1, int(floor)))

def _dynamic_astral_boss_profile(floor):
    source_floors = tuple(sorted(ASTRAL_BOSS_NAMES))
    source = source_floors[((int(floor) // 10) - 1) % len(source_floors)]
    return (
        milestone_boss_name("astral", floor, f"Władca Nieskończonej Wieży Astralnej, poziom {floor}"),
        ASTRAL_BOSS_MECHANICS[source],
        ASTRAL_BOSS_MECHANIC_TEXT[source],
    )

def _dynamic_mythic_astral_boss_profile(floor):
    source_floors = tuple(sorted(ASTRAL_BOSS_MECHANICS))
    source = source_floors[((int(floor) // 10) - 1) % len(source_floors)]
    return (
        milestone_boss_name("mythic_astral", floor, f"Mityczny Suweren Nieskończonej Wieży, poziom {floor}"),
        ASTRAL_BOSS_MECHANICS[source],
        ASTRAL_BOSS_MECHANIC_TEXT[source],
    )

def _dynamic_giant_boss_profile(floor):
    source_floors = tuple(sorted(GIANT_FORTRESS_BOSS_NAMES))
    source = source_floors[((int(floor) // 10) - 1) % len(source_floors)]
    return (
        milestone_boss_name("giant", floor, f"Władca Nieskończonej Twierdzy, poziom {floor}"),
        GIANT_FORTRESS_BOSS_MECHANICS[source],
        {
            10: "Co trzecią odpowiedź używa Miażdżenia Giganta.",
            20: "Co trzecią odpowiedź wyzwala magiczny Promień Cyklopa.",
            30: "Co czwartą odpowiedź rozpoczyna Burzę Głazów.",
            40: "Zmienia typ obrażeń i co trzecią odpowiedź przywołuje Grom Gigantów.",
            50: "Poniżej połowy HP wchodzi w królewską furię; co trzecią odpowiedź używa Królewskiego Trzęsienia.",
        }[source],
    )

def create_infinite_astral_floor_definition(floor, mythic=False):
    floor = max(1, int(floor))
    if mythic:
        room_id = mythic_astral_floor_id(floor)
        mult = infinite_continuation_multiplier(floor, MYTHIC_MAX_FLOOR)
        econ = _capped_dungeon_economy_floor(floor)
        theme = infinite_combat_floor_theme("mythic_astral", floor)
        exits = {
            "down": "mythic_astral_gate" if floor == 1 else mythic_astral_floor_id(floor - 1),
            "up": mythic_astral_floor_id(floor + 1),
        }
        note = " Przy pierwszym przejściu mityczny boss blokuje drogę w górę do chwili pokonania." if is_mythic_astral_boss_floor(floor) else ""
        ROOMS[room_id] = {
            "zone": "Mityczna Wieża Astralna",
            "name": f"Mityczna Wieża Astralna, poziom {floor}",
            "desc": (
                f"Mityczny poziom {floor}. Wieża ciągnie się dalej bez końca. "
                f"Próg głębi {max(0, (floor - 1) // 10)}. "
                f"Motyw piętra: {theme['label']} — {theme['desc']}.{note}"
            ),
            "exits": exits,
            "procedural_infinite": True,
        }
        regular_id = f"mythic_astral_mob_{floor}"
        base_hp = max(1, int(round((5000 + floor * 120) * mult)))
        template = {
            "name": f"Mityczny Strażnik Nieskończonego Astralu, poziom {floor}",
            "max_hp": max(1, int(round(base_hp * GLOBAL_MOB_HP_MULTIPLIER))),
            "base_max_hp": base_hp,
            "damage": max(1, int(round((145 + floor) * mult))),
            "damage_type": "magic" if floor % 2 else "physical",
            "silver": 1000 + econ * 10,
            "gold": 7 + econ // 18,
            "mithril": 0,
            "stat_reward": max(1, int(round((950 + floor * 6) * mult))),
            "class_xp_reward": max(1, int(round((25000 + floor * 350) * mult))),
            "soul_reward": max(1, int(round((5000 + floor * 30) * mult))),
            "drops": {"soul_shard": 0.65},
            "quest_target": None,
            "mythic_astral_floor": floor,
            "corpse_equipment_pool": [
                f"astral_t11_{slot}"
                for slot in CLASS_EQUIPMENT_SLOT_DEFS
            ],
            "corpse_equipment_guaranteed": 1,
        }
        template["template_id"] = regular_id
        _apply_infinite_combat_theme(template, theme)
        MOB_TEMPLATES[regular_id] = template
        _configure_dynamic_corpse_material(template)
        spawns = _dynamic_regular_mob_pack(
            room_id, regular_id, template, MYTHIC_ASTRAL_REGULAR_NAMES, floor, "poziom"
        )
        if floor % 5 == 0 and not is_mythic_astral_boss_floor(floor):
            challenge_id = f"mythic_astral_challenge_{floor}"
            challenge = _infinite_challenge_template(template, "mythic_astral", floor)
            challenge["elite_base_template"] = regular_id
            MOB_TEMPLATES[challenge_id] = challenge
            _configure_dynamic_corpse_material(challenge)
            spawns.append((room_id, challenge_id))
        if is_mythic_astral_boss_floor(floor):
            boss_id = f"mythic_astral_boss_{floor}"
            bname, mechanic, mechanic_text = _dynamic_mythic_astral_boss_profile(floor)
            boss_hp = max(1, int(round((400000 + floor * 6000) * mult)))
            boss = {
                "name": bname,
                "max_hp": boss_hp,
                "base_max_hp": max(1, int(round(boss_hp / GLOBAL_MOB_HP_MULTIPLIER))),
                "damage": max(1, int(round((280 + floor * 2) * mult))),
                "damage_type": "magic",
                "silver": 10000 + econ * 45,
                "gold": 80 + econ // 4,
                "mithril": 1,
                "stat_reward": max(1, int(round((3500 + floor * 14) * mult))),
                "class_xp_reward": max(1, int(round((75000 + floor * 800) * mult))),
                "soul_reward": max(1, int(round((11000 + floor * 55) * mult))),
                "drops": {"soul_shard": 1.0, "soul_elixir": 0.80},
                "quest_target": None,
                "mythic_astral_floor": floor,
                "mythic_astral_boss": True,
                "boss_mechanic": mechanic,
                "boss_mechanic_text": mechanic_text,
                "corpse_equipment_pool": [
                    f"astral_t11_{slot}"
                    for slot in CLASS_EQUIPMENT_SLOT_DEFS
                ],
                "corpse_equipment_guaranteed": 3,
            }
            boss["template_id"] = boss_id
            apply_milestone_boss_identity(boss, "mythic_astral", floor)
            MOB_TEMPLATES[boss_id] = boss
            _configure_dynamic_corpse_material(boss)
            _ensure_dynamic_boss_key("mythic_astral", floor)
            spawns.append((room_id, boss_id))
        return room_id, spawns

    floor = max(ASTRAL_MIN_FLOOR, floor)
    room_id = astral_floor_id(floor)
    mult = infinite_continuation_multiplier(floor, ASTRAL_MAX_FLOOR)
    econ = _capped_dungeon_economy_floor(floor)
    theme = infinite_combat_floor_theme("astral", floor)
    exits = {
        "down": "astral_gate" if floor == ASTRAL_MIN_FLOOR else astral_floor_id(floor - 1),
        "up": astral_floor_id(floor + 1),
    }
    note = " Przy pierwszym przejściu boss tego poziomu blokuje drogę w górę do chwili pokonania." if is_astral_boss_floor(floor) else ""
    ROOMS[room_id] = {
        "zone": "Wieża Astralna",
        "name": f"Wieża Astralna, poziom {floor}",
        "desc": (
            f"Poziom {floor}. Wieża nie ma szczytu; gwiezdne kondygnacje "
            f"ciągną się dalej bez końca. Motyw piętra: {theme['label']} — "
            f"{theme['desc']}.{note}"
        ),
        "exits": exits,
        "procedural_infinite": True,
    }
    relative = floor - ASTRAL_MIN_FLOOR
    regular_id = f"astral_floor_mob_{floor}"
    base_hp = max(1, int(round((1050 + relative * 12) * mult)))
    template = {
        "name": f"{ASTRAL_REGULAR_NAMES[relative % len(ASTRAL_REGULAR_NAMES)]}, poziom {floor}",
        "max_hp": max(1, int(round(base_hp * GLOBAL_MOB_HP_MULTIPLIER))),
        "base_max_hp": base_hp,
        "damage": max(1, int(round((42 + relative // 3) * mult))),
        "damage_type": "magic" if floor % 2 else "physical",
        "silver": 120 + max(0, econ - ASTRAL_MIN_FLOOR) * 2,
        "gold": 1 + max(0, econ - ASTRAL_MIN_FLOOR) // 35,
        "mithril": 0,
        "stat_reward": max(1, int(round((230 + relative * 3) * mult))),
        "class_xp_reward": max(1, int(round((7000 + relative * 100) * mult))),
        "soul_reward": max(1, int(round((1250 + relative * 14) * mult))),
        "drops": {"soul_shard": min(0.45, 0.20 + max(0, econ - ASTRAL_MIN_FLOOR) * 0.002)},
        "quest_target": None,
        "astral_floor": floor,
        "corpse_equipment_pool": [
            f"astral_t11_{slot}"
            for slot in CLASS_EQUIPMENT_SLOT_DEFS
        ],
        "corpse_equipment_guaranteed": 1,
    }
    template["template_id"] = regular_id
    _apply_infinite_combat_theme(template, theme)
    MOB_TEMPLATES[regular_id] = template
    _configure_dynamic_corpse_material(template)
    spawns = _dynamic_regular_mob_pack(
        room_id, regular_id, template, ASTRAL_REGULAR_NAMES, floor, "poziom"
    )
    if floor % 5 == 0 and not is_astral_boss_floor(floor):
        challenge_id = f"astral_challenge_{floor}"
        challenge = _infinite_challenge_template(template, "astral", floor)
        challenge["elite_base_template"] = regular_id
        MOB_TEMPLATES[challenge_id] = challenge
        _configure_dynamic_corpse_material(challenge)
        spawns.append((room_id, challenge_id))
    if is_astral_boss_floor(floor):
        boss_id = f"astral_boss_{floor}"
        bname, mechanic, mechanic_text = _dynamic_astral_boss_profile(floor)
        boss_hp = max(1, int(round(floor * 1000 * mult)))
        boss = {
            "name": bname,
            "max_hp": boss_hp,
            "base_max_hp": max(1, int(round(boss_hp / GLOBAL_MOB_HP_MULTIPLIER))),
            "damage": max(1, int(round((72 + relative // 2) * mult))),
            "damage_type": "magic" if floor % 20 == 0 else "physical",
            "silver": 900 + max(0, econ - ASTRAL_MIN_FLOOR) * 14,
            "gold": 5 + max(0, econ - ASTRAL_MIN_FLOOR) // 20,
            "mithril": 0,
            "stat_reward": max(1, int(round((900 + relative * 8) * mult))),
            "class_xp_reward": max(1, int(round((15000 + relative * 220) * mult))),
            "soul_reward": max(1, int(round((2400 + relative * 28) * mult))),
            "drops": {"soul_shard": 1.0, "soul_elixir": 0.70},
            "quest_target": None,
            "astral_floor": floor,
            "astral_boss": True,
            "boss_mechanic": mechanic,
            "boss_mechanic_text": mechanic_text,
            "corpse_equipment_pool": [
                f"astral_t11_{slot}"
                for slot in CLASS_EQUIPMENT_SLOT_DEFS
            ],
            "corpse_equipment_guaranteed": 3,
        }
        boss["template_id"] = boss_id
        apply_milestone_boss_identity(boss, "astral", floor)
        MOB_TEMPLATES[boss_id] = boss
        _configure_dynamic_corpse_material(boss)
        _ensure_dynamic_boss_key("astral", floor)
        spawns.append((room_id, boss_id))
    return room_id, spawns

def create_infinite_giant_fortress_floor_definition(floor):
    floor = max(1, int(floor))
    room_id = giant_fortress_floor_id(floor)
    mult = infinite_continuation_multiplier(floor, GIANT_FORTRESS_MAX_FLOOR)
    econ = _capped_dungeon_economy_floor(floor)
    theme = infinite_combat_floor_theme("giant", floor)
    exits = {
        "down": "giant_fortress_gate" if floor == 1 else giant_fortress_floor_id(floor - 1),
        "up": giant_fortress_floor_id(floor + 1),
    }
    note = " Przy pierwszym przejściu boss tego poziomu blokuje drogę w górę do chwili pokonania." if is_giant_fortress_boss_floor(floor) else ""
    ROOMS[room_id] = {
        "zone": "Twierdza Gigantów",
        "name": f"Twierdza Gigantów - poziom {floor}",
        "desc": (
            f"Poziom {floor}. Twierdza ciągnie się bez końca w górę. "
            f"Próg głębi {max(0, (floor - 1) // 10)}. "
            f"Motyw piętra: {theme['label']} — {theme['desc']}.{note}"
        ),
        "exits": exits,
        "procedural_infinite": True,
    }
    names = ("Ogr Miotacz Głazów", "Cyklop Strażnik", "Górski Gigant")
    mob_id = f"giant_fortress_mob_{floor}"
    base_hp = max(1, int(round((450 + floor * 55) * mult)))
    template = {
        "name": f"{names[(floor - 1) % len(names)]}, poziom {floor}",
        "max_hp": max(1, int(round(base_hp * GLOBAL_MOB_HP_MULTIPLIER))),
        "base_max_hp": base_hp,
        "damage": max(1, int(round((18 + floor * 2) * mult))),
        "damage_type": "magic" if floor % 5 == 0 else "physical",
        "silver": 80 + econ * 12,
        "gold": max(0, econ // 10),
        "mithril": 0,
        "stat_reward": max(1, int(round((70 + floor * 5) * mult))),
        "class_xp_reward": max(1, int(round((1200 + floor * 140) * mult))),
        "soul_reward": max(1, int(round((300 + floor * 45) * mult))),
        "drops": {
            "iron_ore": 0.08,
            "silver_ore": 0.08,
            "gold_ore": 0.06,
        },
        "quest_target": None,
        "elite_eligible": True,
        "giant_fortress_floor": floor,
        "corpse_equipment_pool": ["iron_guard", "iron_gauntlets", "iron_leggings", "iron_boots"],
        "corpse_equipment_guaranteed": 1,
    }
    template["template_id"] = mob_id
    _apply_infinite_combat_theme(template, theme)
    MOB_TEMPLATES[mob_id] = template
    _configure_dynamic_corpse_material(template)
    spawns = _dynamic_regular_mob_pack(
        room_id, mob_id, template, names, floor, "poziom"
    )
    if floor % 5 == 0 and not is_giant_fortress_boss_floor(floor):
        challenge_id = f"giant_fortress_challenge_{floor}"
        challenge = _infinite_challenge_template(template, "giant", floor)
        challenge["elite_base_template"] = mob_id
        MOB_TEMPLATES[challenge_id] = challenge
        _configure_dynamic_corpse_material(challenge)
        spawns.append((room_id, challenge_id))
    if is_giant_fortress_boss_floor(floor):
        boss_id = f"giant_fortress_boss_{floor}"
        bname, mechanic, mechanic_text = _dynamic_giant_boss_profile(floor)
        boss_base_hp = max(1, int(round((5000 + floor * 300) * mult)))
        boss = {
            "name": bname,
            "max_hp": max(1, int(round(boss_base_hp * GLOBAL_MOB_HP_MULTIPLIER))),
            "base_max_hp": boss_base_hp,
            "damage": max(1, int(round((45 + floor * 3) * mult))),
            "damage_type": "physical",
            "silver": 1000 + econ * 40,
            "gold": 3 + econ // 10,
            "mithril": 0,
            "stat_reward": max(1, int(round((350 + floor * 8) * mult))),
            "class_xp_reward": max(1, int(round((6000 + floor * 400) * mult))),
            "soul_reward": max(1, int(round((1400 + floor * 100) * mult))),
            "drops": {"soul_elixir": 0.20, "soul_shard": 0.60},
            "quest_target": None,
            "world_boss": True,
            "giant_fortress_boss": True,
            "giant_fortress_floor": floor,
            "boss_mechanic": mechanic,
            "boss_mechanic_text": mechanic_text,
            "corpse_equipment_pool": [
                "iron_helmet", "iron_guard", "iron_gauntlets",
                "iron_leggings", "iron_boots", "forge_charm",
            ],
            "corpse_equipment_guaranteed": 2,
        }
        boss["template_id"] = boss_id
        apply_milestone_boss_identity(boss, "giant", floor)
        MOB_TEMPLATES[boss_id] = boss
        _configure_dynamic_corpse_material(boss)
        _ensure_dynamic_boss_key("giant", floor)
        spawns.append((room_id, boss_id))
    return room_id, spawns

def create_infinite_mine_floor_definition(floor):
    floor = max(MINE_MIN_FLOOR, int(floor))
    room_id = mine_floor_id(floor)
    exits = {
        "up": "crystal_chamber" if floor == MINE_MIN_FLOOR else mine_floor_id(floor - 1),
        "down": mine_floor_id(floor + 1),
    }
    effective = min(400, floor)
    feature = infinite_gathering_floor_feature("deep_mine", floor, MINE_PREGENERATED_MAX_FLOOR)
    generated_profile = v0250_mine_floor_profile(floor)
    if effective < 10:
        richness = "zwykłe skały i miedź"
    elif effective < 100:
        richness = "coraz bogatsze żyły metali"
    elif effective < 200:
        richness = "rzadkie rudy endgame"
    else:
        richness = "najwyższe rudy progresji 400"
    ROOMS[room_id] = {
        "zone": "Kopalnia Głębinowa",
        "name": f"Kopalnia - poziom {floor}",
        "desc": (
            f"Poziom {floor}. Kopalnia schodzi bez końca. W skale występują {richness}. "
            "Moc surowców nie przekracza capu progresji 400. "
            f"Generator piętra: {generated_profile['shape']}, {generated_profile['strata']}; "
            f"{generated_profile['sign']}."
            + (f" Specjalny sektor: {feature['label']} — {feature['desc']}." if feature['label'] else "")
        ),
        "exits": exits,
        "procedural_infinite": True,
        "infinite_gather_feature": feature,
        "v0250_generator_profile": generated_profile,
    }
    MINING_DEPTH_ROOMS.add(room_id)
    MINING_ROOMS.add(room_id)
    return room_id, []

def create_infinite_profession_dungeon_floor_definition(dungeon, floor):
    floor = max(1, int(floor))
    room_id = profession_dungeon_room_id(dungeon, floor)
    required = profession_dungeon_required_tool_level(floor)
    feature = infinite_gathering_floor_feature(dungeon, floor, PROF_DUNGEON_MAX_FLOOR)
    previous = profession_dungeon_room_id(dungeon, floor - 1) if floor > 1 else None
    next_room = profession_dungeon_room_id(dungeon, floor + 1)
    if dungeon == "crystal_mine":
        exits = ({"west": "crystal_chamber", "down": next_room} if floor == 1
                 else {"up": previous, "down": next_room})
        zone = "Kryształowe Groty"
        name = f"Kryształowe Groty, komora {floor}"
        desc = (
            f"Kryształowa komora eksploracyjna {floor}. "
            "Wydobycie jest wyłączone; wszystkie rudy są w Kopalni Głębinowej."
        )
    elif dungeon == "sunken_grotto":
        exits = {"up": "sea_pier" if floor == 1 else previous, "down": next_room}
        zone = "Loch Profesyjny - Zatopiona Grota"
        name = f"Zatopiona Grota, głębokość {floor}"
        desc = (
            f"Nieskończona głębokość {floor}. Wymagane Wędkarstwo level {required}. "
            "Najrzadsze ryby nadal respektują cap Wędkarstwa 400."
            + (f" Specjalny sektor: {feature['label']} — {feature['desc']}." if feature['label'] else "")
        )
        OCEAN_FISHING_ROOMS.add(room_id)
        FISHING_ROOMS.add(room_id)
        MARINE_FISHING_ROOMS.add(room_id)
    elif dungeon == "ancient_forest":
        exits = ({"up": "deep_grove", "south": next_room} if floor == 1
                 else {"north": previous, "south": next_room})
        zone = "Loch Profesyjny - Pradawny Las"
        name = f"Pradawny Las, ostęp {floor}"
        desc = (
            f"Nieskończony ostęp {floor}. Wymagane Drwalstwo level {required}. "
            "Jakość drewna zatrzymuje progresję mocy na levelu 400."
            + (f" Specjalny sektor: {feature['label']} — {feature['desc']}." if feature['label'] else "")
        )
        WOODCUTTING_ROOMS.add(room_id)
    elif dungeon == "alchemy_garden":
        exits = ({"south": "herbalist_hut", "east": next_room} if floor == 1
                 else {"west": previous, "east": next_room})
        zone = "Loch Profesyjny - Ogród Alchemika"
        name = f"Ogród Alchemika, sektor {floor}"
        desc = (
            f"Nieskończony sektor {floor}. Wymagane Zielarstwo level {required}. "
            "Rzadkość ziół respektuje cap progresji 400."
            + (f" Specjalny sektor: {feature['label']} — {feature['desc']}." if feature['label'] else "")
        )
        HERBALISM_ROOMS.add(room_id)
    else:
        return None, []
    ROOMS[room_id] = {
        "zone": zone,
        "name": name,
        "desc": desc,
        "exits": exits,
        "procedural_infinite": True,
        "infinite_gather_feature": feature,
    }
    spawns = profession_dungeon_combat_pack(dungeon, floor)
    return room_id, spawns

# ============================================================
# v0.8.63 - COMBAT & LOOT BALANCE PASS
# ============================================================
# Jedno saldo pozostaje bez zmian. Ten etap wyrównuje nagrody z mobów,
# sprzedaż materiałowego EQ oraz kilka mechanik walki endgame.
V0863_MATERIAL_SALE_BASE_SILVER = {
    # v0.8.64: sprzedaż wysokich materiałów pozostaje cenna, ale pojedynczy
    # corpse drop nie może przebić całej ekonomii questa/bounty.
    "iron": 150,
    "steel": 500,
    "mithril": 1_500,
    "adamantite": 4_000,
    "cobalt": 10_000,
    "runic": 30_000,
    "dragonsteel": 75_000,
    "astral": 200_000,
    "void": 1_000_000,
    "eternium": 8_000_000,
}

def v0863_is_boss_template(template):
    return bool(
        template.get("world_boss")
        or template.get("crypt_boss")
        or template.get("astral_boss")
        or template.get("mythic_crypt_boss")
        or template.get("mythic_astral_boss")
        or template.get("boss_mechanic")
    )

def v0863_critical_chance_from_dexterity(dexterity):
    return generator_core_v027.critical_chance_from_dexterity(dexterity)


def v0865_dodge_chance_from_dexterity(dexterity):
    return generator_core_v027.dodge_from_dexterity(dexterity)


def v0863_execute_threshold(template):
    """Bossowie wymagają większego osłabienia przed pełną egzekucją."""
    if template.get("world_boss") or template.get("mythic_crypt_boss") or template.get("mythic_astral_boss"):
        return 0.15
    if v0863_is_boss_template(template):
        return 0.20
    if template.get("mini_boss") or template.get("rare_mob") or template.get("rare_variant") or template.get("rare_troll") or template.get("elite_affix"):
        return 0.25
    return 0.35

def v0863_mob_coin_reward(template):
    """Stała nagroda pieniężna wynikająca z realnej siły przeciwnika."""
    hp = max(1, int(template.get("max_hp", 1) or 1))
    damage = max(1, int(template.get("damage", 1) or 1))
    base = max(10, hp // 10 + damage * 10)

    if template.get("world_boss") or template.get("mythic_crypt_boss") or template.get("mythic_astral_boss"):
        multiplier = 8.0
    elif v0863_is_boss_template(template):
        multiplier = 5.0
    elif template.get("mini_boss"):
        multiplier = 3.0
    elif template.get("rare_mob") or template.get("rare_variant") or template.get("rare_troll"):
        multiplier = 2.5
    elif template.get("elite_affix"):
        multiplier = 1.75
    else:
        multiplier = 1.0

    # Bez pojedynczych przypadkowych wypłat pełnego mithrilu. Wielki zarobek
    # endgame pochodzi z questów, bounty, unikalnego lootu i sprzedaży EQ.
    return max(1, int(round(base * multiplier)))

def rebalance_mob_currency_v0863():
    changed = 0
    for template in MOB_TEMPLATES.values():
        if template.get("training_dummy"):
            template["silver"] = 0
            template["gold"] = 0
            template["mithril"] = 0
            continue
        reward = v0863_mob_coin_reward(template)
        template["silver"] = reward
        template["gold"] = 0
        template["mithril"] = 0
        template["v0863_balanced_currency"] = True
        changed += 1
    return changed

V0863_REBALANCED_MOBS = rebalance_mob_currency_v0863()

# ============================================================
# v0.8.64 - FULL GAME BALANCE AUDIT
# ============================================================
def v0864_progression_rank_factor(template):
    """Ile pasków progresji może maksymalnie dać jedno zabicie.

    Chroni stare konto i nową postać przed przeskoczeniem dziesiątek/setek
    leveli po zabiciu jednego potwora przez silną drużynę, ale boss nadal
    daje wyraźnie większy skok niż zwykły mob.
    """
    if template.get("world_boss") or template.get("mythic_crypt_boss") or template.get("mythic_astral_boss"):
        return 5.0
    if v0863_is_boss_template(template):
        return 3.0
    if template.get("mini_boss"):
        return 2.0
    if template.get("rare_mob") or template.get("rare_variant") or template.get("rare_troll") or template.get("elite_affix"):
        return 1.5
    return 1.0

def v0864_stat_progress_rank_factor(template):
    # v0.8.65: wszystkie sześć statystyk rośnie jednocześnie, więc zwykły
    # mob nie może dawać prawie całego paska niezależnie od progu endgame.
    # Bossowie nadal są wyraźnie lepszym źródłem Postępu Rozwoju.
    if template.get("world_boss") or template.get("mythic_crypt_boss") or template.get("mythic_astral_boss"):
        return 1.00
    if v0863_is_boss_template(template):
        return 0.75
    if template.get("mini_boss"):
        return 0.50
    if template.get("rare_mob") or template.get("rare_variant") or template.get("rare_troll") or template.get("elite_affix"):
        return 0.35
    return 0.20

def configure_v0863_balance_help():
    HELP_TOPICS["krytyki"] = [
        "Trafienia krytyczne zależą od efektywnej Zręczności, także z EQ.",
        "Przy Zręczności 10 szansa wynosi 5 procent. Do 40 każdy punkt daje +0,5 punktu procentowego.",
        "Od 41 do 80 każdy punkt daje +0,25 punktu procentowego; powyżej 80 +0,10 punktu procentowego.",
        "Minimalna szansa wynosi 1 procent, maksymalna 35 procent. Przy około 130 Zręczności osiągasz limit 35 procent.",
        "Trafienie krytyczne zadaje 150 procent normalnych obrażeń i działa dla zwykłego ataku oraz ofensywnych skilli/spelli.",
        "stats pokazuje aktualną szansę na krytyk i mnożnik.",
    ]
    combat_key = "walka" if "walka" in HELP_TOPICS else None
    if combat_key:
        additions = [
            "Od v0.8.63 płaska obrona może zatrzymać maksymalnie 75 procent bazowego trafienia zwykłego moba i 60 procent trafienia bossa; guardy oraz pasywy rasowe/klasowe działają potem osobno.",
            "Execute aktywuje pełny mnożnik przy 35 procent HP zwykłego moba, 25 procent elity/mini-bossa, 20 procent bossa i 15 procent world/mythic bossa.",
            "Drain nadal skaluje się z zadanymi obrażeniami, ale pojedynczy cast może uleczyć najwyżej 25 procent maksymalnego HP gracza.",
        ]
        for line in additions:
            if line not in HELP_TOPICS[combat_key]:
                HELP_TOPICS[combat_key].append(line)

configure_v0863_balance_help()

def configure_v0864_balance_help():
    HELP_TOPICS["balans"] = [
        "v0.8.64 wykonuje pełny audit balansu walki, progresji, profesji, lootu i multiclass.",
        "Soul XP nie podwaja się już co 10 leveli; każdy pełny blok 10 Soul Leveli zwiększa wymaganie o 25 procent.",
        "Każda statystyka ma osobny dynamiczny próg EXP rosnący wraz z jej wartością. Jeden mob ma też limit EXP statystyk, Soul XP i Class XP zależny od swojej rangi.",
        "Skill Level 1-400 ma łagodne, malejące skalowanie mocy i cooldownu; XP skilla zdobywa się szybciej, żeby 200 było osiągalne bez dziesiątek tysięcy użyć jednego skilla.",
        "Różne buffy multiclass nadal działają jednocześnie i uniwersalnie, ale buff nie wzmacnia siły kolejnego buffa, a łączny bonus ma limit +125 procent.",
        "Pojedyncze leczenie ma limit 80 procent maksymalnego HP na cast po wszystkich buffach; leczenie grupowe 60 procent na cel.",
        "Po zużyciu gwarantowanego evade działa wspólny 4-sekundowy lockout dla kolejnego gwarantowanego uniku.",
        "Czysty mithril z Górnictwa pozostaje jackpotem, ale szansa została obniżona dziesięciokrotnie; 1 mithril nadal oznacza 1000000 złota wspólnego salda.",
        "Wyższe materiałowe EQ z ciał wymaga mocniejszych mobów; sprzedaż Astral/Pustka/Eternium nie przebija już ekonomii jednym dropem.",
        "AoE, podstawowa Mana, fazy bossów, quest rewards v0.8.62 i ceny sklepów v0.8.61 przeszły audit bez dodatkowego nerfa.",
    ]

configure_v0864_balance_help()

# ============================================================
# v0.8.65 - FULL GAME BALANCE SIMULATION PASS
# ============================================================
def rebalance_profession_economy_v0865():
    # Widmowy marlin był historycznym reliktem waluty: po redenominacji
    # dominował dochód Wędkarstwa. Nadal jest legendarny, ale nie daje
    # równowartości końcowego questa za pojedynczy zwykły roll.
    ghost = ITEMS.get("ghost_marlin")
    if ghost:
        ghost["sell_silver"] = 0
        ghost["sell_gold"] = 5_000
        ghost["sell_mithril"] = 0
        for key, definition in FISH_RARE_VARIANTS.items():
            variant_id = rare_resource_variant_id("fish", key, "ghost_marlin")
            variant = ITEMS.get(variant_id)
            if variant:
                variant["sell_silver"] = 0
                variant["sell_gold"] = 5_000 * int(definition["value_mult"])
                variant["sell_mithril"] = 0

    # Drwalstwo miało podobny czas akcji do innych profesji, ale znacznie
    # niższą wartość sprzedaży. Podwajamy wyłącznie ceny skupu drewna;
    # receptury, drop rate i użyteczność craftingu pozostają bez zmian.
    for item_id in WOOD_STORAGE_IDS:
        item = ITEMS.get(item_id)
        if not item:
            continue
        if int(item.get("sell_silver", 0) or 0) > 0:
            item["sell_silver"] = int(item["sell_silver"]) * 2
        if int(item.get("sell_gold", 0) or 0) > 0:
            item["sell_gold"] = int(item["sell_gold"]) * 2

rebalance_profession_economy_v0865()

# v0.8.66: historyczne ceny części ryb oceanicznych powodowały ogromny
# skok dochodu w środku progresji (szczególnie 50-100). Normalizujemy
# wyłącznie outliery; wysokopoziomowe rekiny i legendarny endgame zostają
# atrakcyjne. Rzadkie warianty zawsze dziedziczą tę samą bazę * mnożnik.
V0866_FISH_PRICE_GOLD = {
    "albacore": 1,
    "cod": 1,
    "mackerel": 1,
    "sea_bass": 1,
    "giant_pike": 5,
    "bigeye_tuna": 5,
    "cobia": 5,
    "flounder": 5,
    "haddock": 5,
    "halibut": 5,
    "mahi_mahi": 5,
    "pollock": 5,
    "amberjack": 15,
    "barracuda": 15,
    "wahoo": 15,
    "bluefin_tuna": 60,
    "ocean_sunfish": 60,
}

def rebalance_fishing_midgame_v0866():
    for item_id, gold_value in V0866_FISH_PRICE_GOLD.items():
        item = ITEMS.get(item_id)
        if not item:
            continue
        item["sell_silver"] = 0
        item["sell_gold"] = int(gold_value)
        item["sell_mithril"] = 0
        for key, definition in FISH_RARE_VARIANTS.items():
            variant_id = rare_resource_variant_id("fish", key, item_id)
            variant = ITEMS.get(variant_id)
            if not variant:
                continue
            variant["sell_silver"] = 0
            variant["sell_gold"] = int(gold_value) * int(definition["value_mult"])
            variant["sell_mithril"] = 0

rebalance_fishing_midgame_v0866()

def configure_v0865_balance_help():
    HELP_TOPICS["balans 0865"] = [
        "v0.8.65 domyka balans praktyczny symulacją całej gry 1-200.",
        "Pasywny dodge ma malejący przyrost ze Zręczności i limit 35 procent; gwarantowane evade pozostają osobną mechaniką.",
        "Magiczne klasy odzyskują do 5 procent maksymalnej Many, maksymalnie 40, po awaryjnym ataku Bronią Duszy wykonanym przy braku Many.",
        "W drużynie przeciwnik ma jeden aktywny cel aggro; pozostali gracze nie tworzą osobnych pełnych timerów kontrataku.",
        "EXP każdej statystyki z pojedynczego killa jest ograniczony rangą przeciwnika; sześć liczników działa niezależnie i jest czytanych osobno.",
        "Próby Rybaka, Górnika, Drwala i Zielarki startują od 0 i liczą tylko zasoby zdobyte po przyjęciu questa.",
        "Czysty mithril z Górnictwa ma maksymalnie 0,01 procent szansy na akcję. Widmowy marlin odblokowuje się od Wędki 190.",
        "Czas Wędkarstwa zależy od poziomu Wędkarstwa; od poziomu 200 do 400 obowiązuje końcowe minimum 3 sekundy. Level Wędki nie skraca czasu.",
    ]

configure_v0865_balance_help()

def configure_v0866_balance_help():
    HELP_TOPICS["balans 0866"] = [
        "v0.8.66 wykonuje kompletny pass balansu całej gry: tereny, moby, bossowie, RNG, EQ, questy, profesje, crafting, ekonomię i progresję 1-200.",
        "Każdy quest po przyjęciu zaczyna od 0/x. Liczą się wyłącznie wymagane zdarzenia wykonane po przyjęciu; stary zapas przedmiotów ani wcześniejsze zabicia nie dają postępu.",
        "Każda z sześciu statystyk ma własny EXP, własny próg i osobny odczyt NVDA: Siła, Zręczność, Kondycja, Inteligencja, Siła Woli i Charyzma.",
        "Level profesji skraca czas pracy oraz spełnia wymagania zleceń i lochów profesyjnych. Receptury wymagają także odpowiedniego Tieru właściwego narzędzia.",
        "Tier narzędzia odblokowuje lepsze pule surowców i receptur; level wewnątrz Tieru wpływa na progres/bonus, ale nie odblokowuje nowej puli. Narzędzia nadal nie mają trwałości.",
        "Ocena zagrożenia terenu korzysta z realnych spawnów w konkretnym pokoju; wejścia z dużym skokiem trudności są ostrzegane przed przejściem.",
        "Losowe materiałowe EQ ma stały budżet mocy dla materiału i slotu: RNG zmienia rozkład statystyk/właściwości, ale nie tworzy kilku-krotnie silniejszego przedmiotu tego samego tieru.",
        "Wędkarstwo ma czas 16 do 3 sekund zależny od levelu Wędkarstwa. Historyczne cenowe outliery ryb mid-game zostały znormalizowane bez obniżania wartości endgame.",
        "help profesje, help receptury, help statystyki, help atlas i help balans 0866 opisują aktualne zasady.",
    ]
    HELP_TOPICS["questy 0"] = [
        "Każde nowe podejście do questa zaczyna się od postępu 0/x.",
        "Postęp rośnie dopiero po wymaganym zdarzeniu wykonanym po przyjęciu: nowym połowie, zbiorze, wydobyciu, cięciu, craftingu, zabiciu albo rozmowie/dostawie.",
        "Przedmioty posiadane przed przyjęciem nie naliczają postępu. Jeśli quest wymaga oddania zasobów, przy rozliczeniu nadal musisz fizycznie posiadać wymaganą liczbę.",
        "Porzucenie i ponowne rozpoczęcie podejścia zeruje bieżący licznik do 0/x; historia ukończeń zostaje zachowana.",
    ]

configure_v0866_balance_help()

def configure_v0870_grave_moss_help():
    HELP_TOPICS["questy"].append(
        "Terenowe Zielarstwo: Mech Nagrobny startuje od 0/8. Każdy nowy Mech Nagrobny zebrany po przyjęciu questa zwiększa postęp; bonusowy dodatkowy zbiór zwiększa go o dodatkową sztukę."
    )
    HELP_TOPICS["questy 0"].append(
        "Quest na konkretny surowiec rozpoznaje jego bazowy typ także wtedy, gdy zbiór ma rzadki wariant jakości. Taki wariant może również zostać użyty przy oddawaniu wymaganego bazowego surowca."
    )

configure_v0870_grave_moss_help()

# ============================================================
# v0.8.74 - FULL GAME MOB DURABILITY + XP POLISH PASS
# ============================================================
def v0874_min_hp_damage_ratio(template):
    """Minimalna trwałość względem obrażeń dla przeciwników, którzy byli papierowi.

    Generowane bossy Krypty/Astralu/Mityczne i Twierdzy Gigantów mają własne
    duże pule HP i nie są dodatkowo pompowane. Zwykłe, rare/elite, mini i
    starsze world bossy dostają tylko dolną granicę, więc mocne template'y
    pozostają bez zmian.
    """
    power = v0866_mob_progression_power(template)
    if template.get("world_boss"):
        if power <= 80:
            return 45
        if power <= 120:
            return 55
        if power <= 160:
            return 70
        return 85
    if template.get("mini_boss"):
        if power <= 20:
            return 30
        if power <= 50:
            return 34
        if power <= 100:
            return 38
        if power <= 150:
            return 42
        return 46
    elite = bool(
        template.get("rare_mob") or template.get("rare_variant")
        or template.get("rare_troll") or template.get("elite_affix")
    )
    if power <= 20:
        base = 20
    elif power <= 50:
        base = 24
    elif power <= 100:
        base = 28
    elif power <= 150:
        base = 32
    else:
        base = 36
    return base + (4 if elite else 0)

def rebalance_paper_mobs_v0874():
    changed = []
    class_xp_fixed = 0
    for mob_id, template in MOB_TEMPLATES.items():
        if template.get("training_dummy"):
            continue
        # Bossowie piętrowi mają własne precyzyjne reguły HP i długie walki.
        if (
            template.get("crypt_boss") or template.get("astral_boss")
            or template.get("mythic_crypt_boss") or template.get("mythic_astral_boss")
            or template.get("giant_fortress_boss")
        ):
            continue

        old_hp = max(1, int(template.get("max_hp", 1) or 1))
        damage = max(1, int(template.get("damage", 1) or 1))
        ratio = v0874_min_hp_damage_ratio(template)
        target_hp = int(math.ceil((damage * ratio) / 10.0) * 10)
        # Nigdy nie osłabiamy przeciwnika; ten pass ma tylko naprawiać
        # za krótkie walki. Dodatkowo pojedyncza korekta nie przekracza x3.
        new_hp = min(max(old_hp, target_hp), old_hp * 3)
        # Pomijamy kosmetyczne różnice poniżej 5 procent, żeby pass dotykał
        # wyłącznie przeciwników, których walka faktycznie była za krótka.
        if new_hp < int(math.ceil(old_hp * 1.05)):
            new_hp = old_hp

        old_class_xp = int(template.get("class_xp_reward", 0) or 0)
        baseline_class_xp = max(50, int(template.get("stat_reward", 0) or 0) * 10)
        if old_class_xp <= 0:
            template["class_xp_reward"] = baseline_class_xp
            old_class_xp = baseline_class_xp
            class_xp_fixed += 1

        if new_hp <= old_hp:
            continue

        hp_mult = new_hp / float(old_hp)
        # EXP rośnie wolniej niż samo HP, bo mob zachowuje ten sam damage,
        # drop i Postęp Rozwoju statystyk. Maksymalny wzrost x2.25.
        reward_mult = min(2.25, max(1.0, hp_mult ** 0.75))
        old_soul_xp = max(0, int(template.get("soul_reward", 0) or 0))
        template["max_hp"] = int(new_hp)
        template["class_xp_reward"] = max(
            old_class_xp, int(round(old_class_xp * reward_mult))
        )
        if old_soul_xp > 0:
            template["soul_reward"] = max(
                old_soul_xp, int(round(old_soul_xp * reward_mult))
            )
        template["v0874_durability_balanced"] = True
        template["v0874_hp_before"] = old_hp
        template["v0874_reward_multiplier"] = round(reward_mult, 4)
        changed.append(mob_id)
    return tuple(changed), class_xp_fixed

V0874_DURABILITY_CHANGED_MOBS, V0874_FIXED_ZERO_CLASS_XP = rebalance_paper_mobs_v0874()

def v0874_quest_stat_progress_base_grant(character, stat_name, raw_reward, repeatable=False):
    """Bazowy EXP jednej statystyki z questa przed bonusem rasy.

    Zachowuje szybki rozwój, ale nie pozwala jednemu oddaniu przeskoczyć
    kilku pełnych progów tej samej statystyki.
    """
    raw_reward = max(0, int(raw_reward or 0))
    # v0.19: nie obcinamy dużych nagród questowych. Tempo kontroluje
    # rosnący próg statystyki, a nie ukryty procentowy cap.
    return raw_reward

def v0914_combat_quest_stat_reward(quest):
    """v0.19: quest walki korzysta z globalnego generatora stat XP."""
    return v0190_quest_stat_reward(quest)

def v0914_combat_quest_soul_reward(quest, character):
    """v0.19: duży Soul XP z questów bez procentowego przycinania nagrody."""
    return v0190_quest_soul_reward(quest)

def configure_v0874_balance_help():
    HELP_TOPICS["balans 0874"] = [
        "v0.8.74 wykonuje pełny audit długości walk całej gry 1-200 zamiast wzmacniać wszystko jednym mnożnikiem.",
        "Zwykłe, rare/elite, mini-bossy i starsze world bossy z za małym HP względem własnych obrażeń dostały minimalną krzywą trwałości. Mocne moby oraz bossowie Krypty, Astralu, Mityczni i Twierdzy Gigantów zachowują własne pule HP.",
        "Class XP i Soul XP rosną tylko tam, gdzie realnie wzrosła trwałość przeciwnika. Postęp Rozwoju sześciu statystyk z mobów nie został zwiększony.",
        "Stare template'y z Class XP równym 0 otrzymują normalną nagrodę klasową wynikającą z dotychczasowego stat_reward, więc walka nie jest już pusta dla Biegłości klasy.",
        "Od v0.19 nagrody EXP nie są obcinane procentowym limitem paska; długość gry kontrolują rosnące wymagania Global Progression Generatora.",
        "Questy również mogą dawać wielkie liczby EXP, a wymagania kolejnych progów rosną odpowiednio szybciej.",
        "staty i staty info pokazują słowną ocenę bazowej wartości, np. 8 — słabo, 14 — przeciętnie; awans statystyki czyta także nową ocenę.",
        "Samo help albo pomoc otwiera indeks kategorii. help kategorie / help categories pokazuje ten sam indeks.",
        "EQ nie zostało zmienione: corpse EQ nadal ma stały budżet mocy, a limity redukcji płaskiej obrony pozostają 75 procent dla zwykłego moba i 60 procent dla bossa.",
    ]
    HELP_TOPIC_ALIASES.update({
        "balans0874": "balans 0874", "balance0874": "balans 0874",
        "fullbalance": "balans 0874", "pelnybalans": "balans 0874",
    })
    if "statystyki" in HELP_TOPICS:
        HELP_TOPICS["statystyki"].append(
            "Każda bazowa statystyka ma słowną ocenę także powyżej 200; statystyki nie mają twardego capu 200."
        )
        HELP_TOPICS["statystyki"].append(
            "Od v0.19 statystyki korzystają z globalnej krzywej wymagań: nagrody mogą być bardzo duże, a tempo kontroluje coraz wyższy koszt następnego punktu."
        )
    HELP_TOPICS["rozwoj_statystyk"] = list(HELP_TOPICS.get("statystyki", []))

configure_v0874_balance_help()

# v0.9.6: Fishing 16->3 s + Collections + Boss Codex.
HELP_TOPICS.setdefault("wedkarstwo", []).append(
    "v0.9.6: czas pojedynczego połowu zaczyna się od 16 sekund i stopniowo schodzi do minimum 3 sekund przy Wędkarstwie 200. XP i ekonomia wysokich poziomów są kompensowane względem v0.9.5."
)

# ============================================================
# v0.8.18 - Exploration, Achievements & Collection Expansion
# ============================================================
EXPLORATION_ZONE_MIN_ROOMS = 3
DROP_HISTORY_LIMIT = 50

LOOT_RARITY_ORDER = {
    "common": 0,
    "crafted": 0,
    "rare": 1,
    "epic": 2,
    "legendary": 3,
    "unique": 4,
    "mythic": 5,
}
LOOT_FILTER_INPUTS = {
    "all", "wszystko", "rare+", "rzadki+", "rzadkie+",
    "epic+", "epicki+", "epickie+", "legendary", "legendarny",
    "off", "wylacz", "wyłącz", "status",
}

COLLECTION_CATEGORY_LABELS = {
    "fish": "Ryby",
    "minerals": "Minerały",
    "herbs": "Zioła",
    "gems": "Klejnoty",
    "bosses": "Bossowie",
    "rare": "Rare Moby",
    "materials": "Materiały",
    "unique": "Wyjątkowe przedmioty",
    "equipment": "Odkryte EQ",
    # Starsze kategorie pozostają jako dodatkowe widoki kompatybilności.
    "named": "Named Loot",
    "sets": "Sety",
    "chests": "Skrzynie",
}
COLLECTION_CATEGORY_ALIASES = {
    "fish": "fish", "ryby": "fish", "ryba": "fish",
    "minerals": "minerals", "mineral": "minerals", "mineraly": "minerals", "minerały": "minerals", "rudy": "minerals",
    "herbs": "herbs", "herb": "herbs", "ziola": "herbs", "zioła": "herbs",
    "gems": "gems", "gem": "gems", "klejnoty": "gems", "klejnot": "gems",
    "materials": "materials", "material": "materials", "materialy": "materials", "materiały": "materials",
    "unique": "unique", "unikalne": "unique", "wyjatkowe": "unique", "wyjątkowe": "unique",
    "equipment": "equipment", "eq": "equipment", "ekwipunek": "equipment", "sprzet": "equipment", "sprzęt": "equipment",
    "named": "named", "namedloot": "named", "loot": "named",
    "set": "sets", "sets": "sets", "sety": "sets",
    "boss": "bosses", "bosses": "bosses", "bossowie": "bosses",
    "rare": "rare", "raremobs": "rare", "raremoby": "rare",
    "chest": "chests", "chests": "chests", "skrzynie": "chests",
}

ACHIEVEMENT_TRACKS = {
    "goblin_kills": {
        "name": "Pogromca Goblinów",
        "tiers": ((10, "Bronze"), (50, "Silver"), (100, "Gold"), (250, "Platinum")),
    },
    "chests_opened": {
        "name": "Otwieracz Skrzyń",
        "tiers": ((10, "Bronze"), (25, "Silver"), (50, "Gold"), (100, "Platinum")),
    },
    "rare_kills": {
        "name": "Łowca Rare",
        "tiers": ((3, "Bronze"), (10, "Silver"), (25, "Gold"), (50, "Platinum")),
    },
    "boss_kills": {
        "name": "Pogromca Bossów",
        "tiers": ((5, "Bronze"), (15, "Silver"), (30, "Gold"), (60, "Platinum")),
    },
    "exploration_rooms": {
        "name": "Kartograf Świata",
        "tiers": ((100, "Bronze"), (500, "Silver"), (1000, "Gold"), (1272, "Platinum")),
    },
    "profession_masters": {
        "name": "Mistrz Profesji",
        "tiers": ((1, "Bronze"), (3, "Silver"), (5, "Gold"), (8, "Platinum")),
    },
    "profession_transcendents": {
        "name": "Transcendentny Mistrz Profesji",
        "tiers": ((1, "Bronze"), (3, "Silver"), (5, "Gold"), (8, "Platinum")),
    },
    "bestiary_unique": {
        "name": "Kronikarz Bestiariusza",
        "tiers": ((50, "Bronze"), (250, "Silver"), (500, "Gold"), (953, "Platinum")),
    },
    "rare_fish_caught": {
        "name": "Łowca Rzadkich Ryb",
        "tiers": ((1, "Bronze"), (10, "Silver"), (50, "Gold"), (200, "Platinum")),
    },
    "gems_found": {
        "name": "Poszukiwacz Klejnotów",
        "tiers": ((1, "Bronze"), (25, "Silver"), (100, "Gold"), (500, "Platinum")),
    },
    "multiclass_classes": {
        "name": "Droga Wielu Klas",
        "tiers": ((2, "Silver"), (3, "Platinum")),
    },
    "soul_level": {
        "name": "Mistrz Broni Duszy",
        "tiers": ((50, "Bronze"), (100, "Silver"), (150, "Gold"), (200, "Platinum"), (400, "Mythic")),
    },
    "bounties_completed": {
        "name": "Łowca Kontraktów",
        "tiers": ((5, "Bronze"), (25, "Silver"), (100, "Gold"), (250, "Platinum")),
    },
}

ACHIEVEMENT_TITLE_REWARDS = {
    ("rare_kills", "Gold"): "Łowca Rare",
    ("boss_kills", "Gold"): "Pogromca Bossów",
    ("chests_opened", "Gold"): "Mistrz Skrzyń",
    ("goblin_kills", "Gold"): "Goblinobójca",
    ("exploration_rooms", "Gold"): "Kartograf Świata",
    ("exploration_rooms", "Platinum"): "Odkrywca Całego Świata",
    ("profession_masters", "Gold"): "Mistrz Profesji",
    ("profession_masters", "Platinum"): "Arcymistrz Ośmiu Profesji",
    ("profession_transcendents", "Platinum"): "Transcendentny Mistrz Ośmiu Profesji",
    ("bestiary_unique", "Gold"): "Kronikarz Bestiariusza",
    ("bestiary_unique", "Platinum"): "Mistrz Bestiariusza",
    ("rare_fish_caught", "Gold"): "Łowca Rzadkich Ryb",
    ("gems_found", "Gold"): "Poszukiwacz Klejnotów",
    ("multiclass_classes", "Platinum"): "Mistrz Wielu Dróg",
    ("soul_level", "Gold"): "Władca Broni Duszy",
    ("soul_level", "Platinum"): "Dusza Doskonała",
    ("soul_level", "Mythic"): "Dusza Absolutu",
    ("bounties_completed", "Gold"): "Łowca Kontraktów",
}

# v0.9.3 - losowana Tablica Zleceń. Nagrody są umiarkowane i nie zmieniają
# istniejących mnożników walki ani ekonomii. Jedna postać może mieć jeden
# aktywny kontrakt, a jego licznik jest trwały w SQLite.
BOUNTY_OFFER_COUNT = 3
BOUNTY_KINDS = ("kill", "mine", "fish", "wood", "herb", "explore", "event", "secret", "mini")
BOUNTY_RESOURCE_LABELS = {
    "mine": "Wydobycie rud",
    "fish": "Połów ryb",
    "wood": "Pozyskanie drewna",
    "herb": "Zbiór ziół",
    "explore": "Eksploracja rubieży",
    "event": "Wydarzenia świata",
    "secret": "Odkrywanie sekretów",
    "mini": "Mini-lochy",
}
BOUNTY_RESOURCE_NEEDS = {
    "mine": (6, 8, 10, 12),
    "fish": (5, 6, 8, 10),
    "wood": (6, 8, 10, 12),
    "herb": (6, 8, 10, 12),
    "explore": (8, 12, 16, 20),
    "event": (1, 2, 3, 4),
    "secret": (1, 2, 3),
    "mini": (1, 2, 3),
}

def bounty_reward_values(kind, needed):
    needed = max(1, int(needed))
    base = {"kill": 180, "mine": 140, "fish": 120, "wood": 130, "herb": 130, "explore": 160, "event": 260, "secret": 320, "mini": 420}.get(kind, 120)
    per = {"kill": 28, "mine": 22, "fish": 20, "wood": 20, "herb": 20, "explore": 18, "event": 90, "secret": 120, "mini": 150}.get(kind, 20)
    soul_xp = base + needed * per
    gold = max(1, min(5, 1 + needed // 6))
    return soul_xp, gold


def _collection_slug(value):
    text = str(value or "").strip().lower().replace("ł", "l")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text or "region"


def _zone_title(zone):
    special = {
        "Nekropolia": "Pogromca Nekropolii",
        "Lodowe Jaskinie": "Mistrz Wiecznego Lodu",
        "Ruiny Kultystów": "Łamacz Kultu Pustki",
        "Stary Cmentarz": "Strażnik Starego Cmentarza",
        "Legowisko Bestii": "Pogromca Legowiska Bestii",
        "Kanały Pod Miastem": "Odkrywca Podmiejskich Kanałów",
        "Jaskinie Goblinów": "Kartograf Jaskiń Goblinów",
        "Obozowiska Bandytów": "Pogromca Obozowisk Bandytów",
        "Las Szeptów": "Strażnik Lasu Szeptów",
        "Ruiny Strażnicy": "Pogromca Ruin Strażnicy",
    }
    return special.get(zone, f"Odkrywca: {zone}")



# ============================================================
# v0.9.23 - ENDGAME REGIONS 300-400 + STEEL RECYCLING
# ============================================================
# Cztery zwykłe regiony świata dają alternatywę dla nieskończonych Krypt/Wież.
# Każdy region ma własną ZALECANĄ Biegłość aktywnej klasy, kilka gatunków mobów
# i bossa świata. Nie są instancjami i nie generują nieskończonych pięter.
# v0.9.24: zalecenie nigdy nie blokuje wejścia — ryzyko podejmuje gracz.
V0923_ENDGAME_REGIONS = (
    ("Popielne Pustkowia", 300),
    ("Rozbite Niebo", 330),
    ("Wybrzeże Pustki", 360),
    ("Korona Świata", 390),
)

# Zlecenie Haldora: Stalowe Płyty są materiałem rzemieślniczym.
# v0.30.34: najpierw fizycznie trafiają na ciało moba; po zabraniu z ciała
# są przenoszone do Szkatułki i dopiero wtedy zaliczają postęp questa.
ITEMS["salvaged_steel_plate"] = {
    "name": "Stalowa Płyta z Pancerza",
    "type": "craft_material",
    "price": None,
    "desc": (
        "Ciężka płyta odzyskana ze starego pancerza nieumarłych. "
        "Haldor przetapia cztery takie płyty w swoim godzinnym zleceniu."
    ),
}
CRAFT_MATERIAL_STORAGE_IDS = frozenset(
    set(CRAFT_MATERIAL_STORAGE_IDS) | {"salvaged_steel_plate"}
)

QUESTS["haldor_steel_recycling"] = {
    "name": "Zlecenie Haldora: Stal do Przetopu",
    "giver": "Mistrz Rzemiosła Haldor",
    "kind": "collect",
    "target": "salvaged_steel_plate",
    "needed": 4,
    "progress_label": "Stalowe Płyty",
    "description": (
        "Zdobądź po przyjęciu zlecenia 4 Stalowe Płyty z opancerzonych "
        "nieumarłych na Starym Cmentarzu. Płyty znajdują się na ciałach; "
        "przeszukaj ciało albo weź płytę z ciała. Po zabraniu trafiają do "
        "Szkatułki Rzemieślniczej i zaliczają postęp. Przy oddaniu wszystkie "
        "4 płyty są zużywane."
    ),
    "specialist_tool_type": "crafting",
    "min_tool_level": 1,
    "reward_profession": "Kowalstwo",
    "reward_profession_xp": 1300,
    "reward_tool_type": "crafting",
    "reward_tool_xp": 1000,
    "reward_silver": 260,
    "reward_gold": 1,
    "reward_mithril": 0,
    "reward_items": {},
    "repeatable": True,
    "repeat_cooldown": 60 * 60,
}

# Osobny cmentarny szkielet daje czytelne źródło Płyt. Stare moby cmentarza
# również mogą je upuścić, żeby quest nie zależał od jednego respawnu.
MOB_TEMPLATES["cemetery_steel_skeleton"] = {
    "name": "Szkielet w Stalowym Kirysie",
    "max_hp": 390,
    "damage": 29,
    "damage_type": "physical",
    "silver": 72,
    "gold": 0,
    "mithril": 0,
    "stat_reward": 90,
    "class_xp_reward": 1150,
    "soul_reward": 690,
    "drops": {"soul_shard": 0.20},
    "corpse_material_chances": {"salvaged_steel_plate": 0.72},
    "quest_target": "cemetery_steel_skeleton",
}
for _mid, _chance in (
    ("cemetery_restless_dead", 0.28),
    ("cemetery_bone_collector", 0.42),
):
    if _mid in MOB_TEMPLATES:
        # v0.30.34: płyta ma być widoczna na ciele, nie przyznawana automatycznie.
        MOB_TEMPLATES[_mid].setdefault("drops", {}).pop("salvaged_steel_plate", None)
        MOB_TEMPLATES[_mid].setdefault("corpse_material_chances", {})["salvaged_steel_plate"] = _chance
MOB_SPAWNS.extend([
    ("graveyard", "cemetery_steel_skeleton"),
    ("graveyard", "cemetery_steel_skeleton"),
    ("cemetery_bone_field", "cemetery_steel_skeleton"),
    ("cemetery_fallen_chapel", "cemetery_steel_skeleton"),
])

# Endgame world route: z Obozu Szczytowego w górę zaczyna się świat 300-400.
ROOMS["summit_camp"]["exits"]["up"] = "ashen_frontier"

_v0923_rooms = {
    # 300-329
    "ashen_frontier": ("Popielne Pustkowia", "Popielna Granica", 300, {"down":"summit_camp","north":"ashen_waste","east":"cinder_ravine"}),
    "ashen_waste": ("Popielne Pustkowia", "Morze Popiołu", 300, {"south":"ashen_frontier","north":"ember_ruins","east":"ash_bonefield"}),
    "cinder_ravine": ("Popielne Pustkowia", "Wąwóz Żaru", 300, {"west":"ashen_frontier","north":"ember_ruins"}),
    "ash_bonefield": ("Popielne Pustkowia", "Pole Zwęglonych Kości", 300, {"west":"ashen_waste","north":"ashen_citadel"}),
    "ember_ruins": ("Popielne Pustkowia", "Ruiny Ostatniego Paleniska", 300, {"south":"ashen_waste","east":"ashen_citadel"}),
    "ashen_citadel": ("Popielne Pustkowia", "Cytadela Popiołu", 300, {"west":"ember_ruins","south":"ash_bonefield","up":"skybreak_gate"}),
    # 330-359
    "skybreak_gate": ("Rozbite Niebo", "Brama Rozbitego Nieba", 330, {"down":"ashen_citadel","north":"storm_bridge"}),
    "storm_bridge": ("Rozbite Niebo", "Most Burz", 330, {"south":"skybreak_gate","north":"shattered_aerie","east":"thunder_shelf"}),
    "thunder_shelf": ("Rozbite Niebo", "Półka Gromu", 330, {"west":"storm_bridge","north":"cloud_scar"}),
    "cloud_scar": ("Rozbite Niebo", "Blizna Chmur", 330, {"south":"thunder_shelf","west":"shattered_aerie"}),
    "shattered_aerie": ("Rozbite Niebo", "Rozbite Gniazdo", 330, {"south":"storm_bridge","east":"cloud_scar","north":"tempest_sanctum"}),
    "tempest_sanctum": ("Rozbite Niebo", "Sanktuarium Nawałnicy", 330, {"south":"shattered_aerie","up":"void_coast_gate"}),
    # 360-389
    "void_coast_gate": ("Wybrzeże Pustki", "Czarna Przełęcz", 360, {"down":"tempest_sanctum","north":"void_shore"}),
    "void_shore": ("Wybrzeże Pustki", "Brzeg Bez Gwiazd", 360, {"south":"void_coast_gate","north":"drowned_observatory","east":"black_tide_flats"}),
    "black_tide_flats": ("Wybrzeże Pustki", "Równina Czarnego Przypływu", 360, {"west":"void_shore","north":"starless_chapel"}),
    "drowned_observatory": ("Wybrzeże Pustki", "Zatopione Obserwatorium", 360, {"south":"void_shore","east":"starless_chapel"}),
    "starless_chapel": ("Wybrzeże Pustki", "Kaplica Bez Gwiazd", 360, {"west":"drowned_observatory","south":"black_tide_flats","north":"void_throne"}),
    "void_throne": ("Wybrzeże Pustki", "Tron Przypływu Pustki", 360, {"south":"starless_chapel","up":"world_crown_gate"}),
    # 390-400
    "world_crown_gate": ("Korona Świata", "Brama Korony Świata", 390, {"down":"void_throne","north":"eternal_causeway"}),
    "eternal_causeway": ("Korona Świata", "Wieczna Grobla", 390, {"south":"world_crown_gate","north":"crown_stair","east":"absolute_gallery"}),
    "absolute_gallery": ("Korona Świata", "Galeria Absolutu", 390, {"west":"eternal_causeway","north":"crown_stair"}),
    "crown_stair": ("Korona Świata", "Schody Korony", 390, {"south":"eternal_causeway","east":"timeless_balcony","north":"world_crown_summit"}),
    "timeless_balcony": ("Korona Świata", "Ponadczasowy Balkon", 390, {"west":"crown_stair","north":"world_crown_summit"}),
    "world_crown_summit": ("Korona Świata", "Szczyt Korony Świata", 390, {"south":"crown_stair","west":"timeless_balcony"}),
}
for _rid, (_zone, _name, _req, _exits) in _v0923_rooms.items():
    ROOMS[_rid] = {
        "zone": _zone,
        "name": _name,
        "desc": (
            f"Region endgame; zalecana Biegłość {_req}+. "
            "To zwykła strefa świata, nie nieskończona instancja."
        ),
        "exits": dict(_exits),
        "recommended_mastery": int(_req),
    }

EXP_AREAS = EXP_AREAS + (
    {
        "id":"ashen_wastes","name":"Popielne Pustkowia",
        "aliases":("popielne pustkowia","popielna granica","ash wastes"),
        "soul_min":300,"soul_max":329,"mastery_min":300,"mastery_max":329,
        "difficulty":"endgame 300-329","guide":"popielne pustkowia",
        "enemies":"Popielny Revenant, Upiór Żaru, Zwęglony Kolos, Wieszcz Popiołu i Suweren Popielnej Cytadeli",
        "description":"Pierwszy otwarty region endgame po Górach, przeznaczony dla Levelu postaci 300+.",
        "note":"To zwykły region świata, nie instancja. Zalecany Level postaci: 300; wejście nie jest blokowane.",
    },
    {
        "id":"shattered_sky","name":"Rozbite Niebo",
        "aliases":("rozbite niebo","brama rozbitego nieba","shattered sky"),
        "soul_min":330,"soul_max":359,"mastery_min":330,"mastery_max":359,
        "difficulty":"endgame 330-359","guide":"rozbite niebo",
        "enemies":"Serafin Nawałnicy, Łamacz Nieba, Gromowy Harcownik, Tytan Chmur i Królowa Rozbitej Nawałnicy",
        "description":"Wysokogórski region burzowy rozwijający otwarty endgame poza Wieżą.",
        "note":"Zalecany Level postaci: 330; wejście nie jest blokowane.",
    },
    {
        "id":"void_coast","name":"Wybrzeże Pustki",
        "aliases":("wybrzeze pustki","wybrzeże pustki","void coast"),
        "soul_min":360,"soul_max":389,"mastery_min":360,"mastery_max":389,
        "difficulty":"endgame 360-389","guide":"wybrzeze pustki",
        "enemies":"Żeglarz Pustki, Wyrocznia Czarnego Przypływu, Rycerz Bez Gwiazd, Manta Otchłani i Monarcha Przypływu Pustki",
        "description":"Czarny brzeg i zatopione obserwatorium dla późnego endgame.",
        "note":"Zalecany Level postaci: 360; wejście nie jest blokowane.",
    },
    {
        "id":"world_crown","name":"Korona Świata",
        "aliases":("korona swiata","korona świata","world crown"),
        "soul_min":390,"soul_max":400,"mastery_min":390,"mastery_max":400,
        "difficulty":"endgame 390-400","guide":"korona swiata",
        "enemies":"Strażnik Korony, Ponadczasowy Magister, Strażnik Absolutu, Echo Korony Świata i Awatar Korony Świata",
        "description":"Końcowy otwarty region progresji 390-400 z bossem na Szczycie Korony Świata.",
        "note":"Zalecany Level postaci: 390; wejście nie jest blokowane, a finał jest projektowany pod 400.",
    },
)
EXP_ZONE_AREA_ID.update({
    "Popielne Pustkowia":"ashen_wastes",
    "Rozbite Niebo":"shattered_sky",
    "Wybrzeże Pustki":"void_coast",
    "Korona Świata":"world_crown",
})
EXP_AREA_BASE_CATEGORY.update({
    "ashen_wastes":"Endgame", "shattered_sky":"Endgame",
    "void_coast":"Endgame", "world_crown":"Endgame",
})

# Moby są skalowane do odpowiednich odcinków 300-400. Każdy region ma
# kilka archetypów, a finałowy pokój ma własnego world bossa.
_v0923_mob_specs = {
    "ash_revenant": ("Popielny Revenant", 9200, 176, "physical", 28500, 4850, 300),
    "cinder_wraith": ("Upiór Żaru", 8600, 190, "magic", 29200, 5000, 300),
    "charred_colossus": ("Zwęglony Kolos", 11200, 168, "physical", 30500, 5200, 300),
    "ash_seer": ("Wieszcz Popiołu", 8900, 198, "magic", 31000, 5300, 300),
    "storm_seraph": ("Serafin Nawałnicy", 10300, 210, "magic", 34000, 5700, 330),
    "skybreaker": ("Łamacz Nieba", 12100, 205, "physical", 35000, 5900, 330),
    "thunder_harrier": ("Gromowy Harcownik", 9800, 225, "magic", 35500, 6050, 330),
    "cloud_titan": ("Tytan Chmur", 13300, 198, "physical", 36200, 6200, 330),
    "void_mariner": ("Żeglarz Pustki", 11900, 238, "physical", 39500, 6650, 360),
    "black_tide_oracle": ("Wyrocznia Czarnego Przypływu", 11100, 252, "magic", 40500, 6850, 360),
    "starless_knight": ("Rycerz Bez Gwiazd", 13900, 232, "physical", 41500, 7000, 360),
    "abyssal_manta": ("Manta Otchłani", 11600, 260, "magic", 42000, 7150, 360),
    "crown_sentinel": ("Strażnik Korony", 13600, 270, "physical", 45500, 7650, 390),
    "timeless_magister": ("Ponadczasowy Magister", 12800, 292, "magic", 46800, 7900, 390),
    "absolute_guardian": ("Strażnik Absolutu", 15100, 274, "physical", 47800, 8100, 390),
    "worldcrown_echo": ("Echo Korony Świata", 13200, 300, "magic", 48500, 8250, 390),
}
for _mid, (_name, _hp, _dmg, _dtype, _cxp, _sxp, _mastery) in _v0923_mob_specs.items():
    _tmpl = {
        "name": _name, "max_hp": _hp, "damage": _dmg, "damage_type": _dtype,
        "silver": 420 + (_mastery - 300) * 5, "gold": 3 + (_mastery - 300)//30,
        "mithril": 0, "stat_reward": 900 + (_mastery - 300) * 7,
        "class_xp_reward": _cxp, "soul_reward": _sxp,
        "drops": {"soul_shard": 0.35 + (_mastery - 300) / 600.0},
        "quest_target": None, "endgame_region_mastery": _mastery,
    }
    MOB_TEMPLATES[_mid] = _tmpl
    try:
        _configure_dynamic_corpse_material(_tmpl)
    except Exception:
        pass

_v0923_boss_specs = {
    "ashen_sovereign": ("Suweren Popielnej Cytadeli", 260000, 300, "magic", 72000, 11500, 320, "ashen_citadel"),
    "tempest_queen": ("Królowa Rozbitej Nawałnicy", 330000, 345, "magic", 83000, 13000, 350, "tempest_sanctum"),
    "void_tide_monarch": ("Monarcha Przypływu Pustki", 420000, 390, "magic", 96000, 15000, 380, "void_throne"),
    "world_crown_avatar": ("Awatar Korony Świata", 560000, 440, "physical", 120000, 17500, 400, "world_crown_summit"),
}
for _mid, (_name, _hp, _dmg, _dtype, _cxp, _sxp, _mastery, _room) in _v0923_boss_specs.items():
    _tmpl = {
        "name": _name, "max_hp": _hp, "damage": _dmg, "damage_type": _dtype,
        "silver": 3500 + (_mastery - 300) * 20, "gold": 20 + (_mastery - 300)//10,
        "mithril": 1 if _mastery >= 380 else 0,
        "stat_reward": 2600 + (_mastery - 300) * 12,
        "class_xp_reward": _cxp, "soul_reward": _sxp,
        "drops": {"soul_shard": 1.0, "soul_elixir": 0.45},
        "quest_target": None, "world_boss": True,
        "endgame_region_mastery": _mastery,
        "boss_mechanic": "endgame_region_boss",
        "boss_mechanic_text": "Boss endgame ma podwyższone obrażenia i wytrzymałość odpowiednie do regionu.",
    }
    MOB_TEMPLATES[_mid] = _tmpl
    try:
        _configure_dynamic_corpse_material(_tmpl)
    except Exception:
        pass
    MOB_SPAWNS.append((_room, _mid))

_v0923_region_spawns = {
    "ashen_frontier": ("ash_revenant","cinder_wraith","ash_revenant"),
    "ashen_waste": ("ash_revenant","charred_colossus","cinder_wraith"),
    "cinder_ravine": ("charred_colossus","ash_seer","cinder_wraith"),
    "ash_bonefield": ("ash_revenant","charred_colossus","ash_seer"),
    "ember_ruins": ("cinder_wraith","ash_seer","charred_colossus"),
    "skybreak_gate": ("storm_seraph","skybreaker","thunder_harrier"),
    "storm_bridge": ("thunder_harrier","storm_seraph","skybreaker"),
    "thunder_shelf": ("cloud_titan","thunder_harrier","storm_seraph"),
    "cloud_scar": ("skybreaker","cloud_titan","thunder_harrier"),
    "shattered_aerie": ("storm_seraph","cloud_titan","skybreaker"),
    "void_coast_gate": ("void_mariner","black_tide_oracle","starless_knight"),
    "void_shore": ("void_mariner","abyssal_manta","black_tide_oracle"),
    "black_tide_flats": ("abyssal_manta","starless_knight","void_mariner"),
    "drowned_observatory": ("black_tide_oracle","abyssal_manta","starless_knight"),
    "starless_chapel": ("starless_knight","black_tide_oracle","void_mariner"),
    "world_crown_gate": ("crown_sentinel","timeless_magister","absolute_guardian"),
    "eternal_causeway": ("crown_sentinel","worldcrown_echo","timeless_magister"),
    "absolute_gallery": ("absolute_guardian","timeless_magister","worldcrown_echo"),
    "crown_stair": ("crown_sentinel","absolute_guardian","worldcrown_echo"),
    "timeless_balcony": ("timeless_magister","worldcrown_echo","crown_sentinel"),
}
for _room, _mobs in _v0923_region_spawns.items():
    for _mob in _mobs:
        MOB_SPAWNS.append((_room, _mob))

GUIDE_DESTINATION_ALIASES.update({
    "popielne pustkowia": "ashen_frontier", "popielna granica": "ashen_frontier",
    "rozbite niebo": "skybreak_gate", "brama rozbitego nieba": "skybreak_gate",
    "wybrzeze pustki": "void_coast_gate", "wybrzeże pustki": "void_coast_gate",
    "korona swiata": "world_crown_gate", "korona świata": "world_crown_gate",
})

# Polecenia rankingów. Jedna komenda udostępnia pięć trwałych rankingów.
COMMAND_ALIASES.update({
    "rankingi": "leaderboards", "ranking": "leaderboards",
    "leaderboard": "leaderboards", "leaderboards": "leaderboards",
    "tablica rekordow": "leaderboards", "tablica rekordów": "leaderboards",
})
HELP_TOPICS["leaderboards"] = [
    "rankingi / leaderboard - skrócone Top 5 wszystkich kategorii.",
    "rankingi krypta - najwyższe odwiedzone piętro Krypty.",
    "rankingi wieza - najwyższe odwiedzone piętro Wieży Astralnej.",
    "rankingi boss - najszybsze zarejestrowane pokonania bossów.",
    "rankingi legendy - liczba odkrytych legendarnych elementów EQ.",
    "rankingi sety - liczba w pełni skompletowanych zestawów EQ.",
]
HELP_TOPIC_ALIASES.update({
    "rankingi": "leaderboards", "ranking": "leaderboards",
    "leaderboard": "leaderboards", "leaderboards": "leaderboards",
})



# ============================================================
# v0.9.30 - LARGE EXPLORATION REGIONS
# ============================================================
def build_v0930_large_exploration_regions():
    """Rozbudowuje małe expowiska do dużych, zapętlonych regionów.

    Bez nowego eventu eksploracyjnego: zmiana dotyczy wyłącznie świata.
    Nowe sektory tworzą siatki z pętlami i bocznymi drogami zamiast prostych
    krzyży. Istniejące wejścia, bossowie i połączenia między regionami zostają.
    """
    reverse = {"north":"south","south":"north","east":"west","west":"east","up":"down","down":"up"}
    targets = {
        "Obozowiska Bandytów": 24,
        "Jaskinie Goblinów": 24,
        "Ruiny Strażnicy": 24,
        "Stary Cmentarz": 24,
        "Ruiny Kultystów": 24,
        "Legowisko Bestii": 24,
        "Nekropolia": 24,
        "Kanały Pod Miastem": 24,
        "Lodowe Jaskinie": 24,
        "Las Szeptów": 24,
        "Pustynia": 28,
        "Bagna": 28,
        "Góry": 28,
        "Popielne Pustkowia": 30,
        "Rozbite Niebo": 30,
        "Wybrzeże Pustki": 30,
        "Korona Świata": 30,
    }
    anchors = {
        "Obozowiska Bandytów":"bandit_outer_ring",
        "Jaskinie Goblinów":"goblin_scrap_tunnels",
        "Ruiny Strażnicy":"ruin_courtyard",
        "Stary Cmentarz":"cemetery_ossuary_path",
        "Ruiny Kultystów":"cult_ruins_courtyard",
        "Legowisko Bestii":"beast_lair_tracks",
        "Nekropolia":"necropolis_procession",
        "Kanały Pod Miastem":"sewer_runoff",
        "Lodowe Jaskinie":"ice_cave_blue_tunnel",
        "Las Szeptów":"forest_old_oaks",
        "Pustynia":"desert_dunes",
        "Bagna":"reed_mire",
        "Góry":"mountain_lower_slopes",
        "Popielne Pustkowia":"ashen_waste",
        "Rozbite Niebo":"storm_bridge",
        "Wybrzeże Pustki":"void_shore",
        "Korona Świata":"eternal_causeway",
    }
    words = {
        "Obozowiska Bandytów": (("Ścieżka","Namioty","Barykada","Plac","Zaułek"),("Czerwonych Chust","Zrabowanych Wozów","Nocnej Straży","Starych Palisad","Przemytników","Wilczych Zębów"),"Palisady, wozy i boczne przejścia rozbijają obóz na wiele połączonych sektorów."),
        "Jaskinie Goblinów": (("Tunel","Grota","Szyb","Nora","Galeria"),("Zielonego Dymu","Kościanych Totemów","Złomiarzy","Krzywych Kilofów","Grzybowych Lamp","Piszczałek"),"Kręte tunele przecinają się i wracają do wcześniejszych grot, tworząc rozległą sieć."),
        "Ruiny Strażnicy": (("Korytarz","Dziedziniec","Wieża","Komnata","Galeria"),("Pękniętych Tarcz","Starej Warty","Runicznych Murów","Zawalonych Łuków","Zapomnianego Garnizonu","Kamiennych Schodów"),"Pozostałości murów, krużganków i podziemi łączą się wieloma drogami."),
        "Stary Cmentarz": (("Aleja","Kwatera","Mauzoleum","Krypta","Ogród"),("Zapomnianych Imion","Krzywych Krzyży","Czarnych Róż","Otwartych Grobów","Płaczących Figur","Zgaszonych Lamp"),"Nagrobki, mauzolea i boczne alejki tworzą rozległy cmentarz z licznymi pętlami."),
        "Ruiny Kultystów": (("Krużganek","Komnata","Dziedziniec","Galeria","Przejście"),("Czarnej Pieczęci","Zgaszonych Świec","Pękniętych Run","Szeptów Otchłani","Spalonego Pergaminu","Pustych Masek"),"Ruiny świątyni ciągną się przez dziedzińce, biblioteki i boczne przejścia rytualne."),
        "Legowisko Bestii": (("Grota","Korytarz","Gniazdo","Szczelina","Łowisko"),("Starych Kości","Poszarpanych Skór","Żelaznych Korzeni","Ciepłego Oddechu","Śladów Pazurów","Głębokiego Ryku"),"Naturalne jaskinie rozchodzą się na kilka poziomów i łączą z powrotem bocznymi szczelinami."),
        "Nekropolia": (("Aleja","Katakumby","Mauzoleum","Plac","Grobowiec"),("Kamiennych Królów","Bezimiennych","Czarnych Chorągwi","Milczących Straży","Kościanych Bram","Wiecznego Czuwania"),"Monumentalna nekropolia ma wiele ulic grobowych, placów i zejść do katakumb."),
        "Kanały Pod Miastem": (("Kanał","Tunel","Komora","Przepust","Cysterna"),("Czarnej Wody","Starych Krat","Zgniłych Desek","Przemytników","Zielonego Szlamu","Głębokiego Odpływu"),"Kanały tworzą prawdziwy labirynt przepustów, cystern i bocznych odpływów."),
        "Lodowe Jaskinie": (("Tunel","Grota","Szczelina","Komora","Galeria"),("Błękitnego Lodu","Szronowych Kolumn","Zamarzniętych Ech","Kryształowego Pyłu","Pękniętego Lodowca","Wiecznej Zimy"),"Lodowe korytarze rozgałęziają się między szczelinami i zamarzniętymi komorami."),
        "Las Szeptów": (("Ścieżka","Polana","Zagajnik","Parów","Krąg"),("Starych Dębów","Cichego Mchu","Wilczych Tropów","Srebrnych Brzóz","Księżycowych Paproci","Powalonych Pni"),"Leśne trakty przecinają się, zawracają i prowadzą przez liczne polany oraz parowy."),
        "Pustynia": (("Wydmy","Kanion","Równina","Ruiny","Szlak"),("Siedmiu Wiatrów","Białych Kości","Czerwonego Piasku","Zaginionych Karawan","Szklanego Pyłu","Palącego Słońca"),"Wydmy i kaniony tworzą szeroki teren z wieloma szlakami między ruinami i oazami."),
        "Bagna": (("Mokradło","Groble","Rozlewisko","Torfowisko","Zarośla"),("Czarnej Wody","Gnijących Korzeni","Trujących Oparów","Zatopionych Drzew","Bagiennych Świateł","Wężowych Gniazd"),"Groble, wyspy i rozlewiska układają się w duży, zapętlony teren bagienny."),
        "Góry": (("Grań","Przełęcz","Półka","Wąwóz","Szlak"),("Białych Szczytów","Wiecznego Wiatru","Kamiennych Kozic","Starych Kopalń","Burzowych Chmur","Zamarzniętych Turni"),"Górskie trakty rozchodzą się po graniach, półkach i bocznych przełęczach."),
        "Popielne Pustkowia": (("Szlak","Pole","Wąwóz","Ruiny","Krawędź"),("Czarnego Popiołu","Dogasłych Palenisk","Zwęglonych Kości","Czerwonego Żaru","Martwych Pieców","Popielnej Burzy"),"Pustkowia rozciągają się daleko między polami popiołu, ruinami i pęknięciami ziemi."),
        "Rozbite Niebo": (("Most","Półka","Taras","Grań","Platforma"),("Piorunów","Rozdartych Chmur","Nawałnicy","Gromowych Wież","Podniebnych Ruin","Białego Wiatru"),"Podniebne mosty i półki tworzą wielodrogowy region wysoko nad chmurami."),
        "Wybrzeże Pustki": (("Brzeg","Molo","Ruiny","Zatoka","Taras"),("Czarnego Przypływu","Bezgwiezdnej Wody","Zatopionych Dzwonów","Pustych Latarni","Martwych Żagli","Otchłani"),"Czarny brzeg ciągnie się przez zatoki, mola i zatopione ruiny połączone wieloma ścieżkami."),
        "Korona Świata": (("Grobla","Galeria","Taras","Schody","Dziedziniec"),("Absolutu","Wiecznego Światła","Ponadczasowych Bram","Milczących Gwiazd","Białego Kamienia","Ostatniej Korony"),"Monumentalny szczyt tworzy rozległy kompleks tarasów, galerii i wielkich schodów."),
    }
    detail = (
        "Boczna droga wraca do dalszej części regionu, więc nie jest to ślepy krzyż.",
        "Kilka przejść pozwala obejść główny trakt i odkrywać teren różnymi trasami.",
        "Ścieżki łączą ten sektor z sąsiednimi częściami regionu w dużą pętlę.",
        "To jeden z wielu równoległych traktów; mapa ma liczne alternatywne połączenia.",
    )

    # Zbierz zwykłe moby obecnych regionów zanim dołożymy nowe spawny.
    room_zone = {rid: room.get("zone") for rid, room in ROOMS.items()}
    zone_pools = {}
    for rid, mid in list(MOB_SPAWNS):
        zone = room_zone.get(rid)
        if zone not in targets:
            continue
        tmpl = MOB_TEMPLATES.get(mid, {})
        if tmpl.get("world_boss") or tmpl.get("boss") or tmpl.get("boss_mechanic"):
            continue
        zone_pools.setdefault(zone, [])
        if mid not in zone_pools[zone]:
            zone_pools[zone].append(mid)

    # Cmentarz dostaje gęstszy zestaw nieumarłych, aby 0/25 nie wymagało stania na respawnie.
    cemetery_pool = [
        mid for mid in (
            "cemetery_restless_dead", "cemetery_bone_collector",
            "cemetery_bell_wraith", "cemetery_steel_skeleton",
            "cemetery_grave_hound", "cemetery_crypt_reaper",
            "cemetery_mourning_knight",
        ) if mid in MOB_TEMPLATES
    ]
    if cemetery_pool:
        zone_pools["Stary Cmentarz"] = cemetery_pool

    for zone, target in targets.items():
        existing = [rid for rid, room in ROOMS.items() if room.get("zone") == zone]
        need = max(0, int(target) - len(existing))
        if need <= 0:
            continue
        anchor = anchors[zone]
        prefixes, suffixes, zone_desc = words[zone]
        safe = _collection_slug(zone)
        new_ids = [f"v0930_{safe}_{i+1:02d}" for i in range(need)]
        for i, rid in enumerate(new_ids):
            prefix = prefixes[i % len(prefixes)]
            suffix = suffixes[(i // len(prefixes) + i) % len(suffixes)]
            room_data = {
                "zone": zone,
                "name": f"{prefix} {suffix}",
                "desc": f"{zone_desc} {detail[i % len(detail)]}",
                "exits": {},
            }
            endgame_recommended = dict(V0923_ENDGAME_REGIONS).get(zone)
            if endgame_recommended is not None:
                room_data["recommended_mastery"] = int(endgame_recommended)
            ROOMS[rid] = room_data

        # Dołącz nową część bez nadpisywania istniejących wyjść.
        anchor_exits = ROOMS[anchor].setdefault("exits", {})
        attach = next((d for d in ("south","east","west","north","down","up") if d not in anchor_exits), None)
        if attach is None:
            attach = "down"
        anchor_exits[attach] = new_ids[0]
        ROOMS[new_ids[0]]["exits"][reverse[attach]] = anchor

        # Łącznik + nieregularna siatka 5 kolumn. Pełne poziome rzędy i kilka
        # pionowych łączników dają pętle i alternatywne trasy, ale nie prosty krzyż.
        if len(new_ids) > 1:
            back_from_connector = reverse[attach]
            forward = "south" if back_from_connector != "south" else "east"
            ROOMS[new_ids[0]]["exits"][forward] = new_ids[1]
            ROOMS[new_ids[1]]["exits"][reverse[forward]] = new_ids[0]

            grid = new_ids[1:]
            width = 5
            for idx, rid in enumerate(grid):
                row, col = divmod(idx, width)
                # poziome przejścia
                if col + 1 < width and idx + 1 < len(grid):
                    other = grid[idx + 1]
                    ROOMS[rid]["exits"]["east"] = other
                    ROOMS[other]["exits"]["west"] = rid
                # pionowe przejścia: kolumny skrajne zawsze, środkowe naprzemiennie
                down_idx = idx + width
                if down_idx < len(grid) and (col in (0, width-1) or (row + col) % 2 == 0):
                    other = grid[down_idx]
                    ROOMS[rid]["exits"]["south"] = other
                    ROOMS[other]["exits"]["north"] = rid

        # Zaludnij nowe sektory istniejącymi zwykłymi mobami regionu.
        pool = zone_pools.get(zone, [])
        if pool:
            for i, rid in enumerate(new_ids):
                MOB_SPAWNS.append((rid, pool[i % len(pool)]))
                if i % 4 == 0 and len(pool) > 1:
                    MOB_SPAWNS.append((rid, pool[(i + 1) % len(pool)]))

    # Achievement ma oznaczać faktyczne odkrycie całego aktualnego świata.
    tiers = list(ACHIEVEMENT_TRACKS.get("exploration_rooms", {}).get("tiers", ()))
    if tiers:
        fixed = [(req, rank) for req, rank in tiers if rank != "Platinum"]
        fixed.append((len(ROOMS), "Platinum"))
        ACHIEVEMENT_TRACKS["exploration_rooms"]["tiers"] = tuple(fixed)

build_v0930_large_exploration_regions()


# ============================================================
# v0.10.0 - MASSIVE WORLD & DUNGEONS
# ============================================================
V0100_MAJOR_FLOOR_ROOMS = 15
V0100_PROF_FLOOR_ROOMS = 10
V0100_RESOURCE_ROOM_SETS = (
    "MINING_ROOMS", "FISHING_ROOMS", "SEA_FISHING_ROOMS",
    "OCEAN_FISHING_ROOMS", "MARINE_FISHING_ROOMS",
    "WOODCUTTING_ROOMS", "HERBALISM_ROOMS", "MEADOW_HERBALISM_ROOMS",
)

V0100_INSTANCE_LABELS = {
    "crypt": (
        "Galeria Sarkofagów", "Korytarz Kości", "Zawalona Katakumba",
        "Komnata Pieczęci", "Aleja Grobowców", "Sala Zgaszonych Świec",
        "Krypta Bezimiennych", "Kamienny Labirynt", "Przejście Strażników",
        "Komnata Popiołu", "Korytarz Otchłani", "Sala Starych Run",
        "Galeria Umarłych", "Schody Głębi",
    ),
    "mythic_crypt": (
        "Mityczna Galeria Kości", "Korytarz Pękniętej Duszy", "Komnata Otchłani",
        "Sala Czarnego Płomienia", "Katakumba Pustki", "Galeria Krwawych Run",
        "Krypta Bez Końca", "Korytarz Widm", "Komnata Zatraconych",
        "Przejście Nekromantów", "Sala Echa", "Grobowiec Pustki",
        "Labirynt Dusz", "Brama Głębszej Otchłani",
    ),
    "astral": (
        "Gwiezdna Galeria", "Taras Konstelacji", "Korytarz Mgławic",
        "Sala Gwiezdnego Pyłu", "Most Astralny", "Komnata Orbit",
        "Galeria Firmamentu", "Taras Srebrnych Gwiazd", "Sala Światła",
        "Korytarz Meteorytów", "Komnata Sfer", "Most Niebios",
        "Galeria Konstelacji", "Schody Wyższego Kręgu",
    ),
    "mythic_astral": (
        "Mityczna Galeria Gwiazd", "Taras Pustych Konstelacji", "Korytarz Zaćmienia",
        "Sala Rozdartego Nieba", "Most Wieczności", "Komnata Ciemnych Orbit",
        "Galeria Pustki", "Taras Gwiezdnej Burzy", "Sala Załamanego Światła",
        "Korytarz Serafinów", "Komnata Sfer", "Most Firmamentu",
        "Labirynt Gwiazd", "Brama Wyższej Sfery",
    ),
    "giant": (
        "Galeria Kolosów", "Kamienna Hala", "Korytarz Cyklopów",
        "Sala Głazów", "Dziedziniec Tytanów", "Most Gigantów",
        "Zbrojownia Olbrzymów", "Komnata Runicznego Kamienia", "Hala Wojowników",
        "Korytarz Burzy", "Sala Żelaznych Bram", "Taras Twierdzy",
        "Galeria Królewska", "Schody Wyższego Bastionu",
    ),
    "profession": (
        "Boczna Komora", "Rozgałęziony Korytarz", "Głęboki Sektor",
        "Komora Zasobów", "Stare Przejście", "Ukryta Odnoga",
        "Szeroka Galeria", "Mistrzowski Sektor", "Przejście Głębiej",
    ),
    "mine": (
        "Galeria Skał", "Komora Żył", "Tunel Głębinowy",
        "Sala Kryształów", "Zawalony Chodnik", "Szyb Boczny",
        "Komora Rudy", "Stary Przekop", "Schody Głębi",
    ),
}


def v0100_instance_spec(room_id):
    """Zwraca opis kanonicznego pokoju piętra, bez jego nowych odnóg."""
    rid = str(room_id or "")
    floor = crypt_floor_number(rid)
    if floor is not None and rid == crypt_floor_id(floor):
        return {
            "kind": "crypt", "floor": floor, "next_dir": "down",
            "rooms": V0100_MAJOR_FLOOR_ROOMS, "boss_flag": "crypt_boss",
        }
    floor = mythic_crypt_floor_number(rid)
    if floor is not None and rid == mythic_crypt_floor_id(floor):
        return {
            "kind": "mythic_crypt", "floor": floor, "next_dir": "down",
            "rooms": V0100_MAJOR_FLOOR_ROOMS, "boss_flag": "mythic_crypt_boss",
        }
    floor = astral_floor_number(rid)
    if floor is not None and rid == astral_floor_id(floor):
        return {
            "kind": "astral", "floor": floor, "next_dir": "up",
            "rooms": V0100_MAJOR_FLOOR_ROOMS, "boss_flag": "astral_boss",
        }
    floor = mythic_astral_floor_number(rid)
    if floor is not None and rid == mythic_astral_floor_id(floor):
        return {
            "kind": "mythic_astral", "floor": floor, "next_dir": "up",
            "rooms": V0100_MAJOR_FLOOR_ROOMS, "boss_flag": "mythic_astral_boss",
        }
    floor = giant_fortress_floor_number(rid)
    if floor is not None and rid == giant_fortress_floor_id(floor):
        return {
            "kind": "giant", "floor": floor, "next_dir": "up",
            "rooms": V0100_MAJOR_FLOOR_ROOMS, "boss_flag": "giant_fortress_boss",
        }
    floor = mine_floor_number(rid)
    if floor is not None and rid == mine_floor_id(floor):
        return {
            "kind": "mine", "floor": floor, "next_dir": "down",
            "rooms": V0100_PROF_FLOOR_ROOMS, "boss_flag": None,
        }
    dungeon, floor = profession_dungeon_floor(rid)
    if dungeon is not None and rid == profession_dungeon_room_id(dungeon, floor):
        next_dirs = {
            "crystal_mine": "down", "sunken_grotto": "down",
            "ancient_forest": "south", "alchemy_garden": "east",
        }
        return {
            "kind": "profession", "profession_dungeon": dungeon,
            "floor": floor, "next_dir": next_dirs[dungeon],
            "rooms": V0100_PROF_FLOOR_ROOMS, "boss_flag": None,
        }
    return None


def v0100_subroom_id(canonical_room, index):
    return f"{canonical_room}_r{int(index):02d}"


def v0100_copy_resource_membership(canonical_room, subrooms):
    for set_name in V0100_RESOURCE_ROOM_SETS:
        room_set = globals().get(set_name)
        if isinstance(room_set, set) and canonical_room in room_set:
            room_set.update(subrooms)


def v0100_connect_pair(a, direction, b, reverse_direction):
    ROOMS[a].setdefault("exits", {})[direction] = b
    ROOMS[b].setdefault("exits", {})[reverse_direction] = a


def v0100_expand_instance_floor(canonical_room, spawn_pairs=None, runtime=False):
    """Zmienia jedno liniowe piętro w dużą, zapętloną mapę.

    Kanoniczny pokój pozostaje lądowaniem/checkpointem. Wyjście na kolejne
    piętro zostaje przeniesione do ostatniej komnaty. Na piętrze bossa boss
    również trafia do tej komnaty, dzięki czemu naprawdę pilnuje dalszej drogi.
    """
    canonical_room = str(canonical_room or "")
    spec = v0100_instance_spec(canonical_room)
    if not spec or canonical_room not in ROOMS:
        return list(spawn_pairs or ())
    first_sub = v0100_subroom_id(canonical_room, 1)
    if first_sub in ROOMS:
        return list(spawn_pairs or ())

    base = ROOMS[canonical_room]
    exits = base.setdefault("exits", {})
    next_dir = spec["next_dir"]
    vertical_reverse = {"down":"up", "up":"down", "south":"north", "north":"south", "east":"west", "west":"east"}
    previous_dir = vertical_reverse[next_dir]
    # Jeżeli poprzednie piętro jest już rozbudowane, powrót prowadzi do jego
    # prawdziwej komnaty schodów, a nie teleportuje na początek piętra.
    previous_target = exits.get(previous_dir)
    previous_spec = v0100_instance_spec(previous_target) if previous_target else None
    if previous_spec:
        previous_final = v0100_subroom_id(previous_target, int(previous_spec["rooms"]) - 1)
        if previous_final in ROOMS:
            exits[previous_dir] = previous_final
    next_target = exits.pop(next_dir, None)
    total_rooms = max(3, int(spec["rooms"]))
    subrooms = [v0100_subroom_id(canonical_room, i) for i in range(1, total_rooms)]
    maze_rooms = subrooms[:-1]
    final_room = subrooms[-1]
    labels = V0100_INSTANCE_LABELS[spec["kind"]]
    floor = int(spec["floor"])
    zone = base.get("zone", "Loch")
    generated_profile_v025 = v0250_instance_floor_profile(spec["kind"], floor)

    for index, rid in enumerate(subrooms, 1):
        label_seed = int(hashlib.sha256(f"{spec['kind']}:{floor}".encode("utf-8")).hexdigest()[:8], 16)
        label = labels[(label_seed + index - 1) % len(labels)]
        if rid == final_room:
            if spec.get("boss_flag") and is_crypt_boss_floor(floor) and spec["kind"] in {"crypt", "mythic_crypt"}:
                label = "Komnata Strażnika Progu"
            elif spec.get("boss_flag") and spec["kind"] in {"astral", "mythic_astral"} and floor % 10 == 0:
                label = "Komnata Strażnika Kręgu"
            elif spec.get("boss_flag") and spec["kind"] == "giant" and floor % 10 == 0:
                label = "Sala Strażnika Bastionu"
        ROOMS[rid] = {
            "zone": zone,
            "name": f"{label} — {floor}",
            "desc": (
                f"Rozległa część poziomu {floor}. Korytarze rozchodzą się w kilka stron, "
                "łączą w pętle i prowadzą przez boczne komnaty. To pełne piętro lochu, "
                "a nie pojedynczy liniowy pokój. "
                f"Generator piętra: {generated_profile_v025['layout']}; "
                f"motyw: {generated_profile_v025['motif']}."
            ),
            "exits": {},
            "v0100_instance_kind": spec["kind"],
            "v0250_generator_profile": generated_profile_v025,
            "v0100_floor": floor,
            "v0100_floor_room": index + 1,
            "procedural_dynamic": True,
        }
        if "recommended_mastery" in base:
            ROOMS[rid]["recommended_mastery"] = base["recommended_mastery"]
        dungeon = spec.get("profession_dungeon")
        if dungeon:
            ROOMS[rid]["profession_dungeon"] = dungeon
            ROOMS[rid]["profession_dungeon_floor"] = floor

    # v0.11.0: układ jest proceduralny, ale deterministyczny dla rodzaju i numeru
    # piętra. Restart serwera nie zmienia mapy w trakcie progresji gracza.
    seed_text = f"{V0250_WORLD_SEED}:soulbound-v0110:{spec['kind']}:{floor}:{spec.get('profession_dungeon','')}"
    floor_seed = int(hashlib.sha256(seed_text.encode("utf-8")).hexdigest()[:16], 16)
    floor_rng = random.Random(floor_seed)

    # Wejście na piętro prowadzi do labiryntu bokiem, a nie od razu dalej.
    free_attach = [d for d in ("east", "south", "west", "north") if d not in exits]
    attach_dir = floor_rng.choice(free_attach) if free_attach else "east"
    reverse = {"east": "west", "west": "east", "north": "south", "south": "north"}
    v0100_connect_pair(canonical_room, attach_dir, maze_rooms[0], reverse[attach_dir])

    # Różne piętra dostają siatkę o szerokości 3 albo 4. Każdy rząd pozostaje
    # spójny, a między kolejnymi rzędami zawsze istnieje co najmniej jedno
    # przejście; dodatkowe przejścia tworzą losowane, lecz stałe pętle.
    width = 3 + floor_rng.randrange(2)
    for idx, rid in enumerate(maze_rooms):
        row, col = divmod(idx, width)
        if col + 1 < width and idx + 1 < len(maze_rooms):
            other = maze_rooms[idx + 1]
            if "east" not in ROOMS[rid]["exits"] and "west" not in ROOMS[other]["exits"]:
                v0100_connect_pair(rid, "east", other, "west")

    rows = (len(maze_rooms) + width - 1) // width
    for row in range(rows - 1):
        current = list(range(row * width, min((row + 1) * width, len(maze_rooms))))
        below = list(range((row + 1) * width, min((row + 2) * width, len(maze_rooms))))
        possible = [c for c in range(min(len(current), len(below)))]
        if not possible:
            continue
        chosen = {floor_rng.choice(possible)}
        # Każde piętro ma co najmniej jedną prawdziwą pętlę, a część rzędów
        # dostaje dodatkowe alternatywne przejście.
        if len(possible) > 1 and (row == 0 or floor_rng.random() < 0.70):
            extras = [c for c in possible if c not in chosen]
            if extras:
                chosen.add(floor_rng.choice(extras))
        for c in sorted(chosen):
            a = maze_rooms[current[c]]
            b = maze_rooms[below[c]]
            if "south" not in ROOMS[a]["exits"] and "north" not in ROOMS[b]["exits"]:
                v0100_connect_pair(a, "south", b, "north")

    # Ostatnia komnata jest za labiryntem i zawiera drogę na kolejne piętro.
    tail = maze_rooms[-1]
    if "east" in ROOMS[tail]["exits"]:
        # Dla krótszej siatki użyj pierwszej wolnej pary.
        for d, rev in (("south", "north"), ("north", "south"), ("west", "east")):
            if d not in ROOMS[tail]["exits"] and rev not in ROOMS[final_room]["exits"]:
                v0100_connect_pair(tail, d, final_room, rev)
                break
    else:
        v0100_connect_pair(tail, "east", final_room, "west")
    if next_target:
        ROOMS[final_room]["exits"][next_dir] = next_target
        # Gdy następne piętro istnieje już statycznie, jego droga powrotna
        # wskazuje na tę samą klatkę schodową. Dynamiczne piętro naprawi ten
        # link w chwili utworzenia.
        next_spec = v0100_instance_spec(next_target)
        if next_spec and next_target in ROOMS:
            ROOMS[next_target].setdefault("exits", {})[vertical_reverse[next_dir]] = final_room

    v0100_copy_resource_membership(canonical_room, subrooms)

    pairs = list(spawn_pairs or ())
    if not pairs and not runtime:
        pairs = [(r, t) for r, t in MOB_SPAWNS if r == canonical_room]
    boss_flag = spec.get("boss_flag")
    boss_ids = []
    regular_ids = []
    for r, tid in pairs:
        if r != canonical_room:
            continue
        template = MOB_TEMPLATES.get(tid, {})
        if boss_flag and template.get(boss_flag):
            boss_ids.append(tid)
        else:
            regular_ids.append(tid)

    # Przy statycznych piętrach przenieś bossów z lądowania do sali wyjściowej.
    if not runtime and boss_ids:
        moved = set(boss_ids)
        MOB_SPAWNS[:] = [
            (r, t) for r, t in MOB_SPAWNS
            if not (r == canonical_room and t in moved)
        ]
        for tid in boss_ids:
            MOB_SPAWNS.append((final_room, tid))
    elif runtime and boss_ids:
        pairs = [
            (final_room if (r == canonical_room and t in set(boss_ids)) else r, t)
            for r, t in pairs
        ]

    # Każda boczna komnata dostaje przeciwnika; część komnat ma dwa różne typy.
    extra_pairs = []
    if regular_ids:
        for index, rid in enumerate(subrooms):
            if rid == final_room and boss_ids:
                continue
            extra_pairs.append((rid, regular_ids[index % len(regular_ids)]))
            if index % 3 == 1 and len(regular_ids) > 1:
                extra_pairs.append((rid, regular_ids[(index + 1) % len(regular_ids)]))
    if runtime:
        pairs.extend(extra_pairs)
        return pairs
    MOB_SPAWNS.extend(extra_pairs)
    return pairs


def build_v0100_massive_instance_floors():
    canonical = []
    canonical.extend(crypt_floor_id(f) for f in range(1, CRYPT_PREGENERATED_MAX_FLOOR + 1))
    canonical.extend(mythic_crypt_floor_id(f) for f in range(1, MYTHIC_MAX_FLOOR + 1))
    canonical.extend(astral_floor_id(f) for f in range(ASTRAL_MIN_FLOOR, ASTRAL_MAX_FLOOR + 1))
    canonical.extend(mythic_astral_floor_id(f) for f in range(1, MYTHIC_MAX_FLOOR + 1))
    canonical.extend(giant_fortress_floor_id(f) for f in range(1, GIANT_FORTRESS_MAX_FLOOR + 1))
    for dungeon in PROF_DUNGEON_PREFIXES:
        canonical.extend(profession_dungeon_room_id(dungeon, f) for f in range(1, PROF_DUNGEON_MAX_FLOOR + 1))
    for rid in canonical:
        if rid in ROOMS:
            v0100_expand_instance_floor(rid, runtime=False)


V0100_SURFACE_TARGETS = {
    "Wybrzeże": 30,
    "Łąki": 30,
    "Podziemia": 30,
    "Łąki Zielarskie": 30,
    "Jaskinia Trolli": 36,
    "Obozowiska Bandytów": 30,
    "Jaskinie Goblinów": 30,
    "Ruiny Strażnicy": 30,
    "Stary Cmentarz": 30,
    "Ruiny Kultystów": 30,
    "Legowisko Bestii": 30,
    "Nekropolia": 30,
    "Kanały Pod Miastem": 30,
    "Lodowe Jaskinie": 30,
    "Las Szeptów": 30,
    "Dzicz": 36,
    "Pustynia": 36,
    "Bagna": 36,
    "Góry": 36,
    "Popielne Pustkowia": 40,
    "Rozbite Niebo": 40,
    "Wybrzeże Pustki": 40,
    "Korona Świata": 40,
}

V0100_SURFACE_WORDS = {
    "Wybrzeże": ("Brzeg", "Klif", "Zatoka", "Molo", "Wydma"),
    "Łąki": ("Łąka", "Polana", "Pastwisko", "Wzgórze", "Zagajnik"),
    "Podziemia": ("Korytarz", "Komnata", "Galeria", "Katakumba", "Przejście"),
    "Łąki Zielarskie": ("Łąka", "Polana", "Ogród", "Zagajnik", "Dolina"),
    "Jaskinia Trolli": ("Grota", "Tunel", "Sala", "Rozpadlina", "Korytarz"),
    "Dzicz": ("Trakt", "Parów", "Polana", "Urwisko", "Ostęp"),
    "Pustynia": ("Wydmy", "Kanion", "Równina", "Ruiny", "Szlak"),
    "Bagna": ("Mokradło", "Groble", "Rozlewisko", "Torfowisko", "Zarośla"),
    "Góry": ("Grań", "Przełęcz", "Półka", "Wąwóz", "Szlak"),
}


def v0100_zone_regular_pool(zone):
    result = []
    for rid, tid in MOB_SPAWNS:
        if ROOMS.get(rid, {}).get("zone") != zone:
            continue
        template = MOB_TEMPLATES.get(tid, {})
        if (
            template.get("world_boss") or template.get("boss")
            or template.get("boss_mechanic") or template.get("crypt_boss")
            or template.get("astral_boss") or template.get("mythic_crypt_boss")
            or template.get("mythic_astral_boss") or template.get("giant_fortress_boss")
        ):
            continue
        if tid not in result:
            result.append(tid)
    return result


def v0100_find_surface_anchor(zone):
    candidates = [rid for rid, room in ROOMS.items() if room.get("zone") == zone]
    # Najpierw wybierz pomieszczenie z wolnym kierunkiem poziomym i bez bossa.
    boss_rooms = {
        rid for rid, tid in MOB_SPAWNS
        if ROOMS.get(rid, {}).get("zone") == zone
        and (
            MOB_TEMPLATES.get(tid, {}).get("world_boss")
            or MOB_TEMPLATES.get(tid, {}).get("boss_mechanic")
        )
    }
    candidates.sort(key=lambda rid: (rid in boss_rooms, len(ROOMS[rid].get("exits", {})), rid))
    for rid in candidates:
        exits = ROOMS[rid].get("exits", {})
        if any(d not in exits for d in ("east", "south", "west", "north")):
            return rid
    return candidates[0] if candidates else None


def v0100_expand_surface_zone(zone, target):
    existing = [rid for rid, room in ROOMS.items() if room.get("zone") == zone]
    need = max(0, int(target) - len(existing))
    if not need:
        return
    anchor = v0100_find_surface_anchor(zone)
    if not anchor:
        return
    pool = v0100_zone_regular_pool(zone)
    safe = _collection_slug(zone)
    new_ids = [f"v0100_{safe}_{i+1:03d}" for i in range(need)]
    words = V0100_SURFACE_WORDS.get(zone, ("Szlak", "Sektor", "Przejście", "Odnoga", "Rejon"))
    for i, rid in enumerate(new_ids):
        word = words[i % len(words)]
        ROOMS[rid] = {
            "zone": zone,
            "name": f"{word} {zone} {i+1}",
            "desc": (
                f"Rozległa część regionu {zone}. Teren rozchodzi się na boczne drogi, "
                "pętle i alternatywne przejścia, dzięki czemu obszar nie jest małym expowiskiem."
            ),
            "exits": {},
            "procedural_surface_v0100": True,
        }
        endgame_recommended = dict(V0923_ENDGAME_REGIONS).get(zone)
        if endgame_recommended is not None:
            ROOMS[rid]["recommended_mastery"] = int(endgame_recommended)

    reverse = {"east":"west", "west":"east", "north":"south", "south":"north"}
    anchor_exits = ROOMS[anchor].setdefault("exits", {})
    attach = next((d for d in ("east", "south", "west", "north") if d not in anchor_exits), None)
    if attach is None:
        return
    v0100_connect_pair(anchor, attach, new_ids[0], reverse[attach])

    width = 5
    for idx, rid in enumerate(new_ids):
        row, col = divmod(idx, width)
        if col + 1 < width and idx + 1 < len(new_ids):
            other = new_ids[idx + 1]
            if "east" not in ROOMS[rid]["exits"] and "west" not in ROOMS[other]["exits"]:
                v0100_connect_pair(rid, "east", other, "west")
        down_idx = idx + width
        if down_idx < len(new_ids) and (col in (0, width - 1) or (row + col) % 2 == 0):
            other = new_ids[down_idx]
            if "south" not in ROOMS[rid]["exits"] and "north" not in ROOMS[other]["exits"]:
                v0100_connect_pair(rid, "south", other, "north")

    # Skopiuj charakter profesyjny regionu, jeśli stara część już go miała.
    for set_name in V0100_RESOURCE_ROOM_SETS:
        room_set = globals().get(set_name)
        if isinstance(room_set, set) and any(r in room_set for r in existing):
            room_set.update(new_ids)

    if pool:
        for i, rid in enumerate(new_ids):
            MOB_SPAWNS.append((rid, pool[i % len(pool)]))
            if i % 3 == 0 and len(pool) > 1:
                MOB_SPAWNS.append((rid, pool[(i + 1) % len(pool)]))


def build_v0100_massive_surface_world():
    for zone, target in V0100_SURFACE_TARGETS.items():
        v0100_expand_surface_zone(zone, target)


# v0.11.0: piętrowe instancje nie są już rozwijane przy starcie serwera.
# Ich pełne mapy powstają dopiero przy pierwszym wejściu gracza.
build_v0100_massive_surface_world()

# ============================================================
# v0.11.0 - FULL LAZY DYNAMIC DUNGEONS
# ============================================================
# Od tej wersji wszystkie piętrowe instancje są tworzone dopiero przy wejściu.
# Zachowujemy istniejące template'y mobów/EQ dla kompatybilności zapisów i
# questów, ale usuwamy tysiące gotowych pokojów oraz ich statyczne spawny.
# Dzięki temu piętro 1 działa dokładnie tak samo proceduralnie jak piętro 401+.

def v0110_dynamic_instance_kind(room_id):
    rid = str(room_id or "")
    if crypt_floor_number(rid) is not None:
        return "crypt"
    if mythic_crypt_floor_number(rid) is not None:
        return "mythic_crypt"
    if astral_floor_number(rid) is not None:
        return "astral"
    if mythic_astral_floor_number(rid) is not None:
        return "mythic_astral"
    if giant_fortress_floor_number(rid) is not None:
        return "giant"
    if mine_floor_number(rid) is not None:
        return "mine"
    dungeon, floor = profession_dungeon_floor(rid)
    if dungeon is not None and floor is not None:
        return "profession"
    return None


def v0110_is_dynamic_instance_room(room_id):
    return v0110_dynamic_instance_kind(room_id) is not None


def v0110_remove_pregenerated_instance_rooms():
    removed = {rid for rid in tuple(ROOMS) if v0110_is_dynamic_instance_room(rid)}
    if not removed:
        return 0

    # Usuń wyłącznie pokoje piętrowych instancji. Bramy, wejścia i huby świata
    # pozostają i nadal wskazują na identyfikator pierwszego dynamicznego piętra.
    for rid in removed:
        ROOMS.pop(rid, None)

    MOB_SPAWNS[:] = [(rid, tid) for rid, tid in MOB_SPAWNS if rid not in removed]

    # Zestawy zasobowe mają zawierać tylko realnie istniejące pokoje.
    # create_infinite_* doda je ponownie, kiedy piętro faktycznie powstanie.
    for set_name in V0100_RESOURCE_ROOM_SETS + ("MINING_DEPTH_ROOMS",):
        room_set = globals().get(set_name)
        if isinstance(room_set, set):
            room_set.difference_update(removed)

    return len(removed)


V0110_REMOVED_PREGENERATED_INSTANCE_ROOMS = v0110_remove_pregenerated_instance_rooms()

# Kotwice wejściowe są stałe, ale ich cele nie muszą istnieć aż do pierwszego kroku.
V0110_DYNAMIC_DUNGEON_ENTRANCES = {
    "crypt_hall": crypt_floor_id(1),
    "mythic_crypt_gate": mythic_crypt_floor_id(1),
    "astral_gate": astral_floor_id(ASTRAL_MIN_FLOOR),
    "mythic_astral_gate": mythic_astral_floor_id(1),
    "giant_fortress_gate": giant_fortress_floor_id(1),
    "crystal_chamber": mine_floor_id(1),
    "profession_crystal_mine": profession_dungeon_room_id("crystal_mine", 1),
    "sea_pier": profession_dungeon_room_id("sunken_grotto", 1),
    "deep_grove": profession_dungeon_room_id("ancient_forest", 1),
    "herbalist_hut": profession_dungeon_room_id("alchemy_garden", 1),
}

# ============================================================
# v0.10.2 - CITY LIFE + OUTSKIRTS + ROAMING MOBS + TOOL BALANCE
# ============================================================

def build_v0102_city_and_outskirts():
    """Rozbudowuje Miasto Dusz i tworzy żywe przedmieścia.

    Miasto pozostaje strefą bezpieczną bez wrogich spawnów. Przedmieścia
    są niskopoziomowym obszarem przejściowym między bramami i Łąkami.
    """
    city_rooms = {
        "artisan_lane": {
            "zone":"Miasto Dusz", "name":"Ulica Rzemieślników",
            "desc":"Kamienna ulica pachnie drewnem, skórą i rozgrzanym metalem. Z obu stron stoją małe warsztaty miejskich fachowców.",
            "exits":{},
        },
        "tailor_workshop": {
            "zone":"Miasto Dusz", "name":"Pracownia Krawiecka",
            "desc":"Stoły są przykryte tkaninami, nićmi i wykrojami płaszczy dla mieszkańców oraz straży.",
            "exits":{},
        },
        "carpenter_workshop": {
            "zone":"Miasto Dusz", "name":"Warsztat Ciesielski",
            "desc":"Belki, deski i gotowe framugi wypełniają pracownię. Cieśla naprawia wozy i miejskie budynki.",
            "exits":{},
        },
        "leatherworker_workshop": {
            "zone":"Miasto Dusz", "name":"Warsztat Kaletnika",
            "desc":"Na półkach leżą pasy, torby i uprzęże. W powietrzu czuć garbowaną skórę i wosk.",
            "exits":{},
        },
        "mason_yard": {
            "zone":"Miasto Dusz", "name":"Dziedziniec Kamieniarzy",
            "desc":"Kamienne bloki, dłuta i fragmenty nowych murów tworzą głośny plac pracy budowniczych.",
            "exits":{},
        },
        "potter_workshop": {
            "zone":"Miasto Dusz", "name":"Warsztat Garncarski",
            "desc":"Koło garncarskie obraca się obok pieca. Na półkach schną misy, dzbany i naczynia dla karczmy.",
            "exits":{},
        },
        "lantern_alley": {
            "zone":"Miasto Dusz", "name":"Zaułek Latarni",
            "desc":"Wąski zaułek oświetlają rzędy błękitnych lamp. Mieszkańcy skracają tędy drogę do południowej dzielnicy.",
            "exits":{},
        },
        "city_bakery": {
            "zone":"Miasto Dusz", "name":"Piekarnia Pod Złotym Bochenkiem",
            "desc":"Ciepły zapach chleba wypełnia niewielką piekarnię zaopatrującą karczmę i strażników przy bramach.",
            "exits":{},
        },
        "healer_house": {
            "zone":"Miasto Dusz", "name":"Dom Uzdrowicielki",
            "desc":"Cicha izba z łóżkami, bandażami i suszonymi ziołami służy rannym podróżnym oraz mieszkańcom.",
            "exits":{},
        },
        "residential_lane": {
            "zone":"Miasto Dusz", "name":"Ulica Domów",
            "desc":"Szereg niewielkich kamiennych domów otacza spokojną ulicę z ławkami i studzienkami deszczowymi.",
            "exits":{},
        },
        "well_square": {
            "zone":"Miasto Dusz", "name":"Plac Starej Studni",
            "desc":"Mały plac skupia mieszkańców południowej dzielnicy. Pośrodku stoi głęboka, nadal używana studnia.",
            "exits":{},
        },
        "courier_office": {
            "zone":"Miasto Dusz", "name":"Poczta i Biuro Kurierów",
            "desc":"Posłańcy sortują listy, paczki i meldunki przeznaczone dla portu, straży oraz odległych posterunków.",
            "exits":{},
        },
        "dockside_lane": {
            "zone":"Miasto Dusz", "name":"Ulica Portowa",
            "desc":"Szeroka droga biegnie wzdłuż magazynów i nabrzeża. Słychać liny, dzwonki statków i nawoływania tragarzy.",
            "exits":{},
        },
        "harbor_warehouse": {
            "zone":"Miasto Dusz", "name":"Magazyn Portowy",
            "desc":"Skrzynie, beczki i zaplombowane pakunki czekają na odbiór przez kupców oraz rybaków.",
            "exits":{},
        },
        "ropewalk": {
            "zone":"Miasto Dusz", "name":"Powroźnia",
            "desc":"Długi warsztat służy do skręcania lin dla statków, wozów i miejskich dźwigów.",
            "exits":{},
        },
        "shipwright_yard": {
            "zone":"Miasto Dusz", "name":"Stocznia Miejska",
            "desc":"Na drewnianych podporach stoi naprawiany kuter. Szkutnicy wymieniają deski i uszczelniają kadłub.",
            "exits":{},
        },
        "scholar_lane": {
            "zone":"Miasto Dusz", "name":"Ulica Uczonych",
            "desc":"Spokojna uliczka łączy Plac Treningowy z domami skrybów, nauczycieli i kartografów.",
            "exits":{},
        },
        "cartographer_house": {
            "zone":"Miasto Dusz", "name":"Pracownia Kartografa",
            "desc":"Ściany pokrywają mapy traktów, ruin, bagien i gór. Na dużym stole powstają nowe szkice szlaków.",
            "exits":{},
        },
        "city_watch_office": {
            "zone":"Miasto Dusz", "name":"Biuro Patroli Miejskich",
            "desc":"Małe biuro przy północnej dzielnicy zbiera zgłoszenia mieszkańców i rozdziela krótkie patrole poza murami.",
            "exits":{},
        },
    }
    ROOMS.update(city_rooms)

    def connect(a, da, b, db):
        ROOMS[a].setdefault("exits", {})[da] = b
        ROOMS[b].setdefault("exits", {})[db] = a

    # Dzielnica rzemieślnicza przy Kuźni.
    connect("forge", "east", "artisan_lane", "west")
    connect("artisan_lane", "north", "tailor_workshop", "south")
    connect("artisan_lane", "east", "carpenter_workshop", "west")
    connect("artisan_lane", "south", "mason_yard", "north")
    connect("carpenter_workshop", "east", "leatherworker_workshop", "west")
    connect("carpenter_workshop", "south", "potter_workshop", "north")
    connect("potter_workshop", "west", "mason_yard", "east")

    # Południowa dzielnica mieszkalna.
    connect("south_street", "west", "lantern_alley", "east")
    connect("lantern_alley", "west", "residential_lane", "east")
    connect("lantern_alley", "south", "city_bakery", "north")
    connect("residential_lane", "west", "well_square", "east")
    connect("residential_lane", "south", "healer_house", "north")
    connect("well_square", "south", "courier_office", "north")
    connect("courier_office", "east", "healer_house", "west")

    # Dzielnica portowa.
    connect("harbor", "north", "dockside_lane", "south")
    connect("dockside_lane", "west", "harbor_warehouse", "east")
    connect("dockside_lane", "east", "ropewalk", "west")
    connect("ropewalk", "east", "shipwright_yard", "west")
    connect("shipwright_yard", "south", "dockside_lane", "north")

    # Uczeni i patrole.
    connect("training", "east", "scholar_lane", "west")
    connect("scholar_lane", "east", "cartographer_house", "west")
    connect("scholar_lane", "south", "city_watch_office", "north")

    outskirts = {
        "city_outskirts_gate": ("Przedbramie Południowe", "Droga tuż za murami rozdziela się na sad, pola i trakt prowadzący ku Łąkom."),
        "caravan_road": ("Droga Karawan", "Ubity trakt nosi ślady kół, końskich kopyt i pieszych podróżnych zmierzających do miasta."),
        "orchard_path": ("Droga Sadowa", "Niska kamienna ściana oddziela drogę od starych sadów należących do mieszkańców miasta."),
        "old_orchard": ("Stary Sad", "Pomiędzy jabłoniami i gruszami stoją porzucone kosze. Krzewy przyciągają drobną zwierzynę."),
        "mill_road": ("Droga do Młyna", "Boczna droga biegnie w stronę starego młyna i zakola rzeki."),
        "old_mill": ("Stary Młyn", "Koło wodne obraca się powoli przy kamiennym młynie, który nadal obsługuje okolicznych rolników."),
        "riverside_path": ("Ścieżka Nad Rzeką", "Wąska ścieżka ciągnie się wzdłuż trzcin i płytkiego brzegu rzeki."),
        "east_fields": ("Wschodnie Pola", "Niskie pola uprawne i miedze ciągną się aż do łagodnych wzgórz."),
        "shepherd_hill": ("Wzgórze Pasterzy", "Z trawiastego wzgórza widać mury miasta, Łąki i fragment Starego Traktu."),
        "roadside_shrine": ("Kapliczka Podróżnych", "Mała kamienna kapliczka stoi przy skrzyżowaniu dróg. Podróżni zostawiają tu świece i drobne monety."),
        "drainage_ditch": ("Stary Rów Obronny", "Wyschnięty fragment dawnego rowu otacza południową część murów i tworzy osłoniętą ścieżkę."),
        "abandoned_storehouse": ("Opuszczony Magazyn", "Zamknięty kiedyś magazyn ma wyłamane drzwi i ślady nieproszonych gości."),
        "charcoal_camp": ("Obóz Węglarzy", "Dymiące mielerze stoją przy skraju zagajnika. Węglarze wracają tu tylko w dzień."),
        "outer_wall_path": ("Ścieżka Pod Murami", "Patrolowa droga prowadzi wzdłuż zewnętrznej strony miejskich murów ku północnemu posterunkowi."),
    }
    for rid, (name, desc) in outskirts.items():
        ROOMS[rid] = {"zone":"Przedmieścia Miasta Dusz", "name":name, "desc":desc, "exits":{}}

    # Wstaw przedmieścia pomiędzy miasto i Łąki oraz dodaj boczną pętlę do Starego Traktu.
    ROOMS["south_gate"]["exits"]["south"] = "city_outskirts_gate"
    ROOMS["meadow"]["exits"]["north"] = "caravan_road"
    connect("south_gate", "south", "city_outskirts_gate", "north")
    connect("city_outskirts_gate", "south", "caravan_road", "north")
    connect("caravan_road", "south", "meadow", "north")
    connect("city_outskirts_gate", "west", "orchard_path", "east")
    connect("orchard_path", "west", "old_orchard", "east")
    connect("orchard_path", "south", "mill_road", "north")
    connect("mill_road", "west", "old_mill", "east")
    connect("mill_road", "south", "riverside_path", "north")
    connect("riverside_path", "east", "caravan_road", "west")
    connect("city_outskirts_gate", "east", "outer_wall_path", "west")
    connect("outer_wall_path", "south", "east_fields", "north")
    connect("east_fields", "south", "shepherd_hill", "north")
    connect("shepherd_hill", "west", "roadside_shrine", "east")
    connect("roadside_shrine", "north", "caravan_road", "east")
    connect("east_fields", "east", "drainage_ditch", "west")
    connect("drainage_ditch", "south", "abandoned_storehouse", "north")
    connect("abandoned_storehouse", "west", "charcoal_camp", "east")
    connect("charcoal_camp", "north", "shepherd_hill", "south")
    connect("outer_wall_path", "north", "north_watchpost", "south")

build_v0102_city_and_outskirts()

# ============================================================
# v0.24.0 - APTEKA POD SREBRNYM LIŚCIEM
# ============================================================
# Mikstury są osobnym asortymentem aptecznym. Karczma zachowuje kuchnię i
# Gotowanie, ale nie prowadzi już sprzedaży mikstur.
ROOMS["pharmacy"] = {
    "zone": "Miasto Dusz",
    "name": "Apteka Pod Srebrnym Liściem",
    "desc": (
        "Jasne półki wypełniają fiolki, suszone zioła i opisane butelki. "
        "To miejski sklep z podstawowymi miksturami i eliksirami."
    ),
    "exits": {"north": "inn"},
}
ROOMS["inn"].setdefault("exits", {})["south"] = "pharmacy"

SHOPS["market"] = [iid for iid in SHOPS.get("market", ()) if iid != "healing_potion"]
SHOPS["inn"] = [iid for iid in SHOPS.get("inn", ()) if iid != "healing_potion"]
SHOPS["pharmacy"] = [
    "healing_potion", "mana_potion",
    "greater_healing_potion", "greater_mana_potion",
    "vitality_elixir",
]
SHOP_SELLERS["pharmacy"] = "pharmacist_neris"
for _iid, _price in {
    "healing_potion": 100,
    "mana_potion": 140,
    "greater_healing_potion": 420,
    "greater_mana_potion": 520,
    "vitality_elixir": 800,
}.items():
    ITEMS[_iid]["price"] = _price
    ITEMS[_iid]["currency"] = "silver"

NPCS["pharmacist_neris"] = {
    "name": "Aptekarka Neris",
    "room": "pharmacy",
    "dialogue": (
        "Karczma jest od posiłku i odpoczynku. Mikstury kupisz tutaj. "
        "Jeśli zbierasz zioła, mam też dla ciebie regularne zlecenie."
    ),
    "quest": "v024_pharmacy_herbs",
}
QUESTS["v024_pharmacy_herbs"] = {
    "name": "Apteczne zapasy: Świeże zioła",
    "giver": "Aptekarka Neris",
    "kind": "collect_category", "target": "herb", "needed": 8,
    "description": (
        "Po przyjęciu zadania zbierz 8 dowolnych ziół i przynieś je Aptekarce Neris. "
        "Postęp zaczyna od 0/8 i liczy tylko nowe zbiory."
    ),
    "specialist_tool_type": "herbalism", "min_tool_level": 1,
    "reward_profession": "Zielarstwo", "reward_profession_xp": 500,
    "reward_tool_type": "herbalism", "reward_tool_xp": 350,
    "reward_silver": 450, "reward_gold": 0, "reward_mithril": 0,
    "reward_items": {"healing_potion": 1},
    "repeatable": True, "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
}

COMMAND_ALIASES.update({
    "kartografia": "cartography", "kartograf": "cartography",
    "cartography": "cartography", "mapy": "cartography",
})
GUIDE_DESTINATION_ALIASES.update({
    "apteka": "pharmacy",
    "apteka pod srebrnym lisciem": "pharmacy",
    "pharmacy": "pharmacy",
})

HELP_TOPICS["apteka"] = [
    "Apteka Pod Srebrnym Liściem leży na południe od Karczmy Pod Błękitnym Płomieniem.",
    "Karczma i Rynek nie sprzedają już mikstur. Podstawowe gotowe mikstury kupujesz u Aptekarki Neris.",
    "Komendy: sklep/list, kup <nazwa lub numer>, sprzedaj <nazwa>, quest list Neris.",
    "Oferta: Mikstura Leczenia, Mikstura Many, Wielkie Mikstury Leczenia/Many oraz Eliksir Witalności.",
    "Alchemia nadal pozwala wytwarzać mikstury samodzielnie i pozostaje ważna dla wyższych receptur.",
    "Neris ma powtarzalny co 60 minut quest na 8 świeżo zebranych ziół, zawsze od 0/8.",
    "Nawigacja: prowadz apteka albo walk pharmacy.",
]
HELP_TOPIC_ALIASES.update({
    "pharmacy": "apteka", "aptekarz": "apteka", "aptekarstwo": "apteka",
})
if "nawigacja" in HELP_TOPICS:
    HELP_TOPICS["nawigacja"].append(
        "Aktywny trop Mapy Skarbu obsługuje prowadz skarb; przy kilku tropach podaj numer, np. prowadz skarb 2."
    )
if "sklepy" in HELP_TOPICS:
    HELP_TOPICS["sklepy"].append(
        "Mikstury kupuje się w Aptece Pod Srebrnym Liściem, nie w Karczmie ani na Rynku. Użyj prowadz apteka."
    )
if "alchemia" in HELP_TOPICS:
    HELP_TOPICS["alchemia"].append(
        "Podstawowe gotowe mikstury można kupić w Aptece. Karczma i Rynek nie prowadzą już sprzedaży mikstur."
    )

# Nowi mieszkańcy i fachowcy. Są pokojowi i nie są celami walki.
NPCS.update({
    "tailor_lysa": {
        "name":"Krawcowa Lysa", "room":"tailor_workshop",
        "dialogue":"Szyję płaszcze, torby i mundury straży. Najwięcej pracy mam wtedy, gdy karawany przywożą nowe tkaniny.",
        "quest":"city_tailor_guard_delivery",
    },
    "carpenter_edric": {
        "name":"Cieśla Edric", "room":"carpenter_workshop",
        "dialogue":"Miasto ciągle potrzebuje desek do dachów, wozów i rusztowań. Dobre drewno nigdy się nie marnuje.",
        "quest":"city_carpenter_timber",
    },
    "leatherworker_soren": {
        "name":"Kaletnik Soren", "room":"leatherworker_workshop",
        "dialogue":"Naprawiam pasy, sakwy i uprzęże. W warsztacie zawsze znajdzie się robota, nawet gdy na Rynku jest spokojnie.",
    },
    "mason_kelda": {
        "name":"Kamieniarka Kelda", "room":"mason_yard",
        "dialogue":"Mury miasta stoją tak długo, jak długo ktoś pilnuje zaprawy i pękniętych kamieni.",
    },
    "potter_ves": {
        "name":"Garncarz Ves", "room":"potter_workshop",
        "dialogue":"Karczma tłucze dzbany szybciej, niż ja je wypalam. To chyba znak, że interes idzie dobrze.",
    },
    "baker_odo": {
        "name":"Piekarz Odo", "room":"city_bakery",
        "dialogue":"Straż przy bramach dostaje świeży chleb każdego ranka. Czasem brakuje mi rąk do roznoszenia dostaw.",
        "quest":"city_baker_gate_delivery",
    },
    "healer_sava": {
        "name":"Uzdrowicielka Sava", "room":"healer_house",
        "dialogue":"Leczę drobne rany i przygotowuję opatrunki. Świeże zioła z okolic miasta szybko schodzą.",
        "quest":"city_healer_herbs",
    },
    "courier_ina": {
        "name":"Kurierka Ina", "room":"courier_office",
        "dialogue":"Znam każdą ulicę i prawie każdy trakt. Najkrótsza droga nie zawsze jest najbezpieczniejsza.",
    },
    "warehouse_master_berek": {
        "name":"Magazynier Berek", "room":"harbor_warehouse",
        "dialogue":"Każda skrzynia ma znak właściciela. Bez porządku port zamieniłby się w jeden wielki stos towaru.",
    },
    "ropemaker_tina": {
        "name":"Powroźniczka Tina", "room":"ropewalk",
        "dialogue":"Dobra lina musi trzymać i statek, i wóz. Skręcanie jej wygląda prosto dopiero po latach praktyki.",
    },
    "shipwright_marek": {
        "name":"Szkutnik Marek", "room":"shipwright_yard",
        "dialogue":"Kadłub mówi, gdzie dostał falą. Ja tylko muszę umieć go słuchać.",
        "quest":"city_shipwright_fisher_delivery",
    },
    "cartographer_eren": {
        "name":"Kartograf Eren", "room":"cartographer_house",
        "dialogue":"Aktualizuję mapy na podstawie meldunków zwiadowców i podróżnych. Mam kilka zleceń: dostawy map, pomiary rubieży i oznaczanie sekretów.",
        "quest":"city_cartographer_guard_delivery",
    },
    "watchman_dalen": {
        "name":"Strażnik Dalen", "room":"city_watch_office",
        "dialogue":"Patrole pod murami zgłaszają drobnych rabusiów. To nie armia, ale lekceważeni szybko robią się odważniejsi.",
        "quest":"city_outskirts_thieves",
    },
    "orchardist_miro": {
        "name":"Sadownik Miro", "room":"old_orchard",
        "dialogue":"Sad jest stary, ale wciąż owocuje. Gorzej z wilkami, które zaczęły podchodzić pod drzewa.",
        "quest":"city_outskirts_wolves",
    },
})

# Przedmioty do krótkich dostaw miejskich.
ITEMS.update({
    "city_guard_uniform_order": {"name":"Zamówienie na mundury straży", "type":"quest", "price":None, "desc":"Dokument Krawcowej Lysy dla Kwatermistrza Harka."},
    "city_bread_crate": {"name":"Skrzynka świeżego chleba", "type":"quest", "price":None, "desc":"Poranna dostawa Piekarza Oda dla południowej bramy."},
    "city_harbor_repair_list": {"name":"Lista napraw kutrów", "type":"quest", "price":None, "desc":"Lista Szkutnika Marka dla Rybaka Borysa."},
    "city_patrol_map": {"name":"Zaktualizowana mapa patroli", "type":"quest", "price":None, "desc":"Nowa mapa Kartografa Erena dla Kapitana Arvena."},
    "city_harbor_chart": {"name":"Mapa magazynów portowych", "type":"quest", "price":None, "desc":"Plan portowych magazynów przygotowany przez Kartografa Erena dla Magazyniera Berka."},
    "city_mine_route_map": {"name":"Mapa trasy do Kopalni Głębinowej", "type":"quest", "price":None, "desc":"Mapa bezpiecznej drogi z Miasta Dusz do kopalni dla Górnika Torena."},
})

QUESTS.update({
    "city_tailor_guard_delivery": {
        "name":"Miejska przysługa: Mundury dla straży", "giver":"Krawcowa Lysa", "kind":"deliver_npc",
        "target_npc":"guard_quartermaster_harek", "quest_item":"city_guard_uniform_order",
        "accept_items":{"city_guard_uniform_order":1}, "needed":1,
        "description":"Zanieś zamówienie Krawcowej Lysy Kwatermistrzowi Harkowi w Zbrojowni Straży. Zadanie odnawia się co 60 minut.",
        "reward_stat_progress":20, "reward_silver":180, "reward_gold":0, "reward_mithril":0,
        "reward_items":{}, "repeatable":True, "repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS,
        "event_progress_only":True,
    },
    "city_baker_gate_delivery": {
        "name":"Miejska przysługa: Chleb na południową bramę", "giver":"Piekarz Odo", "kind":"deliver_npc",
        "target_npc":"south_gate_guard_lena", "quest_item":"city_bread_crate",
        "accept_items":{"city_bread_crate":1}, "needed":1,
        "description":"Dostarcz skrzynkę świeżego chleba Strażniczce Lenie przy Południowej Bramie. Zadanie odnawia się co 60 minut.",
        "reward_stat_progress":20, "reward_silver":160, "reward_gold":0, "reward_mithril":0,
        "reward_items":{"healing_potion":1}, "repeatable":True,
        "repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS, "event_progress_only":True,
    },
    "city_shipwright_fisher_delivery": {
        "name":"Miejska przysługa: Lista napraw portowych", "giver":"Szkutnik Marek", "kind":"deliver_npc",
        "target_npc":"fisher_tomas", "quest_item":"city_harbor_repair_list",
        "accept_items":{"city_harbor_repair_list":1}, "needed":1,
        "description":"Przekaż Rybakowi Borysowi na Targu Rybnym listę kutrów wymagających naprawy.",
        "reward_stat_progress":25, "reward_silver":220, "reward_gold":0, "reward_mithril":0,
        "reward_items":{}, "repeatable":False, "event_progress_only":True,
    },
    "city_cartographer_guard_delivery": {
        "name":"Miejska przysługa: Nowa mapa patroli", "giver":"Kartograf Eren", "kind":"deliver_npc",
        "target_npc":"captain_arven", "quest_item":"city_patrol_map",
        "accept_items":{"city_patrol_map":1}, "needed":1,
        "description":"Zanieś Kapitanowi Arvenowi w Strażnicy Głównej zaktualizowaną mapę patroli.",
        "reward_stat_progress":30, "reward_silver":260, "reward_gold":0, "reward_mithril":0,
        "reward_items":{}, "repeatable":True, "repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS,
        "event_progress_only":True,
    },
    "city_cartographer_harbor_delivery": {
        "name":"Kartograf Eren: Plan portowych magazynów", "giver":"Kartograf Eren", "kind":"deliver_npc",
        "target_npc":"warehouse_master_berek", "quest_item":"city_harbor_chart",
        "accept_items":{"city_harbor_chart":1}, "needed":1,
        "description":"Dostarcz Magazynierowi Berkowi w Porcie mapę magazynów i nabrzeży przygotowaną przez Erena.",
        "reward_stat_progress":25, "reward_silver":240, "reward_gold":0, "reward_mithril":0,
        "reward_items":{}, "repeatable":True, "repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS,
        "event_progress_only":True,
    },
    "city_cartographer_mine_delivery": {
        "name":"Kartograf Eren: Droga do kopalni", "giver":"Kartograf Eren", "kind":"deliver_npc",
        "target_npc":"miner_toren", "quest_item":"city_mine_route_map",
        "accept_items":{"city_mine_route_map":1}, "needed":1,
        "description":"Zanieś Górnikowi Torenowi przy wejściu do kopalni nową mapę bezpiecznej trasy z miasta.",
        "reward_stat_progress":30, "reward_silver":280, "reward_gold":0, "reward_mithril":0,
        "reward_items":{}, "repeatable":True, "repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS,
        "event_progress_only":True,
    },
    "city_cartographer_frontier_survey": {
        "name":"Kartograf Eren: Pięć nowych sektorów", "giver":"Kartograf Eren",
        "kind":"explore_frontier", "target":"any", "needed":5,
        "description":"Po przyjęciu zadania odkryj 5 nowych sektorów proceduralnych rubieży i wróć do Kartografa Erena.",
        "reward_stat_progress":45, "reward_silver":650, "reward_gold":0, "reward_mithril":0,
        "reward_items":{}, "repeatable":True, "repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS,
        "event_progress_only":True,
    },
    "city_cartographer_secret_marks": {
        "name":"Kartograf Eren: Znak poza mapą", "giver":"Kartograf Eren",
        "kind":"discover_secret", "target":"any", "needed":1,
        "description":"Po przyjęciu zadania otrzymasz Mapę Skarbu Rubieży. Użyj jej, dotrzyj do wskazanego sektora, odkryj 1 nowy sekret proceduralnego świata i wróć do Kartografa Erena.",
        "accept_items":{"quest_map_eren_secret_marks":1}, "accept_items_always":True,
        "reward_stat_progress":55, "reward_silver":900, "reward_gold":0, "reward_mithril":0,
        "reward_items":{}, "repeatable":True, "repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS,
        "event_progress_only":True,
    },
    "city_carpenter_timber": {
        "name":"Miejska robota: Drewno na rusztowania", "giver":"Cieśla Edric", "kind":"collect_category",
        "target":"wood", "needed":10,
        "description":"Po przyjęciu zadania pozyskaj 10 sztuk dowolnego drewna i przynieś je Cieśli Edricowi.",
        "specialist_tool_type":"woodcutting", "min_tool_level":1,
        "reward_profession":"Drwalstwo", "reward_profession_xp":450,
        "reward_tool_type":"woodcutting", "reward_tool_xp":360,
        "reward_silver":240, "reward_gold":0, "reward_mithril":0, "reward_items":{},
        "repeatable":True, "repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "city_healer_herbs": {
        "name":"Miejska robota: Zioła dla lecznicy", "giver":"Uzdrowicielka Sava", "kind":"collect_category",
        "target":"herb", "needed":10,
        "description":"Po przyjęciu zadania zbierz 10 dowolnych ziół i przynieś je Uzdrowicielce Savie.",
        "specialist_tool_type":"herbalism", "min_tool_level":1,
        "reward_profession":"Zielarstwo", "reward_profession_xp":450,
        "reward_tool_type":"herbalism", "reward_tool_xp":360,
        "reward_silver":240, "reward_gold":0, "reward_mithril":0, "reward_items":{"healing_potion":1},
        "repeatable":True, "repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "city_outskirts_thieves": {
        "name":"Patrol przedmieść: Drobni rabusie", "giver":"Strażnik Dalen", "kind":"kill",
        "target":"outskirts_thief", "needed":6,
        "description":"Pokonaj 6 Rabusiów z Przedmieść po przyjęciu zadania i wróć do Strażnika Dalena.",
        "reward_stat_progress":40, "reward_silver":420, "reward_gold":1, "reward_mithril":0,
        "reward_items":{}, "repeatable":True, "repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "city_outskirts_wolves": {
        "name":"Sad pod presją: Wilki pod murami", "giver":"Sadownik Miro", "kind":"kill",
        "target":"outskirts_wolf", "needed":5,
        "description":"Pokonaj 5 Wilków z Przedmieść po przyjęciu zadania i wróć do Sadownika Mira.",
        "reward_stat_progress":35, "reward_silver":360, "reward_gold":0, "reward_mithril":0,
        "reward_items":{"healing_potion":1}, "repeatable":True, "repeat_cooldown":QUEST_REPEAT_COOLDOWN_SECONDS,
    },
})

# v0.24.0: pięć dotychczasowych zleceń Erena pozostaje niezależnych i
# godzinnych. Poniższa seria jest nowym, jednorazowym łańcuchem mistrzowskim.
ITEMS["v024_eren_master_atlas"] = {
    "name": "Wielki Atlas Erena", "type": "quest", "price": None,
    "desc": "Wielki atlas rubieży przygotowany przez Erena dla Kartografki Lysy.",
}
QUESTS.update({
    "v024_eren_master_1": {
        "name": "Wielki Atlas I: Dwanaście nowych sektorów", "giver": "Kartograf Eren",
        "kind": "explore_frontier", "target": "any", "needed": 12,
        "description": "Odkryj 12 nowych sektorów proceduralnych rubieży po przyjęciu zadania.",
        "reward_silver": 5000, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {"treasure_map_frontier": 1},
        "reward_faction_v016": "cartographers", "reward_faction_amount_v016": 8,
        "repeatable": False, "event_progress_only": True,
    },
    "v024_eren_master_2": {
        "name": "Wielki Atlas II: Drogi poza mapą", "giver": "Kartograf Eren",
        "kind": "discover_secret", "target": "any", "needed": 2,
        "description": "Odkryj 2 nowe sekrety proceduralnego świata po przyjęciu zadania.",
        "requires_quest": "v024_eren_master_1",
        "reward_silver": 8500, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {"treasure_map_frontier": 2},
        "reward_faction_v016": "cartographers", "reward_faction_amount_v016": 12,
        "repeatable": False, "event_progress_only": True,
    },
    "v024_eren_master_3": {
        "name": "Wielki Atlas III: Małe głębiny", "giver": "Kartograf Eren",
        "kind": "mini_dungeon", "target": "any", "needed": 2,
        "description": "Dotrzyj do finałowej komnaty 2 nowych proceduralnych mini-lochów.",
        "requires_quest": "v024_eren_master_2",
        "reward_silver": 12000, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {"treasure_map_frontier": 1, "soul_elixir": 1},
        "reward_faction_v016": "cartographers", "reward_faction_amount_v016": 16,
        "repeatable": False, "event_progress_only": True,
    },
    "v024_eren_master_4": {
        "name": "Wielki Atlas IV: Żywy świat", "giver": "Kartograf Eren",
        "kind": "world_event", "target": "any", "needed": 3,
        "description": "Odwiedź 3 nowe aktywne wydarzenia świata po przyjęciu zadania.",
        "requires_quest": "v024_eren_master_3",
        "reward_silver": 16000, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {"treasure_map_frontier": 2, "soul_elixir": 1},
        "reward_faction_v016": "cartographers", "reward_faction_amount_v016": 20,
        "repeatable": False, "event_progress_only": True,
    },
    "v024_eren_master_5": {
        "name": "Wielki Atlas V: Przekazanie dzieła", "giver": "Kartograf Eren",
        "kind": "deliver_npc", "target_npc": "cartographer_lysa",
        "quest_item": "v024_eren_master_atlas", "accept_items": {"v024_eren_master_atlas": 1},
        "needed": 1,
        "description": "Dostarcz Wielki Atlas Erena Kartografce Lysie w Bibliotece.",
        "requires_quest": "v024_eren_master_4",
        "reward_silver": 25000, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {"treasure_map_frontier": 3, "soul_elixir": 2},
        "reward_faction_v016": "cartographers", "reward_faction_amount_v016": 30,
        "repeatable": False, "event_progress_only": True,
    },
})
NPCS["cartographer_eren"]["quest_chain"] = tuple(
    f"v024_eren_master_{i}" for i in range(1, 6)
)
NPCS["cartographer_eren"]["dialogue"] = (
    "Mam pięć godzinnych zleceń kartograficznych oraz pięcioetapową serię Wielkiego Atlasu. "
    "Jeśli chcesz pracować nad mapami dłużej, zapytaj o listę questów."
)

MOB_TEMPLATES.update({
    "outskirts_thief": {
        "name":"Rabuś z Przedmieść", "max_hp":70, "damage":7, "damage_type":"physical",
        "silver":28, "gold":0, "mithril":0, "stat_reward":28, "soul_reward":135,
        "drops":{"healing_potion":0.04}, "quest_target":"outskirts_thief",
    },
    "outskirts_wolf": {
        "name":"Wilk z Przedmieść", "max_hp":56, "damage":6, "damage_type":"physical",
        "silver":18, "gold":0, "mithril":0, "stat_reward":23, "soul_reward":118,
        "drops":{"wolf_fang":0.18}, "quest_target":"outskirts_wolf",
    },
    "outskirts_boar": {
        "name":"Dzik z Pól", "max_hp":68, "damage":7, "damage_type":"physical",
        "silver":22, "gold":0, "mithril":0, "stat_reward":25, "soul_reward":125,
        "drops":{}, "quest_target":None,
    },
    "outskirts_wasp": {
        "name":"Osa Sadowa", "max_hp":44, "damage":5, "damage_type":"physical",
        "silver":15, "gold":0, "mithril":0, "stat_reward":19, "soul_reward":100,
        "drops":{}, "quest_target":None,
    },
})

MOB_SPAWNS.extend([
    ("caravan_road","outskirts_thief"), ("caravan_road","outskirts_wolf"),
    ("orchard_path","outskirts_wolf"),
    ("mill_road","outskirts_thief"),
    ("old_mill","outskirts_boar"),
    ("riverside_path","outskirts_wolf"), ("riverside_path","outskirts_boar"),
    ("east_fields","outskirts_boar"), ("east_fields","outskirts_wasp"),
    ("shepherd_hill","outskirts_wolf"), ("shepherd_hill","outskirts_thief"),
    ("roadside_shrine","outskirts_thief"),
    ("drainage_ditch","outskirts_wasp"), ("drainage_ditch","outskirts_wolf"),
    ("abandoned_storehouse","outskirts_thief"), ("abandoned_storehouse","outskirts_thief"),
    ("charcoal_camp","outskirts_boar"), ("charcoal_camp","outskirts_thief"),
    ("outer_wall_path","outskirts_thief"), ("outer_wall_path","outskirts_wolf"),
])

# Audyt gęstości v0.10.2: puste pokoje Dziczy/Bagien/Pustyni są bezpiecznymi
# hubami NPC. W Podziemiach dwa przejścia bojowe były wyraźnie rzadsze od reszty.
MOB_SPAWNS.extend([
    ("cave_tunnel", "crystal_guardian"),
    ("crypt_entrance", "skeleton"),
])

# Wrogowie w zwykłym świecie mogą przemieszczać się między sąsiednimi pokojami.
# Bossowie, mini-bossowie, aktywnie walczące moby, miasta, huby NPC oraz wielkie
# piętra instancji pozostają stabilne, żeby ruch nie psuł bramek progresji.
MOB_WANDER_MIN_SECONDS = 45
MOB_WANDER_MAX_SECONDS = 110
MOB_WANDER_ROOM_CAP = 4
MOB_WANDER_BLOCKED_ZONES = {
    "Miasto Dusz", "Gildia Dusz", "Wioska Górska",
    "Krypta", "Mityczna Krypta", "Wieża Astralna", "Mityczna Wieża Astralna",
    "Twierdza Gigantów", "Kopalnia Głębinowa",
}
MOB_WANDER_SAFE_ROOMS = frozenset(
    {str(npc.get("room")) for npc in NPCS.values() if npc.get("room")}
    | set(SHOPS)
    | {"city_outskirts_gate", "caravan_camp", "swamp_hunter_post", "sewer_entrance"}
)


def mob_template_can_wander(template):
    if not template or int(template.get("max_hp", 0) or 0) <= 0:
        return False
    if template.get("stationary_mob") or template.get("mini_boss") or template.get("world_boss"):
        return False
    boss_flags = (
        "boss", "boss_mechanic", "crypt_boss", "astral_boss",
        "mythic_crypt_boss", "mythic_astral_boss", "giant_fortress_boss",
    )
    return not any(template.get(flag) for flag in boss_flags)


def mob_room_can_wander(room_id):
    room = ROOMS.get(room_id, {})
    zone = str(room.get("zone", ""))
    if not room or room_id in MOB_WANDER_SAFE_ROOMS:
        return False
    if room.get("procedural_infinite"):
        return False
    if zone in MOB_WANDER_BLOCKED_ZONES:
        return False
    if zone.startswith("Loch Profesyjny"):
        return False
    if any(token in zone for token in ("Krypta", "Wieża Astralna", "Twierdza Gigantów")):
        return False
    return True


def mob_wander_candidates(room_id):
    if not mob_room_can_wander(room_id):
        return []
    room = ROOMS[room_id]
    zone = room.get("zone")
    result = []
    for direction, target in room.get("exits", {}).items():
        if direction not in ("north", "south", "east", "west"):
            continue
        target_room = ROOMS.get(target)
        if not target_room or target_room.get("zone") != zone:
            continue
        if not mob_room_can_wander(target):
            continue
        result.append(target)
    return result

HELP_TOPICS["miasto"] = [
    "Miasto Dusz ma rozbudowane dzielnice: rzemieślniczą, mieszkalną, portową oraz ulicę uczonych.",
    "Nowe warsztaty i budynki mają pokojowych NPC, krótkie dialogi i małe zadania miejskie.",
    "Południowa Brama prowadzi teraz przez Przedmieścia Miasta Dusz do Łąk.",
    "Przedmieścia tworzą zapętlony obszar z sadem, młynem, polami, ścieżką pod murami i alternatywnym dojściem do północnego posterunku.",
    "Samo Miasto Dusz pozostaje bezpieczne i bez wrogich spawnów.",
]
HELP_TOPICS["miasto"].append(
    "Apteka Pod Srebrnym Liściem znajduje się na południe od Karczmy. To jedyny miejski sklep z podstawowymi miksturami."
)
HELP_TOPICS["kartografia"] = [
    "Kartograf Eren ma 5 godzinnych zleceń oraz 5-etapową jednorazową serię Wielkiego Atlasu, razem 10 własnych questów.",
    "kartografia / cartography pokazuje postęp sektorów, sekretów, mini-lochów, wydarzeń i Map Skarbów.",
    "Mapa Skarbu Rubieży zapisuje aktywny trop; mapa skarbu pokazuje wszystkie tropy.",
    "prowadz skarb prowadzi bezpośrednio do jedynego tropu. Przy kilku użyj prowadz skarb <numer>.",
    "Znak poza mapą wydaje przy przyjęciu questową Mapę Erena. Wpisz użyj mapy, potem prowadz skarb, a po dotarciu do sektora sekret / secret. Po porzuceniu questa jego mapa i aktywny trop znikają. Questy kartograficzne zawsze startują 0/x i liczą nowe zdarzenia.",
    "Nawigacja do Erena: prowadz Eren. Lista jego zadań: quest list Eren.",
]
HELP_TOPIC_ALIASES.update({
    "kartograf": "kartografia", "cartography": "kartografia",
    "mapy skarbow": "kartografia", "mapy skarbów": "kartografia",
    "prowadz skarb": "kartografia",
})

HELP_TOPICS["ruchome_moby"] = [
    "Zwykłe moby w świecie mogą przechodzić do sąsiednich pomieszczeń tej samej strefy, ale nigdy nie rozpoczynają walki same.",
    "Moby nie wchodzą do Miasta Dusz, sklepów, pokojów NPC ani innych bezpiecznych hubów.",
    "Bossowie i mini-bossowie nie wędrują. Mob w aktywnej walce również pozostaje na miejscu.",
    "Wielkie piętra Krypt, Wież, Twierdzy i lochów profesyjnych zachowują stałą obsadę, aby nie psuć progresji i bramek bossów.",
    "Po śmierci wędrujący mob odradza się w swoim pierwotnym miejscu spawnu.",
]
HELP_TOPICS["balans_narzedzi"] = [
    "v0.10.2 wyrównuje tempo zdobywania leveli narzędzi zbierackich w czasie rzeczywistym.",
    "Kilof dostaje x3.0 Tool XP z normalnego wydobycia, Piła x2.4, Wędka x1.5, a Sierp zachowuje x1.0.",
    "Mnożniki dotyczą Tool XP z normalnych akcji; nie zwiększają Profession XP, ilości surowców ani nagród questowych.",
    "Narzędzia produkcyjne nie zostały przyspieszone, ponieważ ich realny koszt obejmuje materiały i różne wartości XP receptur.",
]
HELP_TOPIC_ALIASES.update({
    "miasto dusz":"miasto", "city":"miasto", "przedmiescia":"miasto", "przedmieścia":"miasto",
    "ruchome moby":"ruchome_moby", "wedrujace moby":"ruchome_moby", "wędrujące moby":"ruchome_moby",
    "balans narzedzi":"balans_narzedzi", "balans narzędzi":"balans_narzedzi", "tool balance":"balans_narzedzi",
})

HELP_TOPICS["wielkie_lochy"] = [
    "v0.11.0: wszystkie piętrowe Krypty i lochy są generowane dynamicznie od pierwszego poziomu, dopiero gdy gracz do nich wchodzi.",
    "Dotyczy to obu Krypt, obu Wież Astralnych, Twierdzy Gigantów, Kopalni Głębinowej i czterech lochów profesyjnych.",
    "v0.10.0 usuwa małe liniowe piętra z głównych instancji.",
    "Krypta, Mityczna Krypta, Wieża Astralna, Mityczna Wieża Astralna i Twierdza Gigantów mają po 15 pomieszczeń na piętro.",
    "Lochy profesyjne mają po 10 pomieszczeń na poziom.",
    "Schody na następne piętro są w końcowej komnacie, a nie przy wejściu.",
    "Na piętrach co 10 boss pilnuje przejścia dalej; po pierwszym trwałym zaliczeniu jego późniejszy respawn nie blokuje postaci.",
    "Dynamiczne piętra ponad dawnym końcem są generowane w tym samym dużym układzie.",
    "Bojowe piętra mają więcej równoczesnych mobów; wszystkie rudy i Górnictwo są skupione w jednej Kopalni Głębinowej.",
    "Prowadzenie nadal zatrzymuje się przed wejściem do lochu i nie rozwiązuje mapy za gracza.",
]
HELP_TOPIC_ALIASES.update({
    "wielkie lochy": "wielkie_lochy", "massive dungeons": "wielkie_lochy",
    "duze lochy": "wielkie_lochy", "duże lochy": "wielkie_lochy",
    "dynamiczne lochy": "wielkie_lochy", "dynamiczne krypty": "wielkie_lochy",
    "proceduralne lochy": "wielkie_lochy", "dynamic dungeons": "wielkie_lochy",
})

# Platynowy Kartograf zawsze śledzi cały aktualny statyczny świat.
_v0100_tiers = list(ACHIEVEMENT_TRACKS.get("exploration_rooms", {}).get("tiers", ()))
if _v0100_tiers:
    _v0100_tiers = [(req, rank) for req, rank in _v0100_tiers if rank != "Platinum"]
    _v0100_tiers.append((len(ROOMS), "Platinum"))
    ACHIEVEMENT_TRACKS["exploration_rooms"]["tiers"] = tuple(_v0100_tiers)

EXPLORATION_ZONE_ROOMS = {}
for _room_id, _room in ROOMS.items():
    EXPLORATION_ZONE_ROOMS.setdefault(_room["zone"], []).append(_room_id)
for _zone in EXPLORATION_ZONE_ROOMS:
    EXPLORATION_ZONE_ROOMS[_zone].sort()

TRACKED_EXPLORATION_ZONES = {
    zone: tuple(room_ids)
    for zone, room_ids in EXPLORATION_ZONE_ROOMS.items()
    if len(room_ids) >= EXPLORATION_ZONE_MIN_ROOMS
}
ALL_EXPLORATION_ROOMS = tuple(sorted(ROOMS))

EXPLORATION_REWARD_ITEMS = {}
for _zone, _room_ids in TRACKED_EXPLORATION_ZONES.items():
    _reward_item_id = f"exploration_relic_{_collection_slug(_zone)}"
    EXPLORATION_REWARD_ITEMS[_zone] = _reward_item_id
    ITEMS.setdefault(
        _reward_item_id,
        {
            "name": f"Pamiątka Odkrywcy: {_zone}",
            "type": "collectible",
            "price": None,
            "rarity": "unique",
            "rarity_name": "Unikalny",
            "exploration_reward": True,
            "desc": (
                f"Unikalna pamiątka za odkrycie 100 procent strefy {_zone}. "
                "Nie jest przedmiotem do sprzedaży ani elementem ekwipunku."
            ),
        },
    )


def _build_set_catalog():
    catalog = {}
    item_to_set = {}
    for item_id, item in ITEMS.items():
        entry_id = None
        entry_name = None
        piece_key = item_id
        if item.get("regional_set"):
            set_id = str(item["regional_set"])
            entry_id = f"regional:{set_id}"
            entry_name = REGIONAL_SET_BONUSES.get(set_id, {}).get(
                "name", f"Regionalny set {set_id}"
            )
        elif item.get("class_set_name"):
            set_name = str(item.get("class_set_name"))
            req = str(item.get("required_class") or set_name)
            entry_id = f"class:{req}"
            entry_name = f"Zestaw {set_name} ({req})"
            # Wszystkie tiery Biegłości liczą się jako te same 8 logicznych części setu.
            piece_key = str(item.get("class_set_piece") or item.get("slot") or item_id)
        elif item.get("crypt_set_tier"):
            tier = int(item["crypt_set_tier"])
            entry_id = f"crypt:{tier}"
            entry_name = f"Zestaw Krypty Tier {tier}"
            piece_key = str(item.get("crypt_base_item") or item_id)
        elif item.get("astral_set_tier"):
            tier = int(item["astral_set_tier"])
            entry_id = f"astral:{tier}"
            entry_name = f"Astralny Zestaw Kręgu {tier}"
        if not entry_id:
            continue
        row = catalog.setdefault(entry_id, {"name": entry_name, "pieces": set()})
        row["pieces"].add(piece_key)
        item_to_set[item_id] = entry_id
    for row in catalog.values():
        row["pieces"] = tuple(sorted(row["pieces"]))
    return catalog, item_to_set


SET_COLLECTION_CATALOG, SET_ENTRY_BY_ITEM = _build_set_catalog()

def boss_codex_drop_is_unique(item_id):
    item = ITEMS.get(str(item_id), {})
    if not item:
        return False
    rarity = str(item.get("rarity", "")).lower()
    return bool(
        item.get("named_loot")
        or item.get("legendary_set_loot")
        or item.get("legendary_class_relic")
        or item.get("boss_relic_floor") is not None
        or item.get("astral_relic_floor") is not None
        or rarity in ("legendary", "mythic", "eternal", "unique")
    )

NAMED_LOOT_CATALOG = {
    item_id: item["name"]
    for item_id, item in ITEMS.items()
    if (
        item.get("named_loot")
        or item.get("boss_relic_floor") is not None
        or item.get("astral_relic_floor") is not None
        or item_id == "bandit_chief_signet"
        or item_id in WORLD_BOSS_UNIQUES
    )
}

BOSS_COLLECTION_CATALOG = {
    mob_id: data["name"]
    for mob_id, data in MOB_TEMPLATES.items()
    if any(
        data.get(flag)
        for flag in (
            "world_boss", "mini_boss", "crypt_boss", "astral_boss",
            "mythic_crypt_boss", "mythic_astral_boss", "giant_fortress_boss",
        )
    )
}

RARE_MOB_COLLECTION_CATALOG = {
    mob_id: data["name"]
    for mob_id, data in MOB_TEMPLATES.items()
    if data.get("rare_mob")
}

CHEST_COLLECTION_CATALOG = {
    room_id: cfg["name"]
    for room_id, cfg in TREASURE_CHESTS.items()
}

FISH_COLLECTION_CATALOG = {
    item_id: ITEMS[item_id]["name"] for item_id in sorted(FISH_RESOURCE_IDS) if item_id in ITEMS
}
MINERAL_COLLECTION_CATALOG = {
    item_id: ITEMS[item_id]["name"] for item_id in sorted(ORE_RESOURCE_IDS) if item_id in ITEMS
}
HERB_COLLECTION_CATALOG = {
    item_id: ITEMS[item_id]["name"] for item_id in sorted(HERB_RESOURCE_IDS) if item_id in ITEMS
}
GEM_COLLECTION_CATALOG = {
    item_id: ITEMS[item_id]["name"]
    for item_id in sorted(set(RAW_GEM_IDS) | set(CUT_GEM_IDS)) if item_id in ITEMS
}
MATERIAL_COLLECTION_CATALOG = {
    item_id: ITEMS[item_id]["name"]
    for item_id in sorted(
        set(WOOD_RESOURCE_IDS) | {iid for iid, data in ITEMS.items() if data.get("type") == "craft_material"}
    ) if item_id in ITEMS
}
UNIQUE_ITEM_COLLECTION_CATALOG = {
    item_id: data["name"]
    for item_id, data in ITEMS.items()
    if (
        data.get("type") == "collectible"
        or item_id in NAMED_LOOT_CATALOG
        or (str(data.get("rarity", "")).lower() == "unique" and not item_id.startswith("corpse_"))
    )
}

EQUIPMENT_COLLECTION_CATALOG = {
    item_id: data["name"]
    for item_id, data in ITEMS.items()
    if data.get("type") in ("armor", "weapon")
}

COLLECTION_CATALOGS = {
    "fish": FISH_COLLECTION_CATALOG,
    "minerals": MINERAL_COLLECTION_CATALOG,
    "herbs": HERB_COLLECTION_CATALOG,
    "gems": GEM_COLLECTION_CATALOG,
    "bosses": BOSS_COLLECTION_CATALOG,
    "rare": RARE_MOB_COLLECTION_CATALOG,
    "materials": MATERIAL_COLLECTION_CATALOG,
    "unique": UNIQUE_ITEM_COLLECTION_CATALOG,
    "equipment": EQUIPMENT_COLLECTION_CATALOG,
    # Widoki dodatkowe z wcześniejszych wersji.
    "named": NAMED_LOOT_CATALOG,
    "sets": {key: value["name"] for key, value in SET_COLLECTION_CATALOG.items()},
    "chests": CHEST_COLLECTION_CATALOG,
}


# ============================================================
# v0.9.22 - QUEST MOB DENSITY
# Questy typu kill z potrzebą >1 nie powinny zmuszać do czekania na pojedynczy
# respawn. Dla celu questu liczymy również moby oznaczone quest_target/quest_targets
# i dokładamy brakujące instancje w istniejących pokojach. Bossowie (needed=1)
# pozostają pojedynczymi przeciwnikami.
def _v0922_expand_quest_mob_spawns():
    def quest_tags(mob_id):
        template = MOB_TEMPLATES.get(mob_id, {})
        tags = {mob_id}
        primary = template.get("quest_target")
        if primary:
            tags.add(primary)
        tags.update(template.get("quest_targets") or ())
        return tags

    added = []
    for quest_id, quest in QUESTS.items():
        if quest.get("kind") != "kill":
            continue
        needed = max(1, int(quest.get("needed", 1) or 1))
        if needed <= 1:
            continue
        target = str(quest.get("target", ""))
        if not target:
            continue
        eligible = [
            (room_id, mob_id)
            for room_id, mob_id in MOB_SPAWNS
            if target in quest_tags(mob_id)
        ]
        if not eligible:
            continue
        # Im większy quest, tym więcej równoczesnych celów, ale bez zalewania pokoju.
        desired = min(8, max(3, (needed + 1) // 2))
        if len(eligible) >= desired:
            continue
        seed = list(eligible)
        index = 0
        while len(eligible) < desired:
            room_id, mob_id = seed[index % len(seed)]
            MOB_SPAWNS.append((room_id, mob_id))
            eligible.append((room_id, mob_id))
            added.append((quest_id, target, room_id, mob_id))
            index += 1
    return added


V0922_ADDED_QUEST_MOB_SPAWNS = _v0922_expand_quest_mob_spawns()

# v0.9.21 - COLLECTION CODEX 2.0 dynamic group indexes
# ============================================================
def _build_collection_v2_groups():
    class_groups = {name: set() for name in CLASS_EQUIPMENT_SETS}
    legendary_groups = {name: set() for name in CLASS_EQUIPMENT_SETS}
    legendary_groups["Ogólne"] = set()
    material_groups = {tier["key"]: set() for tier in CORPSE_MATERIAL_TIERS}
    set_groups = {}
    set_names = {}
    for item_id, item in ITEMS.items():
        if item.get("type") not in ("armor", "weapon"):
            continue
        req_class = str(item.get("required_class") or "")
        if req_class in class_groups:
            class_groups[req_class].add(item_id)
        if (
            str(item.get("rarity", "")).lower() == "legendary"
            or item.get("legendary_set_loot")
            or item.get("legendary_class_relic")
        ):
            legendary_groups[req_class if req_class in CLASS_EQUIPMENT_SETS else "Ogólne"].add(item_id)
        material = str(item.get("corpse_material") or item.get("blacksmith_material") or "")
        if material in material_groups:
            material_groups[material].add(item_id)

        group_id = None
        group_name = None
        if item.get("class_set_name"):
            mastery = int(item.get("required_mastery", 1) or 1)
            group_id = f"class:{req_class}:{item.get('class_set_name')}:{mastery}"
            group_name = f"{item.get('class_set_name')} — {req_class}, Biegłość {mastery}"
        elif item.get("regional_set"):
            sid = str(item["regional_set"])
            group_id = f"regional:{sid}"
            group_name = REGIONAL_SET_BONUSES.get(sid, {}).get("name", f"Set regionalny {sid}")
        elif item.get("crypt_set_tier"):
            tier = int(item["crypt_set_tier"])
            group_id = f"crypt:{tier}"
            group_name = f"Zestaw Krypty Tier {tier}"
        elif item.get("astral_set_tier"):
            tier = int(item["astral_set_tier"])
            group_id = f"astral:{tier}"
            group_name = f"Astralny Zestaw Kręgu {tier}"
        if group_id:
            set_groups.setdefault(group_id, set()).add(item_id)
            set_names[group_id] = group_name
    return (
        {k: frozenset(v) for k, v in class_groups.items()},
        {k: frozenset(v) for k, v in legendary_groups.items()},
        {k: frozenset(v) for k, v in material_groups.items()},
        {k: frozenset(v) for k, v in set_groups.items()},
        set_names,
    )

(
    COLLECTION_V2_CLASS_GROUPS,
    COLLECTION_V2_LEGENDARY_GROUPS,
    COLLECTION_V2_MATERIAL_GROUPS,
    COLLECTION_V2_SET_GROUPS,
    COLLECTION_V2_SET_NAMES,
) = _build_collection_v2_groups()

COLLECTION_V2_MATERIAL_LABELS = {
    tier["key"]: tier["label"] for tier in CORPSE_MATERIAL_TIERS
}

# ============================================================
# v0.8.76 - persistent Bestiary
# ============================================================
def canonical_bestiary_template_id(template_id):
    """Collapse procedural elite/rare affixes into the underlying species.

    The world contains thousands of generated combat variants.  The Bestiary
    intentionally tracks the actual species instead of requiring a separate
    entry for every affix copy.
    """
    template_id = str(template_id or "")
    seen = set()
    while template_id and template_id not in seen:
        seen.add(template_id)
        template = MOB_TEMPLATES.get(template_id, {})
        base_id = template.get("rare_base_template") or template.get("elite_base_template")
        if not base_id or base_id == template_id:
            break
        template_id = str(base_id)
    return template_id

BESTIARY_CATALOG = {}
BESTIARY_SPAWN_ROOMS = {}
for _bestiary_room_id, _bestiary_template_id in MOB_SPAWNS:
    _bestiary_id = canonical_bestiary_template_id(_bestiary_template_id)
    if _bestiary_id not in MOB_TEMPLATES:
        continue
    BESTIARY_CATALOG[_bestiary_id] = MOB_TEMPLATES[_bestiary_id]["name"]
    BESTIARY_SPAWN_ROOMS.setdefault(_bestiary_id, set()).add(_bestiary_room_id)

# Platinum zawsze oznacza faktyczne 100% aktualnej wersji świata / Bestiariusza.
ACHIEVEMENT_TRACKS["exploration_rooms"]["tiers"] = (
    (100, "Bronze"), (500, "Silver"), (1000, "Gold"),
    (len(ALL_EXPLORATION_ROOMS), "Platinum"),
)
ACHIEVEMENT_TRACKS["bestiary_unique"]["tiers"] = (
    (50, "Bronze"), (250, "Silver"), (500, "Gold"),
    (len(BESTIARY_CATALOG), "Platinum"),
)

def bestiary_resistance_text(template):
    """Describe only resistance data that really exists in combat data."""
    parts = []
    resistances = template.get("resistances") or {}
    if isinstance(resistances, dict):
        labels = {"physical": "fizyczne", "magic": "magiczne"}
        for key, value in sorted(resistances.items()):
            try:
                pct = int(round(float(value) * 100)) if abs(float(value)) <= 1 else int(round(float(value)))
            except (TypeError, ValueError):
                continue
            parts.append(f"{labels.get(str(key), str(key))} {pct}%")
    immunities = template.get("immunities") or ()
    if isinstance(immunities, str):
        immunities = (immunities,)
    if immunities:
        parts.append("odporność całkowita: " + ", ".join(map(str, immunities)))
    weaknesses = template.get("weaknesses") or ()
    if isinstance(weaknesses, str):
        weaknesses = (weaknesses,)
    if weaknesses:
        parts.append("słabość: " + ", ".join(map(str, weaknesses)))
    return "; ".join(parts) if parts else "brak specjalnych odporności"

MINI_BOSS_IDS = frozenset(
    mob_id for mob_id, data in MOB_TEMPLATES.items() if data.get("mini_boss")
)

# Mapa wpisów kolekcji do stref do komendy progress region.
REGION_COLLECTION_ENTRIES = {
    zone: {"named": set(), "bosses": set(), "rare": set(), "chests": set()}
    for zone in EXPLORATION_ZONE_ROOMS
}

_spawn_zones = {}
for _room_id, _mob_id in MOB_SPAWNS:
    _zone = ROOMS.get(_room_id, {}).get("zone")
    if _zone:
        _spawn_zones.setdefault(_mob_id, set()).add(_zone)

for _mob_id in BOSS_COLLECTION_CATALOG:
    for _zone in _spawn_zones.get(_mob_id, ()):
        REGION_COLLECTION_ENTRIES.setdefault(_zone, {}).setdefault("bosses", set()).add(_mob_id)

for _rare_id, _rare_data in MOB_TEMPLATES.items():
    if _rare_id not in RARE_MOB_COLLECTION_CATALOG:
        continue
    _base = _rare_data.get("rare_base_template", _rare_id)
    for _zone in _spawn_zones.get(_base, ()):
        REGION_COLLECTION_ENTRIES.setdefault(_zone, {}).setdefault("rare", set()).add(_rare_id)

for _room_id in CHEST_COLLECTION_CATALOG:
    _zone = ROOMS.get(_room_id, {}).get("zone")
    if _zone:
        REGION_COLLECTION_ENTRIES.setdefault(_zone, {}).setdefault("chests", set()).add(_room_id)

for _mob_id, _mob in MOB_TEMPLATES.items():
    _named_drops = set(_mob.get("drops", {})).intersection(NAMED_LOOT_CATALOG)
    if not _named_drops:
        continue
    _base = _mob.get("rare_base_template") or _mob.get("elite_base_template") or _mob_id
    for _zone in _spawn_zones.get(_base, set()) | _spawn_zones.get(_mob_id, set()):
        REGION_COLLECTION_ENTRIES.setdefault(_zone, {}).setdefault("named", set()).update(_named_drops)


def loot_rarity_rank(item_id):
    item = ITEMS.get(item_id, {})
    return LOOT_RARITY_ORDER.get(str(item.get("rarity", "common")).lower(), 0)


def loot_filter_allows(mode, item_id):
    mode = str(mode or "all").lower()
    rank = loot_rarity_rank(item_id)
    if mode == "off":
        return False
    if mode == "rare+":
        return rank >= 1
    if mode == "epic+":
        return rank >= 2
    if mode == "legendary":
        return rank >= 3
    return True


HELP_TOPIC_ALIASES.update({
    "geody": "geody", "geodes": "geody", "geoda": "geody", "gemquality": "geody",
})
HELP_TOPICS["geody"] = [
    "Geody są rzadkim dodatkowym znaleziskiem podczas Górnictwa i trafiają do Sakwy Górnika.",
    "Geoda Kamienna: Kilof 20+, głębokość 10+; Kryształowa: 80+/60+; Astralna: 160+/150+.",
    "geody / geodes - pokaż posiadane geody.",
    "open geode / otwórz geodę / otworz geode - otwórz najlepszą posiadaną geodę; możesz podać jej nazwę.",
    "Jakości klejnotów: Surowy -> Czysty -> Doskonały -> Perfekcyjny. Wyższa jakość daje mocniejszy bonus po szlifowaniu.",
]
if "gornictwo" in HELP_TOPICS:
    HELP_TOPICS["gornictwo"].append("Kilof 20+ może znajdować geody; wpisz geody albo open geode / otwórz geodę.")
if "profesje" in HELP_TOPICS:
    HELP_TOPICS["profesje"].append("Wędka/Kilof/Piła/Sierp rozwijają się obecnie 1-400; dawna wygładzona część krzywej 1-200 pozostaje zachowana, a 201-400 jest jej dalszą progresją.")

COMMAND_ALIASES.update({
    "bestiariusz": "bestiary", "bestiary": "bestiary",
    "postep": "progress", "postęp": "progress", "progress": "progress",
    "eksploracja": "exploration", "exploration": "exploration",
    "osiagniecia": "achievements", "osiągnięcia": "achievements",
    "achievement": "achievements", "achievements": "achievements",
    "tytuly": "titles", "tytuły": "titles", "titles": "titles",
    "tytul": "title", "tytuł": "title", "title": "title",
    "kolekcja": "collection", "collection": "collection",
    "collectioncodex": "collection", "collection_codex": "collection",
    "historiadropow": "drophistory", "historiadropów": "drophistory",
    "drophistory": "drophistory", "dropy": "drophistory",
    "lootfilter": "lootfilter", "filtrlootu": "lootfilter",
    "regionprogress": "regionprogress", "postepregionu": "regionprogress",
})

