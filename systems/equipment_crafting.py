from data import catalog_mutations as _catalog_mut

# v0.44.0: explicit dependencies; no compatibility-global injection.
import random
from core.classes_skills import ROOMS
from core.mines_threat import ITEMS
from core.progression_600 import CLASS_MASTERY_MAX_LEVEL, PROFESSION_MAX_LEVEL, PROGRESSION_400_LEVELS, TOOL_MAX_LEVEL
from core.progression_resources import RIVER_FISH_ATLAS, class_type_for_name
from systems.items_resources import (
    BLACKSMITH_SLOT_DEFS,
    BLACKSMITH_TIERS,
    CLASS_EQUIPMENT_CLASS_PROFILES,
    CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER,
    CLASS_EQUIPMENT_ITEM_IDS,
    CLASS_EQUIPMENT_MASTERY_LEVELS,
    CLASS_EQUIPMENT_SETS,
    CLASS_EQUIPMENT_SLOT_DEFS,
    CLASS_EQUIPMENT_SLOT_PRIMARY_BIAS,
    CLASS_EQUIPMENT_SLOT_PROPERTY_SCALE,
    CLASS_EQUIPMENT_STYLES,
    CLASS_SHOP_CLASSES_BY_ROOM,
    CLASS_SHOP_ITEMS_BY_ROOM,
    FISH_STORAGE_IDS,
    ORE_STORAGE_IDS,
    _BLACKSMITH_400_LABELS,
    _PROGRESSION_400_NAMES,
    base_fish_species_id,
)



def class_equipment_base_stat_pair(class_name):
    if class_type_for_name(class_name) == "magic":
        return "intelligence", "willpower"
    return "strength", "constitution"


def class_equipment_profile(class_name):
    return CLASS_EQUIPMENT_CLASS_PROFILES.get(
        class_name,
        {"primary_ratio": 0.50, "identity": "równowaga", "properties": {}},
    )


def class_equipment_split_stat_budget(class_name, legacy_amount, slot=None):
    budget = max(2, int(legacy_amount or 0))
    profile = class_equipment_profile(class_name)
    ratio = float(profile.get("primary_ratio", 0.50))
    ratio += float(CLASS_EQUIPMENT_SLOT_PRIMARY_BIAS.get(str(slot or ""), 0.0))
    ratio = max(0.20, min(0.80, ratio))
    # Obie statystyki muszą zawsze pozostać realne.
    primary_amount = int(round(budget * ratio))
    primary_amount = max(1, min(budget - 1, primary_amount))
    secondary_amount = budget - primary_amount
    primary_stat, secondary_stat = class_equipment_base_stat_pair(class_name)
    return primary_stat, primary_amount, secondary_stat, secondary_amount


def class_equipment_profile_properties(class_name, mastery, slot=None):
    profile = class_equipment_profile(class_name)
    weights = dict(profile.get("properties") or {})
    if not weights:
        return {}
    mastery = max(1, min(CLASS_MASTERY_MAX_LEVEL, int(mastery or 1)))
    # Łagodny budżet właściwości: ok. 0.3% na początku do 2.0% na część przy 600.
    total = 0.25 + 1.75 * ((mastery - 1) / float(max(1, CLASS_MASTERY_MAX_LEVEL - 1))) ** 0.90
    total *= float(CLASS_EQUIPMENT_SLOT_PROPERTY_SCALE.get(str(slot or ""), 1.0))
    norm = sum(max(0.0, float(v)) for v in weights.values()) or 1.0
    return {
        prop: round(total * max(0.0, float(weight)) / norm, 2)
        for prop, weight in weights.items()
        if float(weight) > 0
    }

def class_equipment_base_stats_text(class_name, legacy_amount, slot=None):
    pstat, pamount, sstat, samount = class_equipment_split_stat_budget(
        class_name, legacy_amount, slot
    )
    labels = {
        "strength": "Siła",
        "constitution": "Kondycja",
        "intelligence": "Inteligencja",
        "willpower": "Siła Woli",
    }
    return (
        f"{labels.get(pstat, pstat)} +{pamount}, "
        f"{labels.get(sstat, sstat)} +{samount}"
    )


def _class_equipment_tier_label(required_mastery):
    if required_mastery <= 1:
        return "Biegłość 1"
    return f"Biegłość {required_mastery}"


def _class_equipment_rarity_name(required_mastery):
    if required_mastery >= 600:
        return "Klasowy Absolutny"
    if required_mastery >= 500:
        return "Klasowy Kosmiczny"
    if required_mastery >= 400:
        return "Klasowy Transcendentny"
    if required_mastery >= 350:
        return "Klasowy Mityczny"
    if required_mastery >= 300:
        return "Klasowy Pradawny"
    if required_mastery >= 250:
        return "Klasowy Wieczny"
    if required_mastery >= 200:
        return "Klasowy Mistrzowski"
    if required_mastery >= 150:
        return "Klasowy Legendarny"
    if required_mastery >= 100:
        return "Klasowy Epicki"
    if required_mastery >= 50:
        return "Klasowy Rzadki"
    return "Klasowy"


def class_equipment_stat_budget(required_mastery, slot=None):
    """Łączny budżet dwóch bazowych statów klasowego EQ.

    Każdy próg 1/10/20/.../600 zwiększa budżet dokładnie o 1, dzięki czemu
    nawet niskie Tiery mają realnie inne statystyki. Sloty biżuterii zachowują
    lekko wyższy punkt startowy, ale progresja między Tierami jest zawsze
    ścisła i monotoniczna.
    """
    try:
        tier_index = CLASS_EQUIPMENT_MASTERY_LEVELS.index(int(required_mastery))
    except ValueError:
        unlocked = class_equipment_unlocked_tier(required_mastery)
        tier_index = CLASS_EQUIPMENT_MASTERY_LEVELS.index(int(unlocked))
    slot = str(slot or "")
    if slot in ("necklace", "relic"):
        base_affix = 3
    elif slot in ("ring", "charm", "earring", "shoulders", "belt", "cloak", "bracers"):
        base_affix = 2
    else:
        base_affix = 1
    return max(2, int(base_affix)) + int(tier_index)


def class_equipment_unlocked_tier(mastery_level):
    mastery_level = max(1, min(CLASS_MASTERY_MAX_LEVEL, int(mastery_level)))
    unlocked = 1
    for threshold in CLASS_EQUIPMENT_MASTERY_LEVELS:
        if threshold <= mastery_level:
            unlocked = threshold
        else:
            break
    return unlocked


def _register_class_equipment_shops():
    for class_name, definition in CLASS_EQUIPMENT_SETS.items():
        CLASS_SHOP_CLASSES_BY_ROOM.setdefault(definition["room"], []).append(class_name)
        per_tier = CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER.setdefault(class_name, {})
        styles = CLASS_EQUIPMENT_STYLES.get(class_name, (definition["set_name"],))

        for tier_index, required_mastery in enumerate(CLASS_EQUIPMENT_MASTERY_LEVELS):
            tier_items = []
            # v0.9.19: KAŻDY próg Biegłości co 10 daje realnie lepsze EQ.
            # Do 200 zachowujemy ten sam łączny budżet mocy co wcześniej,
            # ale rozkładamy go naprzemiennie: raz rośnie obrona, raz affix.
            # Po 200 kontynuujemy tę samą czytelną zasadę aż do 600.
            # Dzięki temu nie ma "pustych" progów 10/30/50..., a wzrost pozostaje łagodny.
            defense_step = (tier_index + 1) // 2
            # v0.36.0: każdy próg 1/10/20/30/.../600 ma inny realny
            # budżet podstawowych statów. Wcześniej affix rósł co drugi próg,
            # więc np. część niskiego EQ 1/10/20 mogła mieć identyczne
            # Siła/Kondycja albo Inteligencja/Siła Woli. Teraz łączny budżet
            # rośnie dokładnie o 1 na każdym kolejnym Tierze, zachowując
            # klasowy ratio i bias konkretnego slotu.
            # Ceny rosną wyraźnie wraz z Biegłością, ale pozostają w istniejącej ekonomii srebra.
            price_multiplier = 1 + tier_index + (tier_index * tier_index) // 4

            for style_index, style_name in enumerate(styles, 1):
                for slot, (slot_name, defense_delta, base_price) in CLASS_EQUIPMENT_SLOT_DEFS.items():
                    # Pierwsza linia zachowuje stare ID 1:1.
                    style_suffix = "" if style_index == 1 else f"_s{style_index}"
                    if required_mastery == 1:
                        item_id = f"class_{definition['prefix']}{style_suffix}_{slot}"
                    else:
                        item_id = f"class_{definition['prefix']}{style_suffix}_m{required_mastery}_{slot}"

                    if slot in ("necklace", "relic"):
                        base_affix = 3
                    elif slot in ("ring", "charm", "earring", "shoulders", "belt", "cloak", "bracers"):
                        base_affix = 2
                    else:
                        base_affix = 1

                    # Minimalny Tier zawsze ma obie statystyki (budżet >= 2),
                    # a każdy następny próg dodaje kolejny pełny punkt budżetu.
                    legacy_affix_amount = class_equipment_stat_budget(required_mastery, slot)
                    primary_stat, primary_amount, secondary_stat, secondary_amount = (
                        class_equipment_split_stat_budget(class_name, legacy_affix_amount, slot)
                    )
                    defense = max(
                        1,
                        int(definition["base_defense"]) + int(defense_delta) + defense_step,
                    )
                    # Alternatywne linie nie są droższe ani tańsze od bazowej.
                    price = max(1, int(base_price) * int(price_multiplier))
                    tier_label = _class_equipment_tier_label(required_mastery)

                    _catalog_mut.catalog_assign({
                        "name": (
                            f"{slot_name} {style_name}"
                            if required_mastery == 1
                            else f"{slot_name} {style_name} +{required_mastery}"
                        ),
                        "type": "armor",
                        "slot": slot,
                        "defense": defense,
                        "price": price,
                        "currency": "silver",
                        "rarity": "crafted",
                        "rarity_name": _class_equipment_rarity_name(required_mastery),
                        "affix": primary_stat,
                        "affix_amount": primary_amount,
                        "stats": {secondary_stat: secondary_amount},
                        "class_base_stat_pair": (primary_stat, secondary_stat),
                        "required_class": class_name,
                        "required_mastery": required_mastery,
                        "class_shop_item": True,
                        "class_set_name": style_name,
                        "class_set_piece": slot,
                        "class_equipment_tier": tier_index + 1,
                        "class_equipment_style": style_index,
                        # v0.61.2: opis zwykłego klasowego EQ jest składany na żądanie
                        # z istniejących pól. Nie przechowujemy 38k długich kopii tekstu w RAM.
                    }, 'ITEMS', ITEMS, (item_id,))
                    CLASS_EQUIPMENT_ITEM_IDS.add(item_id)
                    tier_items.append(item_id)

            per_tier[required_mastery] = tuple(tier_items)

        # Statyczna lista zachowuje pełną ofertę Tier 1 dla zgodności starych miejsc kodu.
        # Interfejs sklepu dynamicznie pokazuje najlepszy odblokowany Tier.
        CLASS_SHOP_ITEMS_BY_ROOM[definition["room"]].extend(per_tier[1])


_register_class_equipment_shops()

# v0.9.11: brak startowego EQ klasowego. Klasowe wyposażenie zdobywa się w sklepach i z losowego dropu mobów.

GUILD_REPUTATION_MAX = 1000
GUILD_REPUTATION_RANKS = (
    (0, "Nowicjusz", 0.00),
    (100, "Znany", 0.05),
    (250, "Zaufany", 0.10),
    (450, "Weteran", 0.15),
    (700, "Elita Gildii", 0.20),
    (1000, "Legenda Gildii", 0.25),
)

GUILD_EXAM_THRESHOLDS = (50, 100, 150, 200)
GUILD_EXAM_REPUTATION = {50: 100, 100: 250, 150: 450, 200: 700}

GUILD_CLASS_QUESTS = {
    "Wojownik": ("Próba Ostrza", "Pokonaj 8 przeciwników dla Gildii.", 80, 600, 8),
    "Berserker": ("Próba Furii", "Pokonaj 10 przeciwników dla Gildii.", 90, 700, 10),
    "Łotrzyk": ("Próba Cienia", "Pokonaj 8 przeciwników dla Gildii.", 85, 650, 8),
    "Łowca": ("Próba Tropiciela", "Pokonaj 10 przeciwników dla Gildii.", 80, 600, 10),
    "Mnich": ("Próba Dyscypliny", "Pokonaj 8 przeciwników dla Gildii.", 90, 700, 8),
    "Strażnik": ("Próba Bastionu", "Pokonaj 6 przeciwników dla Gildii.", 100, 800, 6),
    "Mag": ("Próba Arkanów", "Pokonaj 10 przeciwników dla Gildii.", 90, 700, 10),
    "Nekromanta": ("Próba Dusz", "Pokonaj 10 przeciwników dla Gildii.", 90, 700, 10),
    "Kapłan": ("Próba Światła", "Pokonaj 6 przeciwników dla Gildii.", 100, 800, 6),
    "Czarownik": ("Próba Otchłani", "Pokonaj 10 przeciwników dla Gildii.", 95, 750, 10),
    "Druid": ("Próba Natury", "Pokonaj 8 przeciwników dla Gildii.", 90, 700, 8),
    "Psionik": ("Próba Umysłu", "Pokonaj 10 przeciwników dla Gildii.", 95, 750, 10),
    "Mec": ("Próba Rdzenia", "Pokonaj 8 przeciwników dla Gildii.", 100, 800, 8),
    "Inżynier": ("Próba Konstruktora", "Pokonaj 10 przeciwników dla Gildii.", 90, 700, 10),
}

GUILD_BOUNTY_TARGETS = (
    # v0.8.61: nagrody są wartościami jednego wspólnego salda w srebrze.
    # 100 srebra = 1 złoto; 1 000 000 złota = 1 mithril.
    ("wild_horned_king", "Rogaty Król Dziczy", 120, 1_000_000),       # 1 000 złota
    ("mountain_storm_eagle", "Orzeł Burzy", 140, 2_500_000),         # 2 500 złota
    ("deep_troll_warlord", "Głęboki Wódz Trolli", 160, 5_000_000),   # 5 000 złota
    ("swamp_hydra", "Hydra Bagienna", 180, 10_000_000),              # 10 000 złota
    ("sun_guardian", "Strażnik Słońca", 200, 20_000_000),            # 20 000 złota
    ("end_wild_primal_avatar", "Pierwotny Avatar Dziczy", 220, 50_000_000),
    ("end_mountain_tempest_titan", "Tytan Wiecznej Burzy", 260, 100_000_000),
    ("end_troll_first_warlord", "Pierwszy Wódz Trolli Grommar", 300, 150_000_000),
    ("end_swamp_primordial_hydra", "Pierwotna Hydra Bagna", 360, 250_000_000),
    ("end_desert_eternal_sun", "Awatar Wiecznego Słońca", 450, 500_000_000),
)

CLASS_SET_BONUSES = {
    "Wojownik": {
        "stats": {"strength": 4},
        "damage": 1.10, "defense": 1.15, "vitality": 1.18,
    },
    "Berserker": {
        "stats": {"strength": 5},
        "damage": 1.15, "defense": 1.08, "vitality": 1.12,
    },
    "Łotrzyk": {
        "stats": {"dexterity": 5},
        "damage": 1.14, "defense": 1.08, "vitality": 1.10,
    },
    "Łowca": {
        "stats": {"dexterity": 4},
        "damage": 1.12, "defense": 1.10, "vitality": 1.12,
    },
    "Mnich": {
        "stats": {"dexterity": 3, "willpower": 2},
        "damage": 1.11, "defense": 1.12, "vitality": 1.15,
    },
    "Strażnik": {
        # Pełny profil tanka: dużo Kondycji i Siły Woli,
        # minimalny bonus obrażeń, bardzo wysoka obrona i HP.
        "stats": {"constitution": 8, "willpower": 4},
        "damage": 1.05, "defense": 1.35, "vitality": 1.40,
    },
    "Mag": {
        "stats": {"intelligence": 5},
        "damage": 1.15, "defense": 1.08, "vitality": 1.14,
    },
    "Nekromanta": {
        "stats": {"intelligence": 4, "willpower": 2},
        "damage": 1.14, "defense": 1.10, "vitality": 1.16,
    },
    "Kapłan": {
        "stats": {"willpower": 5},
        "damage": 1.09, "defense": 1.15, "vitality": 1.20,
    },
    "Czarownik": {
        "stats": {"intelligence": 5},
        "damage": 1.16, "defense": 1.07, "vitality": 1.12,
    },
    "Druid": {
        "stats": {"willpower": 3, "intelligence": 2},
        "damage": 1.11, "defense": 1.12, "vitality": 1.18,
    },
    "Psionik": {
        "stats": {"willpower": 3, "intelligence": 2},
        "damage": 1.13, "defense": 1.11, "vitality": 1.16,
    },
    "Mec": {"stats": {"constitution": 4}, "damage": 1.08, "defense": 1.18, "vitality": 1.20},
    "Inżynier": {"stats": {"dexterity": 4}, "damage": 1.12, "defense": 1.08, "vitality": 1.08},
}

CLASS_SET_STAT_NAMES = {
    "strength": "Siła",
    "dexterity": "Zręczność",
    "constitution": "Kondycja",
    "intelligence": "Inteligencja",
    "willpower": "Siła Woli",
}


# ============================================================
# v0.9.20 - LEGENDARY CLASS LOOT 50/100
# ============================================================
# Bossowie co 50 pięter mogą dawać pełnoprawne setowe EQ dla każdej z 14 klas.
# Bossowie co 100 pięter dodatkowo dają osobny legendarny relikt klasowy.
# Wszystko nadal respektuje Biegłość i ręczne zakładanie EQ.
LEGENDARY_CLASS_LOOT_TIERS = tuple(range(50, CLASS_MASTERY_MAX_LEVEL + 1, 50))
LEGENDARY_CLASS_SET_ITEMS_BY_CLASS_TIER = {}
LEGENDARY_CLASS_RELIC_BY_CLASS_TIER = {}


def _legendary_class_loot_stat_profile(class_name):
    definition = CLASS_EQUIPMENT_SETS[class_name]
    return class_equipment_base_stat_pair(class_name)[0], int(definition["base_defense"])


def _register_legendary_class_loot():
    for class_name, definition in CLASS_EQUIPMENT_SETS.items():
        affix, base_defense = _legendary_class_loot_stat_profile(class_name)
        set_name = f"Legendy {definition['set_name']}"
        class_slug = definition["prefix"]
        class_sets = LEGENDARY_CLASS_SET_ITEMS_BY_CLASS_TIER.setdefault(class_name, {})
        relics = LEGENDARY_CLASS_RELIC_BY_CLASS_TIER.setdefault(class_name, {})

        for mastery in LEGENDARY_CLASS_LOOT_TIERS:
            tier_index = max(1, mastery // 10)
            defense_step = (tier_index + 1) // 2
            affix_step = tier_index // 2
            tier_items = []
            for slot, (slot_name, defense_delta, _base_price) in CLASS_EQUIPMENT_SLOT_DEFS.items():
                item_id = f"legendset_{class_slug}_m{mastery}_{slot}"
                defense = max(1, base_defense + int(defense_delta) + defense_step + 1)
                base_affix = 3 if slot in ("necklace", "relic") else 2 if slot in ("ring", "charm", "earring", "shoulders", "belt", "cloak", "bracers") else 1
                legacy_affix_amount = base_affix + affix_step + 1
                primary_stat, primary_amount, secondary_stat, secondary_amount = (
                    class_equipment_split_stat_budget(class_name, legacy_affix_amount)
                )
                _catalog_mut.catalog_assign({
                    "name": f"{slot_name} {set_name} +{mastery}",
                    "type": "armor",
                    "slot": slot,
                    "defense": defense,
                    "price": None,
                    "rarity": "legendary",
                    "rarity_name": "Legendarny Setowy",
                    "affix": primary_stat,
                    "affix_amount": primary_amount,
                    "stats": {secondary_stat: secondary_amount},
                    "class_base_stat_pair": (primary_stat, secondary_stat),
                    "required_class": class_name,
                    "required_mastery": mastery,
                    # Celowo korzysta z istniejących progów 2/4/6/8 klasy.
                    "class_shop_item": True,
                    "class_set_name": set_name,
                    "class_set_piece": slot,
                    "legendary_set_loot": True,
                    "legendary_loot_tier": mastery,
                    "desc": (
                        f"Legendarna część zestawu dla klasy {class_name}. "
                        f"Wymaga aktywnej klasy {class_name} i Biegłości {mastery}. "
                        f"Zdobywana z bossów kamieni milowych co 50 pięter. Obrona +{defense}. "
                        f"Podstawowe statystyki EQ: "
                        f"{class_equipment_base_stats_text(class_name, legacy_affix_amount, slot)}."
                    ),
                }, 'ITEMS', ITEMS, (item_id,))
                CLASS_EQUIPMENT_ITEM_IDS.add(item_id)
                tier_items.append(item_id)
            class_sets[mastery] = tuple(tier_items)

            relic_id = f"legendrelic_{class_slug}_m{mastery}"
            relic_defense = max(1, base_defense + 4 + defense_step + 2)
            legacy_relic_affix = 4 + affix_step + 2
            relic_primary_stat, relic_primary_amount, relic_secondary_stat, relic_secondary_amount = (
                class_equipment_split_stat_budget(class_name, legacy_relic_affix)
            )
            prop_value = max(1, min(5, mastery // 100 + 1))
            properties = {
                "all_damage_pct": prop_value,
                "physical_defense_pct": prop_value,
                "magic_defense_pct": prop_value,
            }
            if class_type_for_name(class_name) == "magic":
                properties["max_mana_pct"] = prop_value
            else:
                properties["max_hp_pct"] = prop_value
            _catalog_mut.catalog_assign({
                "name": f"Relikwiarz Legendy {definition['set_name']} +{mastery}",
                "type": "armor",
                "slot": "necklace",
                "defense": relic_defense,
                "price": None,
                "rarity": "legendary",
                "rarity_name": "Legendarny Klasowy",
                "affix": relic_primary_stat,
                "affix_amount": relic_primary_amount,
                "stats": {relic_secondary_stat: relic_secondary_amount},
                "class_base_stat_pair": (relic_primary_stat, relic_secondary_stat),
                "required_class": class_name,
                "required_mastery": mastery,
                "properties": properties,
                "legendary_class_relic": True,
                "legendary_loot_tier": mastery,
                "desc": (
                    f"Legendarny relikt klasy {class_name} z bossa kamienia milowego co 100 pięter. "
                    f"Wymaga Biegłości {mastery}. Nie należy do zestawu, więc jest świadomą alternatywą "
                    "dla naszyjnika setowego. "
                    f"Podstawowe statystyki EQ: "
                    f"{class_equipment_base_stats_text(class_name, legacy_relic_affix)}."
                ),
            }, 'ITEMS', ITEMS, (relic_id,))
            relics[mastery] = relic_id


_register_legendary_class_loot()

_catalog_mut.catalog_assign({
    "name": "Szczypce Jubilerskie",
    "type": "tool",
    "tool_type": "jewelcrafting",
    "price": 10,
    "currency": "silver",
    "desc": (
        "Podstawowe narzędzie Jubilerstwa. "
        "Ma własny level 1-600, XP i 60 Tierów. "
        "Nie ma trwałości i nie zużywa się."
    ),
}, 'ITEMS', ITEMS, ("jeweler_pliers",))

from data.shops import SHOPS
for _room_id, _items in CLASS_SHOP_ITEMS_BY_ROOM.items():
    _catalog_mut.catalog_assign(list(_items), 'SHOPS', SHOPS, (_room_id,))



SHOP_SELLERS = {
    "market": "market_trader_radan",
    "fish_market": "specialist_fishing",
    "inn": "innkeeper",
    "forge": "doran",
    "cave_entrance": "miner_toren",
    "lumberjack_camp": "specialist_woodcutting",
    "herbalist_hut": "herbalist_liora",
    "jeweler_workshop": "jeweler_mirella",
    "guild_martial_hall": "guild_quartermaster_martial",
    "guild_shadow_gallery": "guild_quartermaster_shadow",
    "guild_body_hall": "guild_quartermaster_body",
    "guild_arcane_chamber": "guild_quartermaster_arcane",
    "guild_dark_chamber": "guild_quartermaster_dark",
    "guild_sanctuary": "guild_quartermaster_sanctuary",
}


for _room_id in CLASS_SHOP_ITEMS_BY_ROOM:
    _catalog_mut.catalog_aug_path('ROOMS', ROOMS, (_room_id, "desc"), 'Add', " W tej sali działa także klasowy sklep "
        "z pełnym 14-elementowym wyposażeniem.")


from data.crafting_recipes import CRAFT_RECIPES

def _register_blacksmith_recipes():
    # Existing first three ingot recipes become proper
    # Kowalstwo recipes without changing their output IDs.
    basic_requirements = {
        "iron_ingot": (1, 1, 10),
        "silver_ingot": (20, 20, 14),
        "gold_ingot": (40, 40, 18),
    }
    for recipe_id, (
        tool_level, profession_level, profession_xp
    ) in basic_requirements.items():
        recipe = CRAFT_RECIPES[recipe_id]
        recipe["category"] = "smithing"
        recipe["min_tool_level"] = tool_level
        recipe["min_profession_level"] = profession_level
        recipe["profession_xp"] = profession_xp
        recipe["tool_xp"] = max(
            8, int(profession_xp * 0.8)
        )

    for tier_number, tier in enumerate(BLACKSMITH_TIERS, 1):
        ingot_id = tier["ingot"]

        if ingot_id not in {
            "iron_ingot", "silver_ingot", "gold_ingot"
        }:
            _catalog_mut.catalog_assign({
                "name": ITEMS[ingot_id]["name"],
                "stations": ("forge",),
                "ingredients": {
                    tier["ore"]: 1,
                },
                "output": ingot_id,
                "quantity": 1,
                "min_tool_level": tier["tool_level"],
                "min_profession_level": tier[
                    "profession_level"
                ],
                "profession_xp": (
                    16 + tier_number * 4
                ),
                "tool_xp": (
                    12 + tier_number * 4
                ),
                "category": "smithing",
                "desc": (
                    f"Przetop 1 sztukę surowca "
                    f"{ITEMS[tier['ore']]['name']} "
                    f"w 1 sztabkę."
                ),
            }, 'CRAFT_RECIPES', CRAFT_RECIPES, (ingot_id,))

        for slot, (
            slot_name, _def_delta, ingot_cost
        ) in BLACKSMITH_SLOT_DEFS.items():
            output_id = (
                f"smith_{tier['key']}_{slot}"
            )
            recipe_id = (
                f"forge_{tier['key']}_{slot}"
            )
            _catalog_mut.catalog_assign({
                "name": ITEMS[output_id]["name"],
                "stations": ("forge",),
                "ingredients": {
                    ingot_id: ingot_cost,
                },
                "output": output_id,
                "quantity": 1,
                "min_tool_level": tier["tool_level"],
                "min_profession_level": tier[
                    "profession_level"
                ],
                "profession_xp": (
                    20 + tier_number * 6
                ),
                "tool_xp": (
                    15 + tier_number * 5
                ),
                "category": "smithing",
                "desc": (
                    f"Wykuj {slot_name.lower()} z materiału "
                    f"{tier['name']}. "
                    f"Wymaga Kowalstwa level "
                    f"{tier['profession_level']}."
                ),
            }, 'CRAFT_RECIPES', CRAFT_RECIPES, (recipe_id,))

_register_blacksmith_recipes()

from data.alchemy_recipes import ALCHEMY_RECIPES


JEWELCRAFTING_TIERS = (
    {
        "key": "iron", "material": "iron_ore",
        "level": 1, "label": "Żelazny",
        "affix": "constitution", "affix_amount": 1,
        "defense": 1,
    },
    {
        "key": "silver", "material": "silver_ore",
        "level": 20, "label": "Srebrny",
        "affix": "willpower", "affix_amount": 1,
        "defense": 2,
    },
    {
        "key": "gold", "material": "gold_ore",
        "level": 40, "label": "Złoty",
        "affix": "intelligence", "affix_amount": 2,
        "defense": 3,
    },
    {
        "key": "cobalt", "material": "cobalt_ore",
        "level": 100, "label": "Kobaltowy",
        "affix": "strength", "affix_amount": 3,
        "defense": 4,
    },
    {
        "key": "runic", "material": "runestone_ore",
        "level": 120, "label": "Runiczny",
        "affix": "dexterity", "affix_amount": 3,
        "defense": 5,
    },
    {
        "key": "dragonsteel", "material": "dragonsteel_ore",
        "level": 140, "label": "Smoczej Stali",
        "affix": "constitution", "affix_amount": 4,
        "defense": 6,
    },
    {
        "key": "astral", "material": "astral_ore",
        "level": 160, "label": "Astralny",
        "affix": "intelligence", "affix_amount": 5,
        "defense": 7,
    },
    {
        "key": "void", "material": "void_ore",
        "level": 180, "label": "Pustki",
        "affix": "willpower", "affix_amount": 5,
        "defense": 8,
    },
    {
        "key": "eternium", "material": "eternium_ore",
        "level": 200, "label": "Eternium",
        "affix": "strength", "affix_amount": 6,
        "defense": 10,
    },
)

JEWELCRAFTING_TIERS += tuple(
    {
        "key": f"p400_{level}", "material": f"ore_400_{level}",
        "level": level, "label": _BLACKSMITH_400_LABELS[level],
        "affix": ("strength", "dexterity", "constitution", "intelligence", "willpower")[(level // 20) % 5],
        "affix_amount": 6 + (level - 200) // 40,
        "defense": 10 + (level - 200) // 40,
    }
    for level in PROGRESSION_400_LEVELS
)

JEWELCRAFT_RECIPES = {}

def _register_jewelcrafting_recipes():
    for tier in JEWELCRAFTING_TIERS:
        ring_id = f"jewel_{tier['key']}_ring"
        necklace_id = f"jewel_{tier['key']}_necklace"
        earring_id = f"jewel_{tier['key']}_earring"
        socket_count = 3 if tier["level"] >= 180 else 2 if tier["level"] >= 100 else 1
        earring_sockets = 2 if tier["level"] >= 180 else 1

        _catalog_mut.catalog_assign({
            "name": f"{tier['label']} Pierścień Jubilerski", "type": "armor", "slot": "ring",
            "defense": tier["defense"], "price": None, "rarity": "crafted", "rarity_name": "Jubilerski",
            "affix": tier["affix"], "affix_amount": tier["affix_amount"], "jewelcraft_level": tier["level"],
            "sockets": socket_count,
            "desc": f"Pierścień wykonany przez Jubilerstwo. Wymaga Jubilerstwa level {tier['level']}. Obrona +{tier['defense']}.",
        }, 'ITEMS', ITEMS, (ring_id,))
        _catalog_mut.catalog_assign({
            "name": f"{tier['label']} Naszyjnik Jubilerski", "type": "armor", "slot": "necklace",
            "defense": tier["defense"] + 1, "price": None, "rarity": "crafted", "rarity_name": "Jubilerski",
            "affix": tier["affix"], "affix_amount": tier["affix_amount"] + 1, "jewelcraft_level": tier["level"],
            "sockets": socket_count,
            "desc": f"Naszyjnik wykonany przez Jubilerstwo. Wymaga Jubilerstwa level {tier['level']}. Obrona +{tier['defense'] + 1}.",
        }, 'ITEMS', ITEMS, (necklace_id,))
        # Kolczyk ma inny profil: mniej obrony, więcej ofensywnego affixu. Dwie sztuki można nosić naraz.
        _catalog_mut.catalog_assign({
            "name": f"{tier['label']} Kolczyk Jubilerski", "type": "armor", "slot": "earring",
            "defense": max(0, tier["defense"] - 1), "price": None, "rarity": "crafted", "rarity_name": "Jubilerski",
            "affix": tier["affix"], "affix_amount": tier["affix_amount"] + 1, "jewelcraft_level": tier["level"],
            "sockets": earring_sockets,
            "desc": f"Kolczyk wykonany przez Jubilerstwo. Można nosić dwie sztuki. Wymaga Jubilerstwa level {tier['level']}.",
        }, 'ITEMS', ITEMS, (earring_id,))

        base_xp = 12 + tier["level"] // 8
        JEWELCRAFT_RECIPES[ring_id] = {
            "name": ITEMS[ring_id]["name"], "stations": ("jeweler_workshop",), "ingredients": {tier["material"]: 2},
            "output": ring_id, "quantity": 1, "min_tool_level": tier["level"], "min_profession_level": tier["level"],
            "profession_xp": base_xp, "tool_xp": max(8, base_xp - 2),
            "desc": f"Jubilerstwo level {tier['level']}. Wykonuje pierścień z 2 sztuk materiału.",
        }
        JEWELCRAFT_RECIPES[necklace_id] = {
            "name": ITEMS[necklace_id]["name"], "stations": ("jeweler_workshop",), "ingredients": {tier["material"]: 3},
            "output": necklace_id, "quantity": 1, "min_tool_level": tier["level"], "min_profession_level": tier["level"],
            "profession_xp": base_xp + 3, "tool_xp": max(9, base_xp),
            "desc": f"Jubilerstwo level {tier['level']}. Wykonuje naszyjnik z 3 sztuk materiału.",
        }
        JEWELCRAFT_RECIPES[earring_id] = {
            "name": ITEMS[earring_id]["name"], "stations": ("jeweler_workshop",), "ingredients": {tier["material"]: 2},
            "output": earring_id, "quantity": 1, "min_tool_level": tier["level"], "min_profession_level": tier["level"],
            "profession_xp": base_xp + 1, "tool_xp": max(8, base_xp - 1),
            "desc": f"Jubilerstwo level {tier['level']}. Wykonuje jeden kolczyk z 2 sztuk materiału; do obu uszu potrzebujesz dwóch sztuk.",
        }


_register_jewelcrafting_recipes()


GEM_AFFIX_NAMES = {
    "strength": "Siła",
    "dexterity": "Zręczność",
    "constitution": "Kondycja",
    "intelligence": "Inteligencja",
    "willpower": "Siła Woli",
    "hp": "HP",
    "mana": "Mana",
}

GEM_DEFINITIONS = (
    {
        "key": "ruby",
        "raw_name": "Surowy Rubin",
        "cut_name": "Szlifowany Rubin",
        "level": 1,
        "mining_level": 1,
        "min_floor": 1,
        "affix": "strength",
        "amount": 1,
    },
    {
        "key": "sapphire",
        "raw_name": "Surowy Szafir",
        "cut_name": "Szlifowany Szafir",
        "level": 20,
        "mining_level": 20,
        "min_floor": 10,
        "affix": "intelligence",
        "amount": 1,
    },
    {
        "key": "emerald",
        "raw_name": "Surowy Szmaragd",
        "cut_name": "Szlifowany Szmaragd",
        "level": 40,
        "mining_level": 40,
        "min_floor": 25,
        "affix": "dexterity",
        "amount": 2,
    },
    {
        "key": "amethyst",
        "raw_name": "Surowy Ametyst",
        "cut_name": "Szlifowany Ametyst",
        "level": 60,
        "mining_level": 60,
        "min_floor": 40,
        "affix": "willpower",
        "amount": 2,
    },
    {
        "key": "diamond",
        "raw_name": "Surowy Diament",
        "cut_name": "Szlifowany Diament",
        "level": 80,
        "mining_level": 80,
        "min_floor": 60,
        "affix": "constitution",
        "amount": 2,
    },
    {
        "key": "soul_topaz",
        "raw_name": "Surowy Topaz Duszy",
        "cut_name": "Szlifowany Topaz Duszy",
        "level": 100,
        "mining_level": 100,
        "min_floor": 100,
        "affix": "hp",
        "amount": 25,
    },
    {
        "key": "mana_opal",
        "raw_name": "Surowy Opal Many",
        "cut_name": "Szlifowany Opal Many",
        "level": 120,
        "mining_level": 120,
        "min_floor": 120,
        "affix": "mana",
        "amount": 25,
    },
    {
        "key": "dragon_garnet",
        "raw_name": "Surowy Granat Smoczej Stali",
        "cut_name": "Szlifowany Granat Smoczej Stali",
        "level": 140,
        "mining_level": 140,
        "min_floor": 140,
        "affix": "strength",
        "amount": 4,
    },
    {
        "key": "astral_crystal",
        "raw_name": "Surowy Kryształ Astralny",
        "cut_name": "Szlifowany Kryształ Astralny",
        "level": 160,
        "mining_level": 160,
        "min_floor": 160,
        "affix": "intelligence",
        "amount": 5,
    },
    {
        "key": "void_onyx",
        "raw_name": "Surowy Onyks Pustki",
        "cut_name": "Szlifowany Onyks Pustki",
        "level": 180,
        "mining_level": 180,
        "min_floor": 180,
        "affix": "willpower",
        "amount": 5,
    },
    {
        "key": "eternium_prism",
        "raw_name": "Surowy Pryzmat Eternium",
        "cut_name": "Szlifowany Pryzmat Eternium",
        "level": 200,
        "mining_level": 200,
        "min_floor": 200,
        "affix": "constitution",
        "amount": 6,
    },
)

RAW_GEM_IDS = set()
CUT_GEM_IDS = set()

def _register_gem_system():
    for definition in GEM_DEFINITIONS:
        raw_id = f"raw_gem_{definition['key']}"
        cut_id = f"cut_gem_{definition['key']}"
        RAW_GEM_IDS.add(raw_id)
        CUT_GEM_IDS.add(cut_id)

        # v0.8.67: surowe klejnoty są częścią urobku Górnictwa.
        # Trafiają do Sakwy Górnika i mogą zostać sprzedane wyłącznie Dagnie.
        raw_gem_sell_gold = {
            "ruby": 1,
            "sapphire": 3,
            "emerald": 6,
            "amethyst": 12,
            "diamond": 25,
            "soul_topaz": 45,
            "mana_opal": 75,
            "dragon_garnet": 120,
            "astral_crystal": 180,
            "void_onyx": 280,
            "eternium_prism": 450,
        }
        _catalog_mut.catalog_assign({
            "name": definition["raw_name"],
            "type": "gem_raw",
            "price": None,
            "sell_gold": raw_gem_sell_gold[definition["key"]],
            "gem_key": definition["key"],
            "gem_level": definition["level"],
            "mining_bag_resource": True,
            "desc": (
                f"Surowy kamień szlachetny z Górnictwa. "
                f"Trafia do Sakwy Górnika. Dagna skupuje go na Górskim Targu Minerałów. "
                f"Szlifowanie wymaga Jubilerstwa i Szczypiec "
                f"Jubilerskich level {definition['level']}."
            ),
        }, 'ITEMS', ITEMS, (raw_id,))
        _catalog_mut.catalog_assign({
            "name": definition["cut_name"],
            "type": "gem",
            "price": None,
            "gem_key": definition["key"],
            "gem_level": definition["level"],
            "affix": definition["affix"],
            "affix_amount": definition["amount"],
            "desc": (
                f"Osadzany klejnot jubilerski. "
                f"Bonus po osadzeniu: "
                f"{GEM_AFFIX_NAMES.get(definition['affix'], definition['affix'])} "
                f"+{definition['amount']}."
            ),
        }, 'ITEMS', ITEMS, (cut_id,))

        JEWELCRAFT_RECIPES[f"cut_{definition['key']}"] = {
            "name": definition["cut_name"],
            "aliases": (
                definition["raw_name"],
                definition["key"],
            ),
            "stations": ("jeweler_workshop",),
            "ingredients": {raw_id: 1},
            "output": cut_id,
            "quantity": 1,
            "min_tool_level": definition["level"],
            "min_profession_level": definition["level"],
            "profession_xp": 10 + definition["level"] // 5,
            "tool_xp": 8 + definition["level"] // 6,
            "gem_cut_recipe": True,
            "desc": (
                f"Szlifowanie kamienia. Jubilerstwo level "
                f"{definition['level']}."
            ),
        }

_register_gem_system()

# v0.8.75 - jakość klejnotów + geody.
# Nie zmieniamy schematu SQLite: każda jakość jest zwykłym item_id.
GEM_QUALITY_ORDER = ("raw", "pure", "excellent", "perfect")
GEM_QUALITY_INFO = {
    "raw": {"label": "Surowy", "cut_label": "Szlifowany", "sell_mult": 1.0, "power_mult": 1.0},
    "pure": {"label": "Czysty", "cut_label": "Szlifowany Czysty", "sell_mult": 1.6, "power_mult": 1.25},
    "excellent": {"label": "Doskonały", "cut_label": "Szlifowany Doskonały", "sell_mult": 2.5, "power_mult": 1.50},
    "perfect": {"label": "Perfekcyjny", "cut_label": "Szlifowany Perfekcyjny", "sell_mult": 4.0, "power_mult": 1.75},
}

def gem_quality_item_id(kind, gem_key, quality):
    if quality == "raw":
        return f"{kind}_gem_{gem_key}"
    return f"{kind}_gem_{gem_key}_{quality}"

def gem_quality_amount(base_amount, quality):
    base_amount = max(1, int(base_amount))
    index = GEM_QUALITY_ORDER.index(quality)
    scaled = int(round(base_amount * GEM_QUALITY_INFO[quality]["power_mult"]))
    # Każdy wyższy stopień jakości musi być odczuwalny także przy bonusie +1.
    return max(base_amount + index, scaled)

def roll_mined_gem_quality(tool_level, profession_level):
    tool_level = max(1, min(TOOL_MAX_LEVEL, int(tool_level)))
    profession_level = max(1, min(PROFESSION_MAX_LEVEL, int(profession_level)))
    power = (tool_level + profession_level) / 2.0
    old_power = min(200.0, power)
    # 1-200 zachowuje stare szanse. 201-600 dodaje mały dalszy bonus,
    # ale perfekcyjny kamień nadal pozostaje jackpotem.
    perfect = 0.0 if old_power < 120 else min(0.020, (old_power - 120) * 0.00025)
    excellent = 0.0 if old_power < 70 else min(0.100, (old_power - 70) * 0.00077)
    pure = 0.0 if old_power < 30 else min(0.180, (old_power - 30) * 0.00106)
    post = max(0.0, power - 200.0)
    perfect += min(0.020, post * 0.00010)
    excellent += min(0.050, post * 0.00025)
    pure += min(0.040, post * 0.00020)
    roll = random.random()
    if roll < perfect:
        return "perfect"
    if roll < perfect + excellent:
        return "excellent"
    if roll < perfect + excellent + pure:
        return "pure"
    return "raw"

def _register_gem_quality_variants():
    for definition in GEM_DEFINITIONS:
        key = definition["key"]
        base_raw_id = f"raw_gem_{key}"
        base_sell = int(ITEMS[base_raw_id].get("sell_gold", 0) or 0)
        base_name = definition["raw_name"].replace("Surowy ", "", 1)
        cut_base_name = definition["cut_name"].replace("Szlifowany ", "", 1)
        for quality in GEM_QUALITY_ORDER[1:]:
            info = GEM_QUALITY_INFO[quality]
            raw_id = gem_quality_item_id("raw", key, quality)
            cut_id = gem_quality_item_id("cut", key, quality)
            raw_name = f"{info['label']} {base_name}"
            cut_name = f"{info['cut_label']} {cut_base_name}"
            RAW_GEM_IDS.add(raw_id)
            CUT_GEM_IDS.add(cut_id)
            _catalog_mut.catalog_assign({
                "name": raw_name, "type": "gem_raw", "price": None,
                "sell_gold": max(1, int(round(base_sell * info["sell_mult"]))),
                "gem_key": key, "gem_level": definition["level"],
                "gem_quality": quality, "mining_bag_resource": True,
                "desc": (
                    f"{info['label']} wariant kamienia z Górnictwa. Trafia do Sakwy Górnika. "
                    f"Szlifowanie wymaga Jubilerstwa level {definition['level']}."
                ),
            }, 'ITEMS', ITEMS, (raw_id,))
            amount = gem_quality_amount(definition["amount"], quality)
            _catalog_mut.catalog_assign({
                "name": cut_name, "type": "gem", "price": None,
                "gem_key": key, "gem_level": definition["level"],
                "gem_quality": quality, "affix": definition["affix"],
                "affix_amount": amount,
                "desc": (
                    f"Klejnot jakości {info['label'].lower()}. Bonus po osadzeniu: "
                    f"{GEM_AFFIX_NAMES.get(definition['affix'], definition['affix'])} +{amount}."
                ),
            }, 'ITEMS', ITEMS, (cut_id,))
            recipe_id = f"cut_{key}_{quality}"
            JEWELCRAFT_RECIPES[recipe_id] = {
                "name": cut_name,
                "aliases": (raw_name, cut_name, f"{quality} {key}"),
                "stations": ("jeweler_workshop",),
                "ingredients": {raw_id: 1},
                "output": cut_id, "quantity": 1,
                "min_tool_level": definition["level"],
                "min_profession_level": definition["level"],
                "profession_xp": 12 + definition["level"] // 5 + GEM_QUALITY_ORDER.index(quality) * 3,
                "tool_xp": 10 + definition["level"] // 6 + GEM_QUALITY_ORDER.index(quality) * 2,
                "gem_cut_recipe": True,
                "desc": f"Szlifowanie jakości {info['label'].lower()}. Jubilerstwo level {definition['level']}.",
            }

_register_gem_quality_variants()

GEODE_DEFINITIONS = {
    "stone_geode": {
        "name": "Geoda Kamienna", "min_tool": 20, "min_floor": 10, "max_gem_level": 60,
        "sell_gold": 3, "quality_weights": (85, 15, 0, 0), "gold": (0, 1), "gem_qty": (1, 1),
    },
    "crystal_geode": {
        "name": "Geoda Kryształowa", "min_tool": 80, "min_floor": 60, "max_gem_level": 140,
        "sell_gold": 15, "quality_weights": (65, 28, 7, 0), "gold": (1, 3), "gem_qty": (1, 2),
    },
    "astral_geode": {
        "name": "Geoda Astralna", "min_tool": 160, "min_floor": 150, "max_gem_level": 200,
        "sell_gold": 60, "quality_weights": (45, 35, 17, 3), "gold": (3, 10), "gem_qty": (1, 3),
    },
}
GEODE_IDS = set(GEODE_DEFINITIONS)
for _geode_id, _geode in GEODE_DEFINITIONS.items():
    _catalog_mut.catalog_assign({
        "name": _geode["name"], "type": "geode", "price": None,
        "sell_gold": _geode["sell_gold"], "mining_bag_resource": True,
        "desc": (
            f"Rzadkie znalezisko Górnictwa. Kilof {_geode['min_tool']}+, "
            f"głębokość {_geode['min_floor']}+. Możesz sprzedać Dagnie albo otworzyć: "
            "open geode / otwórz geodę."
        ),
    }, 'ITEMS', ITEMS, (_geode_id,))

def roll_mining_geode(tool_level, profession_level, floor):
    tool_level = max(1, min(TOOL_MAX_LEVEL, int(tool_level)))
    profession_level = max(1, min(PROFESSION_MAX_LEVEL, int(profession_level)))
    # v0.9.13: głębokość lochu jest nieskończona, ale zasobowa moc ekonomii
    # zatrzymuje się na progresji 600.
    floor = max(1, min(PROFESSION_MAX_LEVEL, int(floor or 1)))
    eligible = [
        geode_id for geode_id, cfg in GEODE_DEFINITIONS.items()
        if tool_level >= cfg["min_tool"] and floor >= cfg["min_floor"]
    ]
    if not eligible:
        return None
    chance = min(0.045, 0.012 + (tool_level + profession_level) / 20000.0 + floor / 20000.0)
    if random.random() >= chance:
        return None
    if "astral_geode" in eligible:
        return random.choices(["stone_geode", "crystal_geode", "astral_geode"], weights=[4, 5, 3], k=1)[0]
    if "crystal_geode" in eligible:
        return random.choices(["stone_geode", "crystal_geode"], weights=[6, 4], k=1)[0]
    return "stone_geode"

# v0.8.67: osobny zestaw zawartości Sakwy Górnika. ORE_STORAGE_IDS pozostaje
# zestawem prawdziwych rud/minerałów używanym przez questy typu "dowolna ruda",
# więc znalezienie rubinu nie podbija postępu questa na rudy.
MINING_STORAGE_IDS = set(ORE_STORAGE_IDS) | set(RAW_GEM_IDS) | set(GEODE_IDS)

def gem_definition_by_raw_id(item_id):
    if not item_id.startswith("raw_gem_"):
        return None
    key = item_id[len("raw_gem_"):]
    for definition in GEM_DEFINITIONS:
        if definition["key"] == key:
            return definition
    return None

def gem_definition_by_cut_id(item_id):
    if not item_id.startswith("cut_gem_"):
        return None
    key = item_id[len("cut_gem_"):]
    for definition in GEM_DEFINITIONS:
        if definition["key"] == key:
            return definition
    return None

def jewelry_socket_capacity(item):
    if not item or item.get("slot") not in ("ring", "necklace", "earring"):
        return 0

    explicit = item.get("sockets")
    if explicit is not None:
        return max(0, int(explicit))

    if item.get("required_class"):
        return 2 if item.get("slot") == "necklace" else 1

    level = int(item.get("jewelcraft_level", 1))
    if item.get("slot") == "earring":
        return 2 if level >= 180 else 1
    if level >= 180:
        return 3
    if level >= 100:
        return 2
    return 1

# v0.30.39: pełna pula ryb rzecznych do Gotowania. Obejmuje każdy bazowy
# gatunek rzeczny oraz wszystkie rzadkie warianty tych gatunków. Dzięki temu
# późniejszy Tier Wędki nigdy nie blokuje pierwszego zlecenia Kucharza Marcela.
RIVER_FISH_COOKING_IDS = tuple(sorted(
    item_id for item_id in FISH_STORAGE_IDS
    if base_fish_species_id(item_id) in RIVER_FISH_ATLAS
))

COOK_RECIPES = {
    "grilled_river_fish": {
        "name": "Pieczona ryba rzeczna", "stations": ("inn", "fish_market"),
        "ingredients": {},
        "pooled_ingredient_pool": RIVER_FISH_COOKING_IDS,
        "pooled_ingredient_count": 2,
        "pooled_ingredient_label": "dowolne ryby rzeczne",
        "output": "grilled_river_fish", "quantity": 1,
        "min_tool_level": 1, "tool_xp": 8,
        "desc": (
            "Gotowanie level 1. Wymaga 2 dowolnych ryb rzecznych. Mogą to być "
            "te same albo różne gatunki, ryby ze starszych i późniejszych Tierów "
            "oraz rzadkie warianty gatunków rzecznych. Przywraca do 30 HP."
        ),
    },
    "river_fish_stew": {
        "name": "Gulasz rzeczny", "stations": ("inn", "fish_market"),
        "ingredients": {"river_carp": 1, "chub": 1},
        "output": "river_fish_stew", "quantity": 1,
        "min_tool_level": 10, "tool_xp": 10,
        "desc": "Gotowanie level 10. Karp rzeczny + Kleń. Przywraca do 45 HP.",
    },
    "herb_crusted_perch": {
        "name": "Okoń w Ziołowej Skorupce", "stations": ("inn", "fish_market"),
        "ingredients": {"river_perch": 1, "mint": 1},
        "output": "herb_crusted_perch", "quantity": 1,
        "min_tool_level": 20, "tool_xp": 12,
        "desc": "Gotowanie level 20. Okoń rzeczny + Mięta. Przywraca do 42 HP i 5 Many.",
    },
    "lake_fish_stew": {
        "name": "Potrawka jeziorowa", "stations": ("inn", "fish_market"),
        "ingredients": {"bream": 1, "tench": 1},
        "output": "lake_fish_stew", "quantity": 1,
        "min_tool_level": 30, "tool_xp": 13,
        "desc": "Gotowanie level 30. Leszcz + Lin. Przywraca do 50 HP i 10 Many.",
    },
    "silver_trout_soup": {
        "name": "Zupa ze Srebrnego Pstrąga", "stations": ("inn", "fish_market"),
        "ingredients": {"silver_trout": 1, "sage": 1},
        "output": "silver_trout_soup", "quantity": 1,
        "min_tool_level": 40, "tool_xp": 14,
        "desc": "Gotowanie level 40. Srebrny pstrąg + Szałwia. Przywraca do 52 HP i 12 Many.",
    },
    "sea_chowder": {
        "name": "Zupa morska", "stations": ("inn", "fish_market"),
        "ingredients": {"cod": 1, "herring": 1},
        "output": "sea_chowder", "quantity": 1,
        "min_tool_level": 50, "tool_xp": 15,
        "desc": "Gotowanie level 50. Dorsz + Śledź. Przywraca do 60 HP i 15 Many.",
    },
    "lake_fisher_pie": {
        "name": "Zapiekanka Jeziornego Rybaka", "stations": ("inn", "fish_market"),
        "ingredients": {"lake_perch": 1, "bream": 1},
        "output": "lake_fisher_pie", "quantity": 1,
        "min_tool_level": 60, "tool_xp": 17,
        "desc": "Gotowanie level 60. Okoń jeziorowy + Leszcz. Przywraca do 62 HP i 18 Many.",
    },
    "spiced_mackerel": {
        "name": "Makrela Korzenna", "stations": ("inn", "fish_market"),
        "ingredients": {"mackerel": 1, "sage": 1},
        "output": "spiced_mackerel", "quantity": 1,
        "min_tool_level": 70, "tool_xp": 19,
        "desc": "Gotowanie level 70. Makrela + Szałwia. Przywraca do 72 HP i 22 Many.",
    },
    "ocean_steak": {
        "name": "Stek oceaniczny", "stations": ("inn", "fish_market"),
        "ingredients": {"tuna": 1, "mahi_mahi": 1},
        "output": "ocean_steak", "quantity": 1,
        "min_tool_level": 80, "tool_xp": 21,
        "desc": "Gotowanie level 80. Tuńczyk + Mahi-mahi. Przywraca do 75 HP i 25 Many.",
    },
    "salmon_herb_plate": {
        "name": "Łosoś z Ziołami", "stations": ("inn", "fish_market"),
        "ingredients": {"salmon": 1, "lavender": 1},
        "output": "salmon_herb_plate", "quantity": 1,
        "min_tool_level": 90, "tool_xp": 23,
        "desc": "Gotowanie level 90. Łosoś + Lawenda. Przywraca do 88 HP i 30 Many.",
    },
    "master_fisher_feast": {
        "name": "Uczta Mistrza Rybaka", "stations": ("inn", "fish_market"),
        "ingredients": {"salmon": 1, "lake_trout": 1, "turbot": 1, "albacore": 1},
        "output": "master_fisher_feast", "quantity": 1,
        "min_tool_level": 95, "tool_xp": 24,
        "desc": "Gotowanie level 95. Łosoś + Troć jeziorowa + Turbot + Albakora. Przywraca do 100 HP i 40 Many.",
    },
    "moon_eel_broth": {
        "name": "Rosół z Księżycowego Węgorza", "stations": ("inn", "fish_market"),
        "ingredients": {"moon_eel": 1, "moonflower": 1},
        "output": "moon_eel_broth", "quantity": 1,
        "min_tool_level": 99, "tool_xp": 25,
        "desc": "Gotowanie level 99. Księżycowy węgorz + Kwiat księżycowy. Przywraca do 112 HP i 48 Many.",
    },
    "runic_fish_plate": {
        "name": "Runiczny Półmisek Rybny", "stations": ("inn", "fish_market"),
        "ingredients": {"celestial_tuna": 1, "crystal_carp": 1},
        "output": "runic_fish_plate", "quantity": 1,
        "min_tool_level": 100, "tool_xp": 24,
        "desc": "Gotowanie level 100. Przywraca do 120 HP i 40 Many.",
    },
    "dragon_ocean_stew": {
        "name": "Smocza Potrawka Oceaniczna", "stations": ("inn", "fish_market"),
        "ingredients": {"dragon_mahi": 1, "soulfin_trout": 1},
        "output": "dragon_ocean_stew", "quantity": 1,
        "min_tool_level": 120, "tool_xp": 28,
        "desc": "Gotowanie level 120. Przywraca do 135 HP i 55 Many.",
    },
    "abyss_fish_steak": {
        "name": "Stek Rybny Otchłani", "stations": ("inn", "fish_market"),
        "ingredients": {"abyss_tuna": 1, "abyss_halibut": 1},
        "output": "abyss_fish_steak", "quantity": 1,
        "min_tool_level": 140, "tool_xp": 32,
        "desc": "Gotowanie level 140. Przywraca do 155 HP i 75 Many.",
    },
    "storm_marlin_feast": {
        "name": "Uczta Marlina Burzy", "stations": ("inn", "fish_market"),
        "ingredients": {"storm_marlin": 1, "moon_pike": 1},
        "output": "storm_marlin_feast", "quantity": 1,
        "min_tool_level": 160, "tool_xp": 36,
        "desc": "Gotowanie level 160. Przywraca do 180 HP i 95 Many.",
    },
    "leviathan_banquet": {
        "name": "Uczta Lewiatana", "stations": ("inn", "fish_market"),
        "ingredients": {"moon_leviathan": 1, "void_turbot": 1},
        "output": "leviathan_banquet", "quantity": 1,
        "min_tool_level": 180, "tool_xp": 40,
        "desc": "Gotowanie level 180. Przywraca do 210 HP i 120 Many.",
    },
    "eternal_ocean_banquet": {
        "name": "Wieczna Uczta Oceanu", "stations": ("inn", "fish_market"),
        "ingredients": {"eternal_coelacanth": 1, "mirror_leviathan": 1, "crown_monkfish": 1},
        "output": "eternal_ocean_banquet", "quantity": 1,
        "min_tool_level": 200, "tool_xp": 50,
        "desc": "Gotowanie level 200. Przywraca do 260 HP i 160 Many.",
    },
}

# v0.9.12: receptury 220-600. Każdy próg co 20 leveli ma realną
# zawartość dla Gotowania, Alchemii i Kowalstwa/Rzemiosła.
for _level in PROGRESSION_400_LEVELS:
    _suffix = _PROGRESSION_400_NAMES[_level]
    _fish = f"fish_400_ocean_{_level}"
    _herb = f"herb_400_{_level}"
    _ore = f"ore_400_{_level}"
    _ingot = f"ingot_400_{_level}"
    _wood = f"wood_400_{_level}"

    _food_id = f"feast_400_{_level}"
    _catalog_mut.catalog_assign({
        "name": f"Uczta {_suffix}", "type": "consumable", "price": None,
        "heal": 260 + (_level - 200) // 2,
        "mana": 160 + (_level - 200) // 3,
        "desc": f"Gotowanie level {_level}. Potrawa progresji 201-600.",
    }, 'ITEMS', ITEMS, (_food_id,))
    COOK_RECIPES[_food_id] = {
        "name": ITEMS[_food_id]["name"], "stations": ("inn", "fish_market"),
        "ingredients": {_fish: 1, _herb: 1}, "output": _food_id, "quantity": 1,
        "min_tool_level": _level, "min_profession_level": _level,
        "profession_xp": 50 + (_level - 200) // 4,
        "tool_xp": 45 + (_level - 200) // 5,
        "desc": f"Gotowanie level {_level}. Ryba i zioło progresji {_level}.",
    }

    _potion_id = f"elixir_400_{_level}"
    _catalog_mut.catalog_assign({
        "name": f"Eliksir {_suffix}", "type": "consumable", "price": None,
        "heal": 180 + (_level - 200) // 2,
        "mana": 120 + (_level - 200) // 3,
        "soul_xp": 400 + (_level - 200) * 2,
        "desc": f"Alchemia level {_level}. Eliksir progresji 201-600.",
    }, 'ITEMS', ITEMS, (_potion_id,))
    _catalog_mut.catalog_assign({
        "name": ITEMS[_potion_id]["name"], "stations": ("herbalist_hut", "alchemy_lab"),
        "ingredients": {_herb: 2}, "output": _potion_id, "quantity": 1,
        "min_tool_level": _level, "min_profession_level": _level,
        "profession_xp": 52 + (_level - 200) // 4,
        "tool_xp": 46 + (_level - 200) // 5,
        "desc": f"Alchemia level {_level}. Dwa zioła progresji {_level}.",
    }, 'ALCHEMY_RECIPES', ALCHEMY_RECIPES, (_potion_id,))

    _charm_id = f"charm_400_{_level}"
    _catalog_mut.catalog_assign({
        "name": f"Talizman Rzemieślnika {_suffix}", "type": "armor", "slot": "charm",
        "defense": 12 + (_level - 200) // 40, "price": None,
        "rarity": "crafted", "rarity_name": "Rzemieślniczy",
        "affix": "willpower", "affix_amount": 5 + (_level - 200) // 50,
        "desc": f"Kowalstwo level {_level}. Talizman progresji 201-600.",
    }, 'ITEMS', ITEMS, (_charm_id,))
    _catalog_mut.catalog_assign({
        "name": ITEMS[_charm_id]["name"], "stations": ("forge",),
        "ingredients": {_ingot: 2, _wood: 2}, "output": _charm_id, "quantity": 1,
        "min_tool_level": _level, "min_profession_level": _level,
        "profession_xp": 58 + (_level - 200) // 4,
        "tool_xp": 50 + (_level - 200) // 5,
        "category": "smithing",
        "desc": f"Kowalstwo level {_level}. Sztabki i drewno progresji {_level}.",
    }, 'CRAFT_RECIPES', CRAFT_RECIPES, (_charm_id,))
