# -*- coding: utf-8 -*-
"""Soulbound v0.36.0 - Global Progression 600.

Rozszerza wszystkie główne osie, które wcześniej kończyły się na 400,
do 600 bez resetu save'ów. Nazwy historycznych zmiennych *_400 pozostają
celowo dla kompatybilności z istniejącymi modułami i ID przedmiotów.
"""

# Ten moduł musi działać także przy bezpośrednim imporcie (np. narzędzia
# administracyjne przez Railway SSH), a nie tylko w historycznym bootstrapie.
from core.player_math import skill_level_power
from core.bootstrap_economy_professions import (
    SOUL_TIER_THRESHOLDS,
    SOUL_TIER_POWER_BONUSES,
    SOUL_TIER_CLASS_BONUS_PERCENT,
    SOUL_TIER_DODGE_BONUS,
    SOUL_TIER_GUARDIAN_REDUCTION,
    SOUL_TRIAL_QUEST_IDS,
    _SOUL_TRAIT_BASE_NAMES,
    _SOUL_TRAIT_CLASS_PROFILES,
    _SOUL_TRAIT_EFFECT_DESCRIPTIONS,
    PROFESSION_RANK_THRESHOLDS,
    PROFESSION_RANK_NAMES,
    TOOL_TIER_THRESHOLDS,
    TOOL_TIER_BONUS_CHANCES,
    TOOL_TIER_NAMES,
)
from core.progression_resources import (
    ENDGAME_ORE_UNLOCKS,
    ENDGAME_WOOD_UNLOCKS,
    ENDGAME_HERB_UNLOCKS,
    ENDGAME_FISH_UNLOCKS,
)

PROGRESSION_MAX_LEVEL = 800

# Generator Core od v0.64.0 ma własny kanoniczny zakres 1-600.
# progression_600 nie monkey-patchuje już jego globali.

# Główne osie postaci.
CHARACTER_MAX_LEVEL = PROGRESSION_MAX_LEVEL
CLASS_MASTERY_MAX_LEVEL = PROGRESSION_MAX_LEVEL
SKILL_MAX_LEVEL = PROGRESSION_MAX_LEVEL
SOUL_WEAPON_MASTERY_MAX_LEVEL = PROGRESSION_MAX_LEVEL

# v1.11.96: Skill Level is currently a real 1-600 axis. The combat multiplier
# must continue increasing through 600 and reach its authored endpoint there.
_SKILL_POWER_600_POINTS_V11196 = {
    level: skill_level_power(level)
    for level in (1, 100, 200, 300, 400, 500, 600)
}
if SKILL_MAX_LEVEL != 800:
    raise RuntimeError(f"Skill Level audit failed: expected cap 800, got {SKILL_MAX_LEVEL}")
if abs(_SKILL_POWER_600_POINTS_V11196[1] - 1.0) > 0.000001:
    raise RuntimeError("Skill Level audit failed: Level 1 power must be 1.0x")
if abs(_SKILL_POWER_600_POINTS_V11196[600] - 4.0) > 0.000001:
    raise RuntimeError("Skill Level audit failed: Level 600 power must be 4.0x")
if any(
    _SKILL_POWER_600_POINTS_V11196[b] <= _SKILL_POWER_600_POINTS_V11196[a]
    for a, b in zip((1, 100, 200, 300, 400, 500), (100, 200, 300, 400, 500, 600))
):
    raise RuntimeError("Skill Level audit failed: power curve must increase through 600")
SOUL_MAX_LEVEL = PROGRESSION_MAX_LEVEL

# Broń Duszy: stare Tiery 1-40 zostają w tych samych miejscach, 41-60
# kontynuują co 10 poziomów od 410 do 600.
# Era Bez Granic: zachowane tablice i identyfikatory 1-80; kolejne Tiery
# maja prawdziwy próg Soul Level co 10 punktów, do zakresu v104: 10000.
# Rozbudowa 501–1000 bez zmian 1–500; domyślny cap Soul Level 800
# nadal zależy od ustawień Admin Live (dusza bezlimitu lub >=10000).
# Nie nadpisuj ustawień administratora przy starcie serwera.
SOUL_TIER_THRESHOLDS = tuple([1] + [tier*10 for tier in range(2, 3001)])
SOUL_MAX_TIER = len(SOUL_TIER_THRESHOLDS)
SOUL_TIER_POWER_BONUSES = tuple(SOUL_TIER_POWER_BONUSES[:40]) + tuple(142+i*2 for i in range(40)) + tuple(222+i*2 for i in range(2920))
SOUL_TIER_CLASS_BONUS_PERCENT = tuple(SOUL_TIER_CLASS_BONUS_PERCENT[:40]) + tuple(41 + i//2 for i in range(40)) + tuple(61 + i//5 for i in range(2920))
SOUL_TIER_DODGE_BONUS = tuple(SOUL_TIER_DODGE_BONUS[:40]) + (0.05,)*2960
# Redukcji fizycznej nie wolno zwiększać ponad 65% kosztem odporności
# bossow/klas; zachowujemy dawne 80 wartości bez zmian.
SOUL_TIER_GUARDIAN_REDUCTION = tuple(SOUL_TIER_GUARDIAN_REDUCTION[:40]) + tuple(29+i//2 for i in range(40)) + tuple(min(65, 49+i//20) for i in range(2920))

# v106: przedprodukcyjna oś Soul Tier 3001–6000. Bez flagi pozostaje
# dokładna semantyka v105 (3000), wszystkie historyczne wpisy niezmienione.
import os as _sb106_tier_os
# v110 inherits the complete 3,001–6,000 Soul Tier expansion from v106.
# Do NOT use version text or the V110_STAGING flag alone for authorization:
# the test DB must be isolated, or production must have a valid v110 manifest.
_sb106_tier_extension_enabled = _sb106_tier_os.environ.get('SOULBOUND_V106_STAGING') == '1'
if not _sb106_tier_extension_enabled:
    try:
        from pathlib import Path as _sb110_tier_Path  # canonical current dependency
        _sb110_tier_root = _sb110_tier_Path(__file__).resolve().parents[1]
        if tuple(map(int,(_sb110_tier_root / 'VERSION').read_text(encoding='utf-8-sig').strip().split('.'))) >= (110,0,0):
            from systems.runtime_activation import enabled as _sb110_tier_authorized
            _sb106_tier_extension_enabled = bool(_sb110_tier_authorized())
    except (OSError, ImportError, ValueError):
        _sb106_tier_extension_enabled = False
if _sb106_tier_extension_enabled:
    SOUL_TIER_THRESHOLDS += tuple(tier * 10 for tier in range(3001, 6001))
    SOUL_MAX_TIER = len(SOUL_TIER_THRESHOLDS)
    SOUL_TIER_POWER_BONUSES += tuple(222 + (2920+i)*2 for i in range(3000))
    SOUL_TIER_CLASS_BONUS_PERCENT += tuple(61 + (2920+i)//5 for i in range(3000))
    SOUL_TIER_DODGE_BONUS += (0.05,) * 3000
    SOUL_TIER_GUARDIAN_REDUCTION += tuple(min(65,49+(2920+i)//20) for i in range(3000))
    if (SOUL_MAX_TIER != 6000 or SOUL_TIER_THRESHOLDS[2999] != 30000
            or SOUL_TIER_THRESHOLDS[5999] != 60000):
        raise RuntimeError('v106: błąd zachowania osi Soul Tier')
SOUL_TRIAL_QUEST_IDS.update({tier: f'soul_tier_{tier:02d}_trial' for tier in range(41, SOUL_MAX_TIER+1)})

# Weapon Traits 41-60: unikalne nazwy, ten sam klasowy cykl efektów.
_SOUL_TRAIT_BASE_NAMES_41_60 = (
    "Przekroczenie", "Gwiezdny Tron", "Echo Wieczności", "Serce Otchłani",
    "Korona Gwiazd", "Sąd Horyzontu", "Nieskończony Puls", "Pieczęć Kosmosu",
    "Pradawny Rezonans", "Świt Absolutu", "Droga Przeznaczenia", "Oko Wszechświata",
    "Wieczna Iskra", "Transcendentny Znak", "Głos Nieskończoności", "Ostateczny Horyzont",
    "Dusza Kosmosu", "Korona Wieczności", "Apogeum", "Absolut Duszy",
)
_SOUL_TRAIT_BASE_NAMES = tuple(_SOUL_TRAIT_BASE_NAMES[:40]) + _SOUL_TRAIT_BASE_NAMES_41_60 + (
    "Gwiezdna Przystań", "Wieczny Szept", "Żelazna Galaktyka", "Przysięga Otchłani",
    "Ryk Nieskończoności", "Słoneczna Korona", "Domena Czasu", "Sąd Pradawnych",
    "Droga Niebios", "Rdzeń Wszechświata", "Żywa Przestrzeń", "Korona Przeznaczenia",
    "Ostatnia Iskra", "Gwiezdne Dziedzictwo", "Gniew Tysiąca Słońc",
    "Przebudzenie Świata", "Brama Wiecznego Świtu", "Kres Ciemności",
    "Serce Nieba", "Tron Nieskończonej Duszy",
)
# Unikalne nazwy dla Tierów 81–1000; każda ma realny bonus i wpis
# w istniejacym klasowym cyklu efektow (bez dodatkowych tabel SQLite).
_SOUL_TRAIT_BASE_NAMES += tuple((f"Forma Wiecznej Duszy {tier//100}" if tier>=1100 and tier%100==0 else f"Przekroczenie Duszy {tier}") for tier in range(81, SOUL_MAX_TIER+1))
from systems.new_heroes_v900 import SOUL_TRAITS as _V900_SOUL_TRAITS
_SOUL_TRAIT_CLASS_PROFILES.update(_V900_SOUL_TRAITS)
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

def soul_weapon_trait_for_tier_v11193(tier, class_name=None):
    """Cechy Broni Duszy 1–1000, włącznie z klasami Admin Live."""
    tier = max(1, min(SOUL_MAX_TIER, int(tier)))
    class_name = class_name or "Wojownik"
    # Additional Admin Live classes inherit the real soul trait table of their
    # combat archetype instead of silently using the Wojownik fallback.
    if class_name not in SOUL_TIER_TRAITS_BY_CLASS:
        from systems.admin_live_classes_v7700 import inherited_parent
        class_name = inherited_parent(class_name) or class_name
    rows = SOUL_TIER_TRAITS_BY_CLASS.get(class_name) or SOUL_TIER_TRAITS_BY_CLASS["Wojownik"]
    return rows.get(tier)

def soul_weapon_trait_totals_v11193(tier, class_name=None):
    """Wszystkie efekty Broni Duszy do bieżącego Tieru 1–1000."""
    tier = max(1, min(SOUL_MAX_TIER, int(tier)))
    class_name = class_name or "Wojownik"
    # Additional Admin Live classes inherit the real soul trait table of their
    # combat archetype instead of silently using the Wojownik fallback.
    if class_name not in SOUL_TIER_TRAITS_BY_CLASS:
        from systems.admin_live_classes_v7700 import inherited_parent
        class_name = inherited_parent(class_name) or class_name
    rows = SOUL_TIER_TRAITS_BY_CLASS.get(class_name) or SOUL_TIER_TRAITS_BY_CLASS["Wojownik"]
    totals = {
        "damage_percent": 0.0, "crit_chance": 0.0, "crit_damage_percent": 0.0,
        "lifesteal_percent": 0.0, "execute_damage_percent": 0.0,
        "mana_restore_percent": 0.0, "boss_damage_percent": 0.0,
    }
    for _t in range(1, tier + 1):
        row = rows[_t]
        totals[row["effect"]] += float(row["value"])
    return totals

def soul_tier_title_for_class(tier, class_name=None):
    """Unikalny tytuł klasowy Soul Tier 1–1000."""
    row = soul_weapon_trait_for_tier_v11193(tier, class_name)
    return row["name"] if row else f"Tier Duszy {int(tier)}"

_SOUL_TIER_TITLE_AUDIT = [
    soul_tier_title_for_class(_tier, _class_name)
    for _class_name in _SOUL_TRAIT_CLASS_PROFILES
    for _tier in range(1, SOUL_MAX_TIER + 1)
]
# v1.13.30: audit failure is enforced by predeploy_full.py, not production startup.
# v1.13.30: audit failure is enforced by predeploy_full.py, not production startup.
# Profesje i narzędzia 1-600.
PROFESSION_MAX_LEVEL = PROGRESSION_MAX_LEVEL
BLACKSMITHING_MAX_LEVEL = PROGRESSION_MAX_LEVEL
JEWELCRAFTING_MAX_LEVEL = PROGRESSION_MAX_LEVEL
PROFESSION_RANK_THRESHOLDS = tuple(PROFESSION_RANK_THRESHOLDS[:23]) + tuple(range(420, 801, 20))
PROFESSION_MAX_RANK = len(PROFESSION_RANK_THRESHOLDS)
BLACKSMITHING_MAX_RANK = PROFESSION_MAX_RANK
BLACKSMITHING_RANK_THRESHOLDS = PROFESSION_RANK_THRESHOLDS

_PROFESSION_600_RANK_SUFFIXES = (
    "Mistrz Przekroczenia", "Mistrz Gwiezdnego Tronu", "Mistrz Wiecznego Echa",
    "Mistrz Otchłannego Serca", "Mistrz Korony Gwiazd", "Mistrz Horyzontu Absolutu",
    "Mistrz Kosmicznego Szlaku", "Mistrz Wieczności", "Mistrz Apogeum", "Arcymistrz Absolutu",
)
_PROFESSION_600_RANK_SUFFIXES += (
    "Władca Głębin", "Arcymistrz Astralny", "Strażnik Wiecznego Ognia",
    "Mistrz Żywego Metalu", "Mistrz Nieskończonych Szlaków",
    "Arcymistrz Pradawnej Kuźni", "Mistrz Serca Gwiazd",
    "Legenda Złotego Horyzontu", "Mistrz Wiecznych Żywiołów",
    "Arcymistrz Nowej Ery",
)
for _profession_name, _names in list(PROFESSION_RANK_NAMES.items()):
    _base = tuple(_names[:23])
    PROFESSION_RANK_NAMES[_profession_name] = _base + tuple(
        f"{suffix} {_profession_name}" for suffix in _PROFESSION_600_RANK_SUFFIXES
    )

TOOL_MAX_LEVEL = PROGRESSION_MAX_LEVEL
TOOL_TIER_THRESHOLDS = tuple(TOOL_TIER_THRESHOLDS[:40]) + tuple(range(410, 801, 10))
TOOL_MAX_TIER = len(TOOL_TIER_THRESHOLDS)
TOOL_TIER_BONUS_CHANCES = tuple(TOOL_TIER_BONUS_CHANCES[:40]) + tuple(
    round(min(0.80, 0.60 + step * 0.01), 2) for step in range(1, 41)
)
_TOOL_600_SUFFIXES = (
    "Przekroczenia", "Gwiezdnego Tronu", "Wiecznego Echa", "Serca Otchłani",
    "Korony Gwiazd", "Sądu Horyzontu", "Nieskończonego Pulsu", "Kosmicznej Pieczęci",
    "Pradawnego Rezonansu", "Świtu Absolutu", "Przeznaczenia", "Oka Wszechświata",
    "Wiecznej Iskry", "Transcendentnego Znaku", "Głosu Nieskończoności",
    "Ostatecznego Horyzontu", "Duszy Kosmosu", "Korony Wieczności", "Apogeum", "Absolutu",
)
_TOOL_600_SUFFIXES += (
    "Podziemnego Króla", "Echa Atlantydy", "Czarnej Gwiazdy", "Wiecznej Magmy",
    "Przedwiecznych Szlaków", "Kosmicznej Kuźni", "Płomieni Świata",
    "Głębi Wieczności", "Pierwotnego Światła", "Nowej Ery",
    "Astralnej Burzy", "Zorzy Północy", "Ognistego Tronu",
    "Żywej Kryształowej Skały", "Dawnych Mistrzów", "Ostatniego Słońca",
    "Przebudzonej Ziemi", "Nieskończonej Drogi", "Korony Przyszłości", "Ostatecznego Przebudzenia",
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
PROGRESSION_400_LEVELS = tuple(range(220, 801, 20))
_new_levels = tuple(range(420, 801, 20))
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
