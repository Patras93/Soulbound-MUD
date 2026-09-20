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
        # v0.36.5: Soul Tier 7 asks for 4 Niespokojnych Zmarłych. Keep six
        # simultaneous targets distributed across the whole Stary Cmentarz so the
        # trial never depends on waiting for a single respawn.
        ("graveyard","cemetery_restless_dead"),("cemetery_ossuary_path","cemetery_restless_dead"),
        ("cemetery_moon_garden","cemetery_restless_dead"),("cemetery_fallen_chapel","cemetery_restless_dead"),
        ("cemetery_bone_field","cemetery_restless_dead"),("cemetery_bell_tower","cemetery_restless_dead"),
        ("cemetery_moon_garden","cemetery_grave_hound"),("cemetery_fallen_chapel","cemetery_bone_collector"),("cemetery_bone_field","cemetery_grave_hound"),("cemetery_bell_tower","cemetery_bell_wraith"),("cemetery_keeper_tomb","cemetery_keeper"),
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
        "Uczę pracy z drewnem od levelu 1 do 600."
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
        "Prowadzę Jubilerstwo od levelu 1 do 600. "
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
        "Każda z 14 klas ma pełny zestaw 8 części: głowa, korpus, dłonie, nogi, stopy, talizman, pierścień i naszyjnik.",
        "Klasowe EQ ma Tiery Biegłości 1, 10, 20, 30 i dalej co 10 aż do 600; każdy próg daje mocniejszy pełny zestaw.",
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
            "Aktualne profesje 1-600: Wędkarstwo, Górnictwo, Drwalstwo, Zielarstwo, Gotowanie, Alchemia, Kowalstwo i Jubilerstwo. Każda ma własny poziom; odpowiadające narzędzie rozwija się osobno."
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
        "Każda z 14 klas ma teraz własną salę i własnego nauczyciela.",
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

# v0.31.2: sale treningowe nowych klas technologicznych, obecne przed auditami.
ROOMS.setdefault("guild_mec_chamber", {
    "name": "Hangar Meca", "zone": "Gildia Dusz",
    "desc": "Wzmocniony hangar z rdzeniami energetycznymi i stanowiskami ciężkiego pancerza.",
    "exits": {"south": "guild_martial_hall"},
})
ROOMS.setdefault("guild_engineer_chamber", {
    "name": "Warsztat Inżyniera", "zone": "Gildia Dusz",
    "desc": "Warsztat pełen narzędzi, działek testowych, skanerów i mechanicznych konstrukcji.",
    "exits": {"east": "guild_shadow_gallery"},
})
ROOMS.setdefault("guild_martial_hall", {}).setdefault("exits", {})["east"] = "guild_mec_chamber"
ROOMS.setdefault("guild_shadow_gallery", {}).setdefault("exits", {})["west"] = "guild_engineer_chamber"
if "teacher_mec" in NPCS:
    NPCS["teacher_mec"]["room"] = "guild_mec_chamber"
if "teacher_engineer" in NPCS:
    NPCS["teacher_engineer"]["room"] = "guild_engineer_chamber"
