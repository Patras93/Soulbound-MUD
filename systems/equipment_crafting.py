from core.legacy_function_binding_v410 import bind_legacy_function_v410 as _sb410_bind

import systems.v410_equipment_shops as _sb410_mod_v410_equipment_shops
import systems.v410_craft_recipes as _sb410_mod_v410_craft_recipes
import systems.v410_gem_registration as _sb410_mod_v410_gem_registration

from data import catalog_mutations as _catalog_mut

# v0.44.0: explicit dependencies; no compatibility-global injection.
from core.profession_drop_rates_v1149 import mined_gem_quality_chances_v1149, mining_geode_chances_v1149
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
    class_equipment_shop_price_v11314,
    equipment_defense_step_v1138,
    equipment_progression_budget_v1138,
)



def class_equipment_base_stat_triplet(class_name):
    """Trzy obowiązkowe statystyki bazowe każdego klasowego elementu EQ."""
    if class_type_for_name(class_name) == "magic":
        # Każda klasa magiczna dostaje pełne INT + WILL + CON.
        return "intelligence", "willpower", "constitution"
    # Każda klasa fizyczna dostaje pełne STR + DEX + CON. Kolejność dwóch
    # ofensywnych statów zachowuje profil archetypu i steruje proporcjami.
    if class_name in {"Łotrzyk", "Łowca", "Mnich", "Mec", "Inżynier"}:
        return "dexterity", "strength", "constitution"
    return "strength", "dexterity", "constitution"


def class_equipment_base_stat_pair(class_name):
    """Legacy helper: zachowuje pierwsze dwie osie dla starszych wywołań."""
    first, second, _third = class_equipment_base_stat_triplet(class_name)
    return first, second


def class_equipment_profile(class_name):
    return CLASS_EQUIPMENT_CLASS_PROFILES.get(
        class_name,
        {"primary_ratio": 0.50, "identity": "równowaga", "properties": {}},
    )


# v1.13.8: trzy linie w sklepie nie są już kosmetycznymi kopiami.
# Każdy element można mieszać z innymi stylami tej samej klasy; progi 2/4/6/8
# liczą klasę i logiczny slot, nie nazwę linii.
CLASS_EQUIPMENT_STYLE_PROFILES = {
    "zbalansowany": {
        "role": "zbalansowany",
        "defense_multiplier": 1.00,
        "power_multiplier": 0.85,
        "stat_shift": 0.00,
    },
    "ofensywny": {
        "role": "ofensywny",
        "defense_multiplier": 0.88,
        "power_multiplier": 1.25,
        "stat_shift": 0.10,
    },
    "pancerny": {
        "role": "pancerny",
        "defense_multiplier": 1.18,
        "power_multiplier": 0.45,
        "stat_shift": -0.10,
    },
}

# Nazwy istniejących linii sugerują różny charakter zależnie od klasy.
# Pierwsza linia pozostaje zbalansowana dla zgodności; 2/3 są przypisane tak,
# aby np. Tytanowa Rama była pancerna, a Reaktor Bojowy ofensywny.
CLASS_EQUIPMENT_STYLE_ROLES_BY_CLASS = {
    "Wojownik": ("zbalansowany", "pancerny", "ofensywny"),
    "Berserker": ("zbalansowany", "pancerny", "ofensywny"),
    "Łotrzyk": ("zbalansowany", "ofensywny", "pancerny"),
    "Łowca": ("zbalansowany", "pancerny", "ofensywny"),
    "Mnich": ("zbalansowany", "ofensywny", "pancerny"),
    "Strażnik": ("zbalansowany", "pancerny", "ofensywny"),
    "Mag": ("zbalansowany", "ofensywny", "pancerny"),
    "Nekromanta": ("zbalansowany", "pancerny", "ofensywny"),
    "Kapłan": ("zbalansowany", "ofensywny", "pancerny"),
    "Czarownik": ("zbalansowany", "ofensywny", "pancerny"),
    "Druid": ("zbalansowany", "ofensywny", "pancerny"),
    "Psionik": ("zbalansowany", "pancerny", "ofensywny"),
    "Mec": ("zbalansowany", "pancerny", "ofensywny"),
    "Inżynier": ("zbalansowany", "pancerny", "ofensywny"),
}

# Attack/Magic Attack siedzi przede wszystkim na slotach ofensywnych.
# Ciężki pancerz dalej ma sens, ale nie konkuruje z rękawicami/relictem
# jako najlepsze źródło mocy ataku.
CLASS_EQUIPMENT_SLOT_POWER_SCALE = {
    "head": 0.55,
    "body": 0.25,
    "shield": 0.15,
    "hands": 0.95,
    "legs": 0.25,
    "feet": 0.45,
    "charm": 0.70,
    "ring": 0.90,
    "necklace": 0.75,
    "earring": 0.85,
    "shoulders": 0.35,
    "belt": 0.30,
    "cloak": 0.50,
    "bracers": 0.80,
    "bracelet": 0.75,
    "accessory": 0.95,
    "relic": 1.10,
}


def class_equipment_style_role(class_name, style_index):
    roles = CLASS_EQUIPMENT_STYLE_ROLES_BY_CLASS.get(
        class_name,
        ("zbalansowany", "ofensywny", "pancerny"),
    )
    index = max(1, min(3, int(style_index or 1))) - 1
    return roles[index]


def class_equipment_style_profile(class_name, style_index):
    role = class_equipment_style_role(class_name, style_index)
    return CLASS_EQUIPMENT_STYLE_PROFILES[role]


def _merge_equipment_properties_v11326(*property_sets):
    merged = {}
    for property_set in property_sets:
        for key, value in (property_set or {}).items():
            merged[key] = round(
                float(merged.get(key, 0.0)) + float(value or 0.0), 2
            )
    return {key: value for key, value in merged.items() if abs(value) > 1e-9}


def class_equipment_style_properties_v11326(
    class_name, mastery, slot=None, style_index=1
):
    """A real combat identity for the three shop styles.

    The budget is deliberately smaller than class profile properties: style is
    a choice, not a second full item budget.
    """
    mastery = max(1, min(CLASS_MASTERY_MAX_LEVEL, int(mastery or 1)))
    progress = (mastery - 1) / float(max(1, CLASS_MASTERY_MAX_LEVEL - 1))
    amount = 0.15 + 0.85 * (progress ** 0.85)
    amount *= float(CLASS_EQUIPMENT_SLOT_PROPERTY_SCALE.get(str(slot or ""), 1.0))
    role = class_equipment_style_role(class_name, style_index)

    if role == "ofensywny":
        key = (
            "magic_damage_pct"
            if class_type_for_name(class_name) == "magic"
            else "physical_damage_pct"
        )
        return {key: round(amount, 2)}
    if role == "pancerny":
        return {
            "physical_defense_pct": round(amount * 0.55, 2),
            "magic_defense_pct": round(amount * 0.45, 2),
        }

    # Balanced trades peak damage/mitigation for resource stability.
    key = (
        "max_mana_pct"
        if class_type_for_name(class_name) == "magic"
        else "max_hp_pct"
    )
    return {key: round(amount, 2)}


def legendary_class_set_properties_v11326(class_name, mastery, slot=None):
    """Boss-set pieces are a meaningful upgrade, not recolored shop gear."""
    mastery = max(1, min(CLASS_MASTERY_MAX_LEVEL, int(mastery or 1)))
    progress = mastery / float(max(1, CLASS_MASTERY_MAX_LEVEL))
    source_bonus = (0.20 + 0.55 * (progress ** 0.80))
    source_bonus *= float(
        CLASS_EQUIPMENT_SLOT_PROPERTY_SCALE.get(str(slot or ""), 1.0)
    )
    typed_damage = (
        "magic_damage_pct"
        if class_type_for_name(class_name) == "magic"
        else "physical_damage_pct"
    )
    return _merge_equipment_properties_v11326(
        class_equipment_profile_properties(class_name, mastery, slot),
        {
            typed_damage: round(source_bonus, 2),
            "physical_defense_pct": round(source_bonus * 0.35, 2),
            "magic_defense_pct": round(source_bonus * 0.35, 2),
        },
    )


def class_equipment_split_stat_budget(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: class_equipment_split_stat_budget")
class_equipment_split_stat_budget = _sb410_bind(_sb410_mod_v410_equipment_shops.class_equipment_split_stat_budget, globals())


def class_equipment_flat_power_channels(class_name, mastery, slot=None, style_index=1):
    """Attack/Magic Attack z klasowego EQ bez zamiany każdego slotu w broń.

    Czyste klasy dostają jeden kanał. Mec jest hybrydą i dostaje oba, ale każdy
    z nich jest słabszy niż pojedynczy kanał wyspecjalizowanej klasy.
    """
    budget = class_equipment_stat_budget(mastery, slot)
    slot_scale = float(CLASS_EQUIPMENT_SLOT_POWER_SCALE.get(str(slot or ""), 0.50))
    style = class_equipment_style_profile(class_name, style_index)
    style_mult = float(style.get("power_multiplier", 1.0) or 1.0)
    # v1.13.38: każdy klasowy element ma realny kanał ofensywny także na
    # najniższym Tierze. Nie ma już części z poprawnymi statami, ale 0 Attack/
    # Magic Attack wyłącznie przez zaokrąglenie małego budżetu.
    # v1.13.38: kalibracja do UOSS Quartz Charm (+60 Attack/+60 Magic Attack
    # przy wymaganiu 110). Ofensywny klasowy accessory na progu 110 ma być co
    # najmniej równie mocny w swoim właściwym kanale, a późniejsze Tiery mają
    # już wyraźnie go przebijać.
    power = max(1, int(round(budget * 0.45 * slot_scale * style_mult)))
    if class_name == "Mec":
        # Mec jest pełnoprawną hybrydą. Quartz Charm już daje oba kanały po 60,
        # więc własne klasowe EQ nie może być gorsze tylko za sam fakt hybrydy.
        return {"attack": power, "magic_attack": power}
    if class_type_for_name(class_name) == "magic":
        return {"attack": 0, "magic_attack": power}
    return {"attack": power, "magic_attack": 0}


def legendary_class_equipment_flat_power_channels_v11338(
    class_name, mastery, slot=None, *, relic=False
):
    """Bossowe klasowe EQ zawsze przewyższa sklepowy kanał płaskiej mocy.

    Set bierze najlepszy Attack/Magic Attack spośród trzech sklepowych stylów
    tego samego progu i slotu, a następnie dostaje +20%. Relikt używa własnej
    ofensywnej skali slotu relic i +35%, bo nie daje części do progu setowego.
    """
    source_slot = "relic" if relic else slot
    candidates = [
        class_equipment_flat_power_channels(
            class_name, mastery, source_slot, style_index
        )
        for style_index in (1, 2, 3)
    ]
    attack = max(int(row.get("attack", 0) or 0) for row in candidates)
    magic_attack = max(
        int(row.get("magic_attack", 0) or 0) for row in candidates
    )
    multiplier = 1.35 if relic else 1.20
    if attack > 0:
        attack = max(1, int(round(attack * multiplier)))
    if magic_attack > 0:
        magic_attack = max(1, int(round(magic_attack * multiplier)))
    return {"attack": attack, "magic_attack": magic_attack}


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

def mec_hybrid_extra_stats(legacy_amount):
    """Mec is a true five-stat hybrid: STR/DEX/CON plus INT/WILL on every class EQ piece."""
    budget = max(3, int(legacy_amount or 0))
    # Extra hybrid channels are meaningful from tier 1 and grow with the same
    # authored item budget without stealing points from physical identity.
    extra = max(1, int(round(budget * 0.30)))
    return {"intelligence": extra, "willpower": extra}


def class_equipment_base_stats_text(class_name, legacy_amount, slot=None, style_index=1):
    pstat, pamount, sstat, samount, tstat, tamount = class_equipment_split_stat_budget(
        class_name, legacy_amount, slot, style_index
    )
    labels = {
        "strength": "Siła",
        "dexterity": "Zręczność",
        "constitution": "Kondycja",
        "intelligence": "Inteligencja",
        "willpower": "Siła Woli",
    }
    parts = [
        f"{labels.get(pstat, pstat)} +{pamount}",
        f"{labels.get(sstat, sstat)} +{samount}",
        f"{labels.get(tstat, tstat)} +{tamount}",
    ]
    if class_name == "Mec":
        extras = mec_hybrid_extra_stats(legacy_amount)
        parts.extend([
            f"Inteligencja +{extras['intelligence']}",
            f"Siła Woli +{extras['willpower']}",
        ])
    return ", ".join(parts)


# Trwałe, fabularne nazwy 80 rang EQ. Numery istnieją wyłącznie
# w ID i wymaganiu biegłości; tekst przedmiotu jest nazwą własną.
_CLASS_EQUIPMENT_EPITHETS = (
    "Żelaznego Świtu", "Srebrnego Zmierzchu", "Złotej Gwiazdy", "Ognistego Serca",
    "Północnego Wiatru", "Kamiennej Straży", "Księżycowego Blasku", "Lodowego Płomienia",
    "Szmaragdowej Bramy", "Rubinowego Tronu", "Cichej Burzy", "Szeptu Otchłani",
    "Zorzy Bohaterów", "Wiecznej Warty", "Smoczej Korony", "Krwawego Księżyca",
    "Sądu Przodków", "Straży Horyzontu", "Gwiazd Niebios", "Przysięgi Feniksa",
    "Duchowego Ostrza", "Korony Morza", "Żaru Odkupienia", "Kręgu Run",
    "Nieskończonych Ścieżek", "Lustrzanego Nieba", "Zaginionej Kuźni", "Nocnej Straży",
    "Wielkiego Przebudzenia", "Bursztynowej Pieczęci", "Słonecznego Bastionu", "Czarnych Skrzydeł",
    "Świetlistego Przypływu", "Władcy Gromów", "Wiecznego Rezonansu", "Ognistej Przystani",
    "Błękitnego Sztandaru", "Kryształowego Serca", "Ostatniego Świtu", "Pieczęci Kosmosu",
    "Pradawnej Nawałnicy", "Tronu Cieni", "Miedzianej Komety", "Milczącego Słońca",
    "Pierwszej Gwiazdy", "Płonącego Echa", "Miecza Wędrowca", "Serca Galaktyki",
    "Szafirowego Dominium", "Białego Pioruna", "Stalowej Furii", "Harmonii Dusz",
    "Tajemnicy Głębin", "Oka Wszechświata", "Płomienia Nieśmiertelnych", "Łez Tytanów",
    "Wschodzącego Feniksa", "Niebiańskiej Pieśni", "Niezłomnej Pieczęci", "Absolutu Duszy",
    "Wiatru Przeznaczenia", "Runicznej Nocy", "Wielkiej Konstelacji", "Jutra Bogów",
    "Królewskiego Przesilenia", "Serca Otchłani", "Niebieskiej Komety", "Dziedzictwa Gwiazd",
    "Pamięci Starożytnych", "Sądu Galaktyk", "Wieczystej Zorzy", "Władzy Nad Czasem",
    "Przekroczonej Granicy", "Ciszy Przed Burzą", "Bramy Wieczności", "Gwiezdnego Dziedzictwa",
    "Ostatniej Przysięgi", "Woli Wszechświata", "Potęgi Nieskończoności", "Tronu Przyszłości",
)

def _class_equipment_tier_label(required_mastery):
    level = max(1, int(required_mastery))
    if level <= 1:
        return "Początku Drogi"
    return _CLASS_EQUIPMENT_EPITHETS[min(79, level // 10 - 1)]


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
    """Łączny budżet trzech bazowych statów klasowego EQ."""
    mastery = class_equipment_unlocked_tier(required_mastery)
    return equipment_progression_budget_v1138(mastery)


def class_equipment_unlocked_tier(mastery_level):
    mastery_level = max(1, min(CLASS_MASTERY_MAX_LEVEL, int(mastery_level)))
    unlocked = 1
    for threshold in CLASS_EQUIPMENT_MASTERY_LEVELS:
        if threshold <= mastery_level:
            unlocked = threshold
        else:
            break
    return unlocked


def _register_class_equipment_shops(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: _register_class_equipment_shops")
_register_class_equipment_shops = _sb410_bind(_sb410_mod_v410_equipment_shops._register_class_equipment_shops, globals())


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

# v1.12.0: każda z 14 klas ma pięć różnych zadań godzinnych.
# Format pojedynczego zadania pozostaje zgodny ze starszym runtime:
# nazwa, opis, reputacja, srebro, wymagany postęp, rodzaj aktywności.
#
# Pierwsze zadanie każdej klasy zachowuje dawny kontrakt v1.11.32, aby
# nie zerwać kompatybilności ze starszymi save'ami i audytami.
_GUILD_CLASS_QUEST_LEGACY_V11132 = {
    "Wojownik": ("Próba Ostrza", "Pokonaj 3 bossów lub silnych przywódców.", 35, 700, 3, "boss"),
    "Berserker": ("Próba Furii", "Pokonaj 12 przeciwników w walce.", 30, 700, 12, "kill"),
    "Łotrzyk": ("Próba Cienia", "Odkryj 12 nowych lokacji, poruszając się poza utartymi szlakami.", 30, 650, 12, "explore"),
    "Łowca": ("Próba Tropiciela", "Odkryj 18 nowych lokacji i poznaj teren.", 30, 650, 18, "explore"),
    "Mnich": ("Próba Dyscypliny", "Odkryj 10 nowych lokacji podczas wędrówki.", 30, 700, 10, "explore"),
    "Strażnik": ("Próba Bastionu", "Pokonaj 2 bossów, chroniąc szlaki świata.", 35, 800, 2, "boss"),
    "Mag": ("Próba Arkanów", "Odkryj 14 nowych lokacji i zbadaj źródła mocy świata.", 30, 700, 14, "explore"),
    "Nekromanta": ("Próba Dusz", "Pokonaj 10 przeciwników i zbierz doświadczenie bojowe.", 30, 700, 10, "kill"),
    "Kapłan": ("Próba Pielgrzyma", "Odwiedź 12 nowych lokacji świata.", 35, 800, 12, "explore"),
    "Czarownik": ("Próba Otchłani", "Pokonaj 8 przeciwników w walce.", 30, 750, 8, "kill"),
    "Druid": ("Próba Natury", "Zbierz 12 zasobów podczas profesyjnych wypraw.", 30, 700, 12, "gather"),
    "Psionik": ("Próba Umysłu", "Odkryj 15 nowych lokacji i poszerz wiedzę o świecie.", 30, 750, 15, "explore"),
    "Mec": ("Próba Rdzenia", "Pokonaj 3 bossów i przetestuj systemy bojowe.", 35, 800, 3, "boss"),
    "Inżynier": ("Próba Konstruktora", "Zbierz 15 zasobów potrzebnych do dalszych konstrukcji.", 30, 700, 15, "gather"),
}

_GUILD_CLASS_QUEST_IDENTITIES_V1120 = {
    "Wojownik": "Kodeks Ostrza",
    "Berserker": "Szlak Furii",
    "Łotrzyk": "Kodeks Cienia",
    "Łowca": "Szlak Tropiciela",
    "Mnich": "Droga Dyscypliny",
    "Strażnik": "Przysięga Bastionu",
    "Mag": "Krąg Arkanów",
    "Nekromanta": "Kronika Dusz",
    "Kapłan": "Droga Światła",
    "Czarownik": "Pakt Otchłani",
    "Druid": "Krąg Natury",
    "Psionik": "Ścieżka Umysłu",
    "Mec": "Protokół Rdzenia",
    "Inżynier": "Projekt Konstruktora",
}

_GUILD_CLASS_ACTIVITY_V1120 = {
    "kill": ("Próba Starcia", "Pokonaj {needed} przeciwników podczas zwykłej walki."),
    "boss": ("Próba Mistrza", "Pokonaj {needed} bossów lub silnych przywódców."),
    "explore": ("Próba Szlaku", "Odkryj {needed} nowych lokacji świata."),
    "gather": ("Próba Zaopatrzenia", "Zbierz {needed} zasobów podczas profesyjnych wypraw."),
    "craft": ("Próba Warsztatu", "Wykonaj {needed} udanych craftów z dowolnej profesji rzemieślniczej."),
}

_GUILD_CLASS_ACTIVITY_BASE_V1120 = {
    "kill": (10, 28, 700),
    "boss": (2, 35, 850),
    "explore": (12, 30, 700),
    "gather": (14, 30, 700),
    "craft": (4, 32, 800),
}


def _guild_class_quest_pool_v1120(class_name, class_index):
    legacy = _GUILD_CLASS_QUEST_LEGACY_V11132[class_name]
    identity = _GUILD_CLASS_QUEST_IDENTITIES_V1120[class_name]
    rows = [legacy]
    legacy_activity = str(legacy[5])
    for activity in ("kill", "boss", "explore", "gather", "craft"):
        if activity == legacy_activity:
            continue
        base_needed, base_rep, base_silver = _GUILD_CLASS_ACTIVITY_BASE_V1120[activity]
        # Lekka różnica liczb między klasami zapobiega 14 identycznym kopiom.
        if activity == "boss":
            needed = base_needed + (class_index % 2)
        elif activity == "craft":
            needed = base_needed + (class_index % 2)
        else:
            needed = base_needed + (class_index % 4)
        rep = base_rep + (class_index % 3) * 2
        silver = base_silver + (class_index % 4) * 50
        suffix, description = _GUILD_CLASS_ACTIVITY_V1120[activity]
        rows.append((
            f"{identity}: {suffix}",
            description.format(needed=needed),
            rep,
            silver,
            needed,
            activity,
        ))
    return tuple(rows)


GUILD_CLASS_QUEST_POOLS = {
    class_name: _guild_class_quest_pool_v1120(class_name, class_index)
    for class_index, class_name in enumerate(_GUILD_CLASS_QUEST_LEGACY_V11132)
}

# Kompatybilność: starsze audyty/importy oczekują jednego 6-polowego wpisu
# pod GUILD_CLASS_QUESTS. Pierwsza pozycja to dawny kontrakt każdej klasy.
GUILD_CLASS_QUESTS = {
    class_name: quests[0]
    for class_name, quests in GUILD_CLASS_QUEST_POOLS.items()
}

_GUILD_CLASS_REQUIRED_ACTIVITIES_V1120 = {"kill", "boss", "explore", "gather", "craft"}
_GUILD_CLASS_QUEST_AUDIT_ERRORS_V1120 = []
for _class_name, _quests in GUILD_CLASS_QUEST_POOLS.items():
    if len(_quests) != 5:
        _GUILD_CLASS_QUEST_AUDIT_ERRORS_V1120.append(
            f"{_class_name}: expected 5 quests, got {len(_quests)}"
        )
    _activities = {str(_row[5]) for _row in _quests if len(_row) >= 6}
    if _activities != _GUILD_CLASS_REQUIRED_ACTIVITIES_V1120:
        _GUILD_CLASS_QUEST_AUDIT_ERRORS_V1120.append(
            f"{_class_name}: activities {sorted(_activities)}"
        )
    if len({str(_row[0]) for _row in _quests}) != len(_quests):
        _GUILD_CLASS_QUEST_AUDIT_ERRORS_V1120.append(
            f"{_class_name}: duplicate quest names"
        )
if len(GUILD_CLASS_QUEST_POOLS) != 14:
    _GUILD_CLASS_QUEST_AUDIT_ERRORS_V1120.append(
        f"class count: expected 14, got {len(GUILD_CLASS_QUEST_POOLS)}"
    )
GUILD_CLASS_QUEST_AUDIT_V1120 = {
    "version": "1.12.0",
    "class_count": len(GUILD_CLASS_QUEST_POOLS),
    "error_count": len(_GUILD_CLASS_QUEST_AUDIT_ERRORS_V1120),
    "errors": tuple(_GUILD_CLASS_QUEST_AUDIT_ERRORS_V1120),
}


# v1.13.42: godzinne zadania klasowe rosną razem z realną Biegłością klasy.
# Typy aktywności pozostają zgodne ze starym runtime, ale wymagania, nazwy
# i nagrody mają siedem wyraźnych etapów. Bieżący etap jest zamrażany na
# godzinę przez SessionClassGuildProgressMixin, więc level-up w połowie zadania
# nigdy nie podnosi celu pod nogami gracza.
GUILD_CLASS_QUEST_STAGES_V11342 = (
    (1, "Początek", 1.00, 1.00),
    (100, "Adept", 1.25, 1.40),
    (200, "Mistrz", 1.55, 1.90),
    (300, "Legenda", 1.90, 2.60),
    (400, "Transcendencja", 2.25, 3.50),
    (500, "Apogeum", 2.60, 4.60),
    (600, "Absolut", 2.90, 6.00),
)

GUILD_CLASS_QUEST_FOCUS_V11342 = {
    "Wojownik": {"kill", "boss"},
    "Berserker": {"kill", "boss"},
    "Łotrzyk": {"kill", "explore"},
    "Łowca": {"explore", "gather"},
    "Mnich": {"explore", "boss"},
    "Strażnik": {"boss", "craft"},
    "Mag": {"explore", "craft"},
    "Nekromanta": {"kill", "boss"},
    "Kapłan": {"explore", "gather"},
    "Czarownik": {"kill", "craft"},
    "Druid": {"gather", "explore"},
    "Psionik": {"explore", "boss"},
    "Mec": {"boss", "craft"},
    "Inżynier": {"craft", "gather"},
}

GUILD_CLASS_QUEST_FLAVOUR_V11342 = {
    "Wojownik": "walcz jak czempion pierwszej linii",
    "Berserker": "podtrzymuj napór i kontrolowaną furię",
    "Łotrzyk": "działaj szybko, cicho i poza utartym szlakiem",
    "Łowca": "trop cele i poznawaj teren",
    "Mnich": "łącz dyscyplinę walki z drogą mistrza",
    "Strażnik": "utrzymuj linię obrony i wzmacniaj zaplecze",
    "Mag": "badaj świat i przygotowuj zaplecze arkanów",
    "Nekromanta": "zbieraj doświadczenie z najgroźniejszych starć",
    "Kapłan": "poznawaj świat i wspieraj zaplecze wypraw",
    "Czarownik": "łącz walkę z przygotowaniem rytuałów",
    "Druid": "pracuj z naturą i badaj dzikie obszary",
    "Psionik": "poszerzaj wiedzę i podejmuj próby umysłu",
    "Mec": "testuj systemy na bossach i w warsztacie",
    "Inżynier": "buduj, zbieraj i rozwijaj zaplecze konstrukcyjne",
}


def guild_class_quest_stage_v11342(mastery):
    mastery = max(1, min(CLASS_MASTERY_MAX_LEVEL, int(mastery or 1)))
    selected = GUILD_CLASS_QUEST_STAGES_V11342[0]
    for row in GUILD_CLASS_QUEST_STAGES_V11342:
        if mastery >= int(row[0]):
            selected = row
        else:
            break
    return selected


def guild_class_quest_pool_for_mastery_v11342(class_name, mastery):
    base_pool = tuple(GUILD_CLASS_QUEST_POOLS.get(class_name, ()))
    if not base_pool:
        return ()
    threshold, stage_label, effort_mult, reward_mult = guild_class_quest_stage_v11342(
        mastery
    )
    identity = _GUILD_CLASS_QUEST_IDENTITIES_V1120.get(class_name, class_name)
    focus = set(GUILD_CLASS_QUEST_FOCUS_V11342.get(class_name, ()))
    flavour = GUILD_CLASS_QUEST_FLAVOUR_V11342.get(class_name, "")
    rows = []
    for name, _description, rep, silver, needed, activity in base_pool:
        focus_mult = 1.12 if activity in focus and int(threshold) >= 100 else 1.0
        scaled_needed = max(1, int(round(int(needed) * float(effort_mult) * focus_mult)))
        scaled_rep = max(1, int(round(int(rep) * float(reward_mult) * focus_mult)))
        scaled_silver = max(1, int(round(int(silver) * float(reward_mult) * focus_mult)))
        suffix, description_template = _GUILD_CLASS_ACTIVITY_V1120[str(activity)]
        description = description_template.format(needed=scaled_needed)
        if flavour:
            description += " Kierunek klasy: " + flavour + "."
        if int(threshold) <= 1:
            scaled_name = str(name)
        else:
            scaled_name = f"{identity}: {stage_label} — {suffix}"
        rows.append((
            scaled_name,
            description,
            scaled_rep,
            scaled_silver,
            scaled_needed,
            str(activity),
        ))
    return tuple(rows)


_GUILD_CLASS_PROGRESS_AUDIT_ERRORS_V11342 = []
for _class_name in GUILD_CLASS_QUEST_POOLS:
    _previous_effort = 0
    _previous_reward = 0
    for _mastery in (1, 100, 200, 300, 400, 500, 600):
        _pool = guild_class_quest_pool_for_mastery_v11342(_class_name, _mastery)
        if len(_pool) != 5:
            _GUILD_CLASS_PROGRESS_AUDIT_ERRORS_V11342.append(
                f"{_class_name} mastery {_mastery}: expected 5 quests"
            )
            continue
        _effort = sum(int(row[4]) for row in _pool)
        _reward = sum(int(row[2]) + int(row[3]) for row in _pool)
        if _effort < _previous_effort:
            _GUILD_CLASS_PROGRESS_AUDIT_ERRORS_V11342.append(
                f"{_class_name} mastery {_mastery}: effort regressed"
            )
        if _reward < _previous_reward:
            _GUILD_CLASS_PROGRESS_AUDIT_ERRORS_V11342.append(
                f"{_class_name} mastery {_mastery}: reward regressed"
            )
        _previous_effort = _effort
        _previous_reward = _reward

GUILD_CLASS_QUEST_PROGRESS_AUDIT_V11342 = {
    "version": "1.13.42",
    "classes": len(GUILD_CLASS_QUEST_POOLS),
    "stages": len(GUILD_CLASS_QUEST_STAGES_V11342),
    "error_count": len(_GUILD_CLASS_PROGRESS_AUDIT_ERRORS_V11342),
    "errors": tuple(_GUILD_CLASS_PROGRESS_AUDIT_ERRORS_V11342),
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
        # Kapłan leczy z INT + WILL, a ofensywne skille używają INT.
        # Set wspiera oba osie zamiast pompować wyłącznie WILL.
        "stats": {"intelligence": 3, "willpower": 2},
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
    return class_equipment_base_stat_triplet(class_name)[0], int(definition["base_defense"])


def _register_legendary_class_loot(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: _register_legendary_class_loot")
_register_legendary_class_loot = _sb410_bind(_sb410_mod_v410_equipment_shops._register_legendary_class_loot, globals())


_register_legendary_class_loot()


def equipment_identity_audit_v11326(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: equipment_identity_audit_v11326")
equipment_identity_audit_v11326 = _sb410_bind(_sb410_mod_v410_equipment_shops.equipment_identity_audit_v11326, globals())


EQUIPMENT_IDENTITY_AUDIT_V11326 = equipment_identity_audit_v11326()


_catalog_mut.catalog_assign({
    "name": "Szczypce Jubilerskie",
    "type": "tool",
    "tool_type": "jewelcrafting",
    "price": 1200,
    "currency": "silver",
    "desc": (
        "Podstawowe narzędzie Jubilerstwa. "
        "Ma własny level 1-800, XP i 80 Tierów. "
        "Nie ma trwałości i nie zużywa się."
    ),
}, 'ITEMS', ITEMS, ("jeweler_pliers",))

from data.shops import SHOPS
for _room_id, _items in CLASS_SHOP_ITEMS_BY_ROOM.items():
    _catalog_mut.catalog_assign(list(_items), 'SHOPS', SHOPS, (_room_id,))

# v1.13.46: guild_arcane_chamber is both a class-equipment shop and the
# Zaklinanie tool vendor. The class-shop rebuild above must not remove the
# Runic Focus added by systems.professions.
_catalog_mut.catalog_setdefault_path('SHOPS', SHOPS, (), 'guild_arcane_chamber', [])
if 'runic_focus' not in SHOPS['guild_arcane_chamber']:
    SHOPS['guild_arcane_chamber'].append('runic_focus')



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

def _register_blacksmith_recipes(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: _register_blacksmith_recipes")
_register_blacksmith_recipes = _sb410_bind(_sb410_mod_v410_craft_recipes._register_blacksmith_recipes, globals())

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

def _register_jewelcrafting_recipes(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: _register_jewelcrafting_recipes")
_register_jewelcrafting_recipes = _sb410_bind(_sb410_mod_v410_craft_recipes._register_jewelcrafting_recipes, globals())


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

def _register_gem_system(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: _register_gem_system")
_register_gem_system = _sb410_bind(_sb410_mod_v410_gem_registration._register_gem_system, globals())

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
    chances = mined_gem_quality_chances_v1149(tool_level, profession_level)
    roll = random.random()
    for key in ("perfect", "excellent", "pure"):
        if roll < chances[key]:
            return key
        roll -= chances[key]
    return "raw"

def _register_gem_quality_variants(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: _register_gem_quality_variants")
_register_gem_quality_variants = _sb410_bind(_sb410_mod_v410_gem_registration._register_gem_quality_variants, globals())

_register_gem_quality_variants()

GEODE_DEFINITIONS = {
    "stone_geode": {
        "name": "Geoda Kamienna", "min_tool": 20, "min_floor": 10, "max_gem_level": 60,
        "sell_gold": 20, "quality_weights": (85, 15, 0, 0), "gold": (10, 30), "gem_qty": (1, 1),
    },
    "crystal_geode": {
        "name": "Geoda Kryształowa", "min_tool": 80, "min_floor": 60, "max_gem_level": 140,
        "sell_gold": 180, "quality_weights": (65, 28, 7, 0), "gold": (80, 250), "gem_qty": (1, 2),
    },
    "astral_geode": {
        "name": "Geoda Astralna", "min_tool": 160, "min_floor": 150, "max_gem_level": 200,
        "sell_gold": 900, "quality_weights": (45, 35, 17, 3), "gold": (400, 1_500), "gem_qty": (1, 3),
    },
}
GEODE_IDS = set(GEODE_DEFINITIONS)
for _geode_id, _geode in GEODE_DEFINITIONS.items():
    _catalog_mut.catalog_assign({
        "name": _geode["name"], "type": "geode", "price": None,
        "sell_gold": _geode["sell_gold"], "mining_bag_resource": True,
        "min_tool_level": _geode["min_tool"],
        "desc": (
            f"Rzadkie znalezisko Górnictwa. Kilof {_geode['min_tool']}+, "
            f"głębokość {_geode['min_floor']}+. Możesz sprzedać Dagnie albo otworzyć: "
            "open geode / otwórz geodę."
        ),
    }, 'ITEMS', ITEMS, (_geode_id,))

def roll_mining_geode(tool_level, profession_level, floor):
    rates = mining_geode_chances_v1149(tool_level, profession_level, floor)
    roll = random.random()
    for key, rate in rates.items():
        if roll < rate:
            return key
        roll -= rate
    return None

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

# v1.15.0: legendarne receptury i działające, unikalne efekty sprzętu.
from systems.legendary_reborn import register_legendary_content_v1150
register_legendary_content_v1150(CRAFT_RECIPES, JEWELCRAFT_RECIPES)
