"""Authored character resources and class/race passives for Soulbound v1.13.15.

This module is deliberately independent from Generator Core. Character identity is
authored content: race/class choice, real stats and equipment decide HP/Mana and
passives. Generator Core may call these helpers for backward compatibility, but it
does not own their numbers.
"""
from __future__ import annotations

import math

CHARACTER_RESOURCE_MAX_LEVEL = 600

AUTHORED_CLASS_PASSIVE_PROFILES = {
    "Wojownik": {"kind": "physical_damage", "value": 0.10},
    "Berserker": {"kind": "physical_damage", "value": 0.12},
    "Łotrzyk": {"kind": "dodge", "value": 0.05},
    "Łowca": {"kind": "physical_damage", "value": 0.08},
    "Mnich": {"kind": "healing", "value": 0.08},
    "Strażnik": {"kind": "damage_reduction", "value": 0.10},
    "Mag": {"kind": "magic_damage", "value": 0.10},
    "Nekromanta": {"kind": "drain_healing", "value": 0.15},
    "Kapłan": {"kind": "healing", "value": 0.10},
    "Czarownik": {"kind": "magic_damage", "value": 0.12},
    "Druid": {"kind": "healing", "value": 0.10},
    "Psionik": {"kind": "magic_defense", "value": 0.10},
    "Mec": {"kind": "damage_reduction", "value": 0.10},
    "Inżynier": {"kind": "physical_damage", "value": 0.10},
}

AUTHORED_RACE_PASSIVE_PROFILES = {
    "Człowiek": {"kind": "stat_xp", "value": 0.10},
    "Ogr": {"kind": "physical_damage", "value": 0.12},
    "Elf": {"kind": "dodge", "value": 0.05},
    "Krasnolud": {"kind": "damage_reduction", "value": 0.10},
    "Ork": {"kind": "max_hp", "value": 0.10},
    "Niziołek": {"kind": "profession_bonus", "value": 0.03},
    "Mroczny Elf": {"kind": "magic_damage", "value": 0.10},
    "Gnom": {"kind": "max_mana", "value": 0.15},
    "Smok": {"kind": "all_damage", "value": 0.08},
    # Legacy save spelling retained for old characters.
    "Smoczy": {"kind": "all_damage", "value": 0.08},
    "Troll": {"kind": "physical_reduction", "value": 0.12},
    "Diablę": {"kind": "soul_xp", "value": 0.10},
    "Aasimar": {"kind": "magic_defense", "value": 0.12},
    "Driada": {"kind": "healing", "value": 0.15},
    "Cyborg": {"kind": "damage_reduction", "value": 0.10},
}


def _clamp_level(character_level: int) -> int:
    return max(1, min(CHARACTER_RESOURCE_MAX_LEVEL, int(character_level or 1)))


def _character_resource_level_scale(
    character_level: int,
    reference_scale: float,
    post_reference_growth: float,
) -> float:
    """Preserve the proven v1.11-v1.13 resource curve without Generator ownership."""
    level = _clamp_level(character_level)
    reference_level = min(CHARACTER_RESOURCE_MAX_LEVEL, 175)
    if level <= reference_level:
        progress = (level - 1) / float(max(1, reference_level - 1))
        return 1.0 + (max(1.0, float(reference_scale)) - 1.0) * (progress ** 1.05)
    post = (level - reference_level) / float(
        max(1, CHARACTER_RESOURCE_MAX_LEVEL - reference_level)
    )
    return max(1.0, float(reference_scale)) * (
        1.0 + max(0.0, float(post_reference_growth)) * (post ** 0.90)
    )


def character_hp_base(character_level: int, constitution: int) -> int:
    """Base HP from Character Level + real CON; race bonus is applied separately."""
    level = _clamp_level(character_level)
    constitution = max(1, int(constitution or 1))
    legacy_base = 48 + constitution * 5.2 + level * 3.1
    level_scale = _character_resource_level_scale(level, 9.0, 0.50)
    condition_ratio = max(0.01, constitution / 175.0)
    condition_scale = max(0.45, condition_ratio ** 0.75)
    return max(1, int(round(legacy_base * level_scale * condition_scale)))


def character_mana_base(
    character_level: int,
    intelligence: int,
    willpower: int | None = None,
) -> int:
    """Base Mana from Character Level + real INT/WILL; race bonus is separate."""
    level = _clamp_level(character_level)
    intelligence = max(1, int(intelligence or 1))
    willpower = intelligence if willpower is None else max(1, int(willpower or 1))
    legacy_base = 22 + intelligence * 2.4 + willpower * 2.4 + level * 2.0
    level_scale = _character_resource_level_scale(level, 3.8, 0.45)
    average_magic_stat = (intelligence + willpower) / 2.0
    stat_ratio = max(0.01, average_magic_stat / 175.0)
    stat_scale = max(0.50, stat_ratio ** 0.75)
    return max(0, int(round(legacy_base * level_scale * stat_scale)))


def class_passive_profile(class_name: str) -> dict:
    row = AUTHORED_CLASS_PASSIVE_PROFILES.get(str(class_name))
    return dict(row) if row else {"kind": "none", "value": 0.0}


def race_passive_profile(race_name: str) -> dict:
    row = AUTHORED_RACE_PASSIVE_PROFILES.get(str(race_name))
    return dict(row) if row else {"kind": "none", "value": 0.0}


def passive_text_pl(kind: str, value: float) -> str:
    pct = int(round(float(value or 0.0) * 100))
    return {
        "physical_damage": f"+{pct} procent obrażeń fizycznych",
        "magic_damage": f"+{pct} procent obrażeń magicznych",
        "all_damage": f"+{pct} procent wszystkich obrażeń",
        "healing": f"+{pct} procent mocy leczenia",
        "drain_healing": f"+{pct} procent leczenia z wysysania życia",
        "magic_defense": f"+{pct} procent obrony magicznej",
        "damage_reduction": f"{pct} procent redukcji wszystkich obrażeń",
        "physical_reduction": f"{pct} procent redukcji obrażeń fizycznych",
        "dodge": f"+{pct} punktów procentowych uniku",
        "stat_xp": f"+{pct} procent EXP statystyk",
        "max_hp": f"+{pct} procent maksymalnego HP",
        "profession_bonus": f"+{pct} punktów procentowych szansy na bonus profesji",
        "max_mana": f"+{pct} procent maksymalnej Many",
        "soul_xp": f"+{pct} procent Soul XP",
    }.get(str(kind), "brak")


def class_passive_text_pl(class_name: str) -> str:
    row = class_passive_profile(class_name)
    return passive_text_pl(row["kind"], row["value"])


def race_passive_text_pl(race_name: str) -> str:
    row = race_passive_profile(race_name)
    return passive_text_pl(row["kind"], row["value"])


# Small authored-contract audit. These numbers are also stated in class/race
# descriptions, so a text/profile drift should fail loudly.
if len(AUTHORED_CLASS_PASSIVE_PROFILES) != 14:
    raise RuntimeError("Authored class passive profile count must be 14")
if AUTHORED_RACE_PASSIVE_PROFILES["Ork"] != {"kind": "max_hp", "value": 0.10}:
    raise RuntimeError("Ork authored max-HP passive drift")
if AUTHORED_RACE_PASSIVE_PROFILES["Gnom"] != {"kind": "max_mana", "value": 0.15}:
    raise RuntimeError("Gnom authored max-Mana passive drift")
