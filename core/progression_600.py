# -*- coding: utf-8 -*-
"""Soulbound v0.36.0 - Global Progression 600.

Rozszerza wszystkie główne osie, które wcześniej kończyły się na 400,
do 600 bez resetu save'ów. Nazwy historycznych zmiennych *_400 pozostają
celowo dla kompatybilności z istniejącymi modułami i ID przedmiotów.
"""

PROGRESSION_MAX_LEVEL = 600

# Generator Core jest modułem ładowanym z osadzonego źródła. Jego funkcje
# odczytują MAX_LEVEL dynamicznie, więc przełączenie tutaj rozszerza wszystkie
# krzywe bez kopiowania generatora.
generator_core_v027.MAX_LEVEL = PROGRESSION_MAX_LEVEL
generator_core_v027.GENERATOR_VERSION = "0.57.1"

# Główne osie postaci.
CHARACTER_MAX_LEVEL = PROGRESSION_MAX_LEVEL
CLASS_MASTERY_MAX_LEVEL = PROGRESSION_MAX_LEVEL
SKILL_MAX_LEVEL = PROGRESSION_MAX_LEVEL
SOUL_WEAPON_MASTERY_MAX_LEVEL = PROGRESSION_MAX_LEVEL
SOUL_MAX_LEVEL = PROGRESSION_MAX_LEVEL

# Broń Duszy: stare Tiery 1-40 zostają w tych samych miejscach, 41-60
# kontynuują co 10 poziomów od 410 do 600.
SOUL_TIER_THRESHOLDS = tuple(SOUL_TIER_THRESHOLDS[:40]) + tuple(range(410, 601, 10))
SOUL_MAX_TIER = len(SOUL_TIER_THRESHOLDS)
SOUL_TIER_POWER_BONUSES = tuple(SOUL_TIER_POWER_BONUSES[:40]) + tuple(142 + i * 2 for i in range(20))
SOUL_TIER_CLASS_BONUS_PERCENT = tuple(SOUL_TIER_CLASS_BONUS_PERCENT[:40]) + tuple(41 + i // 2 for i in range(20))
SOUL_TIER_DODGE_BONUS = tuple(SOUL_TIER_DODGE_BONUS[:40]) + (0.05,) * 20
SOUL_TIER_GUARDIAN_REDUCTION = tuple(SOUL_TIER_GUARDIAN_REDUCTION[:40]) + tuple(29 + i // 2 for i in range(20))
SOUL_TRIAL_QUEST_IDS.update({tier: f"soul_tier_{tier:02d}_trial" for tier in range(41, 61)})

# Weapon Traits 41-60: unikalne nazwy, ten sam klasowy cykl efektów.
_SOUL_TRAIT_BASE_NAMES_41_60 = (
    "Przekroczenie", "Gwiezdny Tron", "Echo Wieczności", "Serce Otchłani",
    "Korona Gwiazd", "Sąd Horyzontu", "Nieskończony Puls", "Pieczęć Kosmosu",
    "Pradawny Rezonans", "Świt Absolutu", "Droga Przeznaczenia", "Oko Wszechświata",
    "Wieczna Iskra", "Transcendentny Znak", "Głos Nieskończoności", "Ostateczny Horyzont",
    "Dusza Kosmosu", "Korona Wieczności", "Apogeum", "Absolut Duszy",
)
_SOUL_TRAIT_BASE_NAMES = tuple(_SOUL_TRAIT_BASE_NAMES) + _SOUL_TRAIT_BASE_NAMES_41_60
SOUL_TIER_TRAITS_BY_CLASS = {}
for _class_name, _profile in _SOUL_TRAIT_CLASS_PROFILES.items():
    _rows = {}
    _cycle = _profile["cycle"]
    for _tier, _base_name in enumerate(_SOUL_TRAIT_BASE_NAMES, start=1):
        _effect, _value = _cycle[(_tier - 1) % len(_cycle)]
        _rows[_tier] = {
            "name": f"{_base_name} {_profile['theme']}",
            "effect": _effect,
            "value": float(_value),
            "description": _SOUL_TRAIT_EFFECT_DESCRIPTIONS[_effect](float(_value)),
        }
    SOUL_TIER_TRAITS_BY_CLASS[_class_name] = _rows

# Profesje i narzędzia 1-600.
PROFESSION_MAX_LEVEL = PROGRESSION_MAX_LEVEL
BLACKSMITHING_MAX_LEVEL = PROGRESSION_MAX_LEVEL
JEWELCRAFTING_MAX_LEVEL = PROGRESSION_MAX_LEVEL
PROFESSION_RANK_THRESHOLDS = tuple(PROFESSION_RANK_THRESHOLDS[:23]) + tuple(range(420, 601, 20))
PROFESSION_MAX_RANK = len(PROFESSION_RANK_THRESHOLDS)
BLACKSMITHING_MAX_RANK = PROFESSION_MAX_RANK
BLACKSMITHING_RANK_THRESHOLDS = PROFESSION_RANK_THRESHOLDS

_PROFESSION_600_RANK_SUFFIXES = (
    "Mistrz Przekroczenia", "Mistrz Gwiezdnego Tronu", "Mistrz Wiecznego Echa",
    "Mistrz Otchłannego Serca", "Mistrz Korony Gwiazd", "Mistrz Horyzontu Absolutu",
    "Mistrz Kosmicznego Szlaku", "Mistrz Wieczności", "Mistrz Apogeum", "Arcymistrz Absolutu",
)
for _profession_name, _names in list(PROFESSION_RANK_NAMES.items()):
    _base = tuple(_names[:23])
    PROFESSION_RANK_NAMES[_profession_name] = _base + tuple(
        f"{suffix} {_profession_name}" for suffix in _PROFESSION_600_RANK_SUFFIXES
    )

TOOL_MAX_LEVEL = PROGRESSION_MAX_LEVEL
TOOL_TIER_THRESHOLDS = tuple(TOOL_TIER_THRESHOLDS[:40]) + tuple(range(410, 601, 10))
TOOL_MAX_TIER = len(TOOL_TIER_THRESHOLDS)
TOOL_TIER_BONUS_CHANCES = tuple(TOOL_TIER_BONUS_CHANCES[:40]) + tuple(
    round(min(0.80, 0.60 + step * 0.01), 2) for step in range(1, 21)
)
_TOOL_600_SUFFIXES = (
    "Przekroczenia", "Gwiezdnego Tronu", "Wiecznego Echa", "Serca Otchłani",
    "Korony Gwiazd", "Sądu Horyzontu", "Nieskończonego Pulsu", "Kosmicznej Pieczęci",
    "Pradawnego Rezonansu", "Świtu Absolutu", "Przeznaczenia", "Oka Wszechświata",
    "Wiecznej Iskry", "Transcendentnego Znaku", "Głosu Nieskończoności",
    "Ostatecznego Horyzontu", "Duszy Kosmosu", "Korony Wieczności", "Apogeum", "Absolutu",
)
for _tool_type, _names in list(TOOL_TIER_NAMES.items()):
    _base = tuple(_names[:40])
    if len(_base) < 40:
        continue
    _prefix = _base[0].split(" ")[0]
    # Dla czytelności zachowujemy pełną nazwę narzędzia z pierwszego Tieru.
    if _tool_type == "fishing": _stem = "Wędka"
    elif _tool_type == "mining": _stem = "Kilof"
    elif _tool_type == "woodcutting": _stem = "Piła"
    elif _tool_type == "crafting": _stem = "Młot"
    elif _tool_type == "cooking": _stem = "Nóż"
    elif _tool_type == "herbalism": _stem = "Sierp"
    elif _tool_type == "alchemy": _stem = "Moździerz"
    elif _tool_type == "jewelcrafting": _stem = "Szczypce"
    else: _stem = _prefix
    TOOL_TIER_NAMES[_tool_type] = _base + tuple(f"{_stem} {suffix}" for suffix in _TOOL_600_SUFFIXES)

# Zasoby i receptury zachowują historyczne ID *_400_* dla zgodności save'ów,
# ale zmienna obejmuje od teraz całą linię 220-600.
PROGRESSION_400_LEVELS = tuple(range(220, 601, 20))
_new_levels = tuple(range(420, 601, 20))
ENDGAME_ORE_UNLOCKS = tuple(ENDGAME_ORE_UNLOCKS) + tuple((level, f"ore_400_{level}") for level in _new_levels)
ENDGAME_WOOD_UNLOCKS = tuple(ENDGAME_WOOD_UNLOCKS) + tuple((level, f"wood_400_{level}") for level in _new_levels)
ENDGAME_HERB_UNLOCKS = tuple(ENDGAME_HERB_UNLOCKS) + tuple((level, f"herb_400_{level}") for level in _new_levels)
for _habitat in tuple(ENDGAME_FISH_UNLOCKS):
    ENDGAME_FISH_UNLOCKS[_habitat] = tuple(ENDGAME_FISH_UNLOCKS[_habitat]) + tuple(
        (level, f"fish_400_{_habitat}_{level}") for level in _new_levels
    )

# Audytowa sygnatura nowej osi.
PROGRESSION_600_AUDIT = {
    "version": "0.36.0",
    "max_level": PROGRESSION_MAX_LEVEL,
    "character": CHARACTER_MAX_LEVEL,
    "class_mastery": CLASS_MASTERY_MAX_LEVEL,
    "skill": SKILL_MAX_LEVEL,
    "soul": SOUL_MAX_LEVEL,
    "soul_weapon_mastery": SOUL_WEAPON_MASTERY_MAX_LEVEL,
    "profession": PROFESSION_MAX_LEVEL,
    "tool": TOOL_MAX_LEVEL,
    "soul_tiers": SOUL_MAX_TIER,
    "tool_tiers": TOOL_MAX_TIER,
}


# ============================================================
# v0.36.2 - OPEN-WORLD TERRAIN THREAT REBALANCE
# ============================================================
# Generator Core historycznie wyliczał część stref wyłącznie z odległości
# topologicznej. To zaniżało etap obszarów mających jawne recommended_mastery
# (np. endgame 300-390) oraz pokojów tworzonych dopiero przy wejściu.
# Rekomendowany poziom jest od teraz twardą dolną granicą NUMERYCZNEGO balansu
# pokoju, ale nadal nie staje się blokadą wejścia.
_v0362_original_graph_room_levels = generator_core_v027._graph_room_levels
_v0362_original_runtime_room_level = generator_core_v027.runtime_room_level

def _v0362_recommended_room_floor(room):
    try:
        value = int((room or {}).get("recommended_mastery", 0) or 0)
    except Exception:
        value = 0
    return max(0, min(PROGRESSION_MAX_LEVEL, value))

def _v0362_graph_room_levels(rooms):
    levels = _v0362_original_graph_room_levels(rooms)
    for room_id, room in (rooms or {}).items():
        recommended = _v0362_recommended_room_floor(room)
        if recommended > int(levels.get(room_id, 1) or 1):
            levels[room_id] = recommended
            generator_core_v027._write_record_numeric("ROOMS", room, "generator_level", recommended)
    return levels

def _v0362_runtime_room_level(room_id, room, rooms=None):
    level = int(_v0362_original_runtime_room_level(room_id, room, rooms) or 1)
    recommended = _v0362_recommended_room_floor(room)
    if recommended > level:
        level = recommended
        generator_core_v027._write_record_numeric("ROOMS", room, "generator_level", level)
    return level

generator_core_v027._graph_room_levels = _v0362_graph_room_levels
generator_core_v027.runtime_room_level = _v0362_runtime_room_level
generator_core_v027.GENERATOR_VERSION = "0.57.1"
