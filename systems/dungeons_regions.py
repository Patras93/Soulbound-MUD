from core.legacy_function_binding_v410 import bind_legacy_function_v410 as _sb410_bind

import systems.v410_dungeon_loot as _sb410_mod_v410_dungeon_loot
import systems.v410_dungeon_builders as _sb410_mod_v410_dungeon_builders
import systems.v410_dungeon_regions as _sb410_mod_v410_dungeon_regions

from data import catalog_mutations as _catalog_mut

# v0.44.0: explicit dependencies; no compatibility-global injection.
import random
import re
from core.bootstrap_economy_professions import GLOBAL_MOB_HP_MULTIPLIER
from core.classes_skills import HERB_ATLAS_ROOM_MIN_LEVELS, ROOMS
from core.mines_threat import ITEMS
from core.progression_600 import PROFESSION_MAX_LEVEL
from core.progression_resources import (
    FISHING_ROOMS,
    HERBALISM_ROOMS,
    MARINE_FISHING_ROOMS,
    MEADOW_HERBALISM_ROOMS,
    OCEAN_FISHING_ROOMS,
    SEA_FISHING_ROOMS,
    WOODCUTTING_ROOMS,
)
from systems.content_registry import CRYPT_BOSS_FLOORS, CRYPT_MAX_FLOOR, INFINITE_CRYPT_STEP_RATE, MOB_SPAWNS, MOB_TEMPLATES, NPCS, QUESTS
from systems.dungeon_names import dungeon_mob_display_name_v11336
from systems.items_resources import (
    CLASS_EQUIPMENT_SLOT_DEFS,
    MATERIAL_SLOT_POWER_SCALE,
    equipment_defense_step_v1138,
    equipment_progression_budget_v1138,
)


def crypt_depth_step(floor):
    return max(0, int(floor) // 10)

def crypt_depth_multiplier(floor):
    # Wyraźny, ale łagodny próg co 10 pięter. Wzrost liniowy zapobiega
    # eksplozji liczb przy bardzo głębokich piętrach.
    return 1.0 + INFINITE_CRYPT_STEP_RATE * crypt_depth_step(floor)

def is_crypt_boss_floor(floor):
    try:
        floor = int(floor)
    except (TypeError, ValueError):
        return False
    return floor >= 10 and floor % 10 == 0

def is_mythic_crypt_boss_floor(floor):
    return is_crypt_boss_floor(floor)

CRYPT_BOSS_NAMES = {
    10: "Kościany Egzekutor", 20: "Krwawy Kurator",
    30: "Rycerz Grobowca", 40: "Wiedźma Popiołu",
    50: "Pan Katakumb", 60: "Widmowy Tytan",
    70: "Nekromantyczny Kolos", 80: "Arcyupiór Otchłani",
    90: "Król Kości", 100: "Władca Stu Pięter",
    110: "Strażnik Pękniętej Duszy",
    120: "Królowa Otchłannej Krypty",
    130: "Tytan Żelaznych Kości",
    140: "Prorok Czarnego Płomienia",
    150: "Władca Bezdennych Katakumb",
    160: "Astralny Żniwiarz",
    170: "Kolos Pustki",
    180: "Cesarz Upiorów",
    190: "Strażnik Końca",
    200: "Władca Dwustu Pięter",
}

CRYPT_BOSS_MECHANICS = {
    10: "bone_crush",
    20: "blood_drain",
    30: "grave_shield",
    40: "ash_curse",
    50: "catacomb_echo",
    60: "spectral_shift",
    70: "necro_regen",
    80: "ethereal_evade",
    90: "bone_rage",
    100: "hundred_lord",
    110: "soul_breaker",
    120: "abyss_queen",
    130: "iron_bones",
    140: "black_flame",
    150: "endless_echo",
    160: "astral_reaper",
    170: "void_regen",
    180: "phantom_emperor",
    190: "final_guardian",
    200: "two_hundred_lord",
}

CRYPT_BOSS_MECHANIC_TEXT = {
    10: "Co trzeci kontratak: Kościane Miażdżenie, mocniejszy cios fizyczny.",
    20: "Co trzeci kontratak: Krwawy Drenaż, mocniejszy cios leczący bossa.",
    30: "Co trzecie trafienie gracza: Tarcza Grobowca redukuje obrażenia o połowę.",
    40: "Co trzeci kontratak: Klątwa Popiołu, magiczny atak ignorujący połowę obrony magicznej.",
    50: "Co czwarty kontratak: Echo Katakumb, jedna potężna seria liczona jako pojedyncza odpowiedź bossa.",
    60: "Widmowy Tytan zmienia typ obrażeń między fizycznym i magicznym przy każdym własnym ataku.",
    70: "Co czwarty kontratak: Nekroregeneracja odnawia 7 procent maksymalnego HP bossa.",
    80: "Arcyupiór ma 25 procent szansy na eteryczny unik przeciw trafieniu gracza.",
    90: "Poniżej połowy HP Król Kości wpada w furię i zadaje 50 procent więcej obrażeń.",
    100: "Poniżej połowy HP Władca Stu Pięter wzmacnia się; co trzeci kontratak używa Załamania Duszy.",
    110: "Co trzeci kontratak: Rozdarcie Duszy, magiczne obrażenia częściowo omijające obronę.",
    120: "Co czwarty kontratak: Drenaż Otchłani, magiczne obrażenia leczące Królową.",
    130: "Co trzecie trafienie gracza rozbija się o Żelazne Kości i zostaje mocno zredukowane.",
    140: "Co trzeci kontratak: Czarny Płomień, silny atak magiczny ignorujący połowę obrony.",
    150: "Co czwarty kontratak: Bezdenne Echo, jedna bardzo silna odpowiedź bossa.",
    160: "Astralny Żniwiarz zmienia typ obrażeń przy każdym własnym ataku i co piąty atak wzmacnia cios.",
    170: "Co czwarty kontratak Kolos Pustki regeneruje 8 procent maksymalnego HP.",
    180: "Cesarz Upiorów ma 30 procent szansy na Widmowy Unik i co trzeci kontratak wzmacnia magię.",
    190: "Co czwarte trafienie gracza osłabia Straż Końca; poniżej połowy HP boss zadaje 60 procent więcej obrażeń.",
    200: "Władca Dwustu Pięter ma drugą fazę, Barierę Końca co piąte trafienie i Załamanie Wieczności co trzeci kontratak.",
}

CRYPT_TRIAL_TARGETS = {
    120: "crypt_tier4_trial_boss",
    180: "crypt_tier5_trial_boss",
}

CRYPT_REGULAR_NAMES = (
    "Szkielet Krypty", "Upiór Krypty",
    "Strażnik Sarkofagu", "Cień Katakumb",
    "Zjawisko Pustki", "Kościany Herold",
    "Widmo Otchłani", "Strażnik Wieczności",
)

def crypt_floor_id(floor):
    return f"crypt_floor_{int(floor)}"

def crypt_floor_number(room_id):
    m = re.fullmatch(r"crypt_floor_(\d+)(?:_r\d+)?", str(room_id))
    if not m: return None
    floor=int(m.group(1))
    return floor if floor >= 1 else None


_CRYPT_NAME_SYLLABLES = (
    "ar", "bel", "cor", "dra", "eth", "fal", "gor", "hal",
    "ith", "jor", "kael", "lor", "mor", "nar", "or", "prae",
    "qir", "rha", "syl", "tor", "ur", "vael", "wyr", "xan",
    "yor", "zae",
)

def _crypt_unique_word(value):
    """Bijekcyjny kod sylabowy: unikalny dla każdego dodatniego numeru, bez cyfr."""
    n = max(1, int(value))
    base = len(_CRYPT_NAME_SYLLABLES)
    parts = []
    while n > 0:
        n, rem = divmod(n - 1, base)
        parts.append(_CRYPT_NAME_SYLLABLES[rem])
    return "".join(reversed(parts)).capitalize()

def crypt_floor_display_name(floor, mythic=False):
    token = _crypt_unique_word(floor)
    if mythic:
        titles = (
            "Otchłań", "Grobowiec", "Nekropolia", "Komnata Zatracenia",
            "Sanktuarium Cienia", "Katakumba Pustki", "Krypta Echa",
        )
    else:
        titles = (
            "Katakumba", "Grobowiec", "Galeria Umarłych", "Komnata Pieczęci",
            "Krypta Bezimiennych", "Sala Sarkofagów", "Korytarz Kości",
        )
    title = titles[(max(1, int(floor)) - 1) % len(titles)]
    prefix = "Mityczna Krypta" if mythic else "Krypta"
    return f"{prefix}, piętro {max(1, int(floor))}: {title} {token}"

def crypt_subroom_display_name(label, floor, room_index, mythic=False):
    # 64 miejsc na piętro daje osobny, niepowtarzalny kod dla każdego pokoju.
    key = (max(1, int(floor)) - 1) * 64 + max(1, int(room_index))
    token = _crypt_unique_word(key)
    prefix = "Mityczna " if mythic and not str(label).startswith("Mityczna") else ""
    return f"Piętro {max(1, int(floor))}: {prefix}{label} {token}"


CRYPT_RARITIES = {
    "common": {
        "name": "Zwykły",
        "defense_bonus": 0,
        "stat_base": 1,
        "regular_weight": 60,
        "boss_weight": 10,
    },
    "rare": {
        "name": "Rzadki",
        "defense_bonus": 1,
        "stat_base": 2,
        "regular_weight": 25,
        "boss_weight": 30,
    },
    "epic": {
        "name": "Epicki",
        "defense_bonus": 2,
        "stat_base": 3,
        "regular_weight": 10,
        "boss_weight": 30,
    },
    "legendary": {
        "name": "Legendarny",
        "defense_bonus": 3,
        "stat_base": 4,
        "regular_weight": 4,
        "boss_weight": 20,
    },
    "mythic": {
        "name": "Mityczny",
        "defense_bonus": 4,
        "stat_base": 6,
        "regular_weight": 1,
        "boss_weight": 10,
    },
}

CRYPT_AFFIXES = {
    "strength": "Siła",
    "dexterity": "Zręczność",
    "constitution": "Kondycja",
    "intelligence": "Inteligencja",
    "willpower": "Siła Woli",
    "hp": "HP",
    "mana": "Mana",
}

BOSS_RELICS = {
    10: ("relic_bone_executioner", "Odłamek Kościanego Egzekutora", 2, "strength", 2),
    20: ("relic_blood_curator", "Krwawy Medalion Kuratora", 2, "constitution", 2),
    30: ("relic_tomb_knight", "Pieczęć Rycerza Grobowca", 3, "willpower", 2),
    40: ("relic_ash_witch", "Popielny Amulet Wiedźmy", 3, "intelligence", 3),
    50: ("relic_catacomb_lord", "Znak Pana Katakumb", 4, "hp", 40),
    60: ("relic_spectral_titan", "Widmowy Rdzeń Tytana", 4, "mana", 32),
    70: ("relic_necro_colossus", "Runiczna Kość Kolosa", 5, "constitution", 4),
    80: ("relic_archwraith", "Eteryczny Talizman Arcyupiora", 5, "dexterity", 4),
    90: ("relic_bone_king", "Korona Króla Kości", 6, "strength", 5),
    100: ("relic_hundred_lord", "Pieczęć Władcy Stu Pięter", 7, "willpower", 6),
    110: ("relic_soul_breaker", "Odłamek Pękniętej Duszy", 7, "strength", 7),
    120: ("relic_abyss_queen", "Korona Królowej Otchłani", 8, "intelligence", 7),
    130: ("relic_iron_bones", "Rdzeń Żelaznych Kości", 8, "constitution", 7),
    140: ("relic_black_flame", "Serce Czarnego Płomienia", 9, "willpower", 8),
    150: ("relic_endless_catacombs", "Pieczęć Bezdennych Katakumb", 9, "hp", 80),
    160: ("relic_astral_reaper", "Astralne Ostrze Żniwiarza", 10, "dexterity", 8),
    170: ("relic_void_colossus", "Rdzeń Kolosa Pustki", 10, "constitution", 9),
    180: ("relic_phantom_emperor", "Korona Cesarza Upiorów", 11, "intelligence", 9),
    190: ("relic_final_guardian", "Znak Strażnika Końca", 11, "willpower", 10),
    200: ("relic_two_hundred_lord", "Pieczęć Władcy Dwustu Pięter", 13, "hp", 120),
}

for _floor, (_item_id, _name, _defense, _affix, _amount) in BOSS_RELICS.items():
    _budget = equipment_progression_budget_v1138(_floor)
    _scaled_stat = max(1, int(round(_budget * 0.32)))
    if _affix == "hp":
        _scaled_amount = max(int(_amount), _scaled_stat * 10)
    elif _affix == "mana":
        _scaled_amount = max(int(_amount), _scaled_stat * 8)
    else:
        _scaled_amount = max(int(_amount), _scaled_stat)
    _scaled_defense = max(
        int(_defense),
        int(_defense) + equipment_defense_step_v1138(_floor),
    )
    _attack = (
        max(1, int(round(_budget * 0.10)))
        if _affix in {"strength", "dexterity"} else 0
    )
    _magic_attack = (
        max(1, int(round(_budget * 0.10)))
        if _affix in {"intelligence", "willpower"} else 0
    )
    _prop_key = {
        "strength": "physical_damage_pct",
        "dexterity": "physical_damage_pct",
        "constitution": "physical_defense_pct",
        "intelligence": "magic_damage_pct",
        "willpower": "magic_defense_pct",
        "hp": "max_hp_pct",
        "mana": "max_mana_pct",
    }.get(_affix)
    _prop_value = round(1.0 + 4.0 * (min(200, _floor) / 200.0) ** 0.80, 2)
    _sockets = min(5, 1 + max(0, int(_floor) // 50))
    _catalog_mut.catalog_assign({
        "name": _name,
        "type": "armor",
        "slot": "charm",
        "defense": _scaled_defense,
        "attack": _attack,
        "magic_attack": _magic_attack,
        "sockets": _sockets,
        "properties": {_prop_key: _prop_value} if _prop_key else {},
        "price": None,
        "desc": (
            f"Unikalny relikt bossa Krypty z piętra {_floor}. "
            f"Obrona +{_scaled_defense}. "
            f"Bonus: {CRYPT_AFFIXES.get(_affix, _affix)} +{_scaled_amount}. "
            f"Gniazda: {_sockets}."
        ),
        "rarity": "unique",
        "rarity_name": "Unikalny Bossowy",
        "affix": _affix,
        "affix_amount": _scaled_amount,
        "boss_relic_floor": _floor,
        "source_progression_stage": min(800, int(_floor)),
        "equipment_identity_source": "crypt_boss",
        "equipment_identity_role": "unique_relic",
        "equipment_identity_label": (
            "Boss Krypty — unikalny relikt z mocnym affixem i socketami"
        ),
    }, 'ITEMS', ITEMS, (_item_id,))

_catalog_mut.catalog_assign({
    "name": "Sygnet Herszta Bandytów",
    "type": "armor",
    "slot": "charm",
    "defense": 3,
    "price": None,
    "desc": (
        "Unikalny sygnet Herszta Bandytów. Obrona +3. "
        "Bonus: Zręczność +3."
    ),
    "rarity": "unique",
    "rarity_name": "Unikalny",
    "affix": "dexterity",
    "affix_amount": 3,
}, 'ITEMS', ITEMS, ("bandit_chief_signet",))

WORLD_BOSS_UNIQUES = {
    "goblin_king_crown": {
        "name": "Korona Króla Goblinów",
        "type": "armor",
        "slot": "head",
        "defense": 4,
        "price": None,
        "desc": "Unikalna korona Króla Goblinów. Obrona +4. Zręczność +3.",
        "rarity": "unique",
        "rarity_name": "Unikalny",
        "affix": "dexterity",
        "affix_amount": 3,
    },
    "shadow_alpha_fang": {
        "name": "Kieł Alfy Cienia",
        "type": "armor",
        "slot": "charm",
        "defense": 3,
        "price": None,
        "desc": "Unikalny kieł Alfy Wilków Cienia. Obrona +3. Siła +4.",
        "rarity": "unique",
        "rarity_name": "Unikalny",
        "affix": "strength",
        "affix_amount": 4,
    },
    "ruin_warden_plate": {
        "name": "Płyta Strażnika Ruin",
        "type": "armor",
        "slot": "body",
        "defense": 6,
        "price": None,
        "desc": "Unikalny pancerz Strażnika Ruin. Obrona +6. Siła Woli +4.",
        "rarity": "unique",
        "rarity_name": "Unikalny",
        "affix": "willpower",
        "affix_amount": 4,
    },
    "crystal_lord_core": {
        "name": "Rdzeń Kryształowego Władcy",
        "type": "armor",
        "slot": "charm",
        "defense": 5,
        "price": None,
        "desc": "Unikalny rdzeń Kryształowego Władcy. Obrona +5. Inteligencja +5.",
        "rarity": "unique",
        "rarity_name": "Unikalny",
        "affix": "intelligence",
        "affix_amount": 5,
    },
}
_catalog_mut.catalog_update_path('ITEMS', ITEMS, (), WORLD_BOSS_UNIQUES)

# v1.13.27: old named world-boss uniques must scale with the source that drops
# them. We derive a conservative stage from the boss's authored progression
# rewards when no explicit generator/recommended stage exists.
LEGACY_NAMED_UNIQUE_SOURCES_V11327 = {
    "bandit_chief_signet": "bandit_chief",
    "goblin_king_crown": "goblin_king",
    "shadow_alpha_fang": "shadow_alpha",
    "ruin_warden_plate": "ruin_warden",
    "crystal_lord_core": "crystal_lord",
}


def _boss_source_stage_v11327(template):
    template = template or {}
    explicit = []
    for key in (
        "generator_level", "recommended_mastery", "recommended_level", "level"
    ):
        try:
            value = int(template.get(key, 0) or 0)
        except (TypeError, ValueError, OverflowError):
            value = 0
        if value > 0:
            explicit.append(value)
    if explicit:
        return max(1, min(800, max(explicit)))

    proxies = [1]
    for key, divisor in (("stat_reward", 4), ("class_xp_reward", 50)):
        try:
            proxy = int(template.get(key, 0) or 0) // divisor
        except (TypeError, ValueError, OverflowError):
            proxy = 0
        if proxy > 0:
            proxies.append(proxy)
    return max(1, min(800, max(proxies)))


def _named_unique_property_v11327(affix, stage):
    affix = str(affix or "")
    key = {
        "strength": "physical_damage_pct",
        "dexterity": "physical_damage_pct",
        "constitution": "physical_defense_pct",
        "intelligence": "magic_damage_pct",
        "willpower": "magic_defense_pct",
        "hp": "max_hp_pct",
        "mana": "max_mana_pct",
    }.get(affix, "all_damage_pct")
    amount = round(0.75 + 3.25 * ((max(1, stage) / 600.0) ** 0.72), 2)
    return {key: amount}


def _upgrade_named_unique_from_source_v11327(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: _upgrade_named_unique_from_source_v11327")
_upgrade_named_unique_from_source_v11327 = _sb410_bind(_sb410_mod_v410_dungeon_loot._upgrade_named_unique_from_source_v11327, globals())


for _legacy_unique_id_v11327, _source_mob_id_v11327 in (
    LEGACY_NAMED_UNIQUE_SOURCES_V11327.items()
):
    _upgrade_named_unique_from_source_v11327(
        _legacy_unique_id_v11327, _source_mob_id_v11327
    )


def loot_source_progression_audit_v11327(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: loot_source_progression_audit_v11327")
loot_source_progression_audit_v11327 = _sb410_bind(_sb410_mod_v410_dungeon_loot.loot_source_progression_audit_v11327, globals())


LOOT_SOURCE_PROGRESSION_AUDIT_V11327 = loot_source_progression_audit_v11327()
# v1.13.30: audit failure is enforced by predeploy_full.py, not production startup.
for _world_boss_unique_id in WORLD_BOSS_UNIQUES:
    _world_boss_unique_item = ITEMS[_world_boss_unique_id]
    _world_boss_unique_item.setdefault(
        "equipment_identity_source", "world_boss"
    )
    _world_boss_unique_item.setdefault(
        "equipment_identity_role", "named_unique"
    )
    _world_boss_unique_item.setdefault(
        "equipment_identity_label",
        "World Boss — nazwany unikat, nie kopia sklepowego EQ",
    )

def crypt_variant_id(base_item_id, rarity_key, affix_key):
    return f"{base_item_id}__{rarity_key}__{affix_key}"

def crypt_affix_amount(tier, rarity_key, affix_key):
    mastery = max(1, min(800, int(tier) * 10))
    budget = equipment_progression_budget_v1138(mastery)
    scale = {
        "common": 0.16,
        "rare": 0.20,
        "epic": 0.24,
        "legendary": 0.30,
        "mythic": 0.38,
    }.get(str(rarity_key), 0.16)
    stat_value = max(1, int(round(budget * scale)))
    if affix_key == "hp":
        return stat_value * 10
    if affix_key == "mana":
        return stat_value * 8
    return stat_value

def build_crypt_loot_variants(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: build_crypt_loot_variants")
build_crypt_loot_variants = _sb410_bind(_sb410_mod_v410_dungeon_loot.build_crypt_loot_variants, globals())

V11329_CRYPT_END_WEIGHTS = {
    "regular": {
        "common": 30.0,
        "rare": 30.0,
        "epic": 20.0,
        "legendary": 13.0,
        "mythic": 7.0,
    },
    "boss": {
        "common": 3.0,
        "rare": 17.0,
        "epic": 30.0,
        "legendary": 28.0,
        "mythic": 22.0,
    },
}


def crypt_rarity_weights_v11329(is_boss=False, mastery=1):
    mastery = max(1, min(800, int(mastery or 1)))
    progress = ((mastery - 1) / 599.0) ** 0.80
    weight_key = "boss_weight" if is_boss else "regular_weight"
    end_key = "boss" if is_boss else "regular"
    weights = {}
    for rarity_key, rarity in CRYPT_RARITIES.items():
        start_weight = float(rarity[weight_key])
        end_weight = float(V11329_CRYPT_END_WEIGHTS[end_key][rarity_key])
        weights[rarity_key] = (
            start_weight + (end_weight - start_weight) * progress
        )
    return weights


def roll_crypt_rarity(is_boss=False, mastery=1):
    weights_by_key = crypt_rarity_weights_v11329(
        is_boss=is_boss, mastery=mastery
    )
    keys = list(CRYPT_RARITIES)
    weights = [weights_by_key[key] for key in keys]
    return random.choices(keys, weights=weights, k=1)[0]


def roll_crypt_loot_item(base_item_id, is_boss=False):
    item = ITEMS.get(base_item_id)
    if not item or not item.get("crypt_set_tier"):
        return base_item_id

    mastery = max(
        1,
        min(
            600,
            int(
                item.get("source_progression_stage")
                or int(item.get("crypt_set_tier", 1) or 1) * 10
            ),
        ),
    )
    rarity_key = roll_crypt_rarity(
        is_boss=is_boss, mastery=mastery
    )
    affix_key = random.choice(tuple(CRYPT_AFFIXES))
    variant_id = crypt_variant_id(
        base_item_id, rarity_key, affix_key
    )
    return variant_id if variant_id in ITEMS else base_item_id


def crypt_rarity_progression_audit_v11329(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: crypt_rarity_progression_audit_v11329")
crypt_rarity_progression_audit_v11329 = _sb410_bind(_sb410_mod_v410_dungeon_loot.crypt_rarity_progression_audit_v11329, globals())


CRYPT_RARITY_PROGRESSION_AUDIT_V11329 = crypt_rarity_progression_audit_v11329()
# v1.13.30: audit failure is enforced by predeploy_full.py, not production startup.
# v1.13.30: Wieże nie mają już sztucznego Soul Level gate. Trudność, bossy
# i checkpointy są właściwą barierą progresji. Stała 1 pozostaje dla zgodności.
ASTRAL_MIN_SOUL_LEVEL = 1
ASTRAL_MIN_FLOOR = 100
ASTRAL_MAX_FLOOR = 200
ASTRAL_BOSS_FLOORS = tuple(range(100, ASTRAL_MAX_FLOOR + 1, 10))

ASTRAL_BOSS_NAMES = {
    100: "Strażnik Gwiezdnej Bramy",
    110: "Rycerz Konstelacji",
    120: "Tkaczka Nebuli",
    130: "Strażnik Komety",
    140: "Arcykapłan Gwiezdnego Ognia",
    150: "Tytan Orbitalny",
    160: "Władca Konstelacji",
    170: "Serafin Pustki",
    180: "Imperator Gwiezdnej Burzy",
    190: "Strażnik Firmamentu",
    200: "Astralny Suweren",
}

ASTRAL_BOSS_MECHANICS = {
    100: "astral_shift",
    110: "stellar_barrier",
    120: "nebula_drain",
    130: "comet_evade",
    140: "starfire",
    150: "orbital_echo",
    160: "constellation_burst",
    170: "astral_regen",
    180: "stellar_storm",
    190: "firmament_guard",
    200: "astral_sovereign",
}

ASTRAL_BOSS_MECHANIC_TEXT = {
    100: "Zmienia fazę między energią fizyczną i magiczną.",
    110: "Co trzecie trafienie gracza aktywuje Gwiezdną Barierę.",
    120: "Co czwarty kontratak używa Drenażu Nebuli i leczy bossa.",
    130: "Ma 25 procent szansy na Unik Komety.",
    140: "Co trzeci kontratak wyzwala Gwiezdny Ogień omijający część obrony.",
    150: "Co czwarty kontratak uruchamia bardzo silne Echo Orbitalne.",
    160: "Co trzeci kontratak wyzwala Rozbłysk Konstelacji.",
    170: "Co czwarty kontratak regeneruje 8 procent maksymalnego HP.",
    180: "Co trzeci kontratak przywołuje Gwiezdną Burzę.",
    190: "Co czwarte trafienie gracza aktywuje Straż Firmamentu.",
    200: "Druga faza, Bariera Suwerena i Astralne Załamanie co trzeci kontratak.",
}

ASTRAL_REGULAR_NAMES = (
    "Astralny Strażnik",
    "Widmo Konstelacji",
    "Rycerz Gwiezdnego Pyłu",
    "Tkacz Nebuli",
    "Herold Komety",
    "Strażnik Firmamentu",
)
MYTHIC_CRYPT_REGULAR_NAMES = (
    "Mityczny Kościany Rycerz",
    "Mityczny Upiór",
    "Mityczny Żniwiarz Grobowca",
    "Mityczny Strażnik Otchłani",
)
MYTHIC_ASTRAL_REGULAR_NAMES = (
    "Mityczny Astralny Strażnik",
    "Mityczny Rycerz Konstelacji",
    "Mityczne Widmo Nebuli",
    "Mityczny Herold Gwiezdnej Burzy",
)

ASTRAL_BOSS_RELICS = {
    100: ("astral_relic_gate", "Gwiezdny Klucz Bramy", 8, "willpower", 7),
    110: ("astral_relic_constellation", "Pieczęć Konstelacji", 8, "dexterity", 7),
    120: ("astral_relic_nebula", "Serce Nebuli", 9, "intelligence", 8),
    130: ("astral_relic_comet", "Rdzeń Komety", 9, "strength", 8),
    140: ("astral_relic_starfire", "Płomień Gwiazdy", 10, "willpower", 9),
    150: ("astral_relic_orbit", "Rdzeń Orbitalny", 10, "constitution", 9),
    160: ("astral_relic_constellation_lord", "Korona Konstelacji", 11, "intelligence", 10),
    170: ("astral_relic_void_seraph", "Pióro Serafina Pustki", 11, "dexterity", 10),
    180: ("astral_relic_storm_emperor", "Berło Gwiezdnej Burzy", 12, "willpower", 11),
    190: ("astral_relic_firmament", "Znak Firmamentu", 12, "constitution", 11),
    200: ("astral_relic_sovereign", "Korona Astralnego Suwerena", 14, "hp", 140),
}

def astral_floor_id(floor):
    return f"astral_floor_{int(floor)}"

def astral_floor_number(room_id):
    match = re.fullmatch(r"astral_floor_(\d+)(?:_r\d+)?", str(room_id))
    if not match:
        return None
    floor = int(match.group(1))
    return floor if floor >= ASTRAL_MIN_FLOOR else None

def is_astral_boss_floor(floor):
    try:
        floor = int(floor)
    except (TypeError, ValueError):
        return False
    return floor >= ASTRAL_MIN_FLOOR and floor % 10 == 0

for _floor, (_item_id, _name, _defense, _affix, _amount) in ASTRAL_BOSS_RELICS.items():
    _catalog_mut.catalog_assign({
        "name": _name,
        "type": "armor",
        "slot": "charm",
        "defense": _defense,
        "price": None,
        "desc": (
            f"Unikalny relikt Wieży Astralnej z poziomu {_floor}. "
            f"Obrona +{_defense}. "
            f"Bonus: {CRYPT_AFFIXES.get(_affix, _affix)} +{_amount}."
        ),
        "rarity": "unique",
        "rarity_name": "Unikalny",
        "affix": _affix,
        "affix_amount": _amount,
        "astral_relic_floor": _floor,
    }, 'ITEMS', ITEMS, (_item_id,))

MYTHIC_MIN_FLOOR = 1
MYTHIC_MAX_FLOOR = 200
MYTHIC_CRYPT_MIN_SOUL_LEVEL = 1
MYTHIC_ASTRAL_MIN_SOUL_LEVEL = 1
MYTHIC_BOSS_FLOORS = set(range(10, MYTHIC_MAX_FLOOR + 1, 10))
PROF_DUNGEON_MAX_FLOOR = 20

def mythic_crypt_floor_id(floor):
    return f"mythic_crypt_floor_{int(floor)}"

def mythic_crypt_floor_number(room_id):
    match = re.fullmatch(
        r"mythic_crypt_floor_(\d+)(?:_r\d+)?", str(room_id or "")
    )
    if not match:
        return None
    floor = int(match.group(1))
    if floor >= MYTHIC_MIN_FLOOR:
        return floor
    return None

def mythic_astral_floor_id(floor):
    return f"mythic_astral_floor_{int(floor)}"

def mythic_astral_floor_number(room_id):
    match = re.fullmatch(
        r"mythic_astral_floor_(\d+)(?:_r\d+)?", str(room_id or "")
    )
    if not match:
        return None
    floor = int(match.group(1))
    return floor if floor >= MYTHIC_MIN_FLOOR else None

def is_mythic_astral_boss_floor(floor):
    try:
        floor = int(floor)
    except (TypeError, ValueError):
        return False
    return floor >= 10 and floor % 10 == 0

PROF_DUNGEON_PREFIXES = {
    "crystal_mine": "prof_crystal_mine_",
    "sunken_grotto": "prof_sunken_grotto_",
    "ancient_forest": "prof_ancient_forest_",
    "alchemy_garden": "prof_alchemy_garden_",
}

PROF_DUNGEON_TOOL = {
    "crystal_mine": ("mining", "pickaxe", "Kilof"),
    "sunken_grotto": ("fishing", "fishing_rod", "Wędka"),
    "ancient_forest": ("woodcutting", "saw", "Piła"),
    "alchemy_garden": (
        "herbalism", "herbalist_sickle", "Sierp Zielarski"
    ),
}

def profession_dungeon_floor(room_id):
    room_id = str(room_id or "")
    for dungeon, prefix in PROF_DUNGEON_PREFIXES.items():
        if not room_id.startswith(prefix):
            continue
        raw = room_id[len(prefix):]
        match = re.fullmatch(r"(\d+)(?:_r\d+)?", raw)
        if match:
            floor = int(match.group(1))
            if floor >= 1:
                return dungeon, floor
    return None, None

def profession_dungeon_room_id(dungeon, floor):
    return f"{PROF_DUNGEON_PREFIXES[dungeon]}{int(floor)}"

def profession_dungeon_required_tool_level(floor):
    floor = max(1, int(floor))
    if floor == 1:
        return 1
    return min(PROFESSION_MAX_LEVEL, floor * 10)


PROF_DUNGEON_COMBAT_NAMES = {
    "sunken_grotto": (
        "Topielec Zatopionej Groty",
        "Głębinowy Krab Strażnik",
        "Syrena Mętnej Wody",
    ),
    "ancient_forest": (
        "Pradawny Strażnik Kory",
        "Dziki Duch Ostępu",
        "Kolczasty Łowca Gaju",
    ),
    "alchemy_garden": (
        "Alchemiczny Cierniowiec",
        "Toksyczny Strażnik Ogrodu",
        "Mutant Zarodnikowy",
    ),
}

def profession_dungeon_combat_pack(dungeon, floor):
    # v0.9.15: wszystkie lochy profesyjne poza Kopalnią Kryształów
    # mają realną obsadę bojową. Kopalnie pozostają świadomie bez mobów.
    names = PROF_DUNGEON_COMBAT_NAMES.get(dungeon)
    if not names or dungeon == "crystal_mine":
        return []
    floor = max(1, int(floor))
    effective = profession_dungeon_required_tool_level(floor)
    room_id = profession_dungeon_room_id(dungeon, floor)
    spawns = []
    for index, name in enumerate(names, 1):
        mob_id = f"prof_{dungeon}_mob_{floor}_{index}"
        base_hp = 120 + effective * 4 + min(floor, 400) * 12 + index * 35
        base_damage = 8 + effective // 8 + index * 2
        template = {
            "name": dungeon_mob_display_name_v11336(
                dungeon, name, floor, variant=index - 1
            ),
            "max_hp": max(1, int(round(base_hp * GLOBAL_MOB_HP_MULTIPLIER))),
            "base_max_hp": base_hp,
            "damage": max(1, base_damage),
            "damage_type": "magic" if index == 2 else "physical",
            "silver": 20 + effective * 2,
            "gold": max(0, effective // 80),
            "mithril": 0,
            "stat_reward": 35 + effective * 2,
            "class_xp_reward": 600 + effective * 35,
            "soul_reward": 140 + effective * 9,
            "drops": {"healing_potion": 0.04},
            "quest_target": None,
            "profession_dungeon": dungeon,
            "profession_dungeon_floor": floor,
            "elite_eligible": True,
        }
        _catalog_mut.catalog_assign(template, 'MOB_TEMPLATES', MOB_TEMPLATES, (mob_id,))
        spawns.append((room_id, mob_id))
    return spawns

def build_astral_tower(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: build_astral_tower")
build_astral_tower = _sb410_bind(_sb410_mod_v410_dungeon_builders.build_astral_tower, globals())


def build_crypt_200_floors(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: build_crypt_200_floors")
build_crypt_200_floors = _sb410_bind(_sb410_mod_v410_dungeon_builders.build_crypt_200_floors, globals())

def build_mythic_endgame(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: build_mythic_endgame")
build_mythic_endgame = _sb410_bind(_sb410_mod_v410_dungeon_builders.build_mythic_endgame, globals())


def build_profession_dungeons(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: build_profession_dungeons")
build_profession_dungeons = _sb410_bind(_sb410_mod_v410_dungeon_builders.build_profession_dungeons, globals())


HERB_SPECIFIC_MEADOWS = {
    "mint_meadow": "mint",
    "chamomile_meadow": "chamomile",
    "nettle_meadow": "nettle",
    "lemon_balm_meadow": "lemon_balm",
    "lavender_meadow": "lavender",
    "yarrow_meadow": "yarrow",
    "sage_meadow": "sage",
    "valerian_meadow": "valerian",
    "ginseng_meadow": "ginseng",
    "moonflower_meadow": "moonflower",
}

HERB_SPECIFIC_MEADOW_NAMES = {
    "mint_meadow": "Łąka Mięty",
    "chamomile_meadow": "Łąka Rumianku",
    "nettle_meadow": "Łąka Pokrzywy",
    "lemon_balm_meadow": "Łąka Melisy",
    "lavender_meadow": "Łąka Lawendy",
    "yarrow_meadow": "Łąka Krwawnika",
    "sage_meadow": "Łąka Szałwii",
    "valerian_meadow": "Łąka Waleriany",
    "ginseng_meadow": "Łąka Żeń-szenia",
    "moonflower_meadow": "Łąka Księżycowego Kwiatu",
}

# v0.8.66: level narzędzia odblokowuje jakość surowca, a profesja tempo.
# Tematyczne łąki nie mogą omijać progresji Sierpa samą podróżą.
HERB_SPECIFIC_MEADOW_MIN_TOOL_LEVEL = {
    "mint_meadow": 1,
    "chamomile_meadow": 1,
    "nettle_meadow": 1,
    "lemon_balm_meadow": 10,
    "lavender_meadow": 20,
    "yarrow_meadow": 30,
    "sage_meadow": 40,
    "valerian_meadow": 45,
    "ginseng_meadow": 50,
    "moonflower_meadow": 70,
}

FIELD_RESOURCE_MIN_TOOL_LEVEL = {
    "sewer_black_channel": ("fishing", 30, "Wędka"),
    "beast_lair_root_cavern": ("woodcutting", 40, "Piła"),
    "cemetery_moon_garden": ("herbalism", 20, "Sierp Zielarski"),
    "cult_ruins_overgrown_garden": ("herbalism", 60, "Sierp Zielarski"),
}

# Atlas ma pokazywać te same progi, które naprawdę egzekwuje zbieranie.
for _room_id, _required in HERB_SPECIFIC_MEADOW_MIN_TOOL_LEVEL.items():
    _herb_id = HERB_SPECIFIC_MEADOWS.get(_room_id)
    if _herb_id and _room_id in HERB_ATLAS_ROOM_MIN_LEVELS:
        HERB_ATLAS_ROOM_MIN_LEVELS[_room_id][_herb_id] = int(_required)

def build_mountain_region_and_herb_meadows(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: build_mountain_region_and_herb_meadows")
build_mountain_region_and_herb_meadows = _sb410_bind(_sb410_mod_v410_dungeon_regions.build_mountain_region_and_herb_meadows, globals())

    # Prowadzenie do nowej zawartości.
    

GIANT_FORTRESS_MAX_FLOOR = 50
GIANT_FORTRESS_BOSS_FLOORS = (10, 20, 30, 40, 50)
GIANT_FORTRESS_BOSS_NAMES = {
    10: "Kamienny Herszt Grakk",
    20: "Jednooki Tyran Morok",
    30: "Władca Głazów Bront",
    40: "Cyklop Burzy Arges",
    50: "Król Gigantów Tharos",
}
GIANT_FORTRESS_BOSS_MECHANICS = {
    10: "giant_crush",
    20: "cyclops_beam",
    30: "boulder_storm",
    40: "giant_thunder",
    50: "giant_king",
}

ELITE_AFFIXES = {
    "armored": {
        "label": "Opancerzony",
        "text": "Opancerzony: otrzymuje 30 procent mniej normalnych obrażeń.",
    },
    "vampiric": {
        "label": "Wampiryczny",
        "text": "Wampiryczny: leczy się za 35 procent skutecznego trafienia.",
    },
    "regenerating": {
        "label": "Regenerujący",
        "text": "Regenerujący: co trzecią odpowiedź odnawia 4 procent maksymalnego HP.",
    },
    "ice": {
        "label": "Lodowy",
        "text": "Lodowy: ataki stają się magiczne i zadają 15 procent więcej obrażeń.",
    },
    "fire": {
        "label": "Ognisty",
        "text": "Ognisty: ataki stają się magiczne i zadają 25 procent więcej obrażeń.",
    },
    "astral": {
        "label": "Astralny",
        "text": "Astralny: zmienia typ obrażeń, wzmacnia je o 30 procent i częściowo omija obronę.",
    },
    "furious": {
        "label": "Berserker",
        "text": "Berserker: zadaje 40 procent więcej obrażeń.",
    },
    "storm": {
        "label": "Burzowy",
        "text": "Burzowy: atakuje magią burzy, zadaje 30 procent więcej obrażeń i częściowo omija obronę.",
    },
    "toxic": {
        "label": "Toksyczny",
        "text": "Toksyczny: jad zadaje 15 procent więcej obrażeń i silnie omija zwykłą obronę.",
    },
    "cursed": {
        "label": "Przeklęty",
        "text": "Przeklęty: atakuje magią, zadaje 20 procent więcej obrażeń i częściowo omija obronę.",
    },
}

RARE_TROLL_VARIANTS = (
    "albino_troll",
    "crystal_troll",
    "ancient_troll",
    "runic_troll",
)

def giant_fortress_floor_id(floor):
    return f"giant_fortress_{int(floor)}"

def giant_fortress_floor_number(room_id):
    match = re.fullmatch(
        r"giant_fortress_(\d+)(?:_r\d+)?",
        str(room_id),
    )
    if not match:
        return None
    floor = int(match.group(1))
    return floor if floor >= 1 else None

def is_giant_fortress_boss_floor(floor):
    try:
        floor = int(floor)
    except (TypeError, ValueError):
        return False
    return floor >= 10 and floor % 10 == 0

def _register_elite_variants(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: _register_elite_variants")
_register_elite_variants = _sb410_bind(_sb410_mod_v410_dungeon_regions._register_elite_variants, globals())

def _register_rare_variants(base_ids):
    for base_id in tuple(base_ids):
        base_template = MOB_TEMPLATES.get(base_id)
        if not base_template:
            continue
        rare_id = f"{base_id}__rare"
        if rare_id in MOB_TEMPLATES:
            continue
        rare = dict(base_template)
        rare["name"] = f"Rzadki {base_template['name']}"
        rare["rare_mob"] = True
        rare["rare_base_template"] = base_id
        rare["max_hp"] = max(1, int(round(int(base_template["max_hp"]) * 1.60)))
        rare["damage"] = max(1, int(round(int(base_template["damage"]) * 1.30)))
        rare["silver"] = int(round(int(base_template.get("silver", 0)) * 2.20))
        rare["gold"] = int(base_template.get("gold", 0)) + 2
        rare["soul_reward"] = int(round(int(base_template.get("soul_reward", 0)) * 2.20))
        rare["class_xp_reward"] = int(round(int(base_template.get("class_xp_reward", max(50, int(base_template.get("stat_reward", 1))*10))) * 2.20))
        rare["stat_reward"] = int(round(int(base_template.get("stat_reward", 0)) * 1.50))
        rare["drops"] = dict(base_template.get("drops", {}))
        rare["drops"].setdefault("soul_elixir", 0.20)
        rare["drops"].setdefault("soul_shard", 0.45)
        rare["corpse_equipment_guaranteed"] = min(
            len(rare.get("corpse_equipment_pool", ())),
            max(1, int(rare.get("corpse_equipment_guaranteed", 0)) + 1),
        ) if rare.get("corpse_equipment_pool") else 0
        _catalog_mut.catalog_assign(rare, 'MOB_TEMPLATES', MOB_TEMPLATES, (rare_id,))

V0866_RARE_TROLL_SPAWN_CHANCE = 0.12
V0866_RARE_MOB_SPAWN_CHANCE = 0.04
V0866_ELITE_MOB_SPAWN_CHANCE = 0.15


def resolve_world_spawn_template(template_id):
    resolved = template_id

    if (
        resolved == "mountain_troll"
        and random.random() < V0866_RARE_TROLL_SPAWN_CHANCE
    ):
        resolved = random.choices(
            RARE_TROLL_VARIANTS,
            weights=(45, 30, 7, 18),
            k=1,
        )[0]

    template = MOB_TEMPLATES.get(resolved, {})
    if (
        template.get("rare_eligible")
        and random.random() < V0866_RARE_MOB_SPAWN_CHANCE
    ):
        candidate = f"{resolved}__rare"
        if candidate in MOB_TEMPLATES:
            return candidate

    if (
        template.get("elite_eligible")
        and random.random() < V0866_ELITE_MOB_SPAWN_CHANCE
    ):
        affix = random.choice(
            tuple(ELITE_AFFIXES)
        )
        candidate = (
            f"{resolved}__elite_{affix}"
        )
        if candidate in MOB_TEMPLATES:
            resolved = candidate

    return resolved

