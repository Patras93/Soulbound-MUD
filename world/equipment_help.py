

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
                base_name = re.sub(r",\s*(?:poziom|piętro)\s+\d+.*$", "", str(base.get("name", "Przeciwnik")), flags=re.I).strip()
                if base_name.casefold().strip() == str(chosen).casefold().strip():
                    variant["name"] = f"{chosen} — patrolowy łowca{suffix}"
                else:
                    variant["name"] = f"{chosen} — {base_name}{suffix}"
                distinct_archetypes.add(str(chosen).casefold().strip())
            else:
                variant["name"] = f"{base.get('name', 'Przeciwnik')} — patrolowy łowca"
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
        "Pokazuje rasę, główną i aktywne klasy, Biegłość każdej klasy, Soul Level/Tier i Soul Weapon Mastery, HP, Manę i sześć statystyk.",
        "Pokazuje też wspólny portfel konta, aktualną lokację/strefę oraz dynamiczną ocenę terenu.",
        "score i expowiska pokazują orientacyjną ocenę terenu w historycznej skali 1-400; con i dynamiczny EXP walki używają osobnej bieżącej skali siły 1-400. Żadna z tych ocen nie jest levelem postaci.",
    ]
    HELP_TOPICS["dusza"] = [
        "dusza pokazuje krótki stan Broni Duszy: Soul Level, Tier, Soul XP, moc i następny cel.",
        "dusza info pokazuje pełne progi Tierów 1-40 oraz stan Prób Broni Duszy potrzebnych do dalszej progresji.",
        "Kolejne Tiery do 40 wymagają odpowiedniego Soul Levelu i właściwego odblokowania; progi 1-200 zachowują wcześniejsze Próby, a 201-400 kontynuują progresję endgame.",
        "Soul Level ma zakres 1-400 i rozwija Broń Duszy; nie jest levelem postaci. Soul Weapon Mastery ma osobny zakres 1-400 i rozwija wyłącznie zwykły atak broni.",
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
        "Każda z 14 klas ma 3 różne linie EQ na każdym progu Biegłości; alternatywne linie mają równy budżet mocy, więc wybór jest różnorodnością, nie power creepem.",
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
        "Gra ma 14 ras. Od v0.9.0 każda rasa ma dokładnie 50 bazowych punktów rozdzielonych między Siłę, Zręczność, Kondycję, Inteligencję i Siłę Woli; nie ma rasy z ukrytym większym budżetem startowym.",
        "Rasy różnią się rozkładem tych 50 punktów oraz własnym pasywem, więc nadal mają wyraźne specjalizacje.",
        "Każda z 14 klas dokłada dokładnie 9 własnych punktów startowych; startowa Charyzma bazowa wynosi 10 przed bonusem klasy.",
        "Kreator podaje polecane klasy dla każdej rasy, ale żadna kombinacja rasa-klasa nie jest blokowana.",
        "opis <rasa> pokazuje opis rasy oraz polecane klasy.",
    ]
    HELP_TOPICS["umiejetnosci"] = [
        "Każda z 14 klas ma Biegłość 1-400; istniejące progi odblokowania skilli 1-200 pozostają bez zmian.",
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

# v0.30.51: Social & Mentor help
HELP_TOPICS["kanaly"] = [
    "Kanały komunikacji: gossip <tekst> — rozmowy ogólne; newbie <tekst> — pytania i pomoc dla nowych; trade <tekst> — handel.",
    "Lokalnie: say. Prywatnie: tell. Drużyna: pc. Gildia: gildia czat <tekst>.",
    "channels lub kanaly wyświetla skrót kanałów.",
]
HELP_TOPICS["mentor"] = [
    "Mentor System: mentor wymaga Biegłości 50 i Soul Level 50; uczeń może mieć maksymalnie Biegłość 20 i Soul Level 20.",
    "Komendy: mentor; mentor zapros <gracz>; mentor akceptuj <gracz>; mentor zakoncz.",
    "W tej samej drużynie i lokacji obaj dostają +5% Class XP, Soul XP oraz XP profesji i narzędzi.",
]

# v0.30.51 Social Suite 2.0
HELP_TOPICS["social"] = ["Social 2.0: ignore/unignore, friends/friend, afk, whois, mail, board, lfg, inspect, emote/smile/wave/cheer.", "Kanały gossip/newbie/trade mają on/off, historię i ochronę przed spamem."]
HELP_TOPICS["mail"] = ["mail list; mail send <gracz> <tekst>; mail read <id>; mail delete <id>."]
HELP_TOPICS["lfg"] = ["lfg crypt [opis]; lfg boss [opis]; lfg profession [opis]; lfg list; lfg off."]
HELP_TOPICS["house"] = ["house — własny dom; house name <tekst>; house decor <tekst>; house upgrade; house chest; house store/take <przedmiot> [ilość]; house trophies."]
HELP_TOPICS["records"] = ["records [gracz] — rekordy: głębokość lochu, największy krytyk, najcięższa ryba i zabicia."]

# v0.30.52 quick help aliases
HELP_TOPICS.update({
    "collection2": "Collection Codex 2.0: collection2 [braki]. Pokazuje ryby, rudy, sety, bossów, rare i sekrety.",
    "completion": "Completion % 2.0: procent świata, profesji, bossów, kolekcji i całej gry.",
    "deathrecap": "Death Recap: podsumowanie ostatniej śmierci.",
    "combatrecap": "Combat Recap: podsumowanie ostatniej zapisanej walki.",
    "loothistory": "Loot History 2.0: drophistory [tekst] lub loothistory [tekst].",
    "nvda": "Presety dostępności: nvda <combat|social|system|all> <concise|normal|full>.",
})
