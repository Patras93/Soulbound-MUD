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
from systems.content_registry import CRYPT_MAX_FLOOR, INFINITE_CRYPT_STEP_RATE, MOB_SPAWNS, MOB_TEMPLATES, NPCS, QUESTS
from systems.items_resources import CLASS_EQUIPMENT_SLOT_DEFS


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
    _catalog_mut.catalog_assign({
        "name": _name,
        "type": "armor",
        "slot": "charm",
        "defense": _defense,
        "price": None,
        "desc": (
            f"Unikalny relikt bossa Krypty z piętra {_floor}. "
            f"Obrona +{_defense}. "
            f"Bonus: {CRYPT_AFFIXES.get(_affix, _affix)} +{_amount}."
        ),
        "rarity": "unique",
        "rarity_name": "Unikalny",
        "affix": _affix,
        "affix_amount": _amount,
        "boss_relic_floor": _floor,
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

def crypt_variant_id(base_item_id, rarity_key, affix_key):
    return f"{base_item_id}__{rarity_key}__{affix_key}"

def crypt_affix_amount(tier, rarity_key, affix_key):
    rarity = CRYPT_RARITIES[rarity_key]
    stat_value = int(rarity["stat_base"]) + (max(1, int(tier)) - 1) // 4
    if affix_key == "hp":
        return stat_value * 10
    if affix_key == "mana":
        return stat_value * 8
    return stat_value

def build_crypt_loot_variants():
    slot_pattern = "|".join(re.escape(slot) for slot in CLASS_EQUIPMENT_SLOT_DEFS)
    base_ids = [
        item_id
        for item_id, item in list(ITEMS.items())
        if re.fullmatch(rf"crypt_t\d+_(?:{slot_pattern})", item_id)
    ]

    for base_item_id in base_ids:
        base_item = ITEMS[base_item_id]
        m = re.fullmatch(
            rf"crypt_t(\d+)_({slot_pattern})",
            base_item_id,
        )
        if not m:
            continue

        tier = int(m.group(1))
        slot = m.group(2)

        # Stary item bazowy pozostaje kompatybilny i jest zwykłym
        # elementem setu bez affixu.
        base_item["rarity"] = "common"
        base_item["rarity_name"] = "Zwykły"
        base_item["crypt_set_tier"] = tier
        base_item["crypt_base_item"] = base_item_id
        base_item["affix"] = None
        base_item["affix_amount"] = 0

        for rarity_key, rarity in CRYPT_RARITIES.items():
            for affix_key, affix_name in CRYPT_AFFIXES.items():
                amount = crypt_affix_amount(
                    tier, rarity_key, affix_key
                )
                variant_id = crypt_variant_id(
                    base_item_id, rarity_key, affix_key
                )
                defense = (
                    int(base_item.get("defense", 0))
                    + int(rarity["defense_bonus"])
                )
                variant_name = (
                    f"{base_item['name']} "
                    f"[{rarity['name']}, {affix_name} +{amount}]"
                )
                _catalog_mut.catalog_assign({
                    "name": variant_name,
                    "type": "armor",
                    "slot": slot,
                    "defense": defense,
                    "price": None,
                    # v0.61.2: opis wariantu Krypty jest generowany przy wyświetleniu.
                    "rarity": rarity_key,
                    "rarity_name": rarity["name"],
                    "crypt_set_tier": tier,
                    "crypt_base_item": base_item_id,
                    "affix": affix_key,
                    "affix_amount": amount,
                }, 'ITEMS', ITEMS, (variant_id,))

def roll_crypt_rarity(is_boss=False):
    keys = list(CRYPT_RARITIES)
    weight_key = "boss_weight" if is_boss else "regular_weight"
    weights = [
        CRYPT_RARITIES[key][weight_key]
        for key in keys
    ]
    return random.choices(keys, weights=weights, k=1)[0]

def roll_crypt_loot_item(base_item_id, is_boss=False):
    item = ITEMS.get(base_item_id)
    if not item or not item.get("crypt_set_tier"):
        return base_item_id

    rarity_key = roll_crypt_rarity(is_boss=is_boss)
    affix_key = random.choice(tuple(CRYPT_AFFIXES))
    variant_id = crypt_variant_id(
        base_item_id, rarity_key, affix_key
    )
    return variant_id if variant_id in ITEMS else base_item_id


ASTRAL_MIN_SOUL_LEVEL = 100
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
MYTHIC_ASTRAL_MIN_SOUL_LEVEL = 100
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
            "name": f"{name}, poziom {floor}",
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

def build_astral_tower():
    _catalog_mut.catalog_assign("astral_gate", 'ROOMS', ROOMS, ("shrine", "exits", "east"))
    _catalog_mut.catalog_assign({
        "zone": "Wieża Astralna",
        "name": "Astralna Brama",
        "desc": (
            "Nad urwiskiem unosi się błękitno-fioletowa brama z gwiezdnego szkła. "
            "Za nią zaczyna się Wieża Astralna przeznaczona dla bohaterów od Soul Level 100."
        ),
        "exits": {
            "west": "shrine",
            "up": astral_floor_id(ASTRAL_MIN_FLOOR),
        },
    }, 'ROOMS', ROOMS, ("astral_gate",))

    for tier_index, start_floor in enumerate(
        range(ASTRAL_MIN_FLOOR, ASTRAL_MAX_FLOOR + 1, 10),
        1,
    ):
        stat_cycle = (
            "strength", "dexterity", "constitution",
            "intelligence", "willpower"
        )
        defs = (
            ("head", "Astralny Hełm", 6 + tier_index // 2),
            ("body", "Astralny Pancerz", 9 + tier_index),
            ("hands", "Astralne Rękawice", 5 + tier_index // 2),
            ("legs", "Astralne Nogawice", 7 + tier_index // 2),
            ("feet", "Astralne Buty", 5 + tier_index // 2),
            ("charm", "Astralny Talizman", 4 + tier_index // 2),
            ("ring", "Astralny Pierścień", 4 + tier_index // 2),
            ("necklace", "Astralny Naszyjnik", 5 + tier_index // 2),
            ("earring", "Astralny Kolczyk", 4 + tier_index // 2),
            ("shoulders", "Astralne Naramienniki", 7 + tier_index // 2),
            ("belt", "Astralny Pas", 6 + tier_index // 2),
            ("cloak", "Astralna Peleryna", 5 + tier_index // 2),
            ("bracers", "Astralne Karwasze", 5 + tier_index // 2),
            ("relic", "Astralny Relikt", 6 + tier_index // 2),
        )
        affix = stat_cycle[(tier_index - 1) % len(stat_cycle)]
        affix_amount = 5 + tier_index // 2
        for slot, label, defense in defs:
            item_id = f"astral_t{tier_index}_{slot}"
            _catalog_mut.catalog_assign({
                "name": f"{label} Kręgu {tier_index}",
                "type": "armor",
                "slot": slot,
                "defense": defense,
                "price": None,
                "desc": (
                    f"Ekwipunek Wieży Astralnej. Krąg {tier_index}. "
                    f"Obrona +{defense}. "
                    f"Bonus: {CRYPT_AFFIXES[affix]} +{affix_amount}."
                ),
                "rarity": "epic",
                "rarity_name": "Astralny",
                "affix": affix,
                "affix_amount": affix_amount,
                "astral_set_tier": tier_index,
            }, 'ITEMS', ITEMS, (item_id,))

    for floor in range(ASTRAL_MIN_FLOOR, ASTRAL_MAX_FLOOR + 1):
        room_id = astral_floor_id(floor)
        exits = {}
        if floor == ASTRAL_MIN_FLOOR:
            exits["down"] = "astral_gate"
        else:
            exits["down"] = astral_floor_id(floor - 1)
        if floor < ASTRAL_MAX_FLOOR:
            exits["up"] = astral_floor_id(floor + 1)

        if floor in ASTRAL_BOSS_FLOORS:
            note = " Strażnik tego poziomu blokuje drogę w górę; Wieża ciągnie się dalej po jego pokonaniu."
        else:
            note = ""

        _catalog_mut.catalog_assign({
            "zone": "Wieża Astralna",
            "name": f"Wieża Astralna, poziom {floor}",
            "desc": (
                f"Poziom {floor}. Przez przezroczyste ściany widać gwiazdy, "
                f"mgławice i odległe pasma światła.{note}"
            ),
            "exits": exits,
        }, 'ROOMS', ROOMS, (room_id,))

        tier_index = min(
            11,
            (floor - ASTRAL_MIN_FLOOR) // 10 + 1,
        )
        gear = [
            f"astral_t{tier_index}_{slot}"
            for slot in CLASS_EQUIPMENT_SLOT_DEFS
        ]

        regular_id = f"astral_floor_mob_{floor}"
        regular_name = ASTRAL_REGULAR_NAMES[
            (floor - ASTRAL_MIN_FLOOR) % len(ASTRAL_REGULAR_NAMES)
        ]
        relative = floor - ASTRAL_MIN_FLOOR
        _catalog_mut.catalog_assign({
            "name": f"{regular_name}, poziom {floor}",
            "max_hp": 1050 + relative * 12,
            "damage": 42 + relative // 3,
            "damage_type": "magic" if floor % 2 else "physical",
            "silver": 120 + relative * 2,
            "gold": 1 + relative // 35,
            "mithril": 0,
            "stat_reward": 230 + relative * 3,
            "class_xp_reward": 7000 + relative * 100,
            "soul_reward": 1250 + relative * 14,
            "drops": {
                "soul_shard": min(0.45, 0.20 + relative * 0.002),
            },
            "quest_target": None,
            "astral_floor": floor,
            "corpse_equipment_pool": gear,
            "corpse_equipment_guaranteed": 1,
        }, 'MOB_TEMPLATES', MOB_TEMPLATES, (regular_id,))
        MOB_SPAWNS.append((room_id, regular_id))

        if floor in ASTRAL_BOSS_FLOORS:
            boss_id = f"astral_boss_{floor}"
            pool = list(gear)
            relic_id = ASTRAL_BOSS_RELICS[floor][0]
            _catalog_mut.catalog_assign({
                "name": ASTRAL_BOSS_NAMES[floor],
                "max_hp": 3300 + relative * 32,
                "damage": 72 + relative // 2,
                "damage_type": "magic" if floor % 20 == 0 else "physical",
                "silver": 900 + relative * 14,
                "gold": 5 + relative // 20,
                "mithril": 0,
                "stat_reward": 900 + relative * 8,
                "class_xp_reward": 15000 + relative * 220,
                "soul_reward": 2400 + relative * 28,
                "drops": {
                    "soul_shard": 1.0,
                    "soul_elixir": min(0.70, 0.30 + relative * 0.003),
                    relic_id: 1.0 if floor == ASTRAL_MAX_FLOOR else 0.45,
                },
                "quest_target": None,
                "astral_floor": floor,
                "astral_boss": True,
                "boss_mechanic": ASTRAL_BOSS_MECHANICS[floor],
                "boss_mechanic_text": ASTRAL_BOSS_MECHANIC_TEXT[floor],
                "corpse_equipment_pool": pool,
                "corpse_equipment_guaranteed": 3,
            }, 'MOB_TEMPLATES', MOB_TEMPLATES, (boss_id,))
            MOB_SPAWNS.append((room_id, boss_id))


def build_crypt_200_floors():
    _catalog_mut.catalog_assign(crypt_floor_id(1), 'ROOMS', ROOMS, ("crypt_hall", "exits", "down"))
    _catalog_mut.catalog_assign("crypt_depths", 'ROOMS', ROOMS, ("crypt_hall", "exits", "east"))
    _catalog_mut.catalog_assign({"west": "crypt_hall"}, 'ROOMS', ROOMS, ("crypt_depths", "exits"))

    crypt_slot_specs = {
        "head": ("Hełm Krypty", 1),
        "body": ("Napierśnik Krypty", 3),
        "hands": ("Rękawice Krypty", 0),
        "legs": ("Nogawice Krypty", 2),
        "feet": ("Buty Krypty", 0),
        "charm": ("Talizman Krypty", 0),
        "ring": ("Pierścień Krypty", 0),
        "necklace": ("Naszyjnik Krypty", 1),
        "earring": ("Kolczyk Krypty", 0),
        "shoulders": ("Naramienniki Krypty", 2),
        "belt": ("Pas Krypty", 1),
        "cloak": ("Peleryna Krypty", 0),
        "bracers": ("Karwasze Krypty", 0),
        "relic": ("Relikt Krypty", 1),
    }
    for tier in range(1, 41):
        for slot, (label, defense_delta) in crypt_slot_specs.items():
            defense = max(1, 1 + tier // 2 + defense_delta)
            if slot == "body":
                defense = max(defense, 2 + tier)
            item_id=f"crypt_t{tier}_{slot}"
            _catalog_mut.catalog_assign({
                "name":f"{label} Tier {tier}","type":"armor","slot":slot,
                "defense":defense,"price":None,
                "desc":f"Ekwipunek z Krypty. Tier {tier}. Obrona +{defense}.",
            }, 'ITEMS', ITEMS, (item_id,))


    for floor in range(1, CRYPT_MAX_FLOOR+1):
        room_id=crypt_floor_id(floor); exits={}
        exits["up"]="crypt_hall" if floor==1 else crypt_floor_id(floor-1)
        exits["down"]=crypt_floor_id(floor+1)
        if is_crypt_boss_floor(floor):
            note=" Przy pierwszym przejściu boss tego progu blokuje zejście do chwili pokonania."
        else:
            note=""
        _catalog_mut.catalog_assign({
            "zone":"Krypta Nieskończona","name":f"Krypta, piętro {floor}",
            "desc":(
                f"Piętro {floor}. Próg trudności {crypt_depth_step(floor)}. "
                f"Kamienne korytarze stają się coraz bardziej niebezpieczne.{note}"
            ),
            "exits":exits,
        }, 'ROOMS', ROOMS, (room_id,))
        tier=min(40,(floor-1)//10+1)
        gear=[f"crypt_t{tier}_{x}" for x in CLASS_EQUIPMENT_SLOT_DEFS]
        tid=f"crypt_floor_mob_{floor}"
        name=CRYPT_REGULAR_NAMES[(floor-1)%len(CRYPT_REGULAR_NAMES)]
        depth_mult=crypt_depth_multiplier(floor)
        _catalog_mut.catalog_assign({
            "name":f"{name}, piętro {floor}",
            "max_hp":max(1,int(round((70+floor*9)*depth_mult))),
            "damage":max(1,int(round((6+floor//3)*depth_mult))),
            "damage_type":"magic" if (floor%3==0 or floor%4==0) else "physical",
            "silver":8+floor,"gold":0,"mithril":0,
            "stat_reward":max(1,int(round((20+floor*2)*depth_mult))),
            "class_xp_reward":max(1,int(round((450+floor*60)*depth_mult))),
            "soul_reward":max(1,int(round((100+floor*10)*depth_mult))),
            "drops":{"soul_shard":1.0},"quest_target":None,
            "crypt_floor":floor,"corpse_equipment_pool":gear,"corpse_equipment_guaranteed":1,
        }, 'MOB_TEMPLATES', MOB_TEMPLATES, (tid,))
        MOB_SPAWNS.append((room_id,tid))
        if is_crypt_boss_floor(floor):
            bid=f"crypt_boss_{floor}"; pool=list(gear)
            _catalog_mut.catalog_assign({
                "name":CRYPT_BOSS_NAMES[floor],"max_hp":350+floor*25,
                "damage":max(1,int(round((16+floor//2)*depth_mult))),
                "damage_type":"magic" if floor%20==0 else "physical",
                "silver":300+floor*12,"gold":0,"mithril":0,
                "stat_reward":max(1,int(round((350+floor*6)*depth_mult))),
                "class_xp_reward":max(1,int(round((3000+floor*160)*depth_mult))),
                "soul_reward":max(1,int(round((600+floor*20)*depth_mult))),
                "drops":{
                    "soul_shard":1.0,
                    "soul_elixir":min(0.50,0.15+floor*0.003),
                    BOSS_RELICS[floor][0]: (
                        1.0 if floor == CRYPT_MAX_FLOOR else 0.45
                    ),
                },
                "quest_target":CRYPT_TRIAL_TARGETS.get(floor),
                "crypt_floor":floor,
                "crypt_boss":True,
                "boss_mechanic":CRYPT_BOSS_MECHANICS[floor],
                "boss_mechanic_text":CRYPT_BOSS_MECHANIC_TEXT[floor],
                "corpse_equipment_pool":pool,"corpse_equipment_guaranteed":3,
            }, 'MOB_TEMPLATES', MOB_TEMPLATES, (bid,))
            MOB_SPAWNS.append((room_id,bid))

def build_mythic_endgame():
    # Mythic Crypt opens from the old Crypt depths after floor 200 completion.
    _catalog_mut.catalog_assign("mythic_crypt_gate", 'ROOMS', ROOMS, ("crypt_depths", "exits", "east"))
    _catalog_mut.catalog_assign({
        "zone": "Mityczna Krypta",
        "name": "Brama Mitycznej Krypty",
        "desc": (
            "Czarna brama rezonuje mityczną energią Krypty. "
            "Wejście nie ma wymogu Soul Level, ale już pierwsze piętro jest bardzo trudne."
        ),
        "exits": {
            "west": "crypt_depths",
            "down": mythic_crypt_floor_id(1),
        },
    }, 'ROOMS', ROOMS, ("mythic_crypt_gate",))

    # Mythic Astral opens from the ordinary Astral Gate.
    _catalog_mut.catalog_assign("mythic_astral_gate", 'ROOMS', ROOMS, ("astral_gate", "exits", "east"))
    _catalog_mut.catalog_assign({
        "zone": "Mityczna Wieża Astralna",
        "name": "Brama Mitycznej Wieży Astralnej",
        "desc": (
            "Pęknięcie gwiezdnej przestrzeni prowadzi do trudniejszej "
            "wersji Wieży. Wejście wymaga Soul Level 100."
        ),
        "exits": {
            "west": "astral_gate",
            "up": mythic_astral_floor_id(1),
        },
    }, 'ROOMS', ROOMS, ("mythic_astral_gate",))

    crypt_names = (
        "Mityczny Kościany Rycerz",
        "Mityczny Upiór",
        "Mityczny Żniwiarz Grobowca",
        "Mityczny Strażnik Otchłani",
    )
    astral_names = (
        "Mityczny Astralny Strażnik",
        "Mityczny Rycerz Konstelacji",
        "Mityczne Widmo Nebuli",
        "Mityczny Herold Gwiezdnej Burzy",
    )

    for floor in range(MYTHIC_MIN_FLOOR, MYTHIC_MAX_FLOOR + 1):
        # Mythic Crypt
        c_room = mythic_crypt_floor_id(floor)
        c_exits = {
            "up": (
                "mythic_crypt_gate"
                if floor == 1
                else mythic_crypt_floor_id(floor - 1)
            )
        }
        c_exits["down"] = mythic_crypt_floor_id(floor + 1)
        c_note = (
            " Przy pierwszym przejściu mityczny boss blokuje zejście do chwili pokonania."
            if is_mythic_crypt_boss_floor(floor)
            else ""
        )
        _catalog_mut.catalog_assign({
            "zone": "Mityczna Krypta",
            "name": f"Mityczna Krypta, piętro {floor}",
            "desc": (
                f"Mityczne piętro {floor}. Próg trudności {crypt_depth_step(floor)}. "
                f"Ściany są przesycone ciemną energią.{c_note}"
            ),
            "exits": c_exits,
        }, 'ROOMS', ROOMS, (c_room,))

        c_regular = f"mythic_crypt_mob_{floor}"
        c_depth_mult = crypt_depth_multiplier(floor)
        _catalog_mut.catalog_assign({
            "name": (
                f"{crypt_names[(floor - 1) % len(crypt_names)]}, "
                f"piętro {floor}"
            ),
            "max_hp": max(1, int(round((4000 + floor * 100) * c_depth_mult))),
            "damage": max(1, int(round((120 + floor) * c_depth_mult))),
            "damage_type": "magic" if floor % 2 else "physical",
            "silver": 800 + floor * 8,
            "gold": 5 + floor // 20,
            "mithril": 0,
            "stat_reward": max(1, int(round((800 + floor * 5) * c_depth_mult))),
            "class_xp_reward": max(1, int(round((20000 + floor * 300) * c_depth_mult))),
            "soul_reward": max(1, int(round((4000 + floor * 25) * c_depth_mult))),
            "drops": {"soul_shard": 1.0},
            "quest_target": None,
            "mythic_crypt_floor": floor,
            "corpse_equipment_pool": [
                f"crypt_t{min(40, 20 + (floor - 1) // 10)}_{slot}"
                for slot in CLASS_EQUIPMENT_SLOT_DEFS
            ],
            "corpse_equipment_guaranteed": 1,
        }, 'MOB_TEMPLATES', MOB_TEMPLATES, (c_regular,))
        MOB_SPAWNS.append((c_room, c_regular))

        if is_mythic_crypt_boss_floor(floor):
            c_boss = f"mythic_crypt_boss_{floor}"
            _catalog_mut.catalog_assign({
                "name": f"Mityczny Władca Krypty, piętro {floor}",
                "max_hp": 100000,
                "damage": max(1, int(round((240 + floor * 2) * c_depth_mult))),
                "damage_type": "magic" if floor % 20 else "physical",
                "silver": 8000 + floor * 40,
                "gold": 60 + floor // 5,
                "mithril": 1 if floor >= 100 else 0,
                "stat_reward": max(1, int(round((3000 + floor * 12) * c_depth_mult))),
                "class_xp_reward": max(1, int(round((60000 + floor * 700) * c_depth_mult))),
                "soul_reward": max(1, int(round((9000 + floor * 50) * c_depth_mult))),
                "drops": {
                    "soul_shard": 1.0,
                    "soul_elixir": 0.70,
                },
                "quest_target": None,
                "mythic_crypt_floor": floor,
                "mythic_crypt_boss": True,
                "boss_mechanic": "two_hundred_lord",
                "boss_mechanic_text": (
                    "Mityczna Bariera, druga faza i silny "
                    "magiczny kontratak co trzecią odpowiedź."
                ),
                "corpse_equipment_pool": [
                    f"crypt_t{min(40, 20 + (floor - 1) // 10)}_{slot}"
                    for slot in CLASS_EQUIPMENT_SLOT_DEFS
                ],
                "corpse_equipment_guaranteed": 3,
            }, 'MOB_TEMPLATES', MOB_TEMPLATES, (c_boss,))
            MOB_SPAWNS.append((c_room, c_boss))

        # Mythic Astral Tower
        a_room = mythic_astral_floor_id(floor)
        a_exits = {
            "down": (
                "mythic_astral_gate"
                if floor == 1
                else mythic_astral_floor_id(floor - 1)
            )
        }
        if floor < MYTHIC_MAX_FLOOR:
            a_exits["up"] = mythic_astral_floor_id(floor + 1)
        a_note = (
            " Przy pierwszym przejściu mityczny boss blokuje drogę w górę; po pokonaniu próg zostaje odblokowany na stałe."
            if floor in MYTHIC_BOSS_FLOORS
            else ""
        )
        _catalog_mut.catalog_assign({
            "zone": "Mityczna Wieża Astralna",
            "name": f"Mityczna Wieża Astralna, poziom {floor}",
            "desc": (
                f"Mityczny poziom {floor}. Pierwsze 200 poziomów to ręcznie przygotowana część Wieży. "
                f"Gwiazdy wydają się nienaturalnie blisko.{a_note}"
            ),
            "exits": a_exits,
        }, 'ROOMS', ROOMS, (a_room,))

        a_regular = f"mythic_astral_mob_{floor}"
        _catalog_mut.catalog_assign({
            "name": (
                f"{astral_names[(floor - 1) % len(astral_names)]}, "
                f"poziom {floor}"
            ),
            "max_hp": 5000 + floor * 120,
            "damage": 145 + floor,
            "damage_type": "magic" if floor % 2 else "physical",
            "silver": 1000 + floor * 10,
            "gold": 7 + floor // 18,
            "mithril": 0,
            "stat_reward": 950 + floor * 6,
            "class_xp_reward": 25000 + floor * 350,
            "soul_reward": 5000 + floor * 30,
            "drops": {"soul_shard": 0.65},
            "quest_target": None,
            "mythic_astral_floor": floor,
            "corpse_equipment_pool": [
                f"astral_t11_{slot}"
                for slot in CLASS_EQUIPMENT_SLOT_DEFS
            ],
            "corpse_equipment_guaranteed": 1,
        }, 'MOB_TEMPLATES', MOB_TEMPLATES, (a_regular,))
        MOB_SPAWNS.append((a_room, a_regular))

        if floor in MYTHIC_BOSS_FLOORS:
            a_boss = f"mythic_astral_boss_{floor}"
            _catalog_mut.catalog_assign({
                "name": f"Mityczny Suweren Astralny, poziom {floor}",
                "max_hp": 120000,
                "damage": 280 + floor * 2,
                "damage_type": "magic",
                "silver": 10000 + floor * 45,
                "gold": 80 + floor // 4,
                "mithril": 1 if floor >= 80 else 0,
                "stat_reward": 3500 + floor * 14,
                "class_xp_reward": 75000 + floor * 800,
                "soul_reward": 11000 + floor * 55,
                "drops": {
                    "soul_shard": 1.0,
                    "soul_elixir": 0.80,
                },
                "quest_target": None,
                "mythic_astral_floor": floor,
                "mythic_astral_boss": True,
                "boss_mechanic": "astral_sovereign",
                "boss_mechanic_text": (
                    "Mityczna Bariera Suwerena, druga faza i "
                    "Astralne Załamanie."
                ),
                "corpse_equipment_pool": [
                    f"astral_t11_{slot}"
                    for slot in CLASS_EQUIPMENT_SLOT_DEFS
                ],
                "corpse_equipment_guaranteed": 3,
            }, 'MOB_TEMPLATES', MOB_TEMPLATES, (a_boss,))
            MOB_SPAWNS.append((a_room, a_boss))


def build_profession_dungeons():
    # v0.25.1: istnieje tylko jedna aktywna kopalnia — Kopalnia Głębinowa.
    # Dawna Kopalnia Kryształów pozostaje połączona wyłącznie jako zwykły
    # obszar eksploracyjny "Kryształowe Groty" bez możliwości wydobycia.
    _catalog_mut.catalog_assign(profession_dungeon_room_id("crystal_mine", 1), 'ROOMS', ROOMS, ("crystal_chamber", "exits", "east"))
    # 2. Zatopiona Grota - fishing
    _catalog_mut.catalog_assign(profession_dungeon_room_id("sunken_grotto", 1), 'ROOMS', ROOMS, ("sea_pier", "exits", "down"))
    # 3. Pradawny Las - woodcutting
    _catalog_mut.catalog_assign(profession_dungeon_room_id("ancient_forest", 1), 'ROOMS', ROOMS, ("deep_grove", "exits", "south"))
    # 4. Ogród Alchemika - herbalism
    _catalog_mut.catalog_assign(profession_dungeon_room_id("alchemy_garden", 1), 'ROOMS', ROOMS, ("herbalist_hut", "exits", "east"))

    for floor in range(1, PROF_DUNGEON_MAX_FLOOR + 1):
        required = profession_dungeon_required_tool_level(floor)

        # Crystal Mine, down = deeper.
        rid = profession_dungeon_room_id("crystal_mine", floor)
        exits = {
            "up": (
                "crystal_chamber"
                if floor == 1
                else profession_dungeon_room_id(
                    "crystal_mine", floor - 1
                )
            )
        }
        if floor < PROF_DUNGEON_MAX_FLOOR:
            exits["down"] = profession_dungeon_room_id(
                "crystal_mine", floor + 1
            )
        _catalog_mut.catalog_assign({
            "zone": "Kryształowe Groty",
            "name": f"Kryształowe Groty, komora {floor}",
            "desc": (
                f"Kryształowa komora eksploracyjna {floor}. "
                "Nie prowadzi się tu wydobycia. Wszystkie rudy i Górnictwo są w Kopalni Głębinowej."
            ),
            "exits": exits,
        }, 'ROOMS', ROOMS, (rid,))
        # Brak MINING_ROOMS: to nie jest już aktywna kopalnia.

        # Sunken Grotto, down = deeper.
        rid = profession_dungeon_room_id("sunken_grotto", floor)
        exits = {
            "up": (
                "sea_pier"
                if floor == 1
                else profession_dungeon_room_id(
                    "sunken_grotto", floor - 1
                )
            )
        }
        if floor < PROF_DUNGEON_MAX_FLOOR:
            exits["down"] = profession_dungeon_room_id(
                "sunken_grotto", floor + 1
            )
        _catalog_mut.catalog_assign({
            "zone": "Loch Profesyjny - Zatopiona Grota",
            "name": f"Zatopiona Grota, głębokość {floor}",
            "desc": (
                f"Podwodne łowisko {floor}. Pierwsze 20 poziomów to ręcznie przygotowana część, a dalsza głębokość nie ma limitu. "
                f"Wymagane Wędkarstwo level {required}. "
                "Lepsza Wędka odblokowuje lepsze ryby i bonusy jakości. "
                "Niższe komory prowadzą do coraz rzadszych ryb."
            ),
            "exits": exits,
        }, 'ROOMS', ROOMS, (rid,))
        if floor <= 10:
            SEA_FISHING_ROOMS.add(rid)
        else:
            OCEAN_FISHING_ROOMS.add(rid)
        FISHING_ROOMS.add(rid)
        MARINE_FISHING_ROOMS.add(rid)

        # Ancient Forest, south = deeper.
        rid = profession_dungeon_room_id("ancient_forest", floor)
        exits = {
            "north": (
                "deep_grove"
                if floor == 1
                else profession_dungeon_room_id(
                    "ancient_forest", floor - 1
                )
            )
        }
        if floor < PROF_DUNGEON_MAX_FLOOR:
            exits["south"] = profession_dungeon_room_id(
                "ancient_forest", floor + 1
            )
        _catalog_mut.catalog_assign({
            "zone": "Loch Profesyjny - Pradawny Las",
            "name": f"Pradawny Las, ostęp {floor}",
            "desc": (
                f"Pradawny ostęp {floor}. Pierwsze 20 ostępów to ręcznie przygotowana część, a dalsza głębokość nie ma limitu. "
                f"Wymagane Drwalstwo level {required}. "
                "Lepsza Piła odblokowuje lepsze drewno i bonusy jakości. "
                "Głębsze ostępy dają dostęp do rzadszego drewna."
            ),
            "exits": exits,
        }, 'ROOMS', ROOMS, (rid,))
        WOODCUTTING_ROOMS.add(rid)

        # Alchemy Garden, east = deeper.
        rid = profession_dungeon_room_id("alchemy_garden", floor)
        exits = {
            "west": (
                "herbalist_hut"
                if floor == 1
                else profession_dungeon_room_id(
                    "alchemy_garden", floor - 1
                )
            )
        }
        if floor < PROF_DUNGEON_MAX_FLOOR:
            exits["east"] = profession_dungeon_room_id(
                "alchemy_garden", floor + 1
            )
        _catalog_mut.catalog_assign({
            "zone": "Loch Profesyjny - Ogród Alchemika",
            "name": f"Ogród Alchemika, sektor {floor}",
            "desc": (
                f"Alchemiczny sektor {floor}. Pierwsze 20 sektorów to ręcznie przygotowana część, a dalsza głębokość nie ma limitu. "
                f"Wymagane Zielarstwo level {required}. "
                "Lepszy Sierp odblokowuje lepsze zioła i bonusy jakości. "
                "Głębsze sektory zawierają coraz rzadsze rośliny."
            ),
            "exits": exits,
        }, 'ROOMS', ROOMS, (rid,))
        HERBALISM_ROOMS.add(rid)


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

def build_mountain_region_and_herb_meadows():
    # -----------------------------
    # Wioska Górska i góry
    # -----------------------------
    _catalog_mut.catalog_assign("mountain_pass", 'ROOMS', ROOMS, ("hill", "exits", "east"))

    _catalog_mut.catalog_assign({
        "zone": "Góry",
        "name": "Górska Przełęcz",
        "desc": (
            "Wąska kamienna przełęcz pnie się między wysokimi skałami. "
            "Na wschodzie widać dym z kominów Wioski Górskiej."
        ),
        "exits": {
            "west": "hill",
            "east": "mountain_village",
        },
    }, 'ROOMS', ROOMS, ("mountain_pass",))

    _catalog_mut.catalog_assign({
        "zone": "Wioska Górska",
        "name": "Plac Wioski Górskiej",
        "desc": (
            "Kamienne domy stoją wokół niewielkiego placu. "
            "Mieszkańcy mówią o trollach wychodzących z jaskini "
            "na południowym stoku."
        ),
        "exits": {
            "west": "mountain_pass",
            "north": "mountain_guard_house",
            "east": "mountain_inn",
            "south": "mountain_troll_trail",
        },
    }, 'ROOMS', ROOMS, ("mountain_village",))

    _catalog_mut.catalog_assign({
        "zone": "Wioska Górska",
        "name": "Dom Straży Górskiej",
        "desc": (
            "Prosty kamienny budynek służy strażnikom wioski. "
            "Na stole leżą mapy szlaków prowadzących do Jaskini Trolli."
        ),
        "exits": {"south": "mountain_village"},
    }, 'ROOMS', ROOMS, ("mountain_guard_house",))

    _catalog_mut.catalog_assign({
        "zone": "Wioska Górska",
        "name": "Górska Gospoda",
        "desc": (
            "Ciepła gospoda daje schronienie przed górskim wiatrem. "
            "Podróżnicy opowiadają o potężnym Królu Trolli."
        ),
        "exits": {"west": "mountain_village"},
    }, 'ROOMS', ROOMS, ("mountain_inn",))

    _catalog_mut.catalog_assign({
        "zone": "Góry",
        "name": "Szlak Trolli",
        "desc": (
            "Ścieżka prowadzi między głazami pełnymi wielkich śladów. "
            "Na południu czernieje wejście do Jaskini Trolli."
        ),
        "exits": {
            "north": "mountain_village",
            "south": "troll_cave_entrance",
        },
    }, 'ROOMS', ROOMS, ("mountain_troll_trail",))

    _catalog_mut.catalog_assign({
        "zone": "Jaskinia Trolli",
        "name": "Wejście do Jaskini Trolli",
        "desc": (
            "Szerokie wejście prowadzi w głąb góry. "
            "W powietrzu czuć wilgoć i dym z prymitywnych palenisk."
        ),
        "exits": {
            "north": "mountain_troll_trail",
            "down": "troll_cave_1",
        },
    }, 'ROOMS', ROOMS, ("troll_cave_entrance",))

    _catalog_mut.catalog_assign({
        "zone": "Jaskinia Trolli",
        "name": "Jaskinia Trolli - Kamienna Sala",
        "desc": (
            "Wielka komora jest zasłana połamanymi kośćmi i głazami. "
            "Trolle urządziły tu pierwszy posterunek."
        ),
        "exits": {
            "up": "troll_cave_entrance",
            "east": "troll_cave_2",
        },
    }, 'ROOMS', ROOMS, ("troll_cave_1",))

    _catalog_mut.catalog_assign({
        "zone": "Jaskinia Trolli",
        "name": "Jaskinia Trolli - Wilgotny Tunel",
        "desc": (
            "Woda ścieka po ścianach, a ciężkie kroki odbijają się echem."
        ),
        "exits": {
            "west": "troll_cave_1",
            "east": "troll_cave_3",
        },
    }, 'ROOMS', ROOMS, ("troll_cave_2",))

    _catalog_mut.catalog_assign({
        "zone": "Jaskinia Trolli",
        "name": "Jaskinia Trolli - Sala Głazów",
        "desc": (
            "Ogromne głazy służą trollom za stoły i broń. "
            "Na wschodzie znajduje się legowisko ich przywódcy."
        ),
        "exits": {
            "west": "troll_cave_2",
            "east": "troll_king_den",
        },
    }, 'ROOMS', ROOMS, ("troll_cave_3",))

    _catalog_mut.catalog_assign({
        "zone": "Jaskinia Trolli",
        "name": "Legowisko Króla Trolli",
        "desc": (
            "Największa komora jaskini. Pośrodku stoi kamienny tron "
            "otoczony stosami kości i zdobytego żelaza."
        ),
        "exits": {"west": "troll_cave_3"},
    }, 'ROOMS', ROOMS, ("troll_king_den",))

    # -----------------------------
    # NPC + quest na trolle
    # -----------------------------
    _catalog_mut.catalog_assign({
        "name": "Plaga Trolli",
        "giver": "Strażnik Górski Eryk",
        "kind": "kill",
        "target": "mountain_troll",
        "needed": 12,
        "description": (
            "Pokonaj 12 trolli w Jaskini Trolli i wróć do "
            "Strażnika Górskiego Eryka w Wiosce Górskiej."
        ),
        "reward_stat_progress": 280,
        "reward_silver": 750,
        "reward_gold": 2,
        "reward_mithril": 0,
        "reward_items": {
            "healing_potion": 3,
            "soul_shard": 1,
        },
        "repeatable": False,
    }, 'QUESTS', QUESTS, ("mountain_troll_hunt",))

    _catalog_mut.catalog_assign({
        "name": "Strażnik Górski Eryk",
        "room": "mountain_guard_house",
        "dialogue": (
            "Trolle z południowej jaskini coraz częściej schodzą "
            "pod samą wioskę. Potrzebujemy kogoś, kto przerzedzi ich szeregi."
        ),
        "quest": "mountain_troll_hunt",
    }, 'NPCS', NPCS, ("mountain_guard_eryk",))

    # -----------------------------
    # Trolle i boss
    # Wartości bazowe są potem mnożone przez globalne x2 HP.
    # -----------------------------
    _catalog_mut.catalog_assign({
        "name": "Kieł Króla Trolli",
        "type": "armor",
        "slot": "charm",
        "defense": 7,
        "price": None,
        "desc": (
            "Unikalne trofeum Króla Trolli. Obrona +7. "
            "Bonus: Kondycja +6."
        ),
        "rarity": "unique",
        "rarity_name": "Unikalny",
        "affix": "constitution",
        "affix_amount": 6,
    }, 'ITEMS', ITEMS, ("troll_king_tusk",))

    _catalog_mut.catalog_assign({
        "name": "Górski Troll",
        "max_hp": 300,
        "damage": 24,
        "damage_type": "physical",
        "silver": 90,
        "gold": 1,
        "mithril": 0,
        "stat_reward": 85,
        "class_xp_reward": 1400,
        "soul_reward": 360,
        "drops": {
            "healing_potion": 0.08,
            "iron_ore": 0.12,
        },
        "quest_target": "mountain_troll",
        "corpse_equipment_pool": [
            "iron_guard", "iron_gauntlets", "iron_boots"
        ],
        "corpse_equipment_guaranteed": 1,
    }, 'MOB_TEMPLATES', MOB_TEMPLATES, ("mountain_troll",))

    _catalog_mut.catalog_assign({
        "name": "Troll Osiłek",
        "max_hp": 420,
        "damage": 31,
        "damage_type": "physical",
        "silver": 130,
        "gold": 1,
        "mithril": 0,
        "stat_reward": 115,
        "class_xp_reward": 1900,
        "soul_reward": 470,
        "drops": {
            "healing_potion": 0.12,
            "silver_ore": 0.10,
        },
        "quest_target": "mountain_troll",
        "corpse_equipment_pool": [
            "iron_guard", "iron_leggings",
            "iron_gauntlets", "iron_boots"
        ],
        "corpse_equipment_guaranteed": 1,
    }, 'MOB_TEMPLATES', MOB_TEMPLATES, ("troll_brute",))

    _catalog_mut.catalog_assign({
        "name": "Troll Szaman",
        "max_hp": 360,
        "damage": 29,
        "damage_type": "magic",
        "silver": 120,
        "gold": 2,
        "mithril": 0,
        "stat_reward": 110,
        "class_xp_reward": 2000,
        "soul_reward": 500,
        "drops": {
            "mana_potion": 0.15,
            "soul_shard": 0.15,
        },
        "quest_target": "mountain_troll",
        "corpse_equipment_pool": [
            "forge_charm", "lucky_charm"
        ],
        "corpse_equipment_guaranteed": 1,
    }, 'MOB_TEMPLATES', MOB_TEMPLATES, ("troll_shaman",))

    _catalog_mut.catalog_assign({
        "name": "Król Trolli Grum",
        "max_hp": 900,
        "damage": 48,
        "damage_type": "physical",
        "silver": 1200,
        "gold": 6,
        "mithril": 0,
        "stat_reward": 420,
        "class_xp_reward": 6500,
        "soul_reward": 1500,
        "drops": {
            "soul_elixir": 0.25,
            "troll_king_tusk": 0.45,
        },
        "quest_target": "mountain_troll",
        "boss_mechanic": "troll_king",
        "boss_mechanic_text": (
            "Król Trolli używa ciężkich fizycznych uderzeń. "
            "Poniżej połowy HP staje się wyraźnie groźniejszy."
        ),
        "world_boss": True,
        "corpse_equipment_pool": [
            "iron_helmet", "iron_guard", "iron_gauntlets",
            "iron_leggings", "iron_boots", "forge_charm"
        ],
        "corpse_equipment_guaranteed": 2,
    }, 'MOB_TEMPLATES', MOB_TEMPLATES, ("troll_king",))

    MOB_SPAWNS.extend([
        ("mountain_troll_trail", "mountain_troll"),
        ("troll_cave_1", "mountain_troll"),
        ("troll_cave_1", "mountain_troll"),
        ("troll_cave_2", "mountain_troll"),
        ("troll_cave_2", "troll_brute"),
        ("troll_cave_3", "mountain_troll"),
        ("troll_cave_3", "troll_brute"),
        ("troll_cave_3", "troll_shaman"),
        ("troll_king_den", "troll_king"),
    ])

    # -----------------------------
    # Osobne łąki pod konkretne zioła
    # -----------------------------
    _catalog_mut.catalog_assign("herb_meadow_hub", 'ROOMS', ROOMS, ("flower_meadow", "exits", "north"))

    _catalog_mut.catalog_assign({
        "zone": "Łąki Zielarskie",
        "name": "Rozdroże Łąk Zielarskich",
        "desc": (
            "Kilka wyraźnie oddzielonych łąk ciągnie się w różnych "
            "kierunkach. Każda jest znana z jednego dominującego zioła."
        ),
        "exits": {
            "south": "flower_meadow",
            "north": "chamomile_meadow",
            "east": "lavender_meadow",
            "west": "yarrow_meadow",
        },
    }, 'ROOMS', ROOMS, ("herb_meadow_hub",))

    _catalog_mut.catalog_assign({
        "zone": "Łąki Zielarskie",
        "name": "Łąka Rumianku",
        "desc": "Białe kwiaty rumianku pokrywają niemal całą łąkę.",
        "exits": {
            "south": "herb_meadow_hub",
            "north": "nettle_meadow",
        },
    }, 'ROOMS', ROOMS, ("chamomile_meadow",))
    _catalog_mut.catalog_assign({
        "zone": "Łąki Zielarskie",
        "name": "Łąka Pokrzywy",
        "desc": "Gęste kępy pokrzywy rosną między niskimi kamieniami.",
        "exits": {
            "south": "chamomile_meadow",
            "north": "lemon_balm_meadow",
        },
    }, 'ROOMS', ROOMS, ("nettle_meadow",))
    _catalog_mut.catalog_assign({
        "zone": "Łąki Zielarskie",
        "name": "Łąka Melisy",
        "desc": "Powietrze wypełnia łagodny cytrynowy zapach melisy.",
        "exits": {"south": "nettle_meadow"},
    }, 'ROOMS', ROOMS, ("lemon_balm_meadow",))

    _catalog_mut.catalog_assign({
        "zone": "Łąki Zielarskie",
        "name": "Łąka Lawendy",
        "desc": "Fioletowe pasy lawendy ciągną się po łagodnym zboczu.",
        "exits": {
            "west": "herb_meadow_hub",
            "east": "sage_meadow",
        },
    }, 'ROOMS', ROOMS, ("lavender_meadow",))
    _catalog_mut.catalog_assign({
        "zone": "Łąki Zielarskie",
        "name": "Łąka Szałwii",
        "desc": "Srebrzystozielone liście szałwii rosną w suchszej części łąk.",
        "exits": {
            "west": "lavender_meadow",
            "east": "valerian_meadow",
        },
    }, 'ROOMS', ROOMS, ("sage_meadow",))
    _catalog_mut.catalog_assign({
        "zone": "Łąki Zielarskie",
        "name": "Łąka Waleriany",
        "desc": "Wysokie łodygi waleriany rosną w spokojnej kotlinie.",
        "exits": {"west": "sage_meadow"},
    }, 'ROOMS', ROOMS, ("valerian_meadow",))

    _catalog_mut.catalog_assign({
        "zone": "Łąki Zielarskie",
        "name": "Łąka Krwawnika",
        "desc": "Drobne białe kwiaty krwawnika tworzą szerokie skupiska.",
        "exits": {
            "east": "herb_meadow_hub",
            "west": "ginseng_meadow",
        },
    }, 'ROOMS', ROOMS, ("yarrow_meadow",))
    _catalog_mut.catalog_assign({
        "zone": "Łąki Zielarskie",
        "name": "Łąka Żeń-szenia",
        "desc": "W zacienionych zagłębieniach rośnie dziki żeń-szeń.",
        "exits": {
            "east": "yarrow_meadow",
            "west": "moonflower_meadow",
        },
    }, 'ROOMS', ROOMS, ("ginseng_meadow",))
    _catalog_mut.catalog_assign({
        "zone": "Łąki Zielarskie",
        "name": "Łąka Księżycowego Kwiatu",
        "desc": (
            "Blade kwiaty rosną na chłodnej łące, a ich płatki "
            "lekko połyskują nawet w cieniu."
        ),
        "exits": {"east": "ginseng_meadow"},
    }, 'ROOMS', ROOMS, ("moonflower_meadow",))

    # Istniejąca Łąka Mięty jest także pełną łąką tematyczną.
    _catalog_mut.catalog_assign("Łąki Zielarskie", 'ROOMS', ROOMS, ("mint_meadow", "zone"))
    _catalog_mut.catalog_assign("Mięta dominuje na tej łące. Zbieranie tutaj daje Miętę "
        "jako podstawowy plon.", 'ROOMS', ROOMS, ("mint_meadow", "desc"))

    for room_id in HERB_SPECIFIC_MEADOWS:
        HERBALISM_ROOMS.add(room_id)
        MEADOW_HERBALISM_ROOMS.add(room_id)

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

def _register_elite_variants(base_ids):
    for base_id in tuple(base_ids):
        base_template = MOB_TEMPLATES.get(base_id)
        if not base_template:
            continue
        for affix_id, definition in ELITE_AFFIXES.items():
            elite_id = f"{base_id}__elite_{affix_id}"
            elite = dict(base_template)
            elite["name"] = (
                f"{definition['label']} "
                f"{base_template['name']}"
            )
            elite["elite_affix"] = affix_id
            elite["elite_affix_text"] = definition["text"]
            elite["elite_base_template"] = base_id
            elite["max_hp"] = max(
                1,
                int(round(
                    int(base_template["max_hp"])
                    * (1.20 if affix_id == "armored" else 1.10)
                )),
            )
            elite["damage"] = max(
                1,
                int(round(
                    int(base_template["damage"])
                    * (
                        1.15
                        if affix_id in {
                            "fire", "astral"
                        }
                        else 1.05
                    )
                )),
            )
            elite["silver"] = int(
                round(
                    int(base_template.get("silver", 0))
                    * 1.50
                )
            )
            elite["gold"] = int(
                base_template.get("gold", 0)
            ) + 1
            elite["soul_reward"] = int(
                round(
                    int(
                        base_template.get(
                            "soul_reward", 0
                        )
                    )
                    * 1.40
                )
            )
            elite["class_xp_reward"] = int(
                round(
                    int(base_template.get("class_xp_reward", max(50, int(base_template.get("stat_reward", 1)) * 10)))
                    * 1.40
                )
            )
            elite["stat_reward"] = int(round(int(base_template.get("stat_reward", 0)) * 1.25))
            elite["drops"] = dict(base_template.get("drops", {}))
            elite["drops"].setdefault("soul_shard", 0.18)
            _catalog_mut.catalog_assign(elite, 'MOB_TEMPLATES', MOB_TEMPLATES, (elite_id,))

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

