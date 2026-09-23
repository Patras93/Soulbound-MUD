from data import catalog_mutations as _catalog_mut

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
    #    mithril nie może destabilizować skali nagród pojedynczego surowca.
    for item in ITEMS.values():
        old_mithril = int(item.get("sell_mithril", 0) or 0)
        old_gold = int(item.get("sell_gold", 0) or 0)
        if old_mithril > 0:
            # Sprzedawalny przedmiot za dawny 1 mithril daje 100 000 złota,
            # a nie pełny mithril wart 1 000 000 złota.
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
# pozostają nominałami prezentacji: 100 srebra = 1 złoto,
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
for _level in range(210, SOUL_MAX_LEVEL + 1, 10):
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
    _catalog_mut.catalog_assign({"soul_elixir": 2}, 'QUESTS', QUESTS, ("soul_shards", "reward_items"))
if "neris_fish_1" in QUESTS:
    _catalog_mut.catalog_assign(1200, 'QUESTS', QUESTS, ("neris_fish_1", "reward_profession_xp"))
    _catalog_mut.catalog_assign(1000, 'QUESTS', QUESTS, ("neris_fish_1", "reward_tool_xp"))


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
        _catalog_mut.catalog_pop_path('ROOMS', ROOMS, ("troll_cave_3", "exits"), "south", None)

    # Pradawny Las: pierwotne wejście ``south`` z Deep Grove zostało zajęte
    # przez Bagna. Zachowujemy oba tereny i dodajemy niezależne zejście.
    if "deep_grove" in ROOMS and profession_dungeon_room_id("ancient_forest", 1) in ROOMS:
        _catalog_mut.catalog_assign(profession_dungeon_room_id("ancient_forest", 1), 'ROOMS', ROOMS, ("deep_grove", "exits", "down"))
        if "Wejście do Pradawnego Lasu" not in ROOMS["deep_grove"]["desc"]:
            _catalog_mut.catalog_aug_path('ROOMS', ROOMS, ("deep_grove", "desc"), 'Add', " Wejście do Pradawnego Lasu prowadzi w dół, w najgęstszy ostęp.")

    # Ogród Alchemika: wschodnie wyjście Zielarki zajęło później laboratorium.
    # Dodajemy osobne północne wejście, nie usuwając laboratorium ani ogrodu ziół.
    if "herbalist_hut" in ROOMS and profession_dungeon_room_id("alchemy_garden", 1) in ROOMS:
        _catalog_mut.catalog_assign(profession_dungeon_room_id("alchemy_garden", 1), 'ROOMS', ROOMS, ("herbalist_hut", "exits", "north"))
        if "Ogród Alchemika" not in ROOMS["herbalist_hut"]["desc"]:
            _catalog_mut.catalog_aug_path('ROOMS', ROOMS, ("herbalist_hut", "desc"), 'Add', " Na północy znajduje się wejście do Ogrodu Alchemika.")

    # Pustynia: północ Ruin Strażnicy została później zajęta przez Ruiny
    # Kultystów. Pustynia pozostaje podłączona osobnym podejściem w górę.
    if "ruined_watchtower" in ROOMS and "dry_canyon" in ROOMS:
        _catalog_mut.catalog_assign("dry_canyon", 'ROOMS', ROOMS, ("ruined_watchtower", "exits", "up"))
        if "Suchy Kanion" not in ROOMS["ruined_watchtower"]["desc"]:
            _catalog_mut.catalog_aug_path('ROOMS', ROOMS, ("ruined_watchtower", "desc"), 'Add', " Stroma droga w górę prowadzi do Suchego Kanionu i dalej ku Pustyni.")


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
        _catalog_mut.catalog_assign(variant, 'MOB_TEMPLATES', MOB_TEMPLATES, (variant_id,))
        _configure_dynamic_corpse_material(variant)
        spawns.append((room_id, variant_id))
    return spawns

def _ensure_dynamic_boss_key(kind, floor):
    key_id = boss_floor_key_id(kind, floor)
    if key_id not in ITEMS:
        _catalog_mut.catalog_assign({
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
        }, 'ITEMS', ITEMS, (key_id,))
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
    return min(CLASS_MASTERY_MAX_LEVEL, max(50, (floor // 50) * 50))


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
    # EQ rośnie do progresji 600, potem ma twardy cap mimo nieskończonej Krypty.
    tier = min(SOUL_MAX_TIER, max(1, (floor - 1) // 10 + 1))
    if mythic:
        tier = min(SOUL_MAX_TIER, max(20, 20 + (floor - 1) // 10))
    gear = [f"crypt_t{tier}_{slot}" for slot in CLASS_EQUIPMENT_SLOT_DEFS]
    if mythic:
        room_id = mythic_crypt_floor_id(floor)
        exits = {
            "up": "mythic_crypt_gate" if floor == 1 else mythic_crypt_floor_id(floor - 1),
            "down": mythic_crypt_floor_id(floor + 1),
        }
        note = " Przy pierwszym przejściu mityczny boss blokuje zejście do chwili pokonania." if is_mythic_crypt_boss_floor(floor) else ""
        _catalog_mut.catalog_assign({
            "zone": "Mityczna Krypta",
            "name": f"Mityczna Krypta, piętro {floor}",
            "desc": f"Mityczne piętro {floor}. Próg trudności {crypt_depth_step(floor)}.{note}",
            "exits": exits,
            "procedural_infinite": True,
        }, 'ROOMS', ROOMS, (room_id,))
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
        _catalog_mut.catalog_assign(template, 'MOB_TEMPLATES', MOB_TEMPLATES, (regular_id,))
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
            _catalog_mut.catalog_assign(boss, 'MOB_TEMPLATES', MOB_TEMPLATES, (boss_id,))
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
    _catalog_mut.catalog_assign({
        "zone": "Krypta Nieskończona",
        "name": f"Krypta, piętro {floor}",
        "desc": f"Piętro {floor}. Próg trudności {crypt_depth_step(floor)}.{note}",
        "exits": exits,
        "procedural_infinite": True,
    }, 'ROOMS', ROOMS, (room_id,))
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
    _catalog_mut.catalog_assign(template, 'MOB_TEMPLATES', MOB_TEMPLATES, (regular_id,))
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
        _catalog_mut.catalog_assign(boss, 'MOB_TEMPLATES', MOB_TEMPLATES, (boss_id,))
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
    # Waluta, surowce i gear zatrzymują ekonomiczną moc na progresji 600.
    return min(CHARACTER_MAX_LEVEL, max(1, int(floor)))

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
        _catalog_mut.catalog_assign({
            "zone": "Mityczna Wieża Astralna",
            "name": f"Mityczna Wieża Astralna, poziom {floor}",
            "desc": (
                f"Mityczny poziom {floor}. Wieża ciągnie się dalej bez końca. "
                f"Próg głębi {max(0, (floor - 1) // 10)}. "
                f"Motyw piętra: {theme['label']} — {theme['desc']}.{note}"
            ),
            "exits": exits,
            "procedural_infinite": True,
        }, 'ROOMS', ROOMS, (room_id,))
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
        _catalog_mut.catalog_assign(template, 'MOB_TEMPLATES', MOB_TEMPLATES, (regular_id,))
        _configure_dynamic_corpse_material(template)
        spawns = _dynamic_regular_mob_pack(
            room_id, regular_id, template, MYTHIC_ASTRAL_REGULAR_NAMES, floor, "poziom"
        )
        if floor % 5 == 0 and not is_mythic_astral_boss_floor(floor):
            challenge_id = f"mythic_astral_challenge_{floor}"
            challenge = _infinite_challenge_template(template, "mythic_astral", floor)
            challenge["elite_base_template"] = regular_id
            _catalog_mut.catalog_assign(challenge, 'MOB_TEMPLATES', MOB_TEMPLATES, (challenge_id,))
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
            _catalog_mut.catalog_assign(boss, 'MOB_TEMPLATES', MOB_TEMPLATES, (boss_id,))
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
    _catalog_mut.catalog_assign({
        "zone": "Wieża Astralna",
        "name": f"Wieża Astralna, poziom {floor}",
        "desc": (
            f"Poziom {floor}. Wieża nie ma szczytu; gwiezdne kondygnacje "
            f"ciągną się dalej bez końca. Motyw piętra: {theme['label']} — "
            f"{theme['desc']}.{note}"
        ),
        "exits": exits,
        "procedural_infinite": True,
    }, 'ROOMS', ROOMS, (room_id,))
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
    _catalog_mut.catalog_assign(template, 'MOB_TEMPLATES', MOB_TEMPLATES, (regular_id,))
    _configure_dynamic_corpse_material(template)
    spawns = _dynamic_regular_mob_pack(
        room_id, regular_id, template, ASTRAL_REGULAR_NAMES, floor, "poziom"
    )
    if floor % 5 == 0 and not is_astral_boss_floor(floor):
        challenge_id = f"astral_challenge_{floor}"
        challenge = _infinite_challenge_template(template, "astral", floor)
        challenge["elite_base_template"] = regular_id
        _catalog_mut.catalog_assign(challenge, 'MOB_TEMPLATES', MOB_TEMPLATES, (challenge_id,))
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
        _catalog_mut.catalog_assign(boss, 'MOB_TEMPLATES', MOB_TEMPLATES, (boss_id,))
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
    _catalog_mut.catalog_assign({
        "zone": "Twierdza Gigantów",
        "name": f"Twierdza Gigantów - poziom {floor}",
        "desc": (
            f"Poziom {floor}. Twierdza ciągnie się bez końca w górę. "
            f"Próg głębi {max(0, (floor - 1) // 10)}. "
            f"Motyw piętra: {theme['label']} — {theme['desc']}.{note}"
        ),
        "exits": exits,
        "procedural_infinite": True,
    }, 'ROOMS', ROOMS, (room_id,))
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
    _catalog_mut.catalog_assign(template, 'MOB_TEMPLATES', MOB_TEMPLATES, (mob_id,))
    _configure_dynamic_corpse_material(template)
    spawns = _dynamic_regular_mob_pack(
        room_id, mob_id, template, names, floor, "poziom"
    )
    if floor % 5 == 0 and not is_giant_fortress_boss_floor(floor):
        challenge_id = f"giant_fortress_challenge_{floor}"
        challenge = _infinite_challenge_template(template, "giant", floor)
        challenge["elite_base_template"] = mob_id
        _catalog_mut.catalog_assign(challenge, 'MOB_TEMPLATES', MOB_TEMPLATES, (challenge_id,))
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
        _catalog_mut.catalog_assign(boss, 'MOB_TEMPLATES', MOB_TEMPLATES, (boss_id,))
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
    effective = min(TOOL_MAX_LEVEL, floor)
    feature = infinite_gathering_floor_feature("deep_mine", floor, MINE_PREGENERATED_MAX_FLOOR)
    generated_profile = v0250_mine_floor_profile(floor)
    if effective < 10:
        richness = "zwykłe skały i miedź"
    elif effective < 100:
        richness = "coraz bogatsze żyły metali"
    elif effective < 200:
        richness = "rzadkie rudy endgame"
    else:
        richness = "najwyższe rudy progresji 600"
    _catalog_mut.catalog_assign({
        "zone": "Kopalnia Głębinowa",
        "name": f"Kopalnia - poziom {floor}",
        "desc": (
            f"Poziom {floor}. Kopalnia schodzi bez końca. W skale występują {richness}. "
            "Moc surowców nie przekracza capu progresji 600. "
            f"Generator piętra: {generated_profile['shape']}, {generated_profile['strata']}; "
            f"{generated_profile['sign']}."
            + (f" Specjalny sektor: {feature['label']} — {feature['desc']}." if feature['label'] else "")
        ),
        "exits": exits,
        "procedural_infinite": True,
        "infinite_gather_feature": feature,
        "v0250_generator_profile": generated_profile,
    }, 'ROOMS', ROOMS, (room_id,))
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
            "Najrzadsze ryby nadal respektują cap Wędkarstwa 600."
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
            "Jakość drewna zatrzymuje progresję mocy na levelu 600."
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
            "Rzadkość ziół respektuje cap progresji 600."
            + (f" Specjalny sektor: {feature['label']} — {feature['desc']}." if feature['label'] else "")
        )
        HERBALISM_ROOMS.add(room_id)
    else:
        return None, []
    _catalog_mut.catalog_assign({
        "zone": zone,
        "name": name,
        "desc": desc,
        "exits": exits,
        "procedural_infinite": True,
        "infinite_gather_feature": feature,
    }, 'ROOMS', ROOMS, (room_id,))
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
        "Skill Level 1-600 ma łagodne, malejące skalowanie mocy i cooldownu; XP skilla zdobywa się szybciej, żeby 200 było osiągalne bez dziesiątek tysięcy użyć jednego skilla.",
        "Różne buffy multiclass nadal działają jednocześnie i uniwersalnie, ale buff nie wzmacnia siły kolejnego buffa, a łączny bonus ma limit +125 procent.",
        "Pojedyncze leczenie ma limit 80 procent maksymalnego HP na cast po wszystkich buffach; leczenie grupowe 60 procent na cel.",
        "Po zużyciu gwarantowanego evade działa wspólny 4-sekundowy lockout dla kolejnego gwarantowanego uniku.",
        "Mithril z Górnictwa jest walutą, nie rudą. Od poziomu 80 może wypaść jako dodatkowy bonus; szansa rośnie od 0,5 do 2 procent i nie zastępuje zwykłego urobku.",
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
        "Mithril z Górnictwa ma od 0,5 procent szansy na poziomie 80 do 2 procent na poziomie 600. Jest dodatkową walutą i nie zastępuje rudy. Widmowy marlin odblokowuje się od Wędki 190.",
        "Czas Wędkarstwa zależy od poziomu Wędkarstwa; od poziomu 200 do 600 obowiązuje końcowe minimum 3 sekundy. Level Wędki nie skraca czasu.",
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
