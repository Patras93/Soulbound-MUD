# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Soulbound v0.7.37 Jewelcrafting
Wieloosobowy tekstowy MUD TCP/Telnet dla MUSHclienta/Mudleta.

Najważniejsze zasady projektu:
- postać NIE ma levelu ani XP postaci,
- statystyki rosną automatycznie,
- każda klasa rozwija automatycznie wszystkie pięć statystyk,
- Broń Duszy ma osobny Soul Level 1-200,
- Soul Tier 1-5 odblokowuje się osobno,
- wszystkie trwałe dane gracza są zapisywane w SQLite.
"""

import asyncio
import hashlib
import hmac
import math
import os
import random
import re
import secrets
import sqlite3
import sys
import time
import unicodedata
from dataclasses import dataclass
from typing import Optional

VERSION = "0.7.37"

HOST = os.getenv("SOULBOUND_HOST", "0.0.0.0")
_RAILWAY_TCP_PORT = os.getenv("RAILWAY_TCP_APPLICATION_PORT", "").strip()
_SOULBOUND_PORT = os.getenv("SOULBOUND_PORT", "").strip()
_GENERIC_PORT = os.getenv("PORT", "").strip()

if _RAILWAY_TCP_PORT:
    PORT = int(_RAILWAY_TCP_PORT)
elif _SOULBOUND_PORT:
    PORT = int(_SOULBOUND_PORT)
elif _GENERIC_PORT:
    PORT = int(_GENERIC_PORT)
else:
    PORT = 4000

_VOLUME_PATH = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "").strip()
_DEFAULT_DB = os.path.join(_VOLUME_PATH, "soulbound.db") if _VOLUME_PATH else "soulbound.db"
DB_PATH = os.getenv("SOULBOUND_DB", _DEFAULT_DB)

MAX_CLIENTS = int(os.getenv("SOULBOUND_MAX_CLIENTS", "100"))
PBKDF2_ROUNDS = 210_000

STAT_GROWTH_THRESHOLD = 100
SOUL_MAX_LEVEL = 200
TIER2_LEVEL = 25
TIER3_LEVEL = 60
TIER4_LEVEL = 120
TIER5_LEVEL = 180
SOUL_MAX_TIER = 5
REGULAR_MOB_RESPAWN_SECONDS = 120
BOSS_RESPAWN_SECONDS = 300
TRAINING_DUMMY_RESPAWN_SECONDS = 60
GLOBAL_MOB_RESPAWN_MULTIPLIER = 2.0
CORPSE_LIFETIME_SECONDS = 600
GLOBAL_MOB_HP_MULTIPLIER = 2.0
QUEST_REPEAT_COOLDOWN_SECONDS = 60 * 60
BLACKSMITH_QUEST_COOLDOWN_SECONDS = 60 * 60

# Ekonomia:
# 1000 srebrnych monet = 1 złota moneta
# 1 000 000 złotych monet = 1 mithrilowa moneta
SILVER_PER_GOLD = 1000
GOLD_PER_MITHRIL = 1000000

def normalize_currency_values(silver, gold, mithril):
    silver = max(0, int(silver))
    gold = max(0, int(gold))
    mithril = max(0, int(mithril))

    gold_from_silver, silver = divmod(
        silver, SILVER_PER_GOLD
    )
    gold += gold_from_silver

    mithril_from_gold, gold = divmod(
        gold, GOLD_PER_MITHRIL
    )
    mithril += mithril_from_gold

    return silver, gold, mithril


PROFESSION_MAX_LEVEL = 100
BLACKSMITHING_MAX_LEVEL = 200
JEWELCRAFTING_MAX_LEVEL = 200

# v0.6.79:
# Profesje pokazują i otrzymują 2x więcej XP,
# ale koszt każdego levelu jest 4x większy.
# Efektywnie levelowanie profesji jest około 2x wolniejsze.
PROFESSION_XP_GAIN_MULTIPLIER = 2
PROFESSION_XP_REQUIREMENT_MULTIPLIER = 4

CHARISMA_DISCOUNT_STEP = 4
CHARISMA_MAX_DISCOUNT = 25
PARTY_BASE_CAPACITY = 8
PARTY_CHARISMA_STEP = 25

PROFESSION_MAX_RANK = 8
PROFESSION_RANK_THRESHOLDS = (1, 15, 30, 45, 60, 75, 90, 100)
BLACKSMITHING_MAX_RANK = 13
BLACKSMITHING_RANK_THRESHOLDS = (
    1, 15, 30, 45, 60, 75, 90,
    100, 120, 140, 160, 180, 200,
)

PROFESSION_RANK_NAMES = {
    "Wędkarstwo": (
        "Uczeń Wędkarstwa",
        "Adept Wędkarstwa",
        "Czeladnik Wędkarstwa",
        "Specjalista Wędkarstwa",
        "Ekspert Wędkarstwa",
        "Mistrz Wędkarstwa",
        "Arcymistrz Wędkarstwa",
        "Legenda Wędkarstwa",
    ),
    "Górnictwo": (
        "Uczeń Górnictwa",
        "Adept Górnictwa",
        "Czeladnik Górnictwa",
        "Specjalista Górnictwa",
        "Ekspert Górnictwa",
        "Mistrz Górnictwa",
        "Arcymistrz Górnictwa",
        "Legenda Górnictwa",
    ),
    "Drwalstwo": (
        "Uczeń Drwalstwa",
        "Adept Drwalstwa",
        "Czeladnik Drwalstwa",
        "Specjalista Drwalstwa",
        "Ekspert Drwalstwa",
        "Mistrz Drwalstwa",
        "Arcymistrz Drwalstwa",
        "Legenda Drwalstwa",
    ),
    "Zielarstwo": (
        "Uczeń Zielarstwa",
        "Adept Zielarstwa",
        "Czeladnik Zielarstwa",
        "Specjalista Zielarstwa",
        "Ekspert Zielarstwa",
        "Mistrz Zielarstwa",
        "Arcymistrz Zielarstwa",
        "Legenda Zielarstwa",
    ),
    "Alchemia": (
        "Uczeń Alchemii",
        "Adept Alchemii",
        "Czeladnik Alchemii",
        "Specjalista Alchemii",
        "Ekspert Alchemii",
        "Mistrz Alchemii",
        "Arcymistrz Alchemii",
        "Legenda Alchemii",
    ),
    "Kowalstwo": (
        "Uczeń Kowalstwa",
        "Adept Kowalstwa",
        "Czeladnik Kowalstwa",
        "Specjalista Kowalstwa",
        "Ekspert Kowalstwa",
        "Mistrz Kowalstwa",
        "Arcymistrz Kowalstwa",
        "Legenda Kowalstwa",
        "Kowal Runiczny",
        "Kowal Smoczej Stali",
        "Kowal Astralny",
        "Kowal Pustki",
        "Wieczny Mistrz Kowalstwa",
    ),
    "Jubilerstwo": (
        "Uczeń Jubilerstwa",
        "Adept Jubilerstwa",
        "Czeladnik Jubilerstwa",
        "Specjalista Jubilerstwa",
        "Ekspert Jubilerstwa",
        "Mistrz Jubilerstwa",
        "Arcymistrz Jubilerstwa",
        "Legenda Jubilerstwa",
        "Jubiler Runiczny",
        "Jubiler Smoczej Stali",
        "Jubiler Astralny",
        "Jubiler Pustki",
        "Wieczny Mistrz Jubilerstwa",
    ),
}

def normalize_profession_name(profession):
    value = str(profession).strip().lower()
    if value in ("fishing", "wedkarstwo", "wędkarstwo"):
        return "Wędkarstwo"
    if value in ("mining", "gornictwo", "górnictwo"):
        return "Górnictwo"
    if value in ("woodcutting", "drwalstwo", "drwal"):
        return "Drwalstwo"
    if value in ("herbalism", "zielarstwo", "zielarz"):
        return "Zielarstwo"
    if value in ("alchemy", "alchemia"):
        return "Alchemia"
    if value in (
        "blacksmithing", "smithing", "kowalstwo",
        "kowal", "rzemioslo", "rzemiosło",
    ):
        return "Kowalstwo"
    if value in (
        "jewelcrafting", "jewelry", "jubilerstwo",
        "jubiler", "bizuteria", "biżuteria",
    ):
        return "Jubilerstwo"
    return str(profession)

def profession_max_level(profession):
    profession = normalize_profession_name(profession)
    if profession == "Kowalstwo":
        return BLACKSMITHING_MAX_LEVEL
    if profession == "Jubilerstwo":
        return JEWELCRAFTING_MAX_LEVEL
    return PROFESSION_MAX_LEVEL

def profession_rank_thresholds(profession):
    profession = normalize_profession_name(profession)
    if profession in ("Kowalstwo", "Jubilerstwo"):
        return BLACKSMITHING_RANK_THRESHOLDS
    return PROFESSION_RANK_THRESHOLDS

def profession_max_rank(profession):
    profession = normalize_profession_name(profession)
    if profession in ("Kowalstwo", "Jubilerstwo"):
        return BLACKSMITHING_MAX_RANK
    return PROFESSION_MAX_RANK

def profession_rank(level, profession=None):
    if profession is None:
        max_level = PROFESSION_MAX_LEVEL
        thresholds = PROFESSION_RANK_THRESHOLDS
    else:
        profession = normalize_profession_name(profession)
        max_level = profession_max_level(profession)
        thresholds = profession_rank_thresholds(profession)

    level = max(1, min(max_level, int(level)))
    rank = 1
    for number, minimum in enumerate(thresholds, 1):
        if level >= minimum:
            rank = number
        else:
            break
    return rank

def profession_rank_name(profession, level):
    profession = normalize_profession_name(profession)
    rank = profession_rank(level, profession)
    return PROFESSION_RANK_NAMES[profession][rank - 1]

TOOL_MAX_LEVEL = 200
TOOL_MAX_TIER = 13
TOOL_TIER_THRESHOLDS = (
    1, 15, 30, 45, 60, 75, 90, 100,
    120, 140, 160, 180, 200,
)
TOOL_TIER_BONUS_CHANCES = (
    0.00, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12,
    0.15, 0.18, 0.21, 0.24, 0.27, 0.30,
)

def tool_max_level(tool_type):
    return TOOL_MAX_LEVEL

TOOL_TIER_NAMES = {
    "fishing": (
        "Wędka Ucznia",
        "Wędka Rzeczna",
        "Wędka Srebrnego Haczyka",
        "Wędka Morskiego Wiatru",
        "Wędka Głębin",
        "Wędka Mistrza Połowu",
        "Wędka Legendarnego Wędkarza",
        "Wędka Mitycznych Głębin",
        "Wędka Otchłannego Łowcy",
        "Wędka Władcy Oceanów",
        "Wędka Astralnego Połowu",
        "Wędka Pradawnych Głębin",
        "Wędka Wiecznego Oceanu",
    ),
    "mining": (
        "Kilof Ucznia",
        "Kilof Górnika",
        "Kilof Stalowego Ostrza",
        "Kilof Hartowanego Rdzenia",
        "Kilof Kryształowej Żyły",
        "Kilof Mistrza Kopalni",
        "Kilof Legendarnych Złóż",
        "Kilof Mitycznego Rdzenia",
        "Kilof Runicznej Żyły",
        "Kilof Smoczego Kruszcu",
        "Kilof Astralnej Rudy",
        "Kilof Pradawnego Mithrilu",
        "Kilof Serca Świata",
    ),
    "woodcutting": (
        "Piła Ucznia",
        "Piła Leśna",
        "Piła Stalowych Zębów",
        "Piła Hartowanego Ostrza",
        "Piła Żelaznego Dębu",
        "Piła Mistrza Drwali",
        "Piła Legendarnych Pni",
        "Piła Mitycznego Gaju",
        "Piła Runicznego Lasu",
        "Piła Smoczego Drewna",
        "Piła Astralnego Gaju",
        "Piła Pradawnego Drzewa",
        "Piła Drzewa Świata",
    ),
    "crafting": (
        "Młot Rzemieślnika Ucznia",
        "Młot Żelaznego Kowadła",
        "Młot Stalowego Rzemiosła",
        "Młot Hartowanego Rdzenia",
        "Młot Runicznego Kowadła",
        "Młot Mistrza Rzemiosła",
        "Młot Legendarnego Twórcy",
        "Młot Mitycznego Kowadła",
        "Młot Arcyrzemieślnika",
        "Młot Smoczej Kuźni",
        "Młot Astralnego Twórcy",
        "Młot Pradawnej Kuźni",
        "Młot Wiecznego Kowadła",
    ),
    "cooking": (
        "Nóż Kucharski Ucznia",
        "Nóż Karczemnej Kuchni",
        "Nóż Stalowego Ostrza",
        "Nóż Szefa Kuchni",
        "Nóż Mistrza Smaku",
        "Nóż Wielkiego Kucharza",
        "Nóż Legendarnej Uczty",
        "Nóż Mitycznego Szefa",
        "Nóż Królewskiej Uczty",
        "Nóż Smoczej Kuchni",
        "Nóż Astralnego Smaku",
        "Nóż Pradawnej Uczty",
        "Nóż Wiecznego Szefa",
    ),
    "herbalism": (
        "Sierp Zielarski Ucznia",
        "Sierp Łąkowy",
        "Sierp Leśnych Ziół",
        "Sierp Srebrnego Ostrza",
        "Sierp Głębokiego Gaju",
        "Sierp Mistrza Zielarstwa",
        "Sierp Legendarnych Ziół",
        "Sierp Mitycznego Ogrodu",
        "Sierp Runicznego Zielnika",
        "Sierp Smoczego Ogrodu",
        "Sierp Astralnych Ziół",
        "Sierp Pradawnej Flory",
        "Sierp Wiecznego Ogrodu",
    ),
    "alchemy": (
        "Moździerz Alchemika Ucznia",
        "Moździerz Kamienny",
        "Moździerz Srebrnego Pyłu",
        "Moździerz Runiczny",
        "Moździerz Mistycznej Esencji",
        "Moździerz Mistrza Alchemii",
        "Moździerz Legendarnego Eliksiru",
        "Moździerz Mitycznej Transmutacji",
        "Moździerz Arcyalchemika",
        "Moździerz Smoczej Esencji",
        "Moździerz Astralnej Transmutacji",
        "Moździerz Pradawnego Eliksiru",
        "Moździerz Wiecznej Alchemii",
    ),
    "jewelcrafting": (
        "Szczypce Jubilerskie Ucznia",
        "Szczypce Srebrnego Drutu",
        "Szczypce Złotego Splotu",
        "Szczypce Precyzyjnego Szlifu",
        "Szczypce Kryształowej Oprawy",
        "Szczypce Mistrza Jubilerstwa",
        "Szczypce Legendarnej Oprawy",
        "Szczypce Mitycznego Klejnotu",
        "Szczypce Runicznej Oprawy",
        "Szczypce Smoczej Stali",
        "Szczypce Astralnego Splotu",
        "Szczypce Pustki",
        "Szczypce Wiecznego Klejnotu",
    ),
}

def tool_tier(level):
    level = max(1, min(TOOL_MAX_LEVEL, int(level)))
    tier = 1
    for number, minimum in enumerate(TOOL_TIER_THRESHOLDS, 1):
        if level >= minimum:
            tier = number
        else:
            break
    return tier

def tool_tier_name(tool_type, level):
    tier = tool_tier(level)
    names = TOOL_TIER_NAMES.get(tool_type, TOOL_TIER_NAMES["mining"])
    return names[tier - 1]

def tool_tier_bonus_chance(level):
    return TOOL_TIER_BONUS_CHANCES[tool_tier(level) - 1]

CLASS_MASTERY_MAX_LEVEL = 100
CLASS_MASTERY_XP_BASE = 1000
CLASS_MASTERY_XP_STEP = 250
MULTICLASS_MAX_ACTIVE = 3

def class_mastery_xp_to_next(level):
    level = max(1, min(CLASS_MASTERY_MAX_LEVEL, int(level)))
    if level >= CLASS_MASTERY_MAX_LEVEL:
        return 0
    return CLASS_MASTERY_XP_BASE + (level - 1) * CLASS_MASTERY_XP_STEP

def class_type_for_name(class_name):
    for cname, ctype, weapon, base in CLASSES:
        if cname == class_name:
            return ctype
    return "physical"

SKILL_MAX_LEVEL = 200
SKILL_XP_BASE = 50
SKILL_XP_STEP = 25

def skill_xp_to_next(level):
    if level >= SKILL_MAX_LEVEL:
        return 0
    return SKILL_XP_BASE + (level - 1) * SKILL_XP_STEP

def skill_power_multiplier(level):
    # L1 = 1.0, L100 ~= 1.7425, L200 ~= 2.4925.
    return 1.0 + max(0, level - 1) * 0.0075

def skill_cooldown_multiplier(level):
    # Maksymalnie 30% krótszego cooldownu; dalsze levele zwiększają moc.
    reduction = min(0.30, max(0, level - 1) * 0.003)
    return 1.0 - reduction

BANK_ROOM = "market"

PROFESSION_COOLDOWN = 2.0

# v0.6.86 - realny czas wykonywania czynności narzędziem.
# Czas maleje płynnie wraz z levelem narzędzia 1 -> 200.
TOOL_ACTION_BASE_SECONDS = {
    "fishing": 15,
    "mining": 30,
    "woodcutting": 24,
    "crafting": 20,
    "cooking": 12,
    "herbalism": 10,
    "alchemy": 18,
    "jewelcrafting": 20,
}

TOOL_ACTION_MIN_SECONDS = {
    "fishing": 5,
    "mining": 10,
    "woodcutting": 8,
    "crafting": 7,
    "cooking": 4,
    "herbalism": 3,
    "alchemy": 6,
    "jewelcrafting": 7,
}

REST_TICK_SECONDS = 5.0
REST_REGEN_PERCENT = 10

RIVER_FISHING_ROOMS = {"riverbank", "stone_bridge"}
LAKE_FISHING_ROOMS = {"lake_shore"}
SEA_FISHING_ROOMS = {"sea_pier"}
OCEAN_FISHING_ROOMS = {"ocean_platform"}
FRESHWATER_FISHING_ROOMS = RIVER_FISHING_ROOMS | LAKE_FISHING_ROOMS
MARINE_FISHING_ROOMS = SEA_FISHING_ROOMS | OCEAN_FISHING_ROOMS
FISHING_ROOMS = FRESHWATER_FISHING_ROOMS | MARINE_FISHING_ROOMS
MINE_MIN_FLOOR = 1
MINE_MAX_FLOOR = 200
MINE_WALL_HITS_REQUIRED = 5
MINE_WALL_SCALING_START_FLOOR = 10

def mine_wall_hits_required(floor):
    floor = max(
        MINE_MIN_FLOOR,
        min(MINE_MAX_FLOOR, int(floor)),
    )
    if floor < MINE_WALL_SCALING_START_FLOOR:
        return MINE_WALL_HITS_REQUIRED
    return floor

def mine_floor_id(floor):
    return f"mine_floor_{int(floor)}"

def mine_floor_number(room_id):
    match = re.fullmatch(r"mine_floor_(\d+)", str(room_id or ""))
    if not match:
        return None
    floor = int(match.group(1))
    if MINE_MIN_FLOOR <= floor <= MINE_MAX_FLOOR:
        return floor
    return None

MINING_DEPTH_ROOMS = {
    mine_floor_id(floor)
    for floor in range(MINE_MIN_FLOOR, MINE_MAX_FLOOR + 1)
}
MINING_ROOMS = {
    "cave_entrance", "cave_tunnel", "crystal_chamber"
} | MINING_DEPTH_ROOMS

AUTO_FISHING_ROUTE = (
    "riverbank", "lake_shore", "sea_pier", "ocean_platform",
)
AUTO_WOODCUTTING_ROUTE = (
    "lumberjack_camp", "whisper_grove", "meadow",
    "old_road", "deep_grove",
)
AUTO_HERBALISM_ROUTE = (
    "meadow", "mint_meadow", "flower_meadow", "lakeside_meadow",
    "riverbank", "lake_shore", "whisper_grove",
    "herbalist_hut", "old_road", "deep_grove",
)

WOODCUTTING_ROOMS = {"lumberjack_camp", "meadow", "whisper_grove", "deep_grove", "old_road"}
MEADOW_HERBALISM_ROOMS = {
    "meadow", "mint_meadow", "flower_meadow", "lakeside_meadow"
}
HERBALISM_ROOMS = {
    "herbalist_hut", "meadow", "mint_meadow", "flower_meadow",
    "lakeside_meadow", "whisper_grove", "deep_grove",
    "riverbank", "lake_shore", "old_road"
}

ENDGAME_FISH_UNLOCKS = {
    "river": (
        (100, "soulfin_trout"),
        (140, "runic_sturgeon"),
        (180, "chrono_eel"),
        (200, "eternal_salmon"),
    ),
    "lake": (
        (100, "crystal_carp"),
        (140, "moon_pike"),
        (180, "starfin_char"),
        (200, "mirror_leviathan"),
    ),
    "sea": (
        (100, "storm_cod"),
        (140, "abyss_halibut"),
        (180, "void_turbot"),
        (200, "crown_monkfish"),
    ),
    "ocean": (
        (100, "celestial_tuna"),
        (120, "dragon_mahi"),
        (140, "abyss_tuna"),
        (160, "storm_marlin"),
        (180, "moon_leviathan"),
        (200, "eternal_coelacanth"),
    ),
}

BASE_FISH_MIN_TOOL_LEVELS = {
    # Zwykły Tuńczyk jest dużym oceanicznym połowem
    # i nie powinien pojawiać się na niskich levelach Wędki.
    "tuna": 80,
}

MORE_FISH_UNLOCKS = {
    "river": (
        (1, "river_bleak"),
        (5, "stone_loach"),
        (15, "river_bream"),
        (30, "brown_trout"),
        (50, "river_taimen"),
        (75, "emerald_barbel"),
        (110, "spirit_grayling"),
        (150, "bloodfin_salmon"),
        (175, "star_river_eel"),
        (200, "eternal_river_dragon"),
    ),
    "lake": (
        (1, "lake_gudgeon"),
        (8, "lake_smelt"),
        (20, "blue_bream"),
        (35, "golden_tench"),
        (55, "deepwater_pike"),
        (80, "crystal_whitefish"),
        (110, "moon_carp"),
        (150, "astral_pike"),
        (175, "mirror_sturgeon"),
        (200, "eternal_lake_serpent"),
    ),
    "sea": (
        (1, "sand_eel"),
        (10, "garfish"),
        (20, "sea_bream"),
        (35, "bluefish"),
        (55, "conger_eel"),
        (80, "red_snapper"),
        (110, "storm_herring"),
        (150, "abyss_conger"),
        (175, "void_sole"),
        (200, "eternal_sea_drake"),
    ),
    "ocean": (
        (1, "flying_fish"),
        (15, "bonito"),
        (30, "yellowfin_tuna"),
        (50, "king_mackerel"),
        (70, "marlin_black"),
        (90, "opah"),
        (120, "celestial_swordfish"),
        (150, "astral_sunfish"),
        (180, "void_marlin"),
        (200, "world_leviathan"),
    ),
}

ENDGAME_ORE_UNLOCKS = (
    (100, "cobalt_ore"),
    (120, "runestone_ore"),
    (140, "dragonsteel_ore"),
    (160, "astral_ore"),
    (180, "void_ore"),
    (200, "eternium_ore"),
)

ENDGAME_WOOD_UNLOCKS = (
    (100, "runewood_log"),
    (120, "dragonwood_log"),
    (140, "astralwood_log"),
    (160, "voidwood_log"),
    (180, "starheart_log"),
    (200, "eternal_worldwood_log"),
)

ENDGAME_HERB_UNLOCKS = (
    (100, "sunfire_bloom"),
    (120, "dragon_sage"),
    (140, "astral_orchid"),
    (160, "void_lotus"),
    (180, "phoenix_crown"),
    (200, "eternal_blossom"),
)

def unlocked_resource_pool(
    base_items,
    unlocks,
    tool_level,
):
    result = []
    tool_level = int(tool_level)

    for item_id in base_items:
        minimum = int(
            BASE_FISH_MIN_TOOL_LEVELS.get(item_id, 1)
        )
        if tool_level >= minimum and item_id not in result:
            result.append(item_id)

    for required_level, item_id in unlocks:
        if (
            tool_level >= int(required_level)
            and item_id not in result
        ):
            result.append(item_id)

    return tuple(result)


def add_more_fish_to_pool(pool, habitat, tool_level):
    result = list(pool)
    for required_level, item_id in MORE_FISH_UNLOCKS.get(habitat, ()):
        if int(tool_level) >= int(required_level) and item_id not in result:
            result.append(item_id)
    for required_level, item_id, _name in WORLD_FISH_UNLOCKS.get(habitat, ()):
        if int(tool_level) >= int(required_level) and item_id not in result:
            result.append(item_id)
    return tuple(result)

WORLD_FISH_UNLOCKS = {
    "river": (
        (1, 'world_arapaima', 'Arapaima'),
        (5, 'world_red_bellied_piranha', 'Pirania czerwonobrzucha'),
        (10, 'world_black_piranha', 'Pirania czarna'),
        (15, 'world_pacu', 'Pacu'),
        (20, 'world_tambaqui', 'Tambaqui'),
        (25, 'world_golden_dorado', 'Dorado złociste'),
        (30, 'world_peacock_bass', 'Bass pawiooki'),
        (35, 'world_nile_perch', 'Okoń nilowy'),
        (40, 'world_goliath_tigerfish', 'Tygrysica goliat'),
        (45, 'world_mahseer', 'Mahseer'),
        (50, 'world_rohu', 'Rohu'),
        (55, 'world_catla', 'Katla'),
        (60, 'world_giant_snakehead', 'Wężogłów olbrzymi'),
        (65, 'world_giant_gourami', 'Gurami olbrzymi'),
        (70, 'world_clown_knifefish', 'Nożowiec chitala'),
        (75, 'world_electric_eel', 'Węgorz elektryczny'),
        (80, 'world_alligator_gar', 'Niszczuka krokodyla'),
        (85, 'world_american_paddlefish', 'Wiosłonos amerykański'),
        (90, 'world_bowfin', 'Amia'),
        (95, 'world_muskellunge', 'Muskellunge'),
        (100, 'world_brook_trout', 'Pstrąg źródlany'),
        (105, 'world_rainbow_trout', 'Pstrąg tęczowy'),
        (110, 'world_chinook_salmon', 'Łosoś królewski'),
        (115, 'world_sockeye_salmon', 'Łosoś nerka'),
        (120, 'world_coho_salmon', 'Łosoś kiżucz'),
        (125, 'world_chum_salmon', 'Łosoś keta'),
        (130, 'world_pink_salmon', 'Łosoś różowy'),
        (135, 'world_cutthroat_trout', 'Pstrąg łososiowy'),
        (140, 'world_freshwater_drum', 'Kulbak słodkowodny'),
        (145, 'world_blue_catfish', 'Sum błękitny'),
        (150, 'world_channel_catfish', 'Sum kanałowy'),
        (155, 'world_flathead_catfish', 'Sum płaskogłowy'),
        (160, 'world_grass_carp', 'Amur biały'),
        (165, 'world_bighead_carp', 'Tołpyga pstra'),
        (170, 'world_silver_carp', 'Tołpyga biała'),
        (175, 'world_black_carp', 'Amur czarny'),
        (180, 'world_wels_catfish', 'Sum europejski'),
        (185, 'world_freshwater_stingray', 'Płaszczka słodkowodna'),
        (195, 'world_giant_barb', 'Brzana olbrzymia'),
        (200, 'world_mekong_giant_catfish', 'Sum mekongski'),
    ),
    "lake": (
        (1, 'world_largemouth_bass', 'Bass wielkogębowy'),
        (5, 'world_smallmouth_bass', 'Bass małogębowy'),
        (10, 'world_black_crappie', 'Pomoxis czarny'),
        (15, 'world_white_crappie', 'Pomoxis biały'),
        (20, 'world_bluegill', 'Bass słoneczny'),
        (25, 'world_pumpkinseed', 'Bass dyniowy'),
        (30, 'world_yellow_perch', 'Okoń żółty'),
        (35, 'world_walleye', 'Sandacz amerykański'),
        (40, 'world_sauger', 'Sandacz kanadyjski'),
        (45, 'world_kokanee_salmon', 'Kokanee'),
        (50, 'world_cisco', 'Sielawa amerykańska'),
        (55, 'world_lake_sturgeon', 'Jesiotr jeziorowy'),
        (60, 'world_brown_bullhead', 'Sumik brunatny'),
        (65, 'world_black_bullhead', 'Sumik czarny'),
        (70, 'world_yellow_bullhead', 'Sumik żółty'),
        (75, 'world_nile_tilapia', 'Tilapia nilowa'),
        (80, 'world_mozambique_tilapia', 'Tilapia mozambicka'),
        (85, 'world_blue_tilapia', 'Tilapia niebieska'),
        (90, 'world_oscar_cichlid', 'Pielęgnica pawiooka'),
        (95, 'world_discus', 'Paletka'),
        (100, 'world_freshwater_angelfish', 'Skalar'),
        (105, 'world_silver_arowana', 'Arowana srebrna'),
        (110, 'world_asian_arowana', 'Arowana azjatycka'),
        (115, 'world_giant_barbel_siam', 'Brzana syjamska'),
        (120, 'world_giant_freshwater_whipray', 'Płaszczka rzeczna olbrzymia'),
        (125, 'world_pangas_catfish', 'Panga'),
        (130, 'world_redtail_catfish', 'Sum czerwonoogonowy'),
        (135, 'world_ripsaw_catfish', 'Sum kolczasty'),
        (140, 'world_payara', 'Payara'),
        (145, 'world_wolf_fish', 'Trahira'),
        (150, 'world_arctic_grayling', 'Lipień arktyczny'),
        (155, 'world_lake_chub', 'Jelec jeziorowy'),
        (160, 'world_round_whitefish', 'Sieja okrągła'),
        (165, 'world_inconnu', 'Nelma'),
        (170, 'world_huchen', 'Głowacica'),
        (175, 'world_ide_world', 'Jaź syberyjski'),
        (180, 'world_golden_mahseer', 'Mahseer złoty'),
        (185, 'world_marble_trout', 'Pstrąg marmurkowy'),
        (195, 'world_taimen', 'Tajmień syberyjski'),
        (200, 'world_chinese_perch', 'Okoń chiński'),
    ),
    "sea": (
        (1, 'world_atlantic_tarpon', 'Tarpon atlantycki'),
        (5, 'world_bonefish', 'Albula'),
        (10, 'world_permit_fish', 'Permit'),
        (15, 'world_common_snook', 'Snook'),
        (20, 'world_red_drum', 'Kulbin czerwony'),
        (25, 'world_black_drum', 'Kulbin czarny'),
        (30, 'world_striped_bass', 'Moron prążkowany'),
        (35, 'world_atlantic_croaker', 'Kulbin atlantycki'),
        (40, 'world_sheepshead', 'Sargus owczy'),
        (45, 'world_pompano', 'Pompan'),
        (50, 'world_greater_amberjack', 'Seriola olbrzymia'),
        (55, 'world_yellowtail_snapper', 'Lucjan żółtoogonowy'),
        (60, 'world_mangrove_snapper', 'Lucjan namorzynowy'),
        (65, 'world_lane_snapper', 'Lucjan pręgowany'),
        (70, 'world_red_grouper', 'Strzępiel czerwony'),
        (75, 'world_goliath_grouper', 'Strzępiel goliat'),
        (80, 'world_nassau_grouper', 'Strzępiel nassauski'),
        (85, 'world_european_conger', 'Konger europejski'),
        (90, 'world_mediterranean_moray', 'Murena śródziemnomorska'),
        (95, 'world_giant_moray', 'Murena olbrzymia'),
        (100, 'world_red_lionfish', 'Skrzydlica ognista'),
        (105, 'world_stonefish', 'Szkaradnica'),
        (110, 'world_scorpionfish', 'Skorpena'),
        (115, 'world_queen_triggerfish', 'Rogatnica królewska'),
        (120, 'world_clown_triggerfish', 'Rogatnica klaun'),
        (125, 'world_bumphead_parrotfish', 'Papugoryba garbogłowa'),
        (130, 'world_napoleon_wrasse', 'Wargacz garbogłowy'),
        (135, 'world_corkwing_wrasse', 'Wargacz korkowy'),
        (140, 'world_atlantic_bonito', 'Bonito atlantyckie'),
        (145, 'world_spanish_mackerel', 'Makrela hiszpańska'),
        (150, 'world_atlantic_mackerel', 'Makrela atlantycka'),
        (155, 'world_horse_mackerel', 'Ostrobok'),
        (160, 'world_capelin', 'Gromadnik'),
        (165, 'world_atlantic_saury', 'Sajra atlantycka'),
        (170, 'world_john_dory', 'Piotrosz'),
        (175, 'world_tub_gurnard', 'Kurek czerwony'),
        (180, 'world_wolffish', 'Zębacz pasiasty'),
        (185, 'world_lumpsucker', 'Tasza'),
        (195, 'world_atlantic_anglerfish', 'Żabnica atlantycka'),
        (200, 'world_atlantic_halibut_world', 'Halibut atlantycki'),
    ),
    "ocean": (
        (1, 'world_blue_marlin', 'Marlin błękitny'),
        (5, 'world_white_marlin', 'Marlin biały'),
        (10, 'world_striped_marlin', 'Marlin pasiasty'),
        (15, 'world_longbill_spearfish', 'Włócznik długodzioby'),
        (20, 'world_shortbill_spearfish', 'Włócznik krótkodzioby'),
        (25, 'world_atlantic_bluefin_tuna_world', 'Tuńczyk błękitnopłetwy atlantycki'),
        (30, 'world_southern_bluefin_tuna', 'Tuńczyk błękitnopłetwy południowy'),
        (35, 'world_skipjack_tuna', 'Bonito pasiaste'),
        (40, 'world_blackfin_tuna', 'Tuńczyk czarnopłetwy'),
        (45, 'world_longtail_tuna', 'Tuńczyk długogonowy'),
        (50, 'world_escolar', 'Eskolar'),
        (55, 'world_oilfish', 'Kostropak'),
        (60, 'world_oarfish', 'Wstęgor królewski'),
        (65, 'world_lancetfish', 'Lancetnik długonosy'),
        (70, 'world_pomfret', 'Pomfret'),
        (75, 'world_remora', 'Podnawka'),
        (80, 'world_pilot_fish', 'Pilot'),
        (85, 'world_blue_shark', 'Żarłacz błękitny'),
        (90, 'world_oceanic_whitetip_shark', 'Żarłacz białopłetwy oceaniczny'),
        (95, 'world_common_thresher', 'Kosogon pospolity'),
        (100, 'world_bigeye_thresher', 'Kosogon wielkooki'),
        (105, 'world_porbeagle', 'Żarłacz śledziowy'),
        (110, 'world_greenland_shark', 'Rekin polarny'),
        (115, 'world_salmon_shark', 'Rekin łososiowy'),
        (120, 'world_goblin_shark', 'Rekin chochlik'),
        (125, 'world_megamouth_shark', 'Rekin wielkogębowy'),
        (130, 'world_cookiecutter_shark', 'Rekin foremkowy'),
        (135, 'world_bluntnose_sixgill', 'Sześcioszpar szary'),
        (140, 'world_frilled_shark', 'Chlamida'),
        (145, 'world_whale_shark', 'Rekin wielorybi'),
        (150, 'world_manta_ray', 'Manta oceaniczna'),
        (155, 'world_spotted_eagle_ray', 'Orleń cętkowany'),
        (160, 'world_devil_ray', 'Diabeł morski'),
        (165, 'world_sunfish_sharptail', 'Samogłów ostroogonowy'),
        (170, 'world_slender_sunfish', 'Samogłów smukły'),
        (175, 'world_antarctic_toothfish', 'Antarktyczny kłykacz'),
        (180, 'world_patagonian_toothfish', 'Kłykacz patagoński'),
        (185, 'world_orange_roughy', 'Gardłosz atlantycki'),
        (195, 'world_grenadier', 'Buławik'),
        (200, 'world_coelacanth_world', 'Latimeria'),
    ),
}

WORLD_HERB_UNLOCKS = {
    "meadow": (
        (1, 'world_rosemary', 'Rozmaryn'),
        (10, 'world_thyme', 'Tymianek'),
        (20, 'world_basil', 'Bazylia'),
        (30, 'world_oregano', 'Oregano'),
        (40, 'world_parsley', 'Pietruszka'),
        (50, 'world_dill', 'Koper'),
        (60, 'world_coriander', 'Kolendra'),
        (70, 'world_fennel', 'Koper włoski'),
        (80, 'world_tarragon', 'Estragon'),
        (90, 'world_marjoram', 'Majeranek'),
        (100, 'world_savory', 'Cząber'),
        (110, 'world_chives', 'Szczypiorek'),
        (120, 'world_garlic', 'Czosnek'),
        (130, 'world_ginger', 'Imbir'),
        (140, 'world_turmeric', 'Kurkuma'),
        (150, 'world_galangal', 'Galangal'),
        (160, 'world_cardamom', 'Kardamon'),
        (170, 'world_clove', 'Goździk'),
        (190, 'world_vanilla', 'Wanilia'),
        (200, 'world_saffron', 'Szafran'),
    ),
    "water": (
        (1, 'world_lemongrass', 'Trawa cytrynowa'),
        (10, 'world_aloe_vera', 'Aloes'),
        (20, 'world_calendula', 'Nagietek'),
        (30, 'world_echinacea', 'Jeżówka'),
        (40, 'world_st_johns_wort', 'Dziurawiec'),
        (50, 'world_ribwort_plantain', 'Babka lancetowata'),
        (60, 'world_dandelion', 'Mniszek lekarski'),
        (70, 'world_burdock', 'Łopian'),
        (80, 'world_horsetail', 'Skrzyp polny'),
        (90, 'world_elderflower', 'Kwiat bzu czarnego'),
        (100, 'world_hawthorn', 'Głóg'),
        (110, 'world_rosehip', 'Dzika róża'),
        (120, 'world_hibiscus', 'Hibiskus'),
        (130, 'world_jasmine', 'Jaśmin'),
        (140, 'world_arnica', 'Arnika'),
        (150, 'world_comfrey', 'Żywokost'),
        (160, 'world_mugwort', 'Bylica pospolita'),
        (170, 'world_wormwood', 'Piołun'),
        (190, 'world_skullcap', 'Tarczyca bajkalska'),
        (200, 'world_passionflower', 'Męczennica'),
    ),
    "forest": (
        (1, 'world_hops', 'Chmiel'),
        (10, 'world_licorice_root', 'Lukrecja'),
        (20, 'world_marshmallow_root', 'Prawoślaz'),
        (30, 'world_fenugreek', 'Kozieradka'),
        (40, 'world_cumin', 'Kmin rzymski'),
        (50, 'world_anise', 'Anyż'),
        (60, 'world_star_anise', 'Anyż gwiazdkowy'),
        (70, 'world_black_cumin', 'Czarnuszka'),
        (80, 'world_sesame', 'Sezam'),
        (90, 'world_flax', 'Len'),
        (100, 'world_chia', 'Chia'),
        (110, 'world_amaranth', 'Amarantus'),
        (120, 'world_quinoa', 'Komosa ryżowa'),
        (130, 'world_maca', 'Maca'),
        (140, 'world_guarana', 'Guarana'),
        (150, 'world_yerba_mate', 'Yerba mate'),
        (160, 'world_tea_leaf', 'Liść herbaty'),
        (170, 'world_coffee_berry', 'Owoc kawowca'),
        (190, 'world_cocoa_pod', 'Owoc kakaowca'),
        (200, 'world_kola_nut', 'Orzech kola'),
    ),
    "deep": (
        (1, 'world_holy_basil', 'Tulsi'),
        (10, 'world_ashwagandha', 'Ashwagandha'),
        (20, 'world_moringa', 'Moringa'),
        (30, 'world_neem', 'Neem'),
        (40, 'world_gotu_kola', 'Gotu kola'),
        (50, 'world_bacopa', 'Bakopa'),
        (60, 'world_shatavari', 'Shatavari'),
        (70, 'world_rhodiola', 'Różeniec górski'),
        (80, 'world_eleuthero', 'Eleuterokok'),
        (90, 'world_astragalus', 'Traganek'),
        (100, 'world_milk_thistle', 'Ostropest plamisty'),
        (110, 'world_artichoke_leaf', 'Liść karczocha'),
        (120, 'world_gentian', 'Goryczka'),
        (130, 'world_angelica', 'Arcydzięgiel'),
        (140, 'world_juniper_berry', 'Jagoda jałowca'),
        (150, 'world_bay_leaf', 'Liść laurowy'),
        (160, 'world_olive_leaf', 'Liść oliwny'),
        (170, 'world_eucalyptus_leaf', 'Liść eukaliptusa'),
        (190, 'world_myrrh', 'Mirra'),
        (200, 'world_frankincense', 'Olibanum'),
    ),
}

WORLD_WOOD_UNLOCKS = {
    "beginner": (
        (1, 'world_norway_spruce', 'Pień świerku pospolitego'),
        (7, 'world_silver_fir', 'Pień jodły pospolitej'),
        (13, 'world_european_larch', 'Pień modrzewia europejskiego'),
        (19, 'world_douglas_fir', 'Pień daglezji'),
        (25, 'world_western_hemlock', 'Pień choiny zachodniej'),
        (31, 'world_mediterranean_cypress', 'Pień cyprysa'),
        (37, 'world_juniper_wood', 'Pień jałowca'),
        (43, 'world_black_locust', 'Pień robinii akacjowej'),
        (49, 'world_acacia_wood', 'Pień akacji'),
        (55, 'world_american_sycamore', 'Pień platana amerykańskiego'),
        (61, 'world_elm_wood', 'Pień wiązu'),
        (67, 'world_hornbeam_wood', 'Pień grabu'),
        (73, 'world_basswood', 'Pień lipy amerykańskiej'),
        (79, 'world_aspen_wood', 'Pień osiki'),
        (85, 'world_cottonwood', 'Pień topoli bawełnianej'),
    ),
    "forest": (
        (20, 'world_cherry_wood', 'Pień wiśni'),
        (26, 'world_apple_wood', 'Pień jabłoni'),
        (32, 'world_pear_wood', 'Pień gruszy'),
        (38, 'world_plum_wood', 'Pień śliwy'),
        (44, 'world_olive_wood', 'Pień oliwki'),
        (50, 'world_eucalyptus_wood', 'Pień eukaliptusa'),
        (56, 'world_rubberwood', 'Pień kauczukowca'),
        (62, 'world_cork_oak', 'Pień dębu korkowego'),
        (68, 'world_white_oak', 'Pień dębu białego'),
        (74, 'world_red_oak', 'Pień dębu czerwonego'),
        (80, 'world_sugar_maple', 'Pień klonu cukrowego'),
        (86, 'world_red_maple', 'Pień klonu czerwonego'),
        (92, 'world_hickory', 'Pień hikory'),
        (98, 'world_pecan_wood', 'Pień pekana'),
        (104, 'world_rosewood', 'Pień palisandru'),
    ),
    "deep": (
        (60, 'world_padauk', 'Pień padouku'),
        (67, 'world_wenge', 'Pień wenge'),
        (74, 'world_iroko', 'Pień iroko'),
        (81, 'world_sapele', 'Pień sapeli'),
        (88, 'world_merbau', 'Pień merbau'),
        (95, 'world_bubinga', 'Pień bubingi'),
        (102, 'world_zebrawood', 'Pień zebrano'),
        (109, 'world_jatoba', 'Pień jatoby'),
        (116, 'world_purpleheart', 'Pień amarantowca'),
        (123, 'world_greenheart', 'Pień greenheart'),
        (130, 'world_lignum_vitae', 'Pień gwajakowca'),
        (137, 'world_sandalwood', 'Pień sandałowca'),
        (144, 'world_agarwood', 'Drewno agarowe'),
        (151, 'world_koa', 'Pień koa'),
        (158, 'world_paulownia', 'Pień paulowni'),
        (165, 'world_balsa', 'Pień balsy'),
        (172, 'world_baobab', 'Pień baobabu'),
        (179, 'world_kauri', 'Pień kauri'),
        (186, 'world_jarrah', 'Pień jarrah'),
        (193, 'world_tasmanian_blackwood', 'Pień akacji czarnej tasmańskiej'),
    ),
}

WORLD_ORE_UNLOCKS = (
    (5, 5, 'world_cassiterite', 'Ruda cyny - kasyteryt'),
    (10, 10, 'world_galena', 'Ruda ołowiu - galena'),
    (15, 15, 'world_sphalerite', 'Ruda cynku - sfaleryt'),
    (20, 20, 'world_pentlandite', 'Ruda niklu - pentlandyt'),
    (25, 25, 'world_chromite', 'Ruda chromu - chromit'),
    (30, 30, 'world_pyrolusite', 'Ruda manganu - piroluzyt'),
    (35, 35, 'world_bauxite', 'Boksyt'),
    (40, 40, 'world_ilmenite', 'Ruda tytanu - ilmenit'),
    (45, 45, 'world_rutile', 'Ruda tytanu - rutyl'),
    (50, 50, 'world_wolframite', 'Ruda wolframu - wolframit'),
    (55, 55, 'world_scheelite', 'Ruda wolframu - scheelit'),
    (60, 60, 'world_molybdenite', 'Ruda molibdenu - molibdenit'),
    (65, 65, 'world_cinnabar', 'Ruda rtęci - cynober'),
    (70, 70, 'world_stibnite', 'Ruda antymonu - antymonit'),
    (75, 75, 'world_arsenopyrite', 'Arsenopiryt'),
    (80, 80, 'world_cobaltite', 'Kobaltyn'),
    (85, 85, 'world_spodumene', 'Ruda litu - spodumen'),
    (90, 90, 'world_lepidolite', 'Ruda litu - lepidolit'),
    (95, 95, 'world_coltan', 'Kolumbit-tantalit'),
    (100, 100, 'world_pyrochlore', 'Ruda niobu - pirochlor'),
    (105, 105, 'world_monazite', 'Monacyt'),
    (110, 110, 'world_bastnasite', 'Bastnazyt'),
    (115, 115, 'world_uraninite', 'Uraninit'),
    (120, 120, 'world_thorite', 'Toryt'),
    (125, 125, 'world_platinum_ore', 'Ruda platyny'),
    (130, 130, 'world_palladium_ore', 'Ruda palladu'),
    (135, 135, 'world_rhodium_ore', 'Ruda rodu'),
    (140, 140, 'world_iridium_ore', 'Ruda irydu'),
    (145, 145, 'world_osmium_ore', 'Ruda osmu'),
    (150, 150, 'world_vanadinite', 'Ruda wanadu - wanadynit'),
    (155, 155, 'world_magnesite', 'Magnezyt'),
    (160, 160, 'world_celestite', 'Celestyn'),
    (165, 165, 'world_barite', 'Baryt'),
    (170, 170, 'world_apatite', 'Apatyt fosforanowy'),
    (175, 175, 'world_native_sulfur', 'Siarka rodzima'),
    (180, 180, 'world_halite', 'Halit'),
    (185, 185, 'world_sylvite', 'Sylwin'),
    (190, 190, 'world_kimberlite', 'Kimberlit diamentonośny'),
    (195, 195, 'world_graphite', 'Grafit'),
    (200, 200, 'world_magnetite_world', 'Magnetyt'),
)


def _world_resource_sell_fields(level):
    level = max(1, min(200, int(level)))
    if level < 100:
        return {"sell_silver": max(5, 5 + level * 2)}
    return {"sell_gold": max(1, (level - 80) // 8)}

def _register_world_resource_items():
    for habitat, rows in WORLD_FISH_UNLOCKS.items():
        for level, item_id, name in rows:
            item = {
                "name": name,
                "type": "resource",
                "price": None,
                "desc": (
                    f"Ryba świata. Łowisko: {habitat}. "
                    f"Wędka level {level}+."
                ),
            }
            item.update(_world_resource_sell_fields(level))
            ITEMS[item_id] = item

    for group, rows in WORLD_HERB_UNLOCKS.items():
        for level, item_id, name in rows:
            item = {
                "name": name,
                "type": "resource",
                "price": None,
                "desc": (
                    f"Roślina świata. Grupa występowania: {group}. "
                    f"Sierp level {level}+."
                ),
            }
            item.update(_world_resource_sell_fields(level))
            ITEMS[item_id] = item

    for group, rows in WORLD_WOOD_UNLOCKS.items():
        for level, item_id, name in rows:
            item = {
                "name": name,
                "type": "resource",
                "price": None,
                "desc": (
                    f"Drewno świata. Grupa występowania: {group}. "
                    f"Piła level {level}+."
                ),
            }
            item.update(_world_resource_sell_fields(level))
            ITEMS[item_id] = item

    for level, floor, item_id, name in WORLD_ORE_UNLOCKS:
        item = {
            "name": name,
            "type": "resource",
            "price": None,
            "desc": (
                f"Ruda lub minerał świata. Kilof level {level}+, "
                f"Kopalnia Głębinowa poziom {floor}+."
            ),
        }
        item.update(_world_resource_sell_fields(level))
        ITEMS[item_id] = item

def unlocked_world_ids(rows, tool_level):
    return tuple(
        item_id
        for required, item_id, _name in rows
        if int(tool_level) >= int(required)
    )

def unlocked_world_ore_ids(tool_level, floor):
    return tuple(
        item_id
        for required_level, required_floor, item_id, _name
        in WORLD_ORE_UNLOCKS
        if int(tool_level) >= int(required_level)
        and int(floor) >= int(required_floor)
    )

FISH_RESOURCE_IDS = {
    # Rzeka
    "small_fish", "river_carp", "river_perch", "dace", "chub", "common_nase",
    "barbel", "ide", "asp", "grayling", "burbot", "pike", "zander",
    "silver_trout", "golden_trout", "salmon", "river_catfish",
    "ancient_sturgeon", "moon_eel",
    # Jezioro
    "lake_roach", "rudd", "crucian_carp", "bream", "tench", "lake_perch",
    "vendace", "whitefish", "lake_char", "lake_trout", "pike", "zander",
    "giant_pike", "freshwater_eel",
    # Morze
    "sprat", "sardine", "anchovy", "herring", "mackerel", "whiting",
    "cod", "hake", "sea_bass", "red_mullet", "haddock", "pollock",
    "flounder", "sole", "halibut", "turbot", "monkfish",
    # Ocean
    "tuna", "albacore", "bigeye_tuna", "mahi_mahi", "wahoo",
    "barracuda", "cobia", "amberjack", "sailfish", "swordfish",
    "bluefin_tuna", "ocean_sunfish", "reef_shark", "mako_shark",
    "tiger_shark", "hammerhead_shark", "great_white_shark", "ghost_marlin",
    # Endgame 100-200
    "soulfin_trout", "runic_sturgeon", "chrono_eel", "eternal_salmon",
    "crystal_carp", "moon_pike", "starfin_char", "mirror_leviathan",
    "storm_cod", "abyss_halibut", "void_turbot", "crown_monkfish",
    "celestial_tuna", "dragon_mahi", "abyss_tuna", "storm_marlin",
    "moon_leviathan", "eternal_coelacanth",
    # v0.6.98
    "river_bleak", "stone_loach", "river_bream", "brown_trout",
    "river_taimen", "emerald_barbel", "spirit_grayling",
    "bloodfin_salmon", "star_river_eel", "eternal_river_dragon",
    "lake_gudgeon", "lake_smelt", "blue_bream", "golden_tench",
    "deepwater_pike", "crystal_whitefish", "moon_carp",
    "astral_pike", "mirror_sturgeon", "eternal_lake_serpent",
    "sand_eel", "garfish", "sea_bream", "bluefish", "conger_eel",
    "red_snapper", "storm_herring", "abyss_conger", "void_sole",
    "eternal_sea_drake",
    "flying_fish", "bonito", "yellowfin_tuna", "king_mackerel",
    "marlin_black", "opah", "celestial_swordfish", "astral_sunfish",
    "void_marlin", "world_leviathan",
}
ORE_RESOURCE_IDS = {
    "stone_chunk", "copper_ore", "iron_ore",
    "silver_ore", "gold_ore",
    "cobalt_ore", "runestone_ore", "dragonsteel_ore",
    "astral_ore", "void_ore", "eternium_ore",
}
WOOD_RESOURCE_IDS = {
    "fallen_branch", "birch_log", "alder_log", "pine_log", "poplar_log",
    "willow_log", "linden_log", "oak_log", "beech_log", "maple_log",
    "ash_log", "chestnut_log", "walnut_log", "cedar_log", "yew_log",
    "mahogany_log", "teak_log", "redwood_log", "ironwood_log", "ebony_log",
    "silverwood_log", "spiritwood_log", "ancient_heartwood", "worldtree_wood",
    "runewood_log", "dragonwood_log", "astralwood_log",
    "voidwood_log", "starheart_log", "eternal_worldwood_log",
}

HERB_RESOURCE_IDS = {
    "nettle", "chamomile", "mint", "sage", "lavender", "yarrow",
    "lemon_balm", "valerian", "ginseng", "nightshade", "mandrake",
    "moonflower", "soulroot", "phoenix_leaf", "star_moss", "astral_lotus",
    "sunfire_bloom", "dragon_sage", "astral_orchid",
    "void_lotus", "phoenix_crown", "eternal_blossom",
}
HERB_MEADOW_ATLAS = {"nettle", "chamomile", "mint", "yarrow", "lemon_balm", "lavender"}
HERB_FOREST_ATLAS = {"sage", "valerian", "ginseng", "nightshade", "mandrake", "moonflower", "soulroot"}
HERB_WATER_ATLAS = {"mint", "lemon_balm", "star_moss", "moonflower"}
HERB_DEEP_ATLAS = {
    "mandrake", "moonflower", "soulroot", "phoenix_leaf",
    "star_moss", "astral_lotus",
    "sunfire_bloom", "dragon_sage", "astral_orchid",
    "void_lotus", "phoenix_crown", "eternal_blossom",
}

RIVER_FISH_ATLAS = {
    "small_fish", "dace", "river_perch", "chub", "common_nase",
    "river_carp", "barbel", "ide", "asp", "grayling", "burbot",
    "silver_trout", "golden_trout", "pike", "zander", "salmon",
    "river_catfish", "ancient_sturgeon", "moon_eel",
    "soulfin_trout", "runic_sturgeon", "chrono_eel", "eternal_salmon",
    "river_bleak", "stone_loach", "river_bream", "brown_trout",
    "river_taimen", "emerald_barbel", "spirit_grayling",
    "bloodfin_salmon", "star_river_eel", "eternal_river_dragon",
}
LAKE_FISH_ATLAS = {
    "lake_roach", "rudd", "crucian_carp", "bream", "tench",
    "lake_perch", "vendace", "whitefish", "lake_char", "lake_trout",
    "pike", "zander", "giant_pike", "freshwater_eel",
    "crystal_carp", "moon_pike", "starfin_char", "mirror_leviathan",
    "lake_gudgeon", "lake_smelt", "blue_bream", "golden_tench",
    "deepwater_pike", "crystal_whitefish", "moon_carp",
    "astral_pike", "mirror_sturgeon", "eternal_lake_serpent",
}
SEA_FISH_ATLAS = {
    "sprat", "sardine", "anchovy", "herring", "mackerel", "whiting",
    "cod", "hake", "sea_bass", "red_mullet", "haddock", "pollock",
    "flounder", "sole", "halibut", "turbot", "monkfish",
    "storm_cod", "abyss_halibut", "void_turbot", "crown_monkfish",
    "sand_eel", "garfish", "sea_bream", "bluefish", "conger_eel",
    "red_snapper", "storm_herring", "abyss_conger",
    "void_sole", "eternal_sea_drake",
}
OCEAN_FISH_ATLAS = {
    "mackerel", "mahi_mahi", "albacore", "wahoo", "barracuda", "tuna",
    "sailfish", "bigeye_tuna", "cobia", "amberjack", "swordfish",
    "bluefin_tuna", "ocean_sunfish", "reef_shark", "mako_shark",
    "tiger_shark", "hammerhead_shark", "great_white_shark", "ghost_marlin",
    "celestial_tuna", "dragon_mahi", "abyss_tuna",
    "storm_marlin", "moon_leviathan", "eternal_coelacanth",
    "flying_fish", "bonito", "yellowfin_tuna", "king_mackerel",
    "marlin_black", "opah", "celestial_swordfish",
    "astral_sunfish", "void_marlin", "world_leviathan",
}

WOOD_BEGINNER_ATLAS = {
    "fallen_branch", "birch_log", "alder_log", "pine_log", "poplar_log",
    "willow_log", "linden_log", "oak_log", "beech_log", "maple_log",
}
WOOD_FOREST_ATLAS = {
    "linden_log", "oak_log", "beech_log", "maple_log", "ash_log",
    "chestnut_log", "walnut_log", "cedar_log", "yew_log",
    "mahogany_log", "teak_log", "redwood_log", "ironwood_log",
}
WOOD_DEEP_ATLAS = {
    "ash_log", "chestnut_log", "walnut_log", "cedar_log", "yew_log",
    "mahogany_log", "teak_log", "redwood_log", "ironwood_log",
    "ebony_log", "silverwood_log", "spiritwood_log",
    "ancient_heartwood", "worldtree_wood",
    "runewood_log", "dragonwood_log", "astralwood_log",
    "voidwood_log", "starheart_log", "eternal_worldwood_log",
}

WORLD_FISH_IDS = {
    item_id
    for rows in WORLD_FISH_UNLOCKS.values()
    for _level, item_id, _name in rows
}
WORLD_HERB_IDS = {
    item_id
    for rows in WORLD_HERB_UNLOCKS.values()
    for _level, item_id, _name in rows
}
WORLD_WOOD_IDS = {
    item_id
    for rows in WORLD_WOOD_UNLOCKS.values()
    for _level, item_id, _name in rows
}
WORLD_ORE_IDS = {
    item_id
    for _level, _floor, item_id, _name in WORLD_ORE_UNLOCKS
}

FISH_RESOURCE_IDS.update(WORLD_FISH_IDS)
HERB_RESOURCE_IDS.update(WORLD_HERB_IDS)
WOOD_RESOURCE_IDS.update(WORLD_WOOD_IDS)
ORE_RESOURCE_IDS.update(WORLD_ORE_IDS)

RIVER_FISH_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_FISH_UNLOCKS["river"]
)
LAKE_FISH_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_FISH_UNLOCKS["lake"]
)
SEA_FISH_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_FISH_UNLOCKS["sea"]
)
OCEAN_FISH_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_FISH_UNLOCKS["ocean"]
)

HERB_MEADOW_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_HERB_UNLOCKS["meadow"]
)
HERB_WATER_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_HERB_UNLOCKS["water"]
)
HERB_FOREST_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_HERB_UNLOCKS["forest"]
)
HERB_DEEP_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_HERB_UNLOCKS["deep"]
)

WOOD_BEGINNER_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_WOOD_UNLOCKS["beginner"]
)
WOOD_FOREST_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_WOOD_UNLOCKS["forest"]
)
WOOD_DEEP_ATLAS.update(
    item_id for _level, item_id, _name in WORLD_WOOD_UNLOCKS["deep"]
)

# Pełne atlasy zasobów.
# Te zbiory są bezpośrednio oparte na aktywnych RESOURCE_IDS,
# dzięki czemu każda istniejąca ryba, ruda, sztuka drewna i zioło
# zawsze trafia do pełnego widoku atlasu.
FISH_ATLAS_ALL = set(FISH_RESOURCE_IDS)
ORE_ATLAS_ALL = set(ORE_RESOURCE_IDS)
WOOD_ATLAS_ALL = set(WOOD_RESOURCE_IDS)
HERB_ATLAS_ALL = set(HERB_RESOURCE_IDS)

def validate_complete_resource_atlases():
    checks = (
        ("ryby", FISH_RESOURCE_IDS, FISH_ATLAS_ALL),
        ("rudy", ORE_RESOURCE_IDS, ORE_ATLAS_ALL),
        ("drewno", WOOD_RESOURCE_IDS, WOOD_ATLAS_ALL),
        ("zioła", HERB_RESOURCE_IDS, HERB_ATLAS_ALL),
    )
    for label, source_ids, atlas_ids in checks:
        missing = set(source_ids) - set(atlas_ids)
        if missing:
            raise RuntimeError(
                f"Atlas {label} nie zawiera: "
                + ", ".join(sorted(missing))
            )

validate_complete_resource_atlases()

ORE_ATLAS_LEVELS = {
    "stone_chunk": 1,
    "copper_ore": 1,
    "iron_ore": 1,
    "silver_ore": 10,
    "gold_ore": 25,
    "cobalt_ore": 100,
    "runestone_ore": 120,
    "dragonsteel_ore": 140,
    "astral_ore": 160,
    "void_ore": 180,
    "eternium_ore": 200,
}

ORE_MINE_FLOOR_MINIMUMS = {
    "stone_chunk": 1,
    "copper_ore": 1,
    "iron_ore": 10,
    "silver_ore": 25,
    "gold_ore": 50,
    "cobalt_ore": 100,
    "runestone_ore": 120,
    "dragonsteel_ore": 140,
    "astral_ore": 160,
    "void_ore": 180,
    "eternium_ore": 200,
}

for _level, _floor, _item_id, _name in WORLD_ORE_UNLOCKS:
    ORE_ATLAS_LEVELS[_item_id] = _level
    ORE_MINE_FLOOR_MINIMUMS[_item_id] = _floor

RACES = [
    ("Człowiek",
     "Wszechstronny. Wszystkie statystyki startują na równym poziomie. "
     "Pasyw rasowy: +10 procent do zdobywanego Postępu Rozwoju statystyk.",
     10, 10, 10, 10, 10),
    ("Ogr",
     "Bardzo silny i wytrzymały. Wysoka Siła i Kondycja wspierają walkę wręcz. "
     "Pasyw rasowy: +12 procent obrażeń fizycznych.",
     14, 8, 14, 6, 8),
    ("Elf",
     "Bardzo zręczny i inteligentny. Dobrze łączy szybkość z magią. "
     "Pasyw rasowy: +5 punktów procentowych do szansy uniku.",
     8, 14, 9, 13, 11),
    ("Krasnolud",
     "Silny i bardzo odporny. Wysoka Kondycja daje dużo HP, a Siła Woli dobrą obronę magiczną. "
     "Pasyw rasowy: 10 procent redukcji wszystkich otrzymywanych obrażeń.",
     12, 9, 14, 9, 12),
    ("Ork",
     "Urodzony wojownik. Wysoka Siła i Kondycja dają mocne ciosy i dużo HP. "
     "Pasyw rasowy: +10 procent maksymalnego HP.",
     13, 10, 13, 7, 9),
    ("Niziołek",
     "Zręczny i szczęśliwy poszukiwacz. "
     "Pasyw rasowy: +3 punkty procentowe do szansy na bonusowy połów, dodatkową rudę lub dodatkowe drewno.",
     7, 14, 10, 10, 11),
    ("Mroczny Elf",
     "Zręczny i bardzo inteligentny. Dobrze łączy szybkość z magią. "
     "Pasyw rasowy: +10 procent obrażeń magicznych.",
     9, 13, 9, 14, 10),
    ("Gnom",
     "Bardzo inteligentny i odporny magicznie. "
     "Pasyw rasowy: +15 procent maksymalnej Many dla klas magicznych.",
     7, 12, 9, 14, 13),
    ("Smoczy",
     "Silny, wytrzymały i wszechstronny w walce. "
     "Pasyw rasowy: +8 procent wszystkich zadawanych obrażeń, fizycznych i magicznych.",
     13, 9, 13, 10, 10),
    ("Troll",
     "Największa surowa Siła i Kondycja. Jest wolny, ale bardzo trudny do powalenia. "
     "Pasyw rasowy: 12 procent redukcji otrzymywanych obrażeń fizycznych.",
     15, 7, 15, 5, 8),
    ("Diablę",
     "Dobre predyspozycje magiczne i silna więź z energią dusz. "
     "Pasyw rasowy: +10 procent zdobywanego Soul XP Broni Duszy.",
     9, 11, 9, 13, 13),
    ("Aasimar",
     "Bardzo silna Siła Woli i dobra Inteligencja. "
     "Pasyw rasowy: +12 procent obrony magicznej.",
     10, 10, 11, 12, 14),
    ("Driada",
     "Rasa natury nastawiona na życie i odnowę. "
     "Pasyw rasowy: +15 procent mocy wszystkich klasowych umiejętności leczących. "
     "Szczególnie dobrze pasuje do Kapłana i Druida.",
     7, 10, 11, 15, 15),
]

CLASSES = [
    ("Wojownik", "physical", "Miecz Przysięgi", 7),
    ("Berserker", "physical", "Topór Krwi", 9),
    ("Łotrzyk", "physical", "Sztylety Cienia", 6),
    ("Łowca", "physical", "Łuk Echa", 7),
    ("Mnich", "physical", "Rękawice Ducha", 6),
    ("Strażnik", "physical", "Młot Bastionu", 7),
    ("Mag", "magic", "Kostur Arkanów", 7),
    ("Nekromanta", "magic", "Kosa Dusz", 8),
    ("Kapłan", "magic", "Młot Światła", 6),
    ("Czarownik", "magic", "Ostrze Otchłani", 8),
    ("Druid", "magic", "Kostur Korzeni", 6),
    ("Psionik", "magic", "Kryształ Umysłu", 7),
]


CLASS_DESCRIPTIONS = {
    "Wojownik": (
        "Klasa fizyczna. Stabilny wojownik do walki wręcz. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Dobra dla graczy chcących mocnych ciosów, szybkości i dużej ilości HP."
        "Pasyw klasowy: +10 procent obrażeń fizycznych."
    ),
    "Berserker": (
        "Klasa fizyczna nastawiona na bardzo wysokie obrażenia. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Broń Duszy ma wysoki bazowy potencjał ofensywny."
        "Pasyw klasowy: +12 procent obrażeń fizycznych."
    ),
    "Łotrzyk": (
        "Klasa fizyczna nastawiona na szybkość i zwinność. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Dobrze korzysta z wysokiej Zręczności i uników."
        "Pasyw klasowy: +5 punktów procentowych do szansy uniku."
    ),
    "Łowca": (
        "Klasa fizyczna walcząca z dystansu. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Najlepiej współpracuje z rasami o wysokiej Zręczności."
        "Pasyw klasowy: +8 procent obrażeń fizycznych."
    ),
    "Mnich": (
        "Klasa fizyczna oparta na szybkości i kontroli ciała. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Dobrze skaluje się ze Zręcznością oraz Kondycją."
        "Pasyw klasowy: +8 procent mocy klasowych umiejętności leczących."
    ),
    "Strażnik": (
        "Klasa fizyczna nastawiona na przetrwanie. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Dobrze wykorzystuje wysoką Kondycję i cięższy pancerz."
        "Pasyw klasowy: 10 procent redukcji wszystkich otrzymywanych obrażeń."
    ),
    "Mag": (
        "Klasa magiczna. Inteligencja zwiększa Manę i moc czarów, "
        "a Siła Woli obronę magiczną. Automatycznie rozwija wszystkie pięć statystyk."
        "Pasyw klasowy: +10 procent obrażeń magicznych."
    ),
    "Nekromanta": (
        "Klasa magiczna oparta na mrocznej energii i silnych czarach. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Dobrze korzysta z wysokiej Inteligencji."
        "Pasyw klasowy: +15 procent leczenia z umiejętności wysysających życie."
    ),
    "Kapłan": (
        "Klasa magiczna o defensywnym charakterze. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Wysoka Siła Woli wzmacnia obronę magiczną."
        "Pasyw klasowy: +10 procent mocy klasowych umiejętności leczących."
    ),
    "Czarownik": (
        "Ofensywna klasa magiczna z mocną Bronią Duszy. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Dobrze skaluje się z Inteligencją i dużą pulą Many."
        "Pasyw klasowy: +12 procent obrażeń magicznych."
    ),
    "Druid": (
        "Wszechstronna klasa magiczna związana z naturą. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Łączy dobrą moc czarów z obroną magiczną."
        "Pasyw klasowy: +10 procent mocy klasowych umiejętności leczących."
    ),
    "Psionik": (
        "Klasa magiczna oparta na mocy umysłu. "
        "Automatycznie rozwija wszystkie pięć statystyk. "
        "Najlepiej wykorzystuje wysoką Inteligencję i Siłę Woli."
        "Pasyw klasowy: +10 procent obrony magicznej."
    ),
}


CLASS_SKILLS = {'Wojownik': [{'id': 'warrior_power_slash',
               'name': 'Potężne Cięcie',
               'aliases': ['potezne ciecie', 'potężne cięcie', 'power slash'],
               'unlock': 1,
               'kind': 'damage',
               'cooldown': 4,
               'mana': 0,
               'desc': 'Mocny fizyczny cios skalowany Siłą.',
               'scale': 'strength',
               'mult': 1.35},
              {'id': 'warrior_war_cry',
               'name': 'Okrzyk Wojenny',
               'aliases': ['okrzyk wojenny', 'war cry'],
               'unlock': 25,
               'kind': 'boost',
               'cooldown': 12,
               'mana': 0,
               'desc': 'Wzmacnia następną ofensywną umiejętność o 35 procent.',
               'boost': 1.35},
              {'id': 'warrior_unbreakable',
               'name': 'Niezłomność',
               'aliases': ['niezlomnosc', 'niezłomność', 'unbreakable'],
               'unlock': 60,
               'kind': 'guard',
               'cooldown': 15,
               'mana': 0,
               'desc': 'Zmniejsza obrażenia następnego trafienia o dodatkowe 18.',
               'guard': 18}],
 'Berserker': [{'id': 'berserker_blood_swing',
                'name': 'Krwawy Zamach',
                'aliases': ['krwawy zamach', 'blood swing'],
                'unlock': 1,
                'kind': 'damage',
                'cooldown': 5,
                'mana': 0,
                'desc': 'Bardzo mocny cios Siłą, ale kosztuje 4 HP.',
                'scale': 'strength',
                'mult': 1.5,
                'self_damage': 4},
               {'id': 'berserker_blood_fury',
                'name': 'Szał Krwi',
                'aliases': ['szal krwi', 'szał krwi', 'blood fury'],
                'unlock': 25,
                'kind': 'boost',
                'cooldown': 13,
                'mana': 0,
                'desc': 'Wzmacnia następną ofensywną umiejętność o 55 procent.',
                'boost': 1.55},
               {'id': 'berserker_execution',
                'name': 'Egzekucja',
                'aliases': ['egzekucja', 'execution'],
                'unlock': 60,
                'kind': 'execute',
                'cooldown': 10,
                'mana': 0,
                'desc': 'Silny cios, wyjątkowo mocny poniżej 35 procent HP celu.',
                'scale': 'strength',
                'mult': 1.45,
                'execute_mult': 1.9}],
 'Łotrzyk': [{'id': 'rogue_shadow_strike',
              'name': 'Cios z Cienia',
              'aliases': ['cios z cienia', 'shadow strike'],
              'unlock': 1,
              'kind': 'damage',
              'cooldown': 4,
              'mana': 0,
              'desc': 'Szybki atak skalowany Zręcznością.',
              'scale': 'dexterity',
              'mult': 1.38},
             {'id': 'rogue_double_blade',
              'name': 'Podwójne Ostrze',
              'aliases': ['podwojne ostrze', 'podwójne ostrze', 'double blade'],
              'unlock': 25,
              'kind': 'damage',
              'cooldown': 8,
              'mana': 0,
              'desc': 'Seria dwóch cięć jako jeden silny atak.',
              'scale': 'dexterity',
              'mult': 1.68},
             {'id': 'rogue_vanish',
              'name': 'Zniknięcie',
              'aliases': ['znikniecie', 'zniknięcie', 'vanish'],
              'unlock': 60,
              'kind': 'evade',
              'cooldown': 12,
              'mana': 0,
              'desc': 'Gwarantuje unik następnego kontrataku.'}],
 'Łowca': [{'id': 'hunter_precise_shot',
            'name': 'Celny Strzał',
            'aliases': ['celny strzal', 'celny strzał', 'precise shot'],
            'unlock': 1,
            'kind': 'damage',
            'cooldown': 4,
            'mana': 0,
            'desc': 'Precyzyjny atak dystansowy skalowany Zręcznością.',
            'scale': 'dexterity',
            'mult': 1.42},
           {'id': 'hunter_echo_volley',
            'name': 'Salwa Echa',
            'aliases': ['salwa echa', 'echo volley'],
            'unlock': 25,
            'kind': 'damage',
            'cooldown': 8,
            'mana': 0,
            'desc': 'Potężna salwa z Łuku Echa.',
            'scale': 'dexterity',
            'mult': 1.72},
           {'id': 'hunter_instinct',
            'name': 'Instynkt Łowcy',
            'aliases': ['instynkt lowcy', 'instynkt łowcy', 'hunter instinct'],
            'unlock': 60,
            'kind': 'evade',
            'cooldown': 10,
            'mana': 0,
            'desc': 'Gwarantuje unik następnego kontrataku.'}],
 'Mnich': [{'id': 'monk_spirit_punch',
            'name': 'Uderzenie Ducha',
            'aliases': ['uderzenie ducha', 'spirit punch'],
            'unlock': 1,
            'kind': 'damage',
            'cooldown': 3,
            'mana': 0,
            'desc': 'Szybkie uderzenie skalowane Zręcznością.',
            'scale': 'dexterity',
            'mult': 1.32},
           {'id': 'monk_combo',
            'name': 'Seria Ciosów',
            'aliases': ['seria ciosow', 'seria ciosów', 'combo'],
            'unlock': 25,
            'kind': 'damage',
            'cooldown': 7,
            'mana': 0,
            'desc': 'Szybka kombinacja kilku uderzeń.',
            'scale': 'dexterity',
            'mult': 1.65},
           {'id': 'monk_meditation',
            'name': 'Medytacja',
            'aliases': ['medytacja', 'meditation'],
            'unlock': 60,
            'kind': 'heal',
            'cooldown': 16,
            'mana': 0,
            'desc': 'Przywraca 28 procent maksymalnego HP.',
            'heal_pct': 0.28}],
 'Strażnik': [{'id': 'guardian_crushing_blow',
               'name': 'Miażdżący Cios',
               'aliases': ['miazdzacy cios', 'miażdżący cios', 'crushing blow'],
               'unlock': 1,
               'kind': 'damage',
               'cooldown': 4,
               'mana': 0,
               'desc': 'Ciężki fizyczny cios Młotem Bastionu.',
               'scale': 'strength',
               'mult': 1.28},
              {'id': 'guardian_bastion',
               'name': 'Bastion',
               'aliases': ['bastion'],
               'unlock': 25,
               'kind': 'guard',
               'cooldown': 11,
               'mana': 0,
               'desc': 'Zmniejsza obrażenia następnego trafienia o dodatkowe 22.',
               'guard': 22},
              {'id': 'guardian_soul_wall',
               'name': 'Mur Duszy',
               'aliases': ['mur duszy', 'soul wall'],
               'unlock': 60,
               'kind': 'guard',
               'cooldown': 18,
               'mana': 0,
               'desc': 'Potężna osłona redukująca następne trafienie o 35.',
               'guard': 35}],
 'Mag': [{'id': 'mage_arcane_bolt',
          'name': 'Pocisk Arkanów',
          'aliases': ['pocisk arkanow', 'pocisk arkanów', 'arcane bolt'],
          'unlock': 1,
          'kind': 'damage',
          'cooldown': 3,
          'mana': 6,
          'desc': 'Podstawowy czar ofensywny skalowany Inteligencją.',
          'scale': 'intelligence',
          'mult': 1.42},
         {'id': 'mage_chain_energy',
          'name': 'Łańcuch Energii',
          'aliases': ['lancuch energii', 'łańcuch energii', 'chain energy'],
          'unlock': 25,
          'kind': 'damage',
          'cooldown': 7,
          'mana': 12,
          'desc': 'Silny impuls energii magicznej.',
          'scale': 'intelligence',
          'mult': 1.78},
         {'id': 'mage_arcane_barrier',
          'name': 'Bariera Arkanów',
          'aliases': ['bariera arkanow', 'bariera arkanów', 'arcane barrier'],
          'unlock': 60,
          'kind': 'guard',
          'cooldown': 13,
          'mana': 10,
          'desc': 'Magiczna bariera redukująca następne trafienie o 24.',
          'guard': 24}],
 'Nekromanta': [{'id': 'necro_death_touch',
                 'name': 'Dotyk Śmierci',
                 'aliases': ['dotyk smierci', 'dotyk śmierci', 'death touch'],
                 'unlock': 1,
                 'kind': 'damage',
                 'cooldown': 4,
                 'mana': 6,
                 'desc': 'Mroczny atak magiczny skalowany Inteligencją.',
                 'scale': 'intelligence',
                 'mult': 1.38},
                {'id': 'necro_soul_drain',
                 'name': 'Wysysanie Duszy',
                 'aliases': ['wysysanie duszy', 'soul drain'],
                 'unlock': 25,
                 'kind': 'drain',
                 'cooldown': 8,
                 'mana': 10,
                 'desc': 'Zadaje obrażenia i leczy za 45 procent zadanych obrażeń.',
                 'scale': 'intelligence',
                 'mult': 1.45,
                 'drain_pct': 0.45},
                {'id': 'necro_soul_reaping',
                 'name': 'Żniwo Dusz',
                 'aliases': ['zniwo dusz', 'żniwo dusz', 'soul reaping'],
                 'unlock': 60,
                 'kind': 'execute',
                 'cooldown': 11,
                 'mana': 16,
                 'desc': 'Potężny czar silniejszy poniżej 35 procent HP celu.',
                 'scale': 'intelligence',
                 'mult': 1.65,
                 'execute_mult': 1.75}],
 'Kapłan': [{'id': 'priest_small_heal',
             'name': 'Małe Leczenie',
             'aliases': ['male leczenie', 'małe leczenie', 'small heal'],
             'unlock': 1,
             'kind': 'heal',
             'cooldown': 6,
             'mana': 3,
             'desc': 'Podstawowe leczenie dla początkujących Kapłanów. Przywraca 12 procent maksymalnego HP i rośnie wraz ze Skill Level.',
             'heal_pct': 0.12},
            {'id': 'priest_holy_hammer',
             'name': 'Święty Młot',
             'aliases': ['swiety mlot', 'święty młot', 'holy hammer'],
             'unlock': 1,
             'kind': 'damage',
             'cooldown': 4,
             'mana': 5,
             'desc': 'Święty atak magiczny skalowany Inteligencją.',
             'scale': 'intelligence',
             'mult': 1.28},
            {'id': 'priest_great_heal',
             'name': 'Wielkie Leczenie',
             'aliases': ['wielkie leczenie', 'great heal'],
             'unlock': 25,
             'kind': 'heal',
             'cooldown': 14,
             'mana': 10,
             'desc': 'Przywraca 38 procent maksymalnego HP.',
             'heal_pct': 0.38},
            {'id': 'priest_divine_shield',
             'name': 'Boska Tarcza',
             'aliases': ['boska tarcza', 'divine shield'],
             'unlock': 60,
             'kind': 'guard',
             'cooldown': 17,
             'mana': 12,
             'desc': 'Silna tarcza redukująca następne trafienie o 32.',
             'guard': 32}],
 'Czarownik': [{'id': 'warlock_void_blade',
                'name': 'Ostrze Otchłani',
                'aliases': ['ostrze otchlani', 'ostrze otchłani', 'void blade'],
                'unlock': 1,
                'kind': 'damage',
                'cooldown': 4,
                'mana': 7,
                'desc': 'Ofensywny czar Ostrza Otchłani.',
                'scale': 'intelligence',
                'mult': 1.48},
               {'id': 'warlock_void_flame',
                'name': 'Płomień Otchłani',
                'aliases': ['plomien otchlani', 'płomień otchłani', 'void flame'],
                'unlock': 25,
                'kind': 'damage',
                'cooldown': 8,
                'mana': 13,
                'desc': 'Bardzo mocny magiczny atak.',
                'scale': 'intelligence',
                'mult': 1.85},
               {'id': 'warlock_blood_pact',
                'name': 'Pakt Krwi',
                'aliases': ['pakt krwi', 'blood pact'],
                'unlock': 60,
                'kind': 'damage',
                'cooldown': 12,
                'mana': 8,
                'desc': 'Ekstremalnie silny czar kosztujący dodatkowo 10 procent maksymalnego HP.',
                'scale': 'intelligence',
                'mult': 2.15,
                'self_damage_pct': 0.1}],
 'Druid': [{'id': 'druid_thorns',
            'name': 'Ciernie',
            'aliases': ['ciernie', 'thorns'],
            'unlock': 1,
            'kind': 'damage',
            'cooldown': 4,
            'mana': 5,
            'desc': 'Magiczny atak natury skalowany Inteligencją.',
            'scale': 'intelligence',
            'mult': 1.32},
           {'id': 'druid_nature_heal',
            'name': 'Uzdrowienie Natury',
            'aliases': ['uzdrowienie natury', 'nature heal'],
            'unlock': 25,
            'kind': 'heal',
            'cooldown': 13,
            'mana': 9,
            'desc': 'Przywraca 32 procent maksymalnego HP.',
            'heal_pct': 0.32},
           {'id': 'druid_storm_wrath',
            'name': 'Gniew Burzy',
            'aliases': ['gniew burzy', 'storm wrath'],
            'unlock': 60,
            'kind': 'damage',
            'cooldown': 10,
            'mana': 15,
            'desc': 'Potężny czar burzy.',
            'scale': 'intelligence',
            'mult': 1.92}],
 'Psionik': [{'id': 'psion_mind_pulse',
              'name': 'Impuls Umysłu',
              'aliases': ['impuls umyslu', 'impuls umysłu', 'mind pulse'],
              'unlock': 1,
              'kind': 'damage',
              'cooldown': 3,
              'mana': 5,
              'desc': 'Szybki psioniczny atak skalowany Inteligencją.',
              'scale': 'intelligence',
              'mult': 1.38},
             {'id': 'psion_psionic_wave',
              'name': 'Fala Psioniczna',
              'aliases': ['fala psioniczna', 'psionic wave'],
              'unlock': 25,
              'kind': 'damage',
              'cooldown': 7,
              'mana': 11,
              'desc': 'Silna fala energii umysłu.',
              'scale': 'intelligence',
              'mult': 1.75},
             {'id': 'psion_mind_barrier',
              'name': 'Bariera Umysłu',
              'aliases': ['bariera umyslu', 'bariera umysłu', 'mind barrier'],
              'unlock': 60,
              'kind': 'guard',
              'cooldown': 14,
              'mana': 10,
              'desc': 'Psioniczna bariera redukująca następne obrażenia o 28.',
              'guard': 28}]}


ENDGAME_CLASS_SKILLS = {
    "Wojownik": [
        {
            "id": "warrior_soul_rend",
            "name": "Rozdarcie Duszy",
            "aliases": ["rozdarcie duszy", "soul rend"],
            "natural_tags": ["ciecie", "slash", "dusza"],
            "unlock": 100, "kind": "damage", "cooldown": 8, "mana": 0,
            "desc": "Silne cięcie końcowego etapu Wojownika.",
            "scale": "strength", "mult": 2.10,
        },
        {
            "id": "warrior_iron_wall",
            "name": "Żelazny Mur",
            "aliases": ["zelazny mur", "żelazny mur", "iron wall"],
            "natural_tags": ["tarcza", "oslona", "guard", "obrona"],
            "unlock": 140, "kind": "guard", "cooldown": 13, "mana": 0,
            "desc": "Potężna osłona Wojownika redukująca następne trafienie.",
            "guard": 58,
        },
        {
            "id": "warrior_hero_charge",
            "name": "Szarża Bohatera",
            "aliases": ["szarza bohatera", "szarża bohatera", "hero charge"],
            "natural_tags": ["szarza", "charge", "atak"],
            "unlock": 180, "kind": "damage", "cooldown": 11, "mana": 0,
            "desc": "Mocna szarża skalowana Siłą.",
            "scale": "strength", "mult": 2.55,
        },
        {
            "id": "warrior_final_slash",
            "name": "Ostateczne Cięcie",
            "aliases": ["ostateczne ciecie", "ostateczne cięcie", "final slash"],
            "natural_tags": ["ciecie", "slash", "dobij", "egzekucja"],
            "unlock": 200, "kind": "execute", "cooldown": 16, "mana": 0,
            "desc": "Najsilniejsze cięcie Wojownika, szczególnie groźne na osłabionym celu.",
            "scale": "strength", "mult": 2.55, "execute_mult": 1.90,
        },
    ],
    "Berserker": [
        {
            "id": "berserker_butcher_swing",
            "name": "Rzeźniczy Zamach",
            "aliases": ["rzezniczy zamach", "rzeźniczy zamach", "butcher swing"],
            "natural_tags": ["zamach", "ciecie", "atak"],
            "unlock": 100, "kind": "damage", "cooldown": 8, "mana": 0,
            "desc": "Brutalny zamach Berserkera skalowany Siłą.",
            "scale": "strength", "mult": 2.20,
        },
        {
            "id": "berserker_titan_rage",
            "name": "Szał Tytana",
            "aliases": ["szal tytana", "szał tytana", "titan rage"],
            "natural_tags": ["szal", "rage", "buff", "wzmocnienie"],
            "unlock": 140, "kind": "boost", "cooldown": 15, "mana": 0,
            "desc": "Znacznie wzmacnia następną ofensywną umiejętność.",
            "boost": 1.65,
        },
        {
            "id": "berserker_blood_whirl",
            "name": "Krwawy Wir",
            "aliases": ["krwawy wir", "blood whirl"],
            "natural_tags": ["krew", "wir", "drain", "wysysanie"],
            "unlock": 180, "kind": "drain", "cooldown": 12, "mana": 0,
            "desc": "Krwawy atak, który przywraca część zadanych obrażeń jako HP.",
            "scale": "strength", "mult": 2.45, "drain_pct": 0.35,
        },
        {
            "id": "berserker_blood_apocalypse",
            "name": "Apokalipsa Krwi",
            "aliases": ["apokalipsa krwi", "blood apocalypse"],
            "natural_tags": ["krew", "apokalipsa", "dobij", "egzekucja"],
            "unlock": 200, "kind": "execute", "cooldown": 17, "mana": 0,
            "desc": "Ostateczny atak Berserkera, jeszcze silniejszy na osłabionym przeciwniku.",
            "scale": "strength", "mult": 2.65, "execute_mult": 1.95,
        },
    ],
    "Łotrzyk": [
        {
            "id": "rogue_spectral_cut",
            "name": "Cięcie Widma",
            "aliases": ["ciecie widma", "cięcie widma", "spectral cut"],
            "natural_tags": ["ciecie", "slash", "widmo"],
            "unlock": 100, "kind": "damage", "cooldown": 6, "mana": 0,
            "desc": "Błyskawiczne cięcie skalowane Zręcznością.",
            "scale": "dexterity", "mult": 2.05,
        },
        {
            "id": "rogue_shadow_step",
            "name": "Krok Cienia",
            "aliases": ["krok cienia", "shadow step"],
            "natural_tags": ["unik", "evade", "cien"],
            "unlock": 140, "kind": "evade", "cooldown": 11, "mana": 0,
            "desc": "Gwarantuje unik następnego kontrataku.",
        },
        {
            "id": "rogue_blade_dance",
            "name": "Taniec Ostrzy",
            "aliases": ["taniec ostrzy", "blade dance"],
            "natural_tags": ["ostrza", "taniec", "atak"],
            "unlock": 180, "kind": "damage", "cooldown": 10, "mana": 0,
            "desc": "Seria szybkich cięć skalowana Zręcznością.",
            "scale": "dexterity", "mult": 2.55,
        },
        {
            "id": "rogue_shadow_execution",
            "name": "Egzekucja Cienia",
            "aliases": ["egzekucja cienia", "shadow execution"],
            "natural_tags": ["egzekucja", "execute", "dobij", "cien"],
            "unlock": 200, "kind": "execute", "cooldown": 15, "mana": 0,
            "desc": "Kończący cios Łotrzyka na osłabionego przeciwnika.",
            "scale": "dexterity", "mult": 2.50, "execute_mult": 2.00,
        },
    ],
    "Łowca": [
        {
            "id": "hunter_soul_arrow",
            "name": "Strzała Duszy",
            "aliases": ["strzala duszy", "strzała duszy", "soul arrow"],
            "natural_tags": ["strzala", "arrow", "strzal"],
            "unlock": 100, "kind": "damage", "cooldown": 7, "mana": 0,
            "desc": "Silny strzał skalowany Zręcznością.",
            "scale": "dexterity", "mult": 2.10,
        },
        {
            "id": "hunter_predator_camouflage",
            "name": "Kamuflaż Drapieżcy",
            "aliases": ["kamuflaz drapieznika", "kamuflaż drapieżcy", "predator camouflage"],
            "natural_tags": ["unik", "evade", "kamuflaz"],
            "unlock": 140, "kind": "evade", "cooldown": 12, "mana": 0,
            "desc": "Pozwala uniknąć następnego kontrataku.",
        },
        {
            "id": "hunter_echo_rain",
            "name": "Deszcz Echa",
            "aliases": ["deszcz echa", "echo rain"],
            "natural_tags": ["deszcz", "strzaly", "arrow", "atak"],
            "unlock": 180, "kind": "damage", "cooldown": 11, "mana": 0,
            "desc": "Potężna salwa skalowana Zręcznością.",
            "scale": "dexterity", "mult": 2.60,
        },
        {
            "id": "hunter_final_shot",
            "name": "Strzał Końca",
            "aliases": ["strzal konca", "strzał końca", "final shot"],
            "natural_tags": ["strzal", "shot", "dobij", "egzekucja"],
            "unlock": 200, "kind": "execute", "cooldown": 16, "mana": 0,
            "desc": "Ostateczny strzał Łowcy, wyjątkowo mocny na osłabionym celu.",
            "scale": "dexterity", "mult": 2.55, "execute_mult": 1.90,
        },
    ],
    "Mnich": [
        {
            "id": "monk_soul_fist",
            "name": "Pięść Duszy",
            "aliases": ["piesc duszy", "pięść duszy", "soul fist"],
            "natural_tags": ["piesc", "fist", "atak"],
            "unlock": 100, "kind": "damage", "cooldown": 6, "mana": 0,
            "desc": "Skoncentrowane uderzenie skalowane Siłą.",
            "scale": "strength", "mult": 2.05,
        },
        {
            "id": "monk_master_meditation",
            "name": "Medytacja Mistrza",
            "aliases": ["medytacja mistrza", "master meditation"],
            "natural_tags": ["heal", "leczenie", "medytacja", "odnowa"],
            "unlock": 140, "kind": "heal", "cooldown": 12, "mana": 0,
            "desc": "Zaawansowana medytacja przywracająca dużą część HP.",
            "heal_pct": 0.38,
        },
        {
            "id": "monk_dragon_combo",
            "name": "Smocza Seria",
            "aliases": ["smocza seria", "dragon combo"],
            "natural_tags": ["seria", "combo", "smok", "atak"],
            "unlock": 180, "kind": "damage", "cooldown": 10, "mana": 0,
            "desc": "Szybka seria ciosów o wysokiej sile.",
            "scale": "strength", "mult": 2.50,
        },
        {
            "id": "monk_enlightened_strike",
            "name": "Cios Oświecenia",
            "aliases": ["cios oswiecenia", "cios oświecenia", "enlightened strike"],
            "natural_tags": ["cios", "oswiecenie", "dobij", "egzekucja"],
            "unlock": 200, "kind": "execute", "cooldown": 15, "mana": 0,
            "desc": "Ostateczny cios Mnicha, silniejszy na osłabionym przeciwniku.",
            "scale": "strength", "mult": 2.45, "execute_mult": 1.90,
        },
    ],
    "Strażnik": [
        {
            "id": "guardian_fortress_strike",
            "name": "Uderzenie Fortecy",
            "aliases": ["uderzenie fortecy", "fortress strike"],
            "natural_tags": ["uderzenie", "mlot", "hammer", "atak"],
            "unlock": 100, "kind": "damage", "cooldown": 7, "mana": 0,
            "desc": "Ciężkie uderzenie skalowane Siłą.",
            "scale": "strength", "mult": 2.00,
        },
        {
            "id": "guardian_eternal_bastion",
            "name": "Wieczny Bastion",
            "aliases": ["wieczny bastion", "eternal bastion"],
            "natural_tags": ["tarcza", "bastion", "guard", "obrona"],
            "unlock": 140, "kind": "guard", "cooldown": 14, "mana": 0,
            "desc": "Najpotężniejsza osłona Strażnika.",
            "guard": 72,
        },
        {
            "id": "guardian_bastion_wrath",
            "name": "Gniew Bastionu",
            "aliases": ["gniew bastionu", "bastion wrath"],
            "natural_tags": ["gniew", "mlot", "hammer", "atak"],
            "unlock": 180, "kind": "damage", "cooldown": 11, "mana": 0,
            "desc": "Potężny atak Strażnika.",
            "scale": "strength", "mult": 2.45,
        },
        {
            "id": "guardian_final_hammer",
            "name": "Młot Końca",
            "aliases": ["mlot konca", "młot końca", "final hammer"],
            "natural_tags": ["mlot", "hammer", "dobij", "egzekucja"],
            "unlock": 200, "kind": "execute", "cooldown": 17, "mana": 0,
            "desc": "Ostateczne uderzenie Strażnika.",
            "scale": "strength", "mult": 2.60, "execute_mult": 1.85,
        },
    ],
    "Mag": [
        {
            "id": "mage_arcane_lance",
            "name": "Lanca Arkanów",
            "aliases": ["lanca arkanow", "lanca arkanów", "arcane lance"],
            "natural_tags": ["pocisk", "bolt", "lanca", "arkany"],
            "unlock": 100, "kind": "damage", "cooldown": 6, "mana": 18,
            "desc": "Skoncentrowany czar ofensywny skalowany Inteligencją.",
            "scale": "intelligence", "mult": 2.20,
        },
        {
            "id": "mage_arcane_aegis",
            "name": "Aegis Arkanów",
            "aliases": ["aegis arkanow", "aegis arkanów", "arcane aegis"],
            "natural_tags": ["tarcza", "oslona", "guard", "arkany"],
            "unlock": 140, "kind": "guard", "cooldown": 13, "mana": 16,
            "desc": "Silna magiczna osłona.",
            "guard": 62,
        },
        {
            "id": "mage_mana_tempest",
            "name": "Burza Many",
            "aliases": ["burza many", "mana tempest"],
            "natural_tags": ["burza", "storm", "mana", "atak"],
            "unlock": 180, "kind": "damage", "cooldown": 10, "mana": 26,
            "desc": "Potężny wybuch Many skalowany Inteligencją.",
            "scale": "intelligence", "mult": 2.75,
        },
        {
            "id": "mage_arcane_cataclysm",
            "name": "Kataklizm Arkanów",
            "aliases": ["kataklizm arkanow", "kataklizm arkanów", "arcane cataclysm"],
            "natural_tags": ["kataklizm", "arkany", "czar", "atak"],
            "unlock": 200, "kind": "damage", "cooldown": 16, "mana": 35,
            "desc": "Najsilniejszy czar Maga.",
            "scale": "intelligence", "mult": 3.25,
        },
    ],
    "Nekromanta": [
        {
            "id": "necromancer_bone_curse",
            "name": "Klątwa Kości",
            "aliases": ["klatwa kosci", "klątwa kości", "bone curse"],
            "natural_tags": ["klatwa", "kosci", "czar", "atak"],
            "unlock": 100, "kind": "damage", "cooldown": 7, "mana": 17,
            "desc": "Nekromantyczna klątwa skalowana Inteligencją.",
            "scale": "intelligence", "mult": 2.15,
        },
        {
            "id": "necromancer_greater_drain",
            "name": "Wielkie Wysysanie",
            "aliases": ["wielkie wysysanie", "greater drain"],
            "natural_tags": ["drain", "wysysanie", "leech"],
            "unlock": 140, "kind": "drain", "cooldown": 10, "mana": 20,
            "desc": "Silny drenaż życia.",
            "scale": "intelligence", "mult": 2.25, "drain_pct": 0.50,
        },
        {
            "id": "necromancer_dead_reaping",
            "name": "Żniwo Umarłych",
            "aliases": ["zniwo umarlych", "żniwo umarłych", "reaping of the dead"],
            "natural_tags": ["zniwo", "drain", "wysysanie"],
            "unlock": 180, "kind": "drain", "cooldown": 12, "mana": 28,
            "desc": "Potężne żniwo dusz przywracające część HP.",
            "scale": "intelligence", "mult": 2.70, "drain_pct": 0.55,
        },
        {
            "id": "necromancer_death_sentence",
            "name": "Wyrok Śmierci",
            "aliases": ["wyrok smierci", "wyrok śmierci", "death sentence"],
            "natural_tags": ["smierc", "wyrok", "dobij", "egzekucja"],
            "unlock": 200, "kind": "execute", "cooldown": 17, "mana": 34,
            "desc": "Ostateczny nekromantyczny wyrok na osłabionym celu.",
            "scale": "intelligence", "mult": 2.80, "execute_mult": 2.00,
        },
    ],
    "Kapłan": [
        {
            "id": "priest_light_beam",
            "name": "Promień Światła",
            "aliases": ["promien swiatla", "promień światła", "light beam"],
            "natural_tags": ["swiatlo", "promien", "czar", "atak"],
            "unlock": 100, "kind": "damage", "cooldown": 6, "mana": 17,
            "desc": "Silny święty atak skalowany Inteligencją.",
            "scale": "intelligence", "mult": 2.10,
        },
        {
            "id": "priest_greater_restoration",
            "name": "Wielkie Uzdrowienie",
            "aliases": ["wielkie uzdrowienie", "greater restoration"],
            "natural_tags": ["heal", "leczenie", "uzdrowienie", "odnowa"],
            "unlock": 140, "kind": "heal", "cooldown": 10, "mana": 20,
            "desc": "Potężne leczenie Kapłana.",
            "heal_pct": 0.48,
        },
        {
            "id": "priest_aegis_of_light",
            "name": "Aegis Światła",
            "aliases": ["aegis swiatla", "aegis światła", "aegis of light"],
            "natural_tags": ["tarcza", "oslona", "guard", "swiatlo"],
            "unlock": 180, "kind": "guard", "cooldown": 13, "mana": 24,
            "desc": "Święta osłona redukująca następne trafienie.",
            "guard": 68,
        },
        {
            "id": "priest_miracle_rebirth",
            "name": "Cud Odrodzenia",
            "aliases": ["cud odrodzenia", "miracle of rebirth"],
            "natural_tags": ["heal", "leczenie", "cud", "odrodzenie"],
            "unlock": 200, "kind": "heal", "cooldown": 17, "mana": 32,
            "desc": "Najsilniejsze leczenie Kapłana.",
            "heal_pct": 0.68,
        },
    ],
    "Czarownik": [
        {
            "id": "warlock_void_fire",
            "name": "Ogień Pustki",
            "aliases": ["ogien pustki", "ogień pustki", "void fire"],
            "natural_tags": ["ogien", "plomien", "fire", "pustka"],
            "unlock": 100, "kind": "damage", "cooldown": 7, "mana": 18,
            "desc": "Silny ognisty czar Otchłani.",
            "scale": "intelligence", "mult": 2.25,
        },
        {
            "id": "warlock_void_shield",
            "name": "Tarcza Otchłani",
            "aliases": ["tarcza otchlani", "tarcza otchłani", "void shield"],
            "natural_tags": ["tarcza", "oslona", "guard", "pustka"],
            "unlock": 140, "kind": "guard", "cooldown": 13, "mana": 18,
            "desc": "Mroczna osłona Czarownika.",
            "guard": 58,
        },
        {
            "id": "warlock_abyss_inferno",
            "name": "Inferno Otchłani",
            "aliases": ["inferno otchlani", "inferno otchłani", "abyss inferno"],
            "natural_tags": ["ogien", "plomien", "fire", "inferno"],
            "unlock": 180, "kind": "damage", "cooldown": 11, "mana": 29,
            "desc": "Potężne inferno skalowane Inteligencją.",
            "scale": "intelligence", "mult": 2.85,
        },
        {
            "id": "warlock_hell_judgment",
            "name": "Piekielny Wyrok",
            "aliases": ["piekielny wyrok", "hell judgment"],
            "natural_tags": ["ogien", "wyrok", "dobij", "egzekucja"],
            "unlock": 200, "kind": "execute", "cooldown": 17, "mana": 35,
            "desc": "Ostateczny czar Czarownika, szczególnie silny na osłabionym celu.",
            "scale": "intelligence", "mult": 2.80, "execute_mult": 1.95,
        },
    ],
    "Druid": [
        {
            "id": "druid_ancient_roots",
            "name": "Pradawne Korzenie",
            "aliases": ["pradawne korzenie", "ancient roots"],
            "natural_tags": ["korzenie", "natura", "atak"],
            "unlock": 100, "kind": "damage", "cooldown": 7, "mana": 17,
            "desc": "Pradawna magia natury skalowana Inteligencją.",
            "scale": "intelligence", "mult": 2.10,
        },
        {
            "id": "druid_grove_restoration",
            "name": "Odnowa Gaju",
            "aliases": ["odnowa gaju", "grove restoration"],
            "natural_tags": ["heal", "leczenie", "odnowa", "natura"],
            "unlock": 140, "kind": "heal", "cooldown": 11, "mana": 18,
            "desc": "Silna regeneracja Druida.",
            "heal_pct": 0.42,
        },
        {
            "id": "druid_elemental_storm",
            "name": "Burza Żywiołów",
            "aliases": ["burza zywiolow", "burza żywiołów", "elemental storm"],
            "natural_tags": ["burza", "storm", "zywioly", "atak"],
            "unlock": 180, "kind": "damage", "cooldown": 11, "mana": 28,
            "desc": "Potężna burza żywiołów.",
            "scale": "intelligence", "mult": 2.70,
        },
        {
            "id": "druid_worldtree_wrath",
            "name": "Gniew Drzewa Świata",
            "aliases": ["gniew drzewa swiata", "gniew drzewa świata", "worldtree wrath"],
            "natural_tags": ["gniew", "drzewo", "natura", "atak"],
            "unlock": 200, "kind": "damage", "cooldown": 16, "mana": 34,
            "desc": "Najsilniejszy ofensywny czar Druida.",
            "scale": "intelligence", "mult": 3.10,
        },
    ],
    "Psionik": [
        {
            "id": "psion_mind_blade",
            "name": "Ostrze Umysłu",
            "aliases": ["ostrze umyslu", "ostrze umysłu", "mind blade"],
            "natural_tags": ["ostrze", "umysl", "atak"],
            "unlock": 100, "kind": "damage", "cooldown": 6, "mana": 17,
            "desc": "Psioniczne ostrze skalowane Inteligencją.",
            "scale": "intelligence", "mult": 2.20,
        },
        {
            "id": "psion_mind_fortress",
            "name": "Forteca Umysłu",
            "aliases": ["forteca umyslu", "forteca umysłu", "mind fortress"],
            "natural_tags": ["tarcza", "oslona", "guard", "umysl"],
            "unlock": 140, "kind": "guard", "cooldown": 13, "mana": 18,
            "desc": "Potężna psioniczna osłona.",
            "guard": 64,
        },
        {
            "id": "psion_psyche_rend",
            "name": "Rozdarcie Jaźni",
            "aliases": ["rozdarcie jazni", "rozdarcie jaźni", "psyche rend"],
            "natural_tags": ["rozdarcie", "umysl", "atak"],
            "unlock": 180, "kind": "damage", "cooldown": 10, "mana": 28,
            "desc": "Potężny atak psioniczny.",
            "scale": "intelligence", "mult": 2.75,
        },
        {
            "id": "psion_end_of_thought",
            "name": "Koniec Myśli",
            "aliases": ["koniec mysli", "koniec myśli", "end of thought"],
            "natural_tags": ["mysl", "umysl", "dobij", "egzekucja"],
            "unlock": 200, "kind": "execute", "cooldown": 17, "mana": 35,
            "desc": "Ostateczny psioniczny cios na osłabionego przeciwnika.",
            "scale": "intelligence", "mult": 2.75, "execute_mult": 1.95,
        },
    ],
}

for _class_name, _skills in ENDGAME_CLASS_SKILLS.items():
    CLASS_SKILLS.setdefault(_class_name, []).extend(_skills)


NATURAL_SKILL_INTENTS = {
    "heal": {"kinds": {"heal"}},
    "healing": {"kinds": {"heal"}},
    "lecz": {"kinds": {"heal"}},
    "leczenie": {"kinds": {"heal"}},
    "uzdrow": {"kinds": {"heal"}},
    "uzdrowienie": {"kinds": {"heal"}},
    "tarcza": {"kinds": {"guard"}},
    "oslona": {"kinds": {"guard"}},
    "guard": {"kinds": {"guard"}},
    "obrona": {"kinds": {"guard"}},
    "unik": {"kinds": {"evade"}},
    "evade": {"kinds": {"evade"}},
    "buff": {"kinds": {"boost"}},
    "boost": {"kinds": {"boost"}},
    "wzmocnij": {"kinds": {"boost"}},
    "wzmocnienie": {"kinds": {"boost"}},
    "drain": {"kinds": {"drain"}},
    "wysysanie": {"kinds": {"drain"}},
    "wysysaj": {"kinds": {"drain"}},
    "egzekucja": {"kinds": {"execute"}},
    "execute": {"kinds": {"execute"}},
    "dobij": {"kinds": {"execute"}},
    "ciecie": {"tags": {"ciecie", "slash"}},
    "slash": {"tags": {"ciecie", "slash"}},
    "pocisk": {"tags": {"pocisk", "bolt", "lanca"}},
    "bolt": {"tags": {"pocisk", "bolt", "lanca"}},
    "ogien": {"tags": {"ogien", "plomien", "fire", "inferno"}},
    "plomien": {"tags": {"ogien", "plomien", "fire", "inferno"}},
    "fire": {"tags": {"ogien", "plomien", "fire", "inferno"}},
    "burza": {"tags": {"burza", "storm"}},
    "storm": {"tags": {"burza", "storm"}},
    "mlot": {"tags": {"mlot", "hammer"}},
    "hammer": {"tags": {"mlot", "hammer"}},
    "strzal": {"tags": {"strzal", "strzala", "shot", "arrow"}},
    "strzala": {"tags": {"strzal", "strzala", "shot", "arrow"}},
    "arrow": {"tags": {"strzal", "strzala", "shot", "arrow"}},
}


# 28 trwałych lokacji. Opisy są krótkie i przyjazne czytnikom ekranu.
ROOMS = {
    "square": {
        "zone": "Miasto Dusz", "name": "Plac Dusz",
        "desc": "Centralny plac osady. Nad kamienną fontanną płonie błękitny ogień.",
        "exits": {"north": "north_street", "south": "south_street", "east": "market", "west": "temple"},
    },
    "temple": {
        "zone": "Miasto Dusz", "name": "Świątynia Odrodzenia",
        "desc": "Spokojna świątynia. Polegli bohaterowie odzyskują tutaj świadomość.",
        "exits": {"east": "square", "north": "library", "down": "temple_basement"},
    },
    "temple_basement": {
        "zone": "Podziemia", "name": "Piwnica Świątyni",
        "desc": "Wilgotna piwnica pod Świątynią Odrodzenia. Między skrzyniami słychać piski szczurów.",
        "exits": {"up": "temple"},
    },
    "library": {
        "zone": "Miasto Dusz", "name": "Biblioteka Kronik",
        "desc": "Kamienne regały przechowują kroniki o duszach, rasach i dawnych wojnach.",
        "exits": {"south": "temple", "east": "guild_hall"},
    },
    "guild_hall": {
        "zone": "Gildia Dusz", "name": "Sala Główna Gildii",
        "desc": "Centralny hol Gildii Dusz. Korytarze prowadzą do wyspecjalizowanych sal nauczycieli.",
        "exits": {
            "west": "library",
            "south": "north_street",
            "north": "guild_martial_hall",
            "east": "guild_arcane_chamber",
            "up": "guild_shadow_gallery",
            "down": "guild_sanctuary",
        },
    },
    "guild_martial_hall": {
        "zone": "Gildia Dusz", "name": "Sala Oręża Gildii",
        "desc": "Ciężkie manekiny i stojaki treningowe służą Wojownikom i Berserkerom.",
        "exits": {"south": "guild_hall", "east": "guild_body_hall"},
    },
    "guild_body_hall": {
        "zone": "Gildia Dusz", "name": "Sala Dyscypliny Gildii",
        "desc": "Spokojna sala ćwiczeń ciała i obrony przeznaczona dla Mnichów i Strażników.",
        "exits": {"west": "guild_martial_hall"},
    },
    "guild_arcane_chamber": {
        "zone": "Gildia Dusz", "name": "Komnata Arkanów Gildii",
        "desc": "Runy świecą na ścianach. Tutaj Magowie i Psionicy ćwiczą kontrolę energii.",
        "exits": {"west": "guild_hall", "east": "guild_dark_chamber"},
    },
    "guild_dark_chamber": {
        "zone": "Gildia Dusz", "name": "Komnata Mrocznych Sztuk",
        "desc": "Zabezpieczona sala do nauki Nekromantów i Czarowników.",
        "exits": {"west": "guild_arcane_chamber"},
    },
    "guild_shadow_gallery": {
        "zone": "Gildia Dusz", "name": "Galeria Cieni Gildii",
        "desc": "Wąskie przejścia i cele treningowe służą Łotrzykom i Łowcom.",
        "exits": {"down": "guild_hall"},
    },
    "guild_sanctuary": {
        "zone": "Gildia Dusz", "name": "Sanktuarium Gildii",
        "desc": "Cicha sala natury i światła, w której szkolą się Kapłani i Druidzi.",
        "exits": {"up": "guild_hall"},
    },
    "north_street": {
        "zone": "Miasto Dusz", "name": "Ulica Północna",
        "desc": "Szeroka ulica prowadząca ku dziedzińcowi i północnej bramie.",
        "exits": {"south": "square", "north": "training", "east": "guard_hall", "west": "guild_hall"},
    },
    "guard_hall": {
        "zone": "Miasto Dusz", "name": "Strażnica",
        "desc": "Siedziba miejskiej straży. Na ścianach wiszą mapy okolicznych szlaków.",
        "exits": {"west": "north_street"},
    },
    "training": {
        "zone": "Miasto Dusz", "name": "Dziedziniec Treningowy",
        "desc": "Plac do ćwiczeń. Drewniane manekiny stoją obok północnej bramy.",
        "exits": {"south": "north_street", "north": "north_gate"},
    },
    "north_gate": {
        "zone": "Miasto Dusz", "name": "Północna Brama",
        "desc": "Za ciężką bramą zaczyna się Stary Trakt.",
        "exits": {"south": "training", "north": "old_road"},
    },
    "market": {
        "zone": "Miasto Dusz", "name": "Rynek",
        "desc": "Kupcy sprzedają prowiant, mikstury i podstawowe wyposażenie. Przy kamiennym kantorze działa Bank Dusz Bankiera Aldrena.",
        "exits": {"west": "square", "east": "forge", "south": "inn", "north": "fish_market"},
    },
    "fish_market": {
        "zone": "Miasto Dusz", "name": "Targ Rybny",
        "desc": "Stragany pachną świeżą rybą i mokrymi sieciami. Tutaj sprzedaje się sprzęt wędkarski.",
        "exits": {"south": "market", "east": "harbor"},
    },
    "harbor": {
        "zone": "Miasto Dusz", "name": "Port Dusz",
        "desc": "Drewniane pomosty, kutry i skrzynie rybackie wypełniają miejski port.",
        "exits": {"west": "fish_market", "east": "sea_pier"},
    },
    "sea_pier": {
        "zone": "Wybrzeże", "name": "Morskie Molo",
        "desc": "Długie molo wychodzi nad morze. To łowisko typowych ryb morskich.",
        "exits": {"west": "harbor", "east": "ocean_platform"},
    },
    "ocean_platform": {
        "zone": "Wybrzeże", "name": "Oceaniczna Platforma",
        "desc": "Daleka platforma nad otwartym oceanem. Trafiają się tu wielkie ryby oceaniczne i rekiny.",
        "exits": {"west": "sea_pier"},
    },
    "forge": {
        "zone": "Miasto Dusz", "name": "Kuźnia Dusz",
        "desc": "Młoty uderzają o metal, a Broń Duszy odpowiada cichym rezonansem.",
        "exits": {"west": "market"},
    },
    "inn": {
        "zone": "Miasto Dusz", "name": "Karczma Pod Błękitnym Płomieniem",
        "desc": "Ciepła karczma pełna rozmów podróżników.",
        "exits": {"north": "market", "west": "south_street"},
    },
    "south_street": {
        "zone": "Miasto Dusz", "name": "Ulica Południowa",
        "desc": "Cichsza część miasta prowadząca do południowej bramy.",
        "exits": {"north": "square", "east": "inn", "south": "south_gate"},
    },
    "south_gate": {
        "zone": "Miasto Dusz", "name": "Południowa Brama",
        "desc": "Brama otwiera się na łąki i Gaj Szeptów.",
        "exits": {"north": "south_street", "south": "meadow"},
    },
    "meadow": {
        "zone": "Łąki", "name": "Srebrna Łąka",
        "desc": (
            "Centralna część rozległych łąk. W trawie rosną Pokrzywa, "
            "Rumianek, Mięta, Krwawnik, Melisa i Lawenda. "
            "Na zachodzie leży Łąka Kwiatów, na wschodzie Łąka Mięty, "
            "a na południu Łąka Nadjeziorna."
        ),
        "exits": {
            "north": "south_gate",
            "west": "flower_meadow",
            "east": "mint_meadow",
            "south": "lakeside_meadow",
        },
    },
    "mint_meadow": {
        "zone": "Łąki", "name": "Łąka Mięty",
        "desc": (
            "Wilgotniejsza łąka pachnąca Miętą i Melisą. "
            "To dobre miejsce do Zielarstwa, szczególnie dla początkujących."
        ),
        "exits": {"west": "meadow", "east": "riverbank"},
    },
    "flower_meadow": {
        "zone": "Łąki", "name": "Łąka Kwiatów",
        "desc": (
            "Kolorowa łąka pełna Rumianku, Lawendy i Krwawnika. "
            "Dalej na zachodzie zaczyna się Gaj Szeptów."
        ),
        "exits": {"east": "meadow", "west": "whisper_grove"},
    },
    "lakeside_meadow": {
        "zone": "Łąki", "name": "Łąka Nadjeziorna",
        "desc": (
            "Łąka schodząca ku Srebrnemu Jezioru. "
            "Rosną tu Mięta, Melisa, Rumianek i inne zioła lubiące wilgoć."
        ),
        "exits": {"north": "meadow", "south": "lake_shore"},
    },
    "lake_shore": {
        "zone": "Dzicz", "name": "Brzeg Srebrnego Jeziora",
        "desc": "Spokojne jezioro jest osobnym łowiskiem dla ryb jeziorowych.",
        "exits": {"north": "lakeside_meadow"},
    },
    "whisper_grove": {
        "zone": "Dzicz", "name": "Gaj Szeptów",
        "desc": "Stare drzewa szepczą pod wpływem magicznego wiatru.",
        "exits": {"east": "flower_meadow", "south": "deep_grove", "west": "lumberjack_camp", "north": "herbalist_hut"},
    },
    "herbalist_hut": {
        "zone": "Dzicz", "name": "Chata Zielarki",
        "desc": "Półki są pełne suszonych ziół, fiolek i alchemicznych naczyń.",
        "exits": {"south": "whisper_grove"},
    },
    "lumberjack_camp": {
        "zone": "Dzicz", "name": "Obóz Drwala",
        "desc": "Przy stosach drewna stoi warsztat Drwala Brana. Tutaj kupuje się Piłę.",
        "exits": {"east": "whisper_grove"},
    },
    "deep_grove": {
        "zone": "Dzicz", "name": "Głębia Gaju",
        "desc": "Światło prawie nie dociera między gęste konary.",
        "exits": {"north": "whisper_grove", "east": "hill"},
    },
    "hill": {
        "zone": "Dzicz", "name": "Wzgórze Kamiennych Znaków",
        "desc": "Na szczycie stoją stare kamienie pokryte nieczytelnymi runami.",
        "exits": {"west": "deep_grove", "north": "shrine"},
    },
    "shrine": {
        "zone": "Dzicz", "name": "Zapomniana Kapliczka",
        "desc": "Mała kapliczka poświęcona dawnym strażnikom dusz.",
        "exits": {"south": "hill"},
    },
    "riverbank": {
        "zone": "Dzicz", "name": "Brzeg Rzeki",
        "desc": "Szybka rzeka oddziela łąki od ruin starego pogranicza.",
        "exits": {"west": "mint_meadow", "east": "stone_bridge"},
    },
    "stone_bridge": {
        "zone": "Dzicz", "name": "Kamienny Most",
        "desc": "Popękany most prowadzi na wschodni brzeg.",
        "exits": {"west": "riverbank", "east": "ruined_watchtower"},
    },
    "ruined_watchtower": {
        "zone": "Dzicz", "name": "Ruiny Strażnicy",
        "desc": "Zawalona wieża obserwacyjna została opanowana przez gobliny.",
        "exits": {"west": "stone_bridge", "south": "goblin_camp", "east": "graveyard"},
    },
    "goblin_camp": {
        "zone": "Dzicz", "name": "Obóz Goblinów",
        "desc": "Prymitywne namioty stoją wokół dymiącego ogniska.",
        "exits": {"north": "ruined_watchtower", "south": "cave_entrance"},
    },
    "cave_entrance": {
        "zone": "Podziemia", "name": "Wejście do Kryształowej Jaskini",
        "desc": "Z wnętrza jaskini dochodzi chłód i niebieska poświata.",
        "exits": {"north": "goblin_camp", "down": "cave_tunnel"},
    },
    "cave_tunnel": {
        "zone": "Podziemia", "name": "Kryształowy Tunel",
        "desc": "Ściany tunelu przecinają blade żyły kryształów.",
        "exits": {"up": "cave_entrance", "east": "crystal_chamber"},
    },
    "crystal_chamber": {
        "zone": "Podziemia", "name": "Kryształowa Komnata",
        "desc": "Wysokie kryształy pulsują energią przypominającą energię Broni Duszy.",
        "exits": {"west": "cave_tunnel"},
    },
    "graveyard": {
        "zone": "Dzicz", "name": "Stary Cmentarz",
        "desc": "Pęknięte nagrobki otaczają zejście do zapomnianej krypty.",
        "exits": {"west": "ruined_watchtower", "down": "crypt_entrance"},
    },
    "crypt_entrance": {
        "zone": "Podziemia", "name": "Przedsionek Krypty",
        "desc": "Kamienne schody prowadzą w ciemność.",
        "exits": {"up": "graveyard", "south": "crypt_hall"},
    },
    "crypt_hall": {
        "zone": "Podziemia", "name": "Sala Krypty",
        "desc": "W ścianach znajdują się stare nisze grobowe.",
        "exits": {"north": "crypt_entrance", "down": "crypt_depths"},
    },
    "crypt_depths": {
        "zone": "Podziemia", "name": "Głębia Krypty",
        "desc": "Najstarsza część podziemi. Powietrze drży od niespokojnej energii.",
        "exits": {"up": "crypt_hall"},
    },
    "old_road": {
        "zone": "Dzicz", "name": "Stary Trakt",
        "desc": "Kamienny trakt prowadzi między zarośniętymi słupami granicznymi. Na wschodzie widać wartownię straży.",
        "exits": {"south": "north_gate", "north": "crossroads", "east": "north_watchpost"},
    },
    "north_watchpost": {
        "zone": "Dzicz", "name": "Wartownia Północna",
        "desc": "Drewniana wartownia pilnuje północnego szlaku. Strażnicy obserwują ruch na Starym Trakcie.",
        "exits": {"west": "old_road", "east": "frontier_watchpost"},
    },
    "frontier_watchpost": {
        "zone": "Dzicz", "name": "Wartownia Pogranicza",
        "desc": "Kamienno-drewniany posterunek stoi na granicy bezpiecznych ziem. Dalej zaczyna się teren bandytów.",
        "exits": {"west": "north_watchpost", "east": "bandit_camp"},
    },
    "bandit_camp": {
        "zone": "Dzicz", "name": "Obozowisko Bandytów",
        "desc": "Brudne namioty, skrzynie z łupami i wygasające ogniska tworzą rozległy obóz bandytów.",
        "exits": {"west": "frontier_watchpost"},
    },
    "crossroads": {
        "zone": "Dzicz", "name": "Rozdroże",
        "desc": "Stary drogowskaz wskazuje zachód ku lasom i wschód ku ruinom.",
        "exits": {"south": "old_road", "west": "deep_grove", "east": "ruined_watchtower"},
    },
}

def build_mine_depth_rooms():
    ROOMS["crystal_chamber"]["exits"]["down"] = mine_floor_id(1)

    for floor in range(MINE_MIN_FLOOR, MINE_MAX_FLOOR + 1):
        exits = {
            "up": (
                "crystal_chamber"
                if floor == MINE_MIN_FLOOR
                else mine_floor_id(floor - 1)
            )
        }
        if floor < MINE_MAX_FLOOR:
            exits["down"] = mine_floor_id(floor + 1)

        if floor < 10:
            band = "kamień i miedź"
        elif floor < 25:
            band = "miedź i żelazo"
        elif floor < 50:
            band = "żelazo i srebro"
        elif floor < 100:
            band = "srebro i złoto"
        elif floor < 120:
            band = "złoto i kobalt"
        elif floor < 140:
            band = "kobalt i Kamień Runiczny"
        elif floor < 160:
            band = "Kamień Runiczny i Smocza Stal"
        elif floor < 180:
            band = "Smocza Stal i Ruda Astralna"
        elif floor < 200:
            band = "Ruda Astralna i Ruda Pustki"
        else:
            band = "Ruda Pustki i Eternium"

        wall_text = (
            " Niżej znajduje się ściana do przebicia Kilofem."
            if floor < MINE_MAX_FLOOR
            else " To najgłębszy poziom kopalni."
        )
        ROOMS[mine_floor_id(floor)] = {
            "zone": "Kopalnia Głębinowa",
            "name": f"Kopalnia - poziom {floor}",
            "desc": (
                f"Poziom {floor} z {MINE_MAX_FLOOR}. "
                f"Najczęstsze złoża: {band}." + wall_text
            ),
            "exits": exits,
        }

build_mine_depth_rooms()

ROOMS["jeweler_workshop"] = {
    "zone": "Miasto Dusz",
    "name": "Pracownia Jubilerska",
    "desc": (
        "Jasna pracownia pełna drobnych narzędzi, metalowych opraw "
        "i stołów do wykonywania pierścieni oraz naszyjników. "
        "Pracuje tutaj Jubilerka Mirella."
    ),
    "exits": {"down": "market"},
}
ROOMS["market"]["exits"]["up"] = "jeweler_workshop"

DIRECTION_ALIASES = {
    "n": "north", "north": "north", "północ": "north", "polnoc": "north",
    "s": "south", "south": "south", "południe": "south", "poludnie": "south",
    "e": "east", "east": "east", "wschód": "east", "wschod": "east",
    "w": "west", "west": "west", "zachód": "west", "zachod": "west",
    "u": "up", "up": "up", "góra": "up", "gora": "up",
    "d": "down", "down": "down", "dół": "down", "dol": "down",
}

GUIDE_DESTINATION_ALIASES = {
    # Miasto Dusz
    "plac": "square",
    "centrum": "square",
    "plac dusz": "square",
    "swiatynia": "temple",
    "swiatynia odrodzenia": "temple",
    "elor": "temple",
    "kaplan elor": "temple",
    "piwnica": "temple_basement",
    "piwnica swiatyni": "temple_basement",
    "biblioteka": "library",
    "archiwum": "library",
    "sol": "library",
    "archiwista sol": "library",
    "gildia": "guild_hall",
    "sala gildii": "guild_hall",
    "wojownicy": "guild_martial_hall",
    "berserkerzy": "guild_martial_hall",
    "sala oreza": "guild_martial_hall",
    "garran": "guild_martial_hall",
    "brynja": "guild_martial_hall",
    "mnisi": "guild_body_hall",
    "straznicy": "guild_body_hall",
    "sala dyscypliny": "guild_body_hall",
    "shen": "guild_body_hall",
    "borin": "guild_body_hall",
    "magowie": "guild_arcane_chamber",
    "psionicy": "guild_arcane_chamber",
    "arkany": "guild_arcane_chamber",
    "vaelis": "guild_arcane_chamber",
    "ilyra": "guild_arcane_chamber",
    "nekromanci": "guild_dark_chamber",
    "czarownicy": "guild_dark_chamber",
    "mroczne sztuki": "guild_dark_chamber",
    "morwen": "guild_dark_chamber",
    "nyra": "guild_dark_chamber",
    "lotrzycy": "guild_shadow_gallery",
    "lowcy": "guild_shadow_gallery",
    "galeria cieni": "guild_shadow_gallery",
    "kael": "guild_shadow_gallery",
    "eira": "guild_shadow_gallery",
    "kaplani": "guild_sanctuary",
    "druidzi": "guild_sanctuary",
    "sanktuarium": "guild_sanctuary",
    "aureon": "guild_sanctuary",
    "thalen": "guild_sanctuary",
    "straznica": "guard_hall",
    "arven": "guard_hall",
    "kapitan arven": "guard_hall",
    "trening": "training",
    "manekiny": "training",
    "dziedziniec": "training",
    "brama polnocna": "north_gate",
    "polnocna brama": "north_gate",
    "rynek": "market",
    "targ": "market",
    "market": "market",
    "bank": "market",
    "bank dusz": "market",
    "bankier": "market",
    "bankier aldren": "market",
    "aldren": "market",
    "jubiler": "jeweler_workshop",
    "jubilerka": "jeweler_workshop",
    "mirella": "jeweler_workshop",
    "jubilerka mirella": "jeweler_workshop",
    "pracownia jubilerska": "jeweler_workshop",
    "jubilerstwo": "jeweler_workshop",
    "targ rybny": "fish_market",
    "ryby": "fish_market",
    "tomas": "fish_market",
    "rybak tomas": "fish_market",
    "port": "harbor",
    "port dusz": "harbor",
    "harbor": "harbor",
    "molo": "sea_pier",
    "morskie molo": "sea_pier",
    "ocean": "ocean_platform",
    "platforma": "ocean_platform",
    "platforma oceaniczna": "ocean_platform",
    "kuznia": "forge",
    "kowal": "forge",
    "doran": "forge",
    "kowal doran": "forge",
    "karczma": "inn",
    "gospoda": "inn",
    "elia": "inn",
    "karczmarka elia": "inn",
    "brama poludniowa": "south_gate",
    "poludniowa brama": "south_gate",
    "kucharz": "inn",
    "kucharz marcel": "inn",
    "specjalista gotowania": "inn",
    "mistrz rzemiosla": "forge",
    "haldor": "forge",
    "mistrz wedkarstwa": "fish_market",
    "neris": "fish_market",

    # Dzicz i okolice
    "laka": "meadow",
    "laki": "meadow",
    "srebrna laka": "meadow",
    "laka miety": "mint_meadow",
    "mietowa laka": "mint_meadow",
    "laka kwiatow": "flower_meadow",
    "kwiatowa laka": "flower_meadow",
    "laka nadjeziorna": "lakeside_meadow",
    "nadjeziorna laka": "lakeside_meadow",
    "jezioro": "lake_shore",
    "brzeg jeziora": "lake_shore",
    "gaj": "whisper_grove",
    "gaj szeptow": "whisper_grove",
    "mira": "whisper_grove",
    "zielarka mira": "whisper_grove",
    "liora": "herbalist_hut",
    "zielarka liora": "herbalist_hut",
    "chata zielarki": "herbalist_hut",
    "drwal": "lumberjack_camp",
    "bran": "lumberjack_camp",
    "drwal bran": "lumberjack_camp",
    "glebia gaju": "deep_grove",
    "wzgorze": "hill",
    "kamienne znaki": "hill",
    "kapliczka": "shrine",
    "zapomniana kapliczka": "shrine",
    "astralna brama": "astral_gate",
    "brama astralna": "astral_gate",
    "wieza astralna": "astral_gate",
    "wieża astralna": "astral_gate",
    "wieza": "astral_gate",
    "wieża": "astral_gate",
    "astral": "astral_gate",
    "mityczna krypta": "mythic_crypt_gate",
    "mythic crypt": "mythic_crypt_gate",
    "mityczna wieza astralna": "mythic_astral_gate",
    "mythic astral tower": "mythic_astral_gate",
    "kopalnia krysztalow": "prof_crystal_mine_1",
    "krysztalowa kopalnia": "prof_crystal_mine_1",
    "zatopiona grota": "prof_sunken_grotto_1",
    "pradawny las": "prof_ancient_forest_1",
    "ogrod alchemika": "prof_alchemy_garden_1",
    "rzeka": "riverbank",
    "brzeg rzeki": "riverbank",
    "most": "stone_bridge",
    "kamienny most": "stone_bridge",
    "ruiny": "ruined_watchtower",
    "ruiny straznicy": "ruined_watchtower",
    "gobliny": "goblin_camp",
    "oboz goblinow": "goblin_camp",
    "jaskinia": "cave_entrance",
    "wejscie do jaskini": "cave_entrance",
    "kopalnia glebinowa": "mine_floor_1",
    "toren": "cave_entrance",
    "gornik toren": "cave_entrance",
    "mistrz gornictwa": "cave_entrance",
    "kordan": "cave_entrance",
    "mistrz drwalstwa": "lumberjack_camp",
    "oren": "lumberjack_camp",
    "mistrzyni zielarstwa": "herbalist_hut",
    "sena": "herbalist_hut",
    "mistrz alchemii": "herbalist_hut",
    "orin": "herbalist_hut",
    "tunel": "cave_tunnel",
    "krysztalowy tunel": "cave_tunnel",
    "krysztal": "crystal_chamber",
    "komnata krysztalowa": "crystal_chamber",
    "krysztalowa komnata": "crystal_chamber",
    "cmentarz": "graveyard",
    "stary cmentarz": "graveyard",

    # Krypta i szlak bandytów
    "wejscie do krypty": "crypt_entrance",
    "przedsionek krypty": "crypt_entrance",
    "sala krypty": "crypt_hall",
    "glebia krypty": "crypt_depths",
    "trakt": "old_road",
    "stary trakt": "old_road",
    "wartownia polnocna": "north_watchpost",
    "roderik": "north_watchpost",
    "dowodca roderik": "north_watchpost",
    "wartownia pogranicza": "frontier_watchpost",
    "anna": "frontier_watchpost",
    "strazniczka anna": "frontier_watchpost",
    "bandyci": "bandit_camp",
    "oboz bandytow": "bandit_camp",
    "obozowisko bandytow": "bandit_camp",
    "herszt": "bandit_camp",
    "rozdroze": "crossroads",
}

TOOL_BUY_ALIASES = {
    "wedka": "fishing_rod",
    "wedke": "fishing_rod",
    "rod": "fishing_rod",
    "kilof": "pickaxe",
    "pickaxe": "pickaxe",
    "pila": "saw",
    "pile": "saw",
    "saw": "saw",
    "mlot": "crafting_hammer",
    "mlot rzemieslniczy": "crafting_hammer",
    "hammer": "crafting_hammer",
    "noz": "chef_knife",
    "noz kucharski": "chef_knife",
    "knife": "chef_knife",
    "sierp": "herbalist_sickle",
    "sierp zielarski": "herbalist_sickle",
    "sickle": "herbalist_sickle",
    "mozdzierz": "alchemy_mortar",
    "mozdzierz alchemiczny": "alchemy_mortar",
    "mortar": "alchemy_mortar",
    "szczypce": "jeweler_pliers",
    "szczypce jubilerskie": "jeweler_pliers",
    "pliers": "jeweler_pliers",
    "jeweler pliers": "jeweler_pliers",
}

TOOL_SHOP_ROOMS = {
    "fishing_rod": "fish_market",
    "pickaxe": "cave_entrance",
    "saw": "lumberjack_camp",
    "crafting_hammer": "forge",
    "chef_knife": "inn",
    "herbalist_sickle": "herbalist_hut",
    "alchemy_mortar": "herbalist_hut",
    "jeweler_pliers": "jeweler_workshop",
}

EQUIPMENT_SLOT_ALIASES = {
    "helm": "head",
    "helmet": "head",
    "helmik": "head",
    "hełm": "head",
    "glowa": "head",
    "głowa": "head",

    "zbroja": "body",
    "pancerz": "body",
    "napierśnik": "body",
    "napiersnik": "body",
    "korpus": "body",
    "armor": "body",
    "body": "body",

    "rekawice": "hands",
    "rękawice": "hands",
    "dlonie": "hands",
    "dłonie": "hands",
    "gloves": "hands",
    "hands": "hands",

    "nogi": "legs",
    "nogawice": "legs",
    "spodnie": "legs",
    "legs": "legs",

    "buty": "feet",
    "stopy": "feet",
    "boots": "feet",
    "feet": "feet",

    "talizman": "charm",
    "amulet": "charm",
    "charm": "charm",

    "pierścień": "ring",
    "pierscien": "ring",
    "pierścien": "ring",
    "pierscien": "ring",
    "ring": "ring",

    "naszyjnik": "necklace",
    "naszyjnika": "necklace",
    "necklace": "necklace",

}

EQUIPMENT_SLOT_NAMES = {
    "head": "głowa",
    "body": "korpus",
    "hands": "dłonie",
    "legs": "nogi",
    "feet": "stopy",
    "charm": "talizman",
    "ring": "pierścień",
    "necklace": "naszyjnik",
}

EXP_AREAS = (
    {
        "id": "trening",
        "name": "Plac Treningowy",
        "aliases": (
            "trening", "plac treningowy", "manekin", "manekiny",
        ),
        "soul_min": 1,
        "soul_max": 10,
        "difficulty": "bardzo łatwa",
        "guide": "manekiny",
        "enemies": "Żywy Manekin",
        "description": (
            "Najbezpieczniejsze miejsce do sprawdzania obrażeń, "
            "umiejętności i podstaw walki. Dobre na sam początek."
        ),
        "note": (
            "Manekin jest przeznaczony głównie do treningu, "
            "więc szybko warto przenieść się do Podziemi lub Dziczy."
        ),
    },
    {
        "id": "podziemia",
        "name": "Podziemia i Kryształowa Jaskinia",
        "aliases": (
            "podziemia", "krysztalowa jaskinia", "jaskinia",
            "piwnica swiatyni", "krysztalowa komnata",
        ),
        "soul_min": 1,
        "soul_max": 25,
        "difficulty": "łatwa",
        "guide": "jaskinia",
        "enemies": (
            "Szczur Świątynny, Szkielet Strażnik, Upiór Krypty, "
            "Kryształowy Strażnik i Kryształowy Władca"
        ),
        "description": (
            "Wczesne podziemia z rosnącą trudnością. "
            "Dobre miejsce na pierwsze regularne walki i oswojenie się "
            "z silniejszymi przeciwnikami."
        ),
        "note": (
            "Kryształowy Władca jest bossem i jest znacznie mocniejszy "
            "od zwykłych mobów tego regionu."
        ),
    },
    {
        "id": "dzicz",
        "name": "Dzicz",
        "aliases": (
            "dzicz", "ruiny", "gobliny", "bandyci", "wilki",
            "stary cmentarz", "oboz bandytow",
        ),
        "soul_min": 10,
        "soul_max": 45,
        "difficulty": "łatwa do średniej",
        "guide": "ruiny",
        "enemies": (
            "Bandyci, Bandyccy Maruderzy, Gobliny, Goblińskie Osiłki "
            "i Wilki Cienia"
        ),
        "description": (
            "Rozległy teren świata z kilkoma grupami przeciwników. "
            "Dobry do zwykłego expienia, questów i zdobywania sprzętu."
        ),
        "note": (
            "W Dziczy występują także bossowie świata, między innymi "
            "Herszt Bandytów i Król Goblinów."
        ),
    },
    {
        "id": "trolle",
        "name": "Góry i Jaskinia Trolli",
        "aliases": (
            "trolle", "jaskinia trolli", "gory", "góry",
            "gorski szlak", "krol trolli",
        ),
        "soul_min": 25,
        "soul_max": 70,
        "difficulty": "średnia",
        "guide": "jaskinia trolli",
        "enemies": (
            "Górskie Trolle, Trolle Osiłki, Trolle Szamani "
            "oraz rzadkie i elitarne warianty trolli"
        ),
        "description": (
            "Mocniejsze expowisko powiązane z Wioską Górską. "
            "Przeciwnicy mają więcej HP, a rzadkie trolle i elite affixy "
            "mogą wyraźnie zwiększyć trudność."
        ),
        "note": (
            "Na końcu jaskini czeka Król Trolli Grum. "
            "Trolle mogą też zostawiać Skradzione Skrzynie Rudy."
        ),
    },
    {
        "id": "giganci",
        "name": "Twierdza Gigantów 1-50",
        "aliases": (
            "giganci", "twierdza gigantow", "twierdza gigantów",
            "twierdza", "cyklopy", "ogry",
        ),
        "soul_min": 45,
        "soul_max": 130,
        "difficulty": "średnia do bardzo trudnej",
        "guide": "twierdza gigantow",
        "enemies": (
            "Ogrzy Miotacze Głazów, Cyklopi Strażnicy i Górskie Giganty"
        ),
        "description": (
            "Pięćdziesięciopoziomowy górski dungeon. "
            "Z każdym poziomem rośnie HP, obrażenie i nagroda Soul XP. "
            "Nadaje się do dłuższego expienia bez zmiany regionu."
        ),
        "note": (
            "Boss stoi na poziomach 10, 20, 30, 40 i 50 "
            "i musi zostać pokonany, aby wejść wyżej."
        ),
    },
    {
        "id": "krypta",
        "name": "Krypta 1-200",
        "aliases": (
            "krypta", "krypta 1 200", "crypt", "krypta 200",
        ),
        "soul_min": 30,
        "soul_max": 200,
        "difficulty": "skalowana od średniej do endgame",
        "guide": "wejscie do krypty",
        "enemies": (
            "Szkielety Krypty, Upiory Krypty, Strażnicy Sarkofagu, "
            "Cienie Katakumb i Zjawiska Pustki"
        ),
        "description": (
            "Główne wielopoziomowe expowisko 1-200. "
            "Trudność i nagrody rosną z piętrem, więc możesz dobierać "
            "głębokość do aktualnej siły postaci."
        ),
        "note": (
            "Boss stoi co 10 pięter. Boss blokuje zejście niżej. "
            "Pokonani bossowie odblokowują checkpointy portalu."
        ),
    },
    {
        "id": "astral",
        "name": "Wieża Astralna 100-200",
        "aliases": (
            "astral", "wieza astralna", "wieża astralna",
            "astralna wieza", "astralna wieża",
        ),
        "soul_min": 100,
        "soul_max": 200,
        "difficulty": "trudna i endgame",
        "guide": "wieza astralna",
        "enemies": (
            "Astralni Strażnicy, Widma Konstelacji, Rycerze Gwiezdnego Pyłu, "
            "Tkacze Nebuli, Heroldzi Komety i Strażnicy Firmamentu"
        ),
        "description": (
            "Drugie główne expowisko endgame. "
            "Wieża zaczyna się na poziomie 100 i wymaga Soul Level 100. "
            "Daje wysokie Soul XP oraz Astralny ekwipunek."
        ),
        "note": (
            "Boss stoi co 10 poziomów od 100 do 200 "
            "i blokuje drogę w górę."
        ),
    },
    {
        "id": "mythic_crypt",
        "name": "Mityczna Krypta 1-200",
        "aliases": (
            "mityczna krypta", "mythic crypt", "mythic krypta",
        ),
        "soul_min": 100,
        "soul_max": 200,
        "difficulty": "bardzo trudny endgame",
        "guide": "mityczna krypta",
        "enemies": (
            "Mityczni Kościani Rycerze, Mityczne Upiory, "
            "Mityczni Żniwiarze Grobowca i Strażnicy Otchłani"
        ),
        "description": (
            "Mityczna wersja Krypty dostępna od Soul Level 100. "
            "To bardzo trudne expowisko z wysokimi nagrodami Soul XP."
        ),
        "note": (
            "Wejście wymaga Soul Level 100. "
            "Nie wymaga ukończenia zwykłej Krypty do piętra 200. "
            "Mityczny boss występuje co 10 pięter."
        ),
    },
    {
        "id": "mythic_astral",
        "name": "Mityczna Wieża Astralna 1-200",
        "aliases": (
            "mityczna wieza astralna", "mityczna wieża astralna",
            "mythic astral", "mythic astral tower",
        ),
        "soul_min": 100,
        "soul_max": 200,
        "difficulty": "najtrudniejszy endgame",
        "guide": "mityczna wieza astralna",
        "enemies": (
            "Mityczni Astralni Strażnicy, Mityczni Rycerze Konstelacji, "
            "Mityczne Widma Nebuli i Heroldzi Gwiezdnej Burzy"
        ),
        "description": (
            "Mityczna Wieża Astralna jest dostępna od Soul Level 100. "
            "To ekstremalnie trudne expowisko z bardzo wysokimi nagrodami Soul XP."
        ),
        "note": (
            "Wejście wymaga Soul Level 100. "
            "Nie wymaga ukończenia zwykłej Wieży Astralnej do poziomu 200. "
            "Mityczny boss występuje co 10 poziomów."
        ),
    },
)

COMMAND_ALIASES = {
    "pomoc": "help", "pomoce": "help",
    "kodowanie": "encoding", "encoding": "encoding",
    "charset": "encoding", "znaki": "encoding",
    "opis": "describe", "opisz": "describe", "describe": "describe", "description": "describe",
    "changes": "changes", "zmiany": "changes", "changelog": "changes",
    "spójrz": "look", "spojrz": "look", "l": "look",
    "wyjścia": "exits", "wyjscia": "exits",
    "mapa": "map",
    "gdzie": "where",
    "kto": "who",
    "expowiska": "expareas", "expowisko": "expareas",
    "terenyexp": "expareas", "terenydoexpienia": "expareas",
    "expienie": "expareas",
    "say": "say", "powiedz": "say", "mow": "say", "mów": "say",
    "atlas": "atlas", "atlasy": "atlas",
    "codex": "codex", "kodeks": "codex",
    "encyklopedia": "codex", "encyclopedia": "codex",
    "charyzma": "charisma", "haryzma": "charisma", "charisma": "charisma",
    "drużyna": "party", "druzyna": "party", "party": "party",
    "wspieraj": "assist", "assist": "assist", "pomagaj": "assist",
    "pc": "partychat", "dczat": "partychat", "partychat": "partychat",
    "multiclass": "multiclass", "multiklasa": "multiclass",
    "multiklas": "multiclass", "klasy": "multiclass",
    "odpoczywaj": "rest", "odpocznij": "rest", "odpoczynek": "rest",
    "rest": "rest", "regen": "rest", "regeneruj": "rest",
    "staty": "stats", "status": "stats",
    "mana": "mana", "manaregen": "mana",
    "odmiana": "declension", "przypadki": "declension", "namecases": "declension", "declension": "declension",
    "skills": "skills", "umiejętności": "skills", "umiejetnosci": "skills", "zdolności": "skills", "zdolnosci": "skills",
    "skillnames": "skillnames", "nazwyskilli": "skillnames", "nazwyumiejetnosci": "skillnames", "nazwyumiejętności": "skillnames",
    "skill": "skill", "umiejętność": "skill", "umiejetnosc": "skill", "zdolność": "skill", "zdolnosc": "skill",
    "cast": "skill", "rzuc": "skill", "rzuć": "skill",
    "learn": "learn", "naucz": "learn", "ucz": "learn", "uczsię": "learn", "uczsie": "learn",
    "dusza": "soul",
    "ekwipunek": "inventory", "inv": "inventory", "i": "inventory",
    "załóż": "equip", "zaloz": "equip",
    "wyposażenie": "equipment", "wyposazenie": "equipment", "eq": "equipment",
    "użyj": "use", "uzyj": "use", "use": "use",
    "sklep": "shop", "list": "shop", "lista": "shop",
    "kup": "buy",
    "mów": "say", "mow": "say", "powiedz": "say",
    "rozmawiaj": "talk",
    "oddaj": "turnin", "zdaj": "turnin",
    "turnin": "turnin", "turn-in": "turnin",
    "teachers": "teachers", "nauczyciele": "teachers", "trenerzy": "teachers",
    "zadania": "quests", "questy": "quests",
    "atakuj": "attack", "walcz": "attack", "zabij": "attack", "kill": "attack",
    "consider": "consider", "con": "consider",
    "ocen": "consider", "oceń": "consider",
    "ocenmob": "consider", "oceńmob": "consider",
    "ciało": "corpse", "cialo": "corpse", "zwłoki": "corpse", "zwloki": "corpse",
    "body": "corpse", "corpse": "corpse",
    "przeszukaj": "lootcorpse", "loot": "lootcorpse", "ograb": "lootcorpse",
    "krypta": "cryptinfo", "crypt": "cryptinfo",
    "wieza": "astralinfo", "wieża": "astralinfo",
    "astral": "astralinfo", "astralna": "astralinfo",
    "wiezainfo": "astralinfo", "astralinfo": "astralinfo",
    "astralportal": "astralportal",
    "portalastralny": "astralportal",
    "portalwiezy": "astralportal", "portalwieży": "astralportal",
    "checkpointwiezy": "astralportal", "checkpointwieży": "astralportal",
    "portal": "portal", "portale": "portal",
    "portalkrypty": "portal", "portalekrypty": "portal",
    "cryptportal": "portal",
    "checkpoint": "portal", "check": "portal",
    "checkpointkrypty": "portal", "punktkrypty": "portal",
    "punktykrypty": "portal", "cryptcheckpoint": "portal",
    "uciekaj": "flee",
    "odblokuj": "unlock",
    "zapisz": "save",
    "włóż": "put", "wloz": "put", "put": "put",
    "wyjmij": "take", "wyciągnij": "take", "wyciagnij": "take", "take": "take",
    "siatka": "net", "net": "net",
    "woda": "waterinfo", "water": "waterinfo",
    "lowisko": "waterinfo", "łowisko": "waterinfo",
    "sakwa": "bag", "worek": "bag", "bag": "bag",
    "wędkuj": "fish", "wedkuj": "fish", "łów": "fish", "low": "fish",
    "prowadź": "guide", "prowadz": "guide", "guide": "guide",
    "walk": "guide", "walkto": "guide", "go": "guide",
    "idź": "guide", "idz": "guide",
    "lokalizacja": "location", "lokacja": "location", "location": "location",
    "kop": "mine", "wydobywaj": "mine",
    "kopalnia": "mineinfo", "mineinfo": "mineinfo",
    "glebokosc": "mineinfo", "głębokość": "mineinfo",
    "tnij": "woodcut", "drwal": "woodcut", "woodcut": "woodcut", "saw": "woodcut",
    "drewno": "woodpile", "stos": "woodpile", "woodpile": "woodpile",
    "zbieraj": "herb", "zbierz": "herb", "zielarstwo": "herb", "herbalism": "herb",
    "zioła": "herbbag", "ziola": "herbbag", "herbs": "herbbag", "herbbag": "herbbag",
    "alchemia": "alchemy", "alchemy": "alchemy", "warz": "alchemy", "warzenie": "alchemy",
    "jubilerstwo": "jewelcraftinginfo", "jewelcrafting": "jewelcraftinginfo",
    "jub": "jewelcraft", "jubcraft": "jewelcraft",
    "bizuteria": "jewelcraftinginfo", "biżuteria": "jewelcraftinginfo",
    "sprzedaj": "sell",
    "receptury": "recipes", "przepisy": "recipes", "recipes": "recipes",
    "rzemiosło": "recipes", "rzemioslo": "recipes",
    "przetop": "smelt", "przetapiaj": "smelt", "smelt": "smelt",
    "kowalstwo": "blacksmithinginfo",
    "blacksmithing": "blacksmithinginfo",
    "smithing": "blacksmithinginfo",
    "kuj": "craft", "wykuj": "craft",
    "stwórz": "craft", "stworz": "craft", "wytwórz": "craft", "wytworz": "craft", "craft": "craft",
    "gotuj": "cook", "ugotuj": "cook", "cook": "cook",
    "gotowanie": "cookinginfo", "kuchnia": "cookinginfo",
    "cooking": "cookinginfo",
    "profesje": "professions",
    "rangi": "ranks", "ranks": "ranks", "rangiprofesji": "ranks", "professionranks": "ranks",
    "narzędzia": "tools", "narzedzia": "tools",
    "wędka": "toolinfo_fishing", "wedka": "toolinfo_fishing", "rod": "toolinfo_fishing",
    "kilof": "toolinfo_mining", "pickaxe": "toolinfo_mining",
    "piła": "toolinfo_woodcutting", "pila": "toolinfo_woodcutting",
    "młot": "toolinfo_crafting", "mlot": "toolinfo_crafting", "hammer": "toolinfo_crafting",
    "nóż": "toolinfo_cooking", "noz": "toolinfo_cooking", "knife": "toolinfo_cooking",
    "sierp": "toolinfo_herbalism", "sickle": "toolinfo_herbalism",
    "moździerz": "toolinfo_alchemy", "mozdzierz": "toolinfo_alchemy", "mortar": "toolinfo_alchemy",
    "szczypce": "toolinfo_jewelcrafting",
    "szczypcejubilerskie": "toolinfo_jewelcrafting",
    "pliers": "toolinfo_jewelcrafting",
    "tiers": "tiers", "tiery": "tiers", "tiernazwy": "tiers", "nazwytierow": "tiers", "nazwytierów": "tiers",
    "wyjście": "quit", "wyjscie": "quit",
}

ITEMS = {
    "healing_potion": {
        "name": "Mikstura leczenia", "type": "consumable", "price": 24, "currency": "silver",
        "desc": "Przywraca 35 punktów życia podczas walki.", "heal": 35,
    },
    "soul_elixir": {
        "name": "Eliksir Duszy", "type": "consumable", "price": None,
        "desc": "Daje 80 Soul XP.", "soul_xp": 80,
    },
    "leather_vest": {
        "name": "Skórzana kamizelka", "type": "armor", "slot": "body", "defense": 2,
        "price": 48, "currency": "silver", "desc": "Lekki pancerz. Obrona +2.",
    },
    "iron_helmet": {
        "name": "Żelazny hełm", "type": "armor", "slot": "head", "defense": 2,
        "price": 90, "currency": "silver",
        "desc": "Hełm kowalskiego zestawu. Slot głowa. Obrona fizyczna +2.",
    },
    "iron_guard": {
        "name": "Żelazny napierśnik", "type": "armor", "slot": "body", "defense": 4,
        "price": 180, "currency": "silver",
        "desc": "Główna część kowalskiego zestawu. Slot korpus. Obrona fizyczna +4.",
    },
    "iron_gauntlets": {
        "name": "Żelazne rękawice", "type": "armor", "slot": "hands", "defense": 1,
        "price": 70, "currency": "silver",
        "desc": "Rękawice kowalskiego zestawu. Slot dłonie. Obrona fizyczna +1.",
    },
    "iron_leggings": {
        "name": "Żelazne nogawice", "type": "armor", "slot": "legs", "defense": 3,
        "price": 130, "currency": "silver",
        "desc": "Osłona nóg kowalskiego zestawu. Slot nogi. Obrona fizyczna +3.",
    },
    "iron_boots": {
        "name": "Żelazne buty", "type": "armor", "slot": "feet", "defense": 1,
        "price": 70, "currency": "silver",
        "desc": "Buty kowalskiego zestawu. Slot stopy. Obrona fizyczna +1.",
    },
    "forge_charm": {
        "name": "Talizman Kowala", "type": "armor", "slot": "charm", "defense": 1,
        "price": 110, "currency": "silver",
        "desc": "Hartowany talizman ochronny. Slot talizman. Obrona fizyczna +1.",
    },
    "lucky_charm": {
        "name": "Talizman Wędrowca", "type": "armor", "slot": "charm", "defense": 1,
        "price": 72, "currency": "silver", "desc": "Drobny talizman. Obrona +1.",
    },
    "fishing_rod": {
        "name": "Wędka", "type": "tool", "tool_type": "fishing",
        "price": 10, "currency": "silver",
        "desc": "Podstawowe narzędzie do Wędkarstwa. Ma własny level 1-200 i 13 Tierów.",
    },
    "pickaxe": {
        "name": "Kilof", "type": "tool", "tool_type": "mining",
        "price": 10, "currency": "silver",
        "desc": "Podstawowe narzędzie do Górnictwa. Ma własny level 1-200 i 13 Tierów.",
    },
    "saw": {
        "name": "Piła", "type": "tool", "tool_type": "woodcutting",
        "price": 10, "currency": "silver",
        "desc": "Podstawowe narzędzie do Drwalstwa. Ma własny level 1-200 i 13 Tierów.",
    },
    "crafting_hammer": {
        "name": "Młot Rzemieślniczy", "type": "tool", "tool_type": "crafting",
        "price": 10, "currency": "silver",
        "desc": "Narzędzie wymagane do Rzemiosła. Ma własny level 1-200, XP i 13 Tierów.",
    },
    "chef_knife": {
        "name": "Nóż Kucharski", "type": "tool", "tool_type": "cooking",
        "price": 10, "currency": "silver",
        "desc": "Narzędzie wymagane do Gotowania. Ma własny level 1-200, XP i 13 Tierów.",
    },
    "herbalist_sickle": {
        "name": "Sierp Zielarski", "type": "tool", "tool_type": "herbalism",
        "price": 10, "currency": "silver",
        "desc": "Narzędzie do Zielarstwa. Ma własny level 1-200, XP i 13 Tierów.",
    },
    "alchemy_mortar": {
        "name": "Moździerz Alchemiczny", "type": "tool", "tool_type": "alchemy",
        "price": 10, "currency": "silver",
        "desc": "Narzędzie do Alchemii. Ma własny level 1-200, XP i 13 Tierów.",
    },
    "nettle": {"name": "Pokrzywa", "type": "resource", "price": None, "sell_silver": 5, "desc": "Pospolite zioło lecznicze."},
    "chamomile": {"name": "Rumianek", "type": "resource", "price": None, "sell_silver": 7, "desc": "Łagodne zioło lecznicze."},
    "mint": {"name": "Mięta", "type": "resource", "price": None, "sell_silver": 8, "desc": "Aromatyczne zioło."},
    "sage": {"name": "Szałwia", "type": "resource", "price": None, "sell_silver": 12, "desc": "Silne zioło alchemiczne."},
    "lavender": {"name": "Lawenda", "type": "resource", "price": None, "sell_silver": 14, "desc": "Pachnące zioło."},
    "yarrow": {"name": "Krwawnik", "type": "resource", "price": None, "sell_silver": 16, "desc": "Zioło lecznicze."},
    "lemon_balm": {"name": "Melisa", "type": "resource", "price": None, "sell_silver": 18, "desc": "Zioło przydatne w miksturach Many."},
    "valerian": {"name": "Kozłek", "type": "resource", "price": None, "sell_silver": 25, "desc": "Leśne zioło."},
    "ginseng": {"name": "Żeń-szeń", "type": "resource", "price": None, "sell_silver": 40, "desc": "Cenny korzeń alchemiczny."},
    "nightshade": {"name": "Wilcza jagoda", "type": "resource", "price": None, "sell_silver": 55, "desc": "Rzadkie zioło alchemiczne."},
    "mandrake": {"name": "Mandragora", "type": "resource", "price": None, "sell_gold": 1, "desc": "Rzadki magiczny korzeń."},
    "moonflower": {"name": "Kwiat księżycowy", "type": "resource", "price": None, "sell_gold": 2, "desc": "Magiczny kwiat."},
    "soulroot": {"name": "Korzeń duszy", "type": "resource", "price": None, "sell_gold": 3, "desc": "Korzeń nasycony energią dusz."},
    "phoenix_leaf": {"name": "Liść feniksa", "type": "resource", "price": None, "sell_gold": 5, "desc": "Bardzo rzadki liść."},
    "star_moss": {"name": "Gwiezdny mech", "type": "resource", "price": None, "sell_gold": 8, "desc": "Rzadki magiczny mech."},
    "astral_lotus": {"name": "Astralny lotos", "type": "resource", "price": None, "sell_gold": 15, "desc": "Mityczne zioło."},
    "mana_potion": {"name": "Mikstura Many", "type": "consumable", "price": None, "mana": 35, "desc": "Przywraca do 35 Many."},
    "greater_healing_potion": {"name": "Wielka Mikstura Leczenia", "type": "consumable", "price": None, "heal": 70, "desc": "Przywraca do 70 HP."},
    "greater_mana_potion": {"name": "Wielka Mikstura Many", "type": "consumable", "price": None, "mana": 70, "desc": "Przywraca do 70 Many."},
    "vitality_elixir": {"name": "Eliksir Witalności", "type": "consumable", "price": None, "heal": 55, "mana": 30, "desc": "Przywraca do 55 HP i 30 Many."},
    "fallen_branch": {"name": "Suche gałęzie", "type": "resource", "price": None, "sell_silver": 6, "desc": "Najprostszy materiał drwala."},
    "birch_log": {"name": "Pień brzozy", "type": "resource", "price": None, "sell_silver": 10, "desc": "Lekkie drewno brzozowe."},
    "pine_log": {"name": "Pień sosny", "type": "resource", "price": None, "sell_silver": 15, "desc": "Pospolite drewno sosnowe."},
    "willow_log": {"name": "Pień wierzby", "type": "resource", "price": None, "sell_silver": 22, "desc": "Miękkie drewno wierzby."},
    "oak_log": {"name": "Pień dębu", "type": "resource", "price": None, "sell_silver": 40, "desc": "Twarde drewno dębowe."},
    "beech_log": {"name": "Pień buku", "type": "resource", "price": None, "sell_silver": 55, "desc": "Mocne drewno bukowe."},
    "maple_log": {"name": "Pień klonu", "type": "resource", "price": None, "sell_silver": 70, "desc": "Cenne drewno klonowe."},
    "ash_log": {"name": "Pień jesionu", "type": "resource", "price": None, "sell_silver": 90, "desc": "Sprężyste drewno jesionowe."},
    "cedar_log": {"name": "Pień cedru", "type": "resource", "price": None, "sell_silver": 130, "desc": "Aromatyczne drewno cedrowe."},
    "yew_log": {"name": "Pień cisu", "type": "resource", "price": None, "sell_gold": 2, "desc": "Rzadkie drewno cisu."},
    "ironwood_log": {"name": "Pień żelaznego drzewa", "type": "resource", "price": None, "sell_gold": 5, "desc": "Niezwykle twarde drewno."},
    "ebony_log": {"name": "Pień hebanu", "type": "resource", "price": None, "sell_gold": 8, "desc": "Ciężkie i bardzo cenne drewno."},
    "silverwood_log": {"name": "Pień srebrnego drzewa", "type": "resource", "price": None, "sell_gold": 10, "desc": "Magiczne srebrzyste drewno."},
    "spiritwood_log": {"name": "Pień drzewa duchów", "type": "resource", "price": None, "sell_gold": 15, "desc": "Drewno nasycone energią dusz."},
    "ancient_heartwood": {"name": "Pradawna twardziel", "type": "resource", "price": None, "sell_gold": 30, "desc": "Rdzeń bardzo starego drzewa."},
    "worldtree_wood": {"name": "Drewno Drzewa Świata", "type": "resource", "price": None, "sell_gold": 75, "desc": "Mityczny materiał dla najlepszych drwali."},
    "iron_ingot": {
        "name": "Żelazna sztabka", "type": "craft_material", "price": None,
        "desc": "Przetopione żelazo używane w recepturach rzemieślniczych.",
    },
    "silver_ingot": {
        "name": "Srebrna sztabka", "type": "craft_material", "price": None,
        "desc": "Przetopione srebro używane w lepszych recepturach.",
    },
    "gold_ingot": {
        "name": "Złota sztabka", "type": "craft_material", "price": None,
        "desc": "Przetopione złoto używane w zaawansowanych recepturach.",
    },
    "oak_plank": {
        "name": "Deska dębowa", "type": "craft_material", "price": None,
        "desc": "Obrobiona deska z drewna dębowego.",
    },
    "ash_plank": {
        "name": "Deska jesionowa", "type": "craft_material", "price": None,
        "desc": "Sprężysta deska jesionowa.",
    },
    "yew_plank": {
        "name": "Deska cisowa", "type": "craft_material", "price": None,
        "desc": "Rzadka deska z drewna cisu.",
    },
    "ironwood_plank": {
        "name": "Deska żelaznego drzewa", "type": "craft_material", "price": None,
        "desc": "Bardzo twarda deska z żelaznego drzewa.",
    },
    "spiritwood_plank": {
        "name": "Deska drzewa duchów", "type": "craft_material", "price": None,
        "desc": "Magiczna deska nasycona energią dusz.",
    },
    "oak_iron_charm": {
        "name": "Talizman Dębu i Żelaza", "type": "armor", "slot": "charm",
        "defense": 2, "price": None,
        "desc": "Wytwarzany talizman. Slot talizman. Obrona fizyczna +2.",
    },
    "yew_silver_charm": {
        "name": "Talizman Cisu i Srebra", "type": "armor", "slot": "charm",
        "defense": 3, "price": None,
        "desc": "Rzadki wytwarzany talizman. Slot talizman. Obrona fizyczna +3.",
    },
    "spiritwood_gold_charm": {
        "name": "Talizman Drzewa Dusz", "type": "armor", "slot": "charm",
        "defense": 5, "price": None,
        "desc": "Zaawansowany talizman z magicznego drewna i złota. Obrona fizyczna +5.",
    },
    "grilled_river_fish": {
        "name": "Pieczona ryba rzeczna", "type": "consumable", "price": None,
        "heal": 30,
        "desc": "Prosta potrawa. Przywraca do 30 HP.",
    },
    "river_fish_stew": {
        "name": "Gulasz rzeczny", "type": "consumable", "price": None,
        "heal": 45,
        "desc": "Syta potrawa z ryb rzecznych. Przywraca do 45 HP.",
    },
    "lake_fish_stew": {
        "name": "Potrawka jeziorowa", "type": "consumable", "price": None,
        "heal": 50, "mana": 10,
        "desc": "Potrawa z ryb jeziorowych. Przywraca do 50 HP i 10 Many.",
    },
    "sea_chowder": {
        "name": "Zupa morska", "type": "consumable", "price": None,
        "heal": 60, "mana": 15,
        "desc": "Gęsta zupa morska. Przywraca do 60 HP i 15 Many.",
    },
    "ocean_steak": {
        "name": "Stek oceaniczny", "type": "consumable", "price": None,
        "heal": 75, "mana": 25,
        "desc": "Potężna potrawa z ryb oceanu. Przywraca do 75 HP i 25 Many.",
    },
    "master_fisher_feast": {
        "name": "Uczta Mistrza Rybaka", "type": "consumable", "price": None,
        "heal": 100, "mana": 40,
        "desc": "Wielka uczta z czterech środowisk. Przywraca do 100 HP i 40 Many.",
    },

    "herb_crusted_perch": {
        "name": "Okoń w Ziołowej Skorupce",
        "type": "consumable",
        "price": None,
        "heal": 42,
        "mana": 5,
        "desc": "Lekka potrawa rybna z Miętą. Przywraca do 42 HP i 5 Many.",
    },
    "silver_trout_soup": {
        "name": "Zupa ze Srebrnego Pstrąga",
        "type": "consumable",
        "price": None,
        "heal": 52,
        "mana": 12,
        "desc": "Gorąca zupa z pstrąga i Szałwii. Przywraca do 52 HP i 12 Many.",
    },
    "lake_fisher_pie": {
        "name": "Zapiekanka Jeziornego Rybaka",
        "type": "consumable",
        "price": None,
        "heal": 62,
        "mana": 18,
        "desc": "Treściwa zapiekanka z ryb jeziorowych. Przywraca do 62 HP i 18 Many.",
    },
    "spiced_mackerel": {
        "name": "Makrela Korzenna",
        "type": "consumable",
        "price": None,
        "heal": 72,
        "mana": 22,
        "desc": "Makrela doprawiona Szałwią. Przywraca do 72 HP i 22 Many.",
    },
    "salmon_herb_plate": {
        "name": "Łosoś z Ziołami",
        "type": "consumable",
        "price": None,
        "heal": 88,
        "mana": 30,
        "desc": "Łosoś z Lawendą. Przywraca do 88 HP i 30 Many.",
    },
    "moon_eel_broth": {
        "name": "Rosół z Księżycowego Węgorza",
        "type": "consumable",
        "price": None,
        "heal": 112,
        "mana": 48,
        "desc": "Rzadka potrawa z Księżycowego Węgorza i Kwiatu księżycowego. Przywraca do 112 HP i 48 Many.",
    },

    # Nowe ryby v0.6.98 - rzeka
    "river_bleak": {"name": "Ukleja Rzeczna", "type": "resource", "price": None, "sell_silver": 4, "desc": "Mała rzeczna ryba. Wędka level 1+."},
    "stone_loach": {"name": "Śliz Kamienny", "type": "resource", "price": None, "sell_silver": 6, "desc": "Niewielka ryba denna rzeki. Wędka level 5+."},
    "river_bream": {"name": "Krąp Rzeczny", "type": "resource", "price": None, "sell_silver": 10, "desc": "Pospolita ryba rzeczna. Wędka level 15+."},
    "brown_trout": {"name": "Pstrąg Potokowy", "type": "resource", "price": None, "sell_silver": 18, "desc": "Szybka ryba czystych rzek. Wędka level 30+."},
    "river_taimen": {"name": "Tajmień Rzeczny", "type": "resource", "price": None, "sell_silver": 34, "desc": "Duży drapieżnik rzeczny. Wędka level 50+."},
    "emerald_barbel": {"name": "Szmaragdowa Brzana", "type": "resource", "price": None, "sell_silver": 60, "desc": "Rzadka brzana o zielonym połysku. Wędka level 75+."},
    "spirit_grayling": {"name": "Lipień Duchów", "type": "resource", "price": None, "sell_gold": 2, "desc": "Magiczny lipień. Wędka level 110+."},
    "bloodfin_salmon": {"name": "Krwawopłetwy Łosoś", "type": "resource", "price": None, "sell_gold": 5, "desc": "Rzadki łosoś endgame. Wędka level 150+."},
    "star_river_eel": {"name": "Gwiezdny Węgorz Rzeczny", "type": "resource", "price": None, "sell_gold": 12, "desc": "Węgorz nasycony energią gwiazd. Wędka level 175+."},
    "eternal_river_dragon": {"name": "Wieczny Smok Rzeczny", "type": "resource", "price": None, "sell_gold": 35, "desc": "Legendarny drapieżnik rzeki. Wędka level 200."},

    # Nowe ryby v0.6.98 - jezioro
    "lake_gudgeon": {"name": "Kiełb Jeziorowy", "type": "resource", "price": None, "sell_silver": 5, "desc": "Mała ryba przybrzeżna jeziora. Wędka level 1+."},
    "lake_smelt": {"name": "Stynka Jeziorowa", "type": "resource", "price": None, "sell_silver": 7, "desc": "Drobna srebrzysta ryba jeziorowa. Wędka level 8+."},
    "blue_bream": {"name": "Niebieski Leszcz", "type": "resource", "price": None, "sell_silver": 12, "desc": "Rzadziej spotykany leszcz. Wędka level 20+."},
    "golden_tench": {"name": "Złoty Lin", "type": "resource", "price": None, "sell_silver": 22, "desc": "Cenny lin jeziorowy. Wędka level 35+."},
    "deepwater_pike": {"name": "Szczupak Głębinowy", "type": "resource", "price": None, "sell_silver": 40, "desc": "Duży szczupak z głębokich partii jeziora. Wędka level 55+."},
    "crystal_whitefish": {"name": "Kryształowa Sieja", "type": "resource", "price": None, "sell_silver": 70, "desc": "Jasna magiczna sieja. Wędka level 80+."},
    "moon_carp": {"name": "Karp Księżycowy", "type": "resource", "price": None, "sell_gold": 2, "desc": "Karp aktywny przy blasku księżyca. Wędka level 110+."},
    "astral_pike": {"name": "Astralny Szczupak", "type": "resource", "price": None, "sell_gold": 6, "desc": "Endgame drapieżnik jeziorowy. Wędka level 150+."},
    "mirror_sturgeon": {"name": "Lustrzany Jesiotr", "type": "resource", "price": None, "sell_gold": 14, "desc": "Rzadki jesiotr z lustrzanymi łuskami. Wędka level 175+."},
    "eternal_lake_serpent": {"name": "Wieczny Wąż Jeziora", "type": "resource", "price": None, "sell_gold": 38, "desc": "Legendarny mieszkaniec najgłębszej toni. Wędka level 200."},

    # Nowe ryby v0.6.98 - morze
    "sand_eel": {"name": "Dobijak Piaskowy", "type": "resource", "price": None, "sell_silver": 5, "desc": "Mała ryba przybrzeżna morza. Wędka level 1+."},
    "garfish": {"name": "Belona", "type": "resource", "price": None, "sell_silver": 8, "desc": "Długa ryba morska. Wędka level 10+."},
    "sea_bream": {"name": "Prażma Morska", "type": "resource", "price": None, "sell_silver": 14, "desc": "Smaczna ryba morska. Wędka level 20+."},
    "bluefish": {"name": "Lufar", "type": "resource", "price": None, "sell_silver": 25, "desc": "Waleczny morski drapieżnik. Wędka level 35+."},
    "conger_eel": {"name": "Konger", "type": "resource", "price": None, "sell_silver": 45, "desc": "Duży węgorz morski. Wędka level 55+."},
    "red_snapper": {"name": "Lucjan Czerwony", "type": "resource", "price": None, "sell_silver": 80, "desc": "Cenna ryba morska. Wędka level 80+."},
    "storm_herring": {"name": "Śledź Burzy", "type": "resource", "price": None, "sell_gold": 2, "desc": "Ryba pojawiająca się przy wzburzonym morzu. Wędka level 110+."},
    "abyss_conger": {"name": "Konger Otchłani", "type": "resource", "price": None, "sell_gold": 7, "desc": "Mroczny endgame węgorz morski. Wędka level 150+."},
    "void_sole": {"name": "Sola Pustki", "type": "resource", "price": None, "sell_gold": 15, "desc": "Rzadka płastuga nasycona Pustką. Wędka level 175+."},
    "eternal_sea_drake": {"name": "Wieczny Smok Morza", "type": "resource", "price": None, "sell_gold": 40, "desc": "Legendarny morski drapieżnik. Wędka level 200."},

    # Nowe ryby v0.6.98 - ocean
    "flying_fish": {"name": "Ryba Latająca", "type": "resource", "price": None, "sell_silver": 8, "desc": "Szybka ryba otwartego oceanu. Wędka level 1+."},
    "bonito": {"name": "Bonito", "type": "resource", "price": None, "sell_silver": 12, "desc": "Mały krewniak tuńczyka. Wędka level 15+."},
    "yellowfin_tuna": {"name": "Tuńczyk Żółtopłetwy", "type": "resource", "price": None, "sell_silver": 24, "desc": "Popularny oceaniczny tuńczyk. Wędka level 30+."},
    "king_mackerel": {"name": "Makrela Królewska", "type": "resource", "price": None, "sell_silver": 42, "desc": "Duża makrela otwartego oceanu. Wędka level 50+."},
    "marlin_black": {"name": "Marlin Czarny", "type": "resource", "price": None, "sell_silver": 78, "desc": "Potężny oceaniczny drapieżnik. Wędka level 70+."},
    "opah": {"name": "Strojnik Oceaniczny", "type": "resource", "price": None, "sell_gold": 1, "desc": "Rzadka głębinowa ryba oceanu. Wędka level 90+."},
    "celestial_swordfish": {"name": "Niebiański Miecznik", "type": "resource", "price": None, "sell_gold": 4, "desc": "Magiczny miecznik endgame. Wędka level 120+."},
    "astral_sunfish": {"name": "Astralny Samogłów", "type": "resource", "price": None, "sell_gold": 9, "desc": "Ogromny samogłów nasycony Astralem. Wędka level 150+."},
    "void_marlin": {"name": "Marlin Pustki", "type": "resource", "price": None, "sell_gold": 18, "desc": "Skrajnie rzadka ryba oceaniczna. Wędka level 180+."},
    "world_leviathan": {"name": "Lewiatan Świata", "type": "resource", "price": None, "sell_gold": 50, "desc": "Legendarny szczyt oceanicznego połowu. Wędka level 200."},

    "small_fish": {
        "name": "Mała ryba", "type": "resource", "price": None,
        "desc": "Pospolity połów z płytkiej wody.", "sell_silver": 8,
    },
    "river_carp": {
        "name": "Karp rzeczny", "type": "resource", "price": None,
        "desc": "Solidna ryba rzeczna.", "sell_silver": 20,
    },
    "silver_trout": {
        "name": "Srebrny pstrąg", "type": "resource", "price": None,
        "desc": "Rzadsza ryba o srebrzystych łuskach.", "sell_silver": 55,
    },
    "golden_trout": {
        "name": "Złoty pstrąg", "type": "resource", "price": None,
        "desc": "Cenny połów dostępny przy lepszej wędce.", "sell_gold": 1,
    },
    "ancient_sturgeon": {
        "name": "Pradawny jesiotr", "type": "resource", "price": None,
        "desc": "Bardzo duża i cenna ryba.", "sell_gold": 3,
    },
    "moon_eel": {
        "name": "Księżycowy węgorz", "type": "resource", "price": None,
        "desc": "Niezwykle rzadki połów z wysokiego poziomu Wędkarstwa.", "sell_gold": 8,
    },
    "herring": {
        "name": "Śledź", "type": "resource", "price": None,
        "desc": "Morska ryba dostępna dopiero od levelu 30 Wędki.", "sell_gold": 1,
    },
    "mackerel": {
        "name": "Makrela", "type": "resource", "price": None,
        "desc": "Szybka ryba morska.", "sell_gold": 2,
    },
    "salmon": {
        "name": "Łosoś", "type": "resource", "price": None,
        "desc": "Cenny połów z rozwiniętego Wędkarstwa.", "sell_gold": 5,
    },
    "tuna": {
        "name": "Tuńczyk", "type": "resource", "price": None,
        "desc": "Duży i cenny połów oceaniczny. Wędka level 80+.",
        "sell_gold": 15,
    },
    "swordfish": {
        "name": "Miecznik", "type": "resource", "price": None,
        "desc": "Rzadki i silny morski okaz.", "sell_gold": 30,
    },
    "bluefin_tuna": {
        "name": "Tuńczyk błękitnopłetwy", "type": "resource", "price": None,
        "desc": "Bardzo rzadki tuńczyk dostępny na wysokim levelu Wędki.", "sell_gold": 75,
    },
    "reef_shark": {
        "name": "Rekin rafowy", "type": "resource", "price": None,
        "desc": "Rzadki rekin możliwy do złowienia dopiero bardzo dobrą Wędką.", "sell_gold": 125,
    },
    "hammerhead_shark": {
        "name": "Rekin młot", "type": "resource", "price": None,
        "desc": "Bardzo rzadki rekin dla mistrzów Wędkarstwa.", "sell_gold": 250,
    },
    "great_white_shark": {
        "name": "Żarłacz biały", "type": "resource", "price": None,
        "desc": "Ekstremalnie rzadki okaz dla najwyższych leveli Wędki.", "sell_gold": 500,
    },
    "ghost_marlin": {
        "name": "Widmowy marlin", "type": "resource", "price": None,
        "desc": "Legendarny połów dostępny jedynie mistrzom Wędkarstwa.", "sell_mithril": 1,
    },
    "sardine": {
        "name": "Sardynka", "type": "resource", "price": None,
        "desc": "Niewielka morska ryba ławicowa.", "sell_silver": 35,
    },
    "anchovy": {
        "name": "Sardela", "type": "resource", "price": None,
        "desc": "Mała ryba morska spotykana w dużych ławicach.", "sell_silver": 45,
    },
    "cod": {
        "name": "Dorsz", "type": "resource", "price": None,
        "desc": "Cenna ryba morska o jasnym mięsie.", "sell_gold": 3,
    },
    "sea_bass": {
        "name": "Labraks", "type": "resource", "price": None,
        "desc": "Drapieżna ryba morska ceniona przez kupców.", "sell_gold": 4,
    },
    "haddock": {
        "name": "Plamiak", "type": "resource", "price": None,
        "desc": "Krewniak dorsza, trudniejszy do złowienia.", "sell_gold": 6,
    },
    "pollock": {
        "name": "Mintaj", "type": "resource", "price": None,
        "desc": "Silna ryba morska z chłodnych wód.", "sell_gold": 8,
    },
    "flounder": {
        "name": "Flądra", "type": "resource", "price": None,
        "desc": "Płaska ryba denna wymagająca lepszej Wędki.", "sell_gold": 10,
    },
    "halibut": {
        "name": "Halibut", "type": "resource", "price": None,
        "desc": "Duża i droga ryba denna.", "sell_gold": 20,
    },
    "river_perch": {"name": "Okoń rzeczny", "type": "resource", "price": None, "sell_silver": 14, "desc": "Pospolity drapieżnik rzeczny."},
    "barbel": {"name": "Brzana", "type": "resource", "price": None, "sell_silver": 25, "desc": "Silna ryba nurtu rzecznego."},
    "pike": {"name": "Szczupak", "type": "resource", "price": None, "sell_silver": 60, "desc": "Duży słodkowodny drapieżnik."},
    "zander": {"name": "Sandacz", "type": "resource", "price": None, "sell_silver": 85, "desc": "Cenny drapieżnik słodkowodny."},
    "river_catfish": {"name": "Sum rzeczny", "type": "resource", "price": None, "sell_gold": 3, "desc": "Wielki mieszkaniec głębokiej rzeki."},
    "lake_roach": {"name": "Płoć jeziorowa", "type": "resource", "price": None, "sell_silver": 10, "desc": "Pospolita ryba jeziorowa."},
    "bream": {"name": "Leszcz", "type": "resource", "price": None, "sell_silver": 20, "desc": "Popularna ryba jezior."},
    "tench": {"name": "Lin", "type": "resource", "price": None, "sell_silver": 35, "desc": "Ryba spokojnych, zarośniętych jezior."},
    "lake_perch": {"name": "Okoń jeziorowy", "type": "resource", "price": None, "sell_silver": 45, "desc": "Drapieżnik jeziorowy."},
    "lake_trout": {"name": "Troć jeziorowa", "type": "resource", "price": None, "sell_gold": 2, "desc": "Rzadka duża ryba chłodnych jezior."},
    "giant_pike": {"name": "Olbrzymi szczupak", "type": "resource", "price": None, "sell_gold": 6, "desc": "Bardzo stary szczupak."},
    "freshwater_eel": {"name": "Węgorz jeziorowy", "type": "resource", "price": None, "sell_gold": 8, "desc": "Rzadki węgorz z głębin jeziora."},
    "turbot": {"name": "Turbot", "type": "resource", "price": None, "sell_gold": 6, "desc": "Cenna ryba denna morza."},
    "mahi_mahi": {"name": "Mahi-mahi", "type": "resource", "price": None, "sell_gold": 10, "desc": "Szybka ryba oceaniczna."},
    "wahoo": {"name": "Wahoo", "type": "resource", "price": None, "sell_gold": 15, "desc": "Bardzo szybki drapieżnik oceanu."},
    "sailfish": {"name": "Żaglica", "type": "resource", "price": None, "sell_gold": 25, "desc": "Ekstremalnie szybka ryba oceaniczna."},
    "ocean_sunfish": {"name": "Samogłów oceaniczny", "type": "resource", "price": None, "sell_gold": 40, "desc": "Ogromna ryba otwartego oceanu."},
    # Dodatkowe ryby rzeczne
    "dace": {"name": "Jelec", "type": "resource", "price": None, "sell_silver": 12, "desc": "Mała szybka ryba rzeczna."},
    "chub": {"name": "Kleń", "type": "resource", "price": None, "sell_silver": 18, "desc": "Pospolita, silna ryba rzeczna."},
    "common_nase": {"name": "Świnka", "type": "resource", "price": None, "sell_silver": 22, "desc": "Ryba czystych, płynących wód."},
    "ide": {"name": "Jaź", "type": "resource", "price": None, "sell_silver": 32, "desc": "Cenna ryba większych rzek."},
    "asp": {"name": "Boleń", "type": "resource", "price": None, "sell_silver": 70, "desc": "Szybki drapieżnik rzeczny."},
    "grayling": {"name": "Lipień", "type": "resource", "price": None, "sell_silver": 90, "desc": "Cenna ryba chłodnych rzek."},
    "burbot": {"name": "Miętus", "type": "resource", "price": None, "sell_gold": 2, "desc": "Rzadki denny drapieżnik rzeczny."},

    # Dodatkowe ryby jeziorowe
    "rudd": {"name": "Wzdręga", "type": "resource", "price": None, "sell_silver": 14, "desc": "Kolorowa ryba spokojnych jezior."},
    "crucian_carp": {"name": "Karaś", "type": "resource", "price": None, "sell_silver": 18, "desc": "Wytrzymała ryba jeziorowa."},
    "vendace": {"name": "Sielawa", "type": "resource", "price": None, "sell_silver": 55, "desc": "Ryba chłodnych, czystych jezior."},
    "whitefish": {"name": "Sieja", "type": "resource", "price": None, "sell_gold": 1, "desc": "Cenna ryba głębokich jezior."},
    "lake_char": {"name": "Palia jeziorowa", "type": "resource", "price": None, "sell_gold": 3, "desc": "Rzadki drapieżnik zimnych jezior."},

    # Dodatkowe ryby morskie
    "sprat": {"name": "Szprot", "type": "resource", "price": None, "sell_silver": 8, "desc": "Mała ryba morska żyjąca w ławicach."},
    "whiting": {"name": "Witlinek", "type": "resource", "price": None, "sell_silver": 32, "desc": "Pospolita ryba morska."},
    "hake": {"name": "Morszczuk", "type": "resource", "price": None, "sell_silver": 85, "desc": "Drapieżna ryba morska."},
    "red_mullet": {"name": "Barwena", "type": "resource", "price": None, "sell_gold": 2, "desc": "Cenna morska ryba przydenna."},
    "sole": {"name": "Sola", "type": "resource", "price": None, "sell_gold": 4, "desc": "Cenna płaska ryba morska."},
    "monkfish": {"name": "Żabnica", "type": "resource", "price": None, "sell_gold": 9, "desc": "Duży morski drapieżnik głębinowy."},

    # Dodatkowe ryby oceaniczne
    "albacore": {"name": "Albakora", "type": "resource", "price": None, "sell_gold": 12, "desc": "Oceaniczny gatunek tuńczyka."},
    "bigeye_tuna": {"name": "Tuńczyk wielkooki", "type": "resource", "price": None, "sell_gold": 20, "desc": "Cenny tuńczyk głębokiego oceanu."},
    "barracuda": {"name": "Barakuda", "type": "resource", "price": None, "sell_gold": 18, "desc": "Szybki oceaniczny drapieżnik."},
    "cobia": {"name": "Kobia", "type": "resource", "price": None, "sell_gold": 22, "desc": "Duża ryba otwartego morza i oceanu."},
    "amberjack": {"name": "Seriola", "type": "resource", "price": None, "sell_gold": 28, "desc": "Silna oceaniczna ryba sportowa."},
    "mako_shark": {"name": "Rekin mako", "type": "resource", "price": None, "sell_gold": 180, "desc": "Bardzo szybki i rzadki rekin oceaniczny."},
    "tiger_shark": {"name": "Rekin tygrysi", "type": "resource", "price": None, "sell_gold": 300, "desc": "Wielki, bardzo rzadki drapieżnik oceaniczny."},

    # Dodatkowe gatunki drewna
    "alder_log": {"name": "Pień olchy", "type": "resource", "price": None, "sell_silver": 12, "desc": "Drewno lubiące wilgotne tereny."},
    "poplar_log": {"name": "Pień topoli", "type": "resource", "price": None, "sell_silver": 18, "desc": "Lekkie i łatwe w obróbce drewno."},
    "linden_log": {"name": "Pień lipy", "type": "resource", "price": None, "sell_silver": 28, "desc": "Miękkie drewno cenione przez rzemieślników."},
    "chestnut_log": {"name": "Pień kasztana", "type": "resource", "price": None, "sell_silver": 110, "desc": "Twarde, trwałe drewno."},
    "walnut_log": {"name": "Pień orzecha", "type": "resource", "price": None, "sell_gold": 2, "desc": "Cenne ciemne drewno orzechowe."},
    "mahogany_log": {"name": "Pień mahoniu", "type": "resource", "price": None, "sell_gold": 6, "desc": "Szlachetne, ciemnoczerwone drewno."},
    "teak_log": {"name": "Pień teku", "type": "resource", "price": None, "sell_gold": 9, "desc": "Bardzo trwałe i odporne drewno."},
    "redwood_log": {"name": "Pień sekwoi", "type": "resource", "price": None, "sell_gold": 18, "desc": "Ogromne i rzadkie drewno ze starych drzew."},

    "stone_chunk": {
        "name": "Odłamek skały", "type": "resource", "price": None,
        "desc": "Pospolity urobek.", "sell_silver": 3,
    },
    "copper_ore": {
        "name": "Ruda miedzi", "type": "resource", "price": None,
        "desc": "Podstawowa ruda górnicza.", "sell_silver": 12,
    },
    "iron_ore": {
        "name": "Ruda żelaza", "type": "resource", "price": None,
        "desc": "Użyteczna ruda metalu.", "sell_silver": 35,
    },
    "silver_ore": {
        "name": "Ruda srebra", "type": "resource", "price": None,
        "desc": "Cenniejsza ruda wydobywana lepszym kilofem.", "sell_gold": 1,
    },
    "gold_ore": {
        "name": "Ruda złota", "type": "resource", "price": None,
        "desc": "Rzadka i cenna ruda.", "sell_gold": 4,
    },
    "mithril_ore": {
        "name": "Ruda mithrilu (stary przedmiot)", "type": "resource", "price": None,
        "desc": "Przedmiot zgodności ze starszych wersji. Nie można go już wydobyć.",
        "sell_gold": 120,
    },
    "soul_shard": {
        "name": "Odłamek Duszy", "type": "quest", "price": None,
        "desc": "Niestabilny odłamek znaleziony przy istotach z krypty.",
    },
    "wolf_fang": {
        "name": "Kieł Wilka Cienia", "type": "loot", "price": None,
        "desc": "Ciemny kieł pulsujący słabą energią.",
    },
}

ENDGAME_PROFESSION_ITEMS = {
    # Ryby endgame - Rzeka
    "soulfin_trout": {"name": "Pstrąg Duszopłetwy", "type": "resource", "price": None, "sell_gold": 25, "desc": "Rzadka ryba rzeczna. Wędka level 100+."},
    "runic_sturgeon": {"name": "Jesiotr Runiczny", "type": "resource", "price": None, "sell_gold": 45, "desc": "Runiczny jesiotr. Wędka level 140+."},
    "chrono_eel": {"name": "Węgorz Czasu", "type": "resource", "price": None, "sell_gold": 80, "desc": "Niezwykły węgorz. Wędka level 180+."},
    "eternal_salmon": {"name": "Wieczny Łosoś", "type": "resource", "price": None, "sell_gold": 140, "desc": "Mityczny rzeczny połów. Wędka level 200."},

    # Jezioro
    "crystal_carp": {"name": "Kryształowy Karp", "type": "resource", "price": None, "sell_gold": 25, "desc": "Karp o kryształowych łuskach. Wędka level 100+."},
    "moon_pike": {"name": "Księżycowy Szczupak", "type": "resource", "price": None, "sell_gold": 45, "desc": "Rzadka jeziorowa ryba. Wędka level 140+."},
    "starfin_char": {"name": "Gwiezdnopłetwy Golec", "type": "resource", "price": None, "sell_gold": 80, "desc": "Magiczna ryba jeziorowa. Wędka level 180+."},
    "mirror_leviathan": {"name": "Lustrzany Lewiatan", "type": "resource", "price": None, "sell_gold": 150, "desc": "Legendarny mieszkaniec jeziora. Wędka level 200."},

    # Morze
    "storm_cod": {"name": "Sztormowy Dorsz", "type": "resource", "price": None, "sell_gold": 28, "desc": "Ryba nasycona energią sztormu. Wędka level 100+."},
    "abyss_halibut": {"name": "Halibut Otchłani", "type": "resource", "price": None, "sell_gold": 50, "desc": "Głębinowa ryba morska. Wędka level 140+."},
    "void_turbot": {"name": "Turbot Pustki", "type": "resource", "price": None, "sell_gold": 90, "desc": "Mroczny połów morski. Wędka level 180+."},
    "crown_monkfish": {"name": "Koronna Żabnica", "type": "resource", "price": None, "sell_gold": 160, "desc": "Mityczna żabnica. Wędka level 200."},

    # Ocean - po jednym odblokowaniu na każdy próg 100-200
    "celestial_tuna": {"name": "Niebiański Tuńczyk", "type": "resource", "price": None, "sell_gold": 30, "desc": "Oceaniczny połów. Wędka level 100+."},
    "dragon_mahi": {"name": "Smocze Mahi-mahi", "type": "resource", "price": None, "sell_gold": 40, "desc": "Rzadka ryba oceaniczna. Wędka level 120+."},
    "abyss_tuna": {"name": "Tuńczyk Otchłani", "type": "resource", "price": None, "sell_gold": 55, "desc": "Głębinowy tuńczyk. Wędka level 140+."},
    "storm_marlin": {"name": "Marlin Burzy", "type": "resource", "price": None, "sell_gold": 75, "desc": "Potężny marlin. Wędka level 160+."},
    "moon_leviathan": {"name": "Księżycowy Lewiatan", "type": "resource", "price": None, "sell_gold": 110, "desc": "Olbrzymi oceaniczny połów. Wędka level 180+."},
    "eternal_coelacanth": {"name": "Wieczna Latimeria", "type": "resource", "price": None, "sell_gold": 200, "desc": "Najrzadsza ryba oceanu. Wędka level 200."},

    # Rudy 100-200
    "cobalt_ore": {"name": "Ruda Kobaltu", "type": "resource", "price": None, "sell_gold": 18, "desc": "Ruda dostępna od Kilofa level 100."},
    "runestone_ore": {"name": "Ruda Kamienia Runicznego", "type": "resource", "price": None, "sell_gold": 28, "desc": "Ruda dostępna od Kilofa level 120."},
    "dragonsteel_ore": {"name": "Ruda Smoczej Stali", "type": "resource", "price": None, "sell_gold": 42, "desc": "Ruda dostępna od Kilofa level 140."},
    "astral_ore": {"name": "Ruda Astralna", "type": "resource", "price": None, "sell_gold": 65, "desc": "Ruda dostępna od Kilofa level 160."},
    "void_ore": {"name": "Ruda Pustki", "type": "resource", "price": None, "sell_gold": 100, "desc": "Ruda dostępna od Kilofa level 180."},
    "eternium_ore": {"name": "Ruda Eternium", "type": "resource", "price": None, "sell_gold": 180, "desc": "Najrzadsza ruda. Kilof level 200."},

    # Drewno 100-200
    "runewood_log": {"name": "Pień Runicznego Drzewa", "type": "resource", "price": None, "sell_gold": 18, "desc": "Drewno Głębi Gaju. Piła level 100+."},
    "dragonwood_log": {"name": "Pień Smoczego Drzewa", "type": "resource", "price": None, "sell_gold": 28, "desc": "Drewno Głębi Gaju. Piła level 120+."},
    "astralwood_log": {"name": "Pień Astralnego Drzewa", "type": "resource", "price": None, "sell_gold": 42, "desc": "Drewno Głębi Gaju. Piła level 140+."},
    "voidwood_log": {"name": "Pień Drzewa Pustki", "type": "resource", "price": None, "sell_gold": 65, "desc": "Drewno Głębi Gaju. Piła level 160+."},
    "starheart_log": {"name": "Pień Gwiezdnego Serca", "type": "resource", "price": None, "sell_gold": 100, "desc": "Drewno Głębi Gaju. Piła level 180+."},
    "eternal_worldwood_log": {"name": "Pień Wiecznego Drzewa Świata", "type": "resource", "price": None, "sell_gold": 180, "desc": "Najrzadsze drewno. Piła level 200."},

    # Zioła 100-200
    "sunfire_bloom": {"name": "Kwiat Słonecznego Ognia", "type": "resource", "price": None, "sell_gold": 18, "desc": "Zioło Głębi Gaju. Sierp level 100+."},
    "dragon_sage": {"name": "Smocza Szałwia", "type": "resource", "price": None, "sell_gold": 28, "desc": "Zioło Głębi Gaju. Sierp level 120+."},
    "astral_orchid": {"name": "Astralna Orchidea", "type": "resource", "price": None, "sell_gold": 42, "desc": "Zioło Głębi Gaju. Sierp level 140+."},
    "void_lotus": {"name": "Lotos Pustki", "type": "resource", "price": None, "sell_gold": 65, "desc": "Zioło Głębi Gaju. Sierp level 160+."},
    "phoenix_crown": {"name": "Korona Feniksa", "type": "resource", "price": None, "sell_gold": 100, "desc": "Zioło Głębi Gaju. Sierp level 180+."},
    "eternal_blossom": {"name": "Wieczny Kwiat", "type": "resource", "price": None, "sell_gold": 180, "desc": "Najrzadsze zioło. Sierp level 200."},

    # Rzemiosło 100-200
    "runic_guard_charm": {"name": "Runiczny Talizman Straży", "type": "armor", "slot": "charm", "defense": 6, "price": None, "rarity": "crafted", "rarity_name": "Rzemieślniczy", "affix": "constitution", "affix_amount": 2, "desc": "Endgame Rzemiosło level 100. Obrona +6, Kondycja +2."},
    "dragonforge_charm": {"name": "Talizman Smoczej Kuźni", "type": "armor", "slot": "charm", "defense": 7, "price": None, "rarity": "crafted", "rarity_name": "Rzemieślniczy", "affix": "strength", "affix_amount": 3, "desc": "Endgame Rzemiosło level 120. Obrona +7, Siła +3."},
    "astral_forge_charm": {"name": "Astralny Talizman Kuźni", "type": "armor", "slot": "charm", "defense": 8, "price": None, "rarity": "crafted", "rarity_name": "Rzemieślniczy", "affix": "intelligence", "affix_amount": 3, "desc": "Endgame Rzemiosło level 140. Obrona +8, Inteligencja +3."},
    "void_guard_charm": {"name": "Talizman Straży Pustki", "type": "armor", "slot": "charm", "defense": 9, "price": None, "rarity": "crafted", "rarity_name": "Rzemieślniczy", "affix": "willpower", "affix_amount": 4, "desc": "Endgame Rzemiosło level 160. Obrona +9, Siła Woli +4."},
    "worldheart_charm": {"name": "Talizman Serca Świata", "type": "armor", "slot": "charm", "defense": 10, "price": None, "rarity": "crafted", "rarity_name": "Rzemieślniczy", "affix": "hp", "affix_amount": 60, "desc": "Endgame Rzemiosło level 180. Obrona +10, HP +60."},
    "eternal_soul_charm": {"name": "Talizman Wiecznej Duszy", "type": "armor", "slot": "charm", "defense": 12, "price": None, "rarity": "crafted", "rarity_name": "Rzemieślniczy", "affix": "dexterity", "affix_amount": 5, "desc": "Endgame Rzemiosło level 200. Obrona +12, Zręczność +5."},

    # Gotowanie 100-200
    "runic_fish_plate": {"name": "Runiczny Półmisek Rybny", "type": "consumable", "price": None, "heal": 120, "mana": 40, "desc": "Gotowanie level 100. Przywraca do 120 HP i 40 Many."},
    "dragon_ocean_stew": {"name": "Smocza Potrawka Oceaniczna", "type": "consumable", "price": None, "heal": 135, "mana": 55, "desc": "Gotowanie level 120. Przywraca do 135 HP i 55 Many."},
    "abyss_fish_steak": {"name": "Stek Rybny Otchłani", "type": "consumable", "price": None, "heal": 155, "mana": 75, "desc": "Gotowanie level 140. Przywraca do 155 HP i 75 Many."},
    "storm_marlin_feast": {"name": "Uczta Marlina Burzy", "type": "consumable", "price": None, "heal": 180, "mana": 95, "desc": "Gotowanie level 160. Przywraca do 180 HP i 95 Many."},
    "leviathan_banquet": {"name": "Uczta Lewiatana", "type": "consumable", "price": None, "heal": 210, "mana": 120, "desc": "Gotowanie level 180. Przywraca do 210 HP i 120 Many."},
    "eternal_ocean_banquet": {"name": "Wieczna Uczta Oceanu", "type": "consumable", "price": None, "heal": 260, "mana": 160, "desc": "Gotowanie level 200. Przywraca do 260 HP i 160 Many."},

    # Alchemia 100-200
    "supreme_healing_potion": {"name": "Najwyższa Mikstura Leczenia", "type": "consumable", "price": None, "heal": 130, "desc": "Alchemia level 100. Przywraca do 130 HP."},
    "supreme_mana_potion": {"name": "Najwyższa Mikstura Many", "type": "consumable", "price": None, "mana": 130, "desc": "Alchemia level 120. Przywraca do 130 Many."},
    "grand_vitality_elixir": {"name": "Wielki Eliksir Witalności", "type": "consumable", "price": None, "heal": 120, "mana": 80, "desc": "Alchemia level 140. Przywraca do 120 HP i 80 Many."},
    "soul_tonic": {"name": "Tonik Duszy", "type": "consumable", "price": None, "soul_xp": 180, "desc": "Alchemia level 160. Daje 180 Soul XP."},
    "astral_restoration_elixir": {"name": "Astralny Eliksir Odnowy", "type": "consumable", "price": None, "heal": 180, "mana": 120, "desc": "Alchemia level 180. Przywraca do 180 HP i 120 Many."},
    "eternal_soul_elixir": {"name": "Eliksir Wiecznej Duszy", "type": "consumable", "price": None, "soul_xp": 400, "desc": "Alchemia level 200. Daje 400 Soul XP."},
}
ITEMS.update(ENDGAME_PROFESSION_ITEMS)
_register_world_resource_items()

BLACKSMITH_TIERS = (
    {
        "key": "iron",
        "name": "Żelazny",
        "ore": "iron_ore",
        "ingot": "iron_ingot",
        "tool_level": 1,
        "profession_level": 1,
        "base_defense": 2,
    },
    {
        "key": "silver",
        "name": "Srebrny",
        "ore": "silver_ore",
        "ingot": "silver_ingot",
        "tool_level": 20,
        "profession_level": 20,
        "base_defense": 3,
    },
    {
        "key": "gold",
        "name": "Złoty",
        "ore": "gold_ore",
        "ingot": "gold_ingot",
        "tool_level": 40,
        "profession_level": 40,
        "base_defense": 4,
    },
    {
        "key": "cobalt",
        "name": "Kobaltowy",
        "ore": "cobalt_ore",
        "ingot": "cobalt_ingot",
        "tool_level": 100,
        "profession_level": 100,
        "base_defense": 6,
    },
    {
        "key": "runic",
        "name": "Runiczny",
        "ore": "runestone_ore",
        "ingot": "runestone_ingot",
        "tool_level": 120,
        "profession_level": 120,
        "base_defense": 7,
    },
    {
        "key": "dragonsteel",
        "name": "Smoczej Stali",
        "ore": "dragonsteel_ore",
        "ingot": "dragonsteel_ingot",
        "tool_level": 140,
        "profession_level": 140,
        "base_defense": 8,
    },
    {
        "key": "astral",
        "name": "Astralny",
        "ore": "astral_ore",
        "ingot": "astral_ingot",
        "tool_level": 160,
        "profession_level": 160,
        "base_defense": 9,
    },
    {
        "key": "void",
        "name": "Pustki",
        "ore": "void_ore",
        "ingot": "void_ingot",
        "tool_level": 180,
        "profession_level": 180,
        "base_defense": 10,
    },
    {
        "key": "eternium",
        "name": "Eternium",
        "ore": "eternium_ore",
        "ingot": "eternium_ingot",
        "tool_level": 200,
        "profession_level": 200,
        "base_defense": 12,
    },
)

BLACKSMITH_SLOT_DEFS = {
    "head": ("Hełm", 0, 3),
    "body": ("Pancerz", 3, 5),
    "hands": ("Rękawice", -1, 2),
    "legs": ("Nogawice", 1, 4),
    "feet": ("Buty", -1, 2),
    "charm": ("Talizman", -2, 2),
}

def _register_blacksmith_items():
    extra_ingots = (
        ("cobalt_ingot", "Kobaltowa sztabka"),
        ("runestone_ingot", "Runiczna sztabka"),
        ("dragonsteel_ingot", "Sztabka Smoczej Stali"),
        ("astral_ingot", "Astralna sztabka"),
        ("void_ingot", "Sztabka Pustki"),
        ("eternium_ingot", "Sztabka Eternium"),
    )
    for item_id, name in extra_ingots:
        ITEMS[item_id] = {
            "name": name,
            "type": "craft_material",
            "price": None,
            "desc": (
                "Przetopiony metal używany w zaawansowanym "
                "Kowalstwie."
            ),
        }

    for tier_number, tier in enumerate(BLACKSMITH_TIERS, 1):
        for slot, (
            slot_name, defense_delta, _ingot_cost
        ) in BLACKSMITH_SLOT_DEFS.items():
            item_id = (
                f"smith_{tier['key']}_{slot}"
            )
            defense = max(
                1,
                int(tier["base_defense"])
                + int(defense_delta),
            )
            ITEMS[item_id] = {
                "name": (
                    f"{slot_name} - {tier['name']} "
                    f"[Kowalstwo Tier {tier_number}]"
                ),
                "type": "armor",
                "slot": slot,
                "defense": defense,
                "price": None,
                "desc": (
                    f"Wyposażenie wykute przez Kowala. "
                    f"Kowalstwo level {tier['profession_level']}+, "
                    f"Młot Rzemieślniczy level "
                    f"{tier['tool_level']}+. "
                    f"Obrona +{defense}."
                ),
                "blacksmith_tier": tier_number,
                "blacksmith_material": tier["key"],
            }

_register_blacksmith_items()

FISH_RARE_VARIANTS = {
    "albino": {
        "label": "Albinos",
        "name_prefix": "Albinos - ",
        "value_mult": 2,
        "weight": 50,
        "desc": "Rzadki albinos danego gatunku.",
    },
    "golden": {
        "label": "Złoty",
        "name_prefix": "Złoty okaz - ",
        "value_mult": 4,
        "weight": 25,
        "desc": "Bardzo rzadki złoty wariant.",
    },
    "giant": {
        "label": "Olbrzymi",
        "name_prefix": "Olbrzymi okaz - ",
        "value_mult": 3,
        "weight": 18,
        "desc": "Nienaturalnie duży okaz gatunku.",
    },
    "ancient": {
        "label": "Pradawny",
        "name_prefix": "Pradawny okaz - ",
        "value_mult": 8,
        "weight": 7,
        "desc": "Ekstremalnie rzadki pradawny okaz.",
    },
}

WOOD_RARE_VARIANTS = {
    "lush": {
        "label": "Bujne",
        "name_prefix": "Bujne drewno - ",
        "value_mult": 2,
        "weight": 50,
        "desc": "Wyjątkowo zdrowe i gęste drewno.",
    },
    "ancient": {
        "label": "Pradawne",
        "name_prefix": "Pradawne drewno - ",
        "value_mult": 4,
        "weight": 30,
        "desc": "Drewno pochodzące z bardzo starego drzewa.",
    },
    "crystal": {
        "label": "Kryształowe",
        "name_prefix": "Kryształowe drewno - ",
        "value_mult": 6,
        "weight": 15,
        "desc": "Rzadkie drewno przesiąknięte kryształową energią.",
    },
    "legendary": {
        "label": "Legendarne",
        "name_prefix": "Legendarne drewno - ",
        "value_mult": 10,
        "weight": 5,
        "desc": "Najrzadszy wariant drewna.",
    },
}

HERB_RARE_VARIANTS = {
    "lush": {
        "label": "Bujna",
        "name_prefix": "Bujna roślina - ",
        "value_mult": 2,
        "weight": 50,
        "desc": "Wyjątkowo dorodny okaz rośliny.",
    },
    "glowing": {
        "label": "Lśniąca",
        "name_prefix": "Lśniąca roślina - ",
        "value_mult": 4,
        "weight": 25,
        "desc": "Rzadki okaz emanujący delikatnym blaskiem.",
    },
    "ancient": {
        "label": "Pradawna",
        "name_prefix": "Pradawna roślina - ",
        "value_mult": 6,
        "weight": 18,
        "desc": "Bardzo stary i wyjątkowo silny okaz.",
    },
    "legendary": {
        "label": "Legendarna",
        "name_prefix": "Legendarna roślina - ",
        "value_mult": 10,
        "weight": 7,
        "desc": "Najrzadszy wariant rośliny.",
    },
}

MINING_VEINS = {
    "common": {
        "name": "Zwykła żyła",
        "quantity": 1,
    },
    "rich": {
        "name": "Bogata żyła",
        "quantity": 2,
    },
    "crystal": {
        "name": "Kryształowa żyła",
        "quantity": 3,
    },
    "legendary": {
        "name": "Legendarna żyła",
        "quantity": 5,
    },
}

def rare_resource_variant_id(category, key, base_item_id):
    return f"rare_{category}_{key}__{base_item_id}"

def _scaled_resource_sale_fields(base_item, multiplier):
    result = {}
    for currency in ("silver", "gold", "mithril"):
        key = f"sell_{currency}"
        value = int(base_item.get(key, 0))
        if value > 0:
            result[key] = max(1, value * int(multiplier))
    return result

def _register_rare_resource_variants():
    groups = (
        (
            "fish",
            tuple(FISH_RESOURCE_IDS),
            FISH_RARE_VARIANTS,
        ),
        (
            "wood",
            tuple(WOOD_RESOURCE_IDS),
            WOOD_RARE_VARIANTS,
        ),
        (
            "herb",
            tuple(HERB_RESOURCE_IDS),
            HERB_RARE_VARIANTS,
        ),
    )

    for category, base_ids, variants in groups:
        for base_item_id in base_ids:
            base_item = ITEMS.get(base_item_id)
            if not base_item:
                continue

            for key, definition in variants.items():
                variant_id = rare_resource_variant_id(
                    category, key, base_item_id
                )
                value_mult = int(definition["value_mult"])
                item = {
                    "name": (
                        definition["name_prefix"]
                        + base_item["name"]
                    ),
                    "type": "resource",
                    "price": None,
                    "desc": (
                        f"{definition['desc']} "
                        f"Bazowy zasób: {base_item['name']}. "
                        f"Wartość sprzedaży x{value_mult}."
                    ),
                    "resource_category": category,
                    "base_resource_id": base_item_id,
                    "rare_resource_variant": key,
                    "rare_resource_label": definition["label"],
                    "rare_value_multiplier": value_mult,
                }
                item.update(
                    _scaled_resource_sale_fields(
                        base_item, value_mult
                    )
                )
                ITEMS[variant_id] = item

_register_rare_resource_variants()

RARE_FISH_VARIANT_IDS = {
    item_id
    for item_id, item in ITEMS.items()
    if item.get("resource_category") == "fish"
    and item.get("rare_resource_variant")
}
RARE_WOOD_VARIANT_IDS = {
    item_id
    for item_id, item in ITEMS.items()
    if item.get("resource_category") == "wood"
    and item.get("rare_resource_variant")
}
RARE_HERB_VARIANT_IDS = {
    item_id
    for item_id, item in ITEMS.items()
    if item.get("resource_category") == "herb"
    and item.get("rare_resource_variant")
}

FISH_STORAGE_IDS = set(FISH_RESOURCE_IDS) | RARE_FISH_VARIANT_IDS
ORE_STORAGE_IDS = set(ORE_RESOURCE_IDS)
WOOD_STORAGE_IDS = set(WOOD_RESOURCE_IDS) | RARE_WOOD_VARIANT_IDS
HERB_STORAGE_IDS = set(HERB_RESOURCE_IDS) | RARE_HERB_VARIANT_IDS

def _rare_variant_roll(
    base_item_id,
    category,
    definitions,
    tool_level,
    base_chance,
    max_extra_chance,
):
    tool_level = max(1, min(200, int(tool_level)))
    chance = min(
        0.25,
        float(base_chance)
        + (tool_level / 200.0) * float(max_extra_chance),
    )
    if random.random() >= chance:
        return base_item_id

    keys = list(definitions)
    weights = [
        int(definitions[key]["weight"])
        for key in keys
    ]
    key = random.choices(keys, weights=weights, k=1)[0]
    variant_id = rare_resource_variant_id(
        category, key, base_item_id
    )
    return variant_id if variant_id in ITEMS else base_item_id

def roll_fish_variant(base_item_id, tool_level):
    return _rare_variant_roll(
        base_item_id,
        "fish",
        FISH_RARE_VARIANTS,
        tool_level,
        0.08,
        0.04,
    )

def roll_wood_variant(base_item_id, tool_level):
    return _rare_variant_roll(
        base_item_id,
        "wood",
        WOOD_RARE_VARIANTS,
        tool_level,
        0.06,
        0.06,
    )

def roll_herb_variant(base_item_id, tool_level):
    return _rare_variant_roll(
        base_item_id,
        "herb",
        HERB_RARE_VARIANTS,
        tool_level,
        0.08,
        0.04,
    )

def roll_mining_vein(tool_level):
    tool_level = max(1, min(200, int(tool_level)))
    weights = {
        "common": max(55.0, 82.0 - tool_level * 0.10),
        "rich": 14.0 + tool_level * 0.04,
        "crystal": 3.0 + tool_level * 0.04,
        "legendary": 1.0 + tool_level * 0.02,
    }
    keys = tuple(weights)
    key = random.choices(
        keys,
        weights=[weights[k] for k in keys],
        k=1,
    )[0]
    result = dict(MINING_VEINS[key])
    result["key"] = key
    return result


CLASS_EQUIPMENT_SETS = {
    "Wojownik": {
        "prefix": "warrior_oath",
        "set_name": "Przysięgi",
        "affix": "strength",
        "base_defense": 2,
        "room": "guild_martial_hall",
    },
    "Berserker": {
        "prefix": "berserker_fury",
        "set_name": "Krwawej Furii",
        "affix": "strength",
        "base_defense": 2,
        "room": "guild_martial_hall",
    },
    "Łotrzyk": {
        "prefix": "rogue_shadow",
        "set_name": "Cienia",
        "affix": "dexterity",
        "base_defense": 1,
        "room": "guild_shadow_gallery",
    },
    "Łowca": {
        "prefix": "hunter_echo",
        "set_name": "Echa",
        "affix": "dexterity",
        "base_defense": 1,
        "room": "guild_shadow_gallery",
    },
    "Mnich": {
        "prefix": "monk_spirit",
        "set_name": "Ducha",
        "affix": "willpower",
        "base_defense": 1,
        "room": "guild_body_hall",
    },
    "Strażnik": {
        "prefix": "guardian_bastion",
        "set_name": "Bastionu",
        "affix": "constitution",
        "base_defense": 3,
        "room": "guild_body_hall",
    },
    "Mag": {
        "prefix": "mage_arcane",
        "set_name": "Arkanów",
        "affix": "intelligence",
        "base_defense": 1,
        "room": "guild_arcane_chamber",
    },
    "Nekromanta": {
        "prefix": "necromancer_souls",
        "set_name": "Dusz",
        "affix": "intelligence",
        "base_defense": 1,
        "room": "guild_dark_chamber",
    },
    "Kapłan": {
        "prefix": "priest_light",
        "set_name": "Światła",
        "affix": "willpower",
        "base_defense": 2,
        "room": "guild_sanctuary",
    },
    "Czarownik": {
        "prefix": "warlock_abyss",
        "set_name": "Otchłani",
        "affix": "intelligence",
        "base_defense": 1,
        "room": "guild_dark_chamber",
    },
    "Druid": {
        "prefix": "druid_roots",
        "set_name": "Korzeni",
        "affix": "willpower",
        "base_defense": 1,
        "room": "guild_sanctuary",
    },
    "Psionik": {
        "prefix": "psion_mind",
        "set_name": "Umysłu",
        "affix": "willpower",
        "base_defense": 1,
        "room": "guild_arcane_chamber",
    },
}

CLASS_EQUIPMENT_SLOT_DEFS = {
    "head": ("Hełm", 1, 90),
    "body": ("Pancerz", 3, 160),
    "hands": ("Rękawice", 0, 80),
    "legs": ("Nogawice", 2, 130),
    "feet": ("Buty", 0, 80),
    "charm": ("Talizman", 0, 120),
    "ring": ("Pierścień", 0, 140),
    "necklace": ("Naszyjnik", 1, 180),
}

CLASS_SHOP_ITEMS_BY_ROOM = {
    "guild_martial_hall": [],
    "guild_shadow_gallery": [],
    "guild_body_hall": [],
    "guild_arcane_chamber": [],
    "guild_dark_chamber": [],
    "guild_sanctuary": [],
}

CLASS_EQUIPMENT_ITEM_IDS = set()

def _register_class_equipment_shops():
    for class_name, definition in CLASS_EQUIPMENT_SETS.items():
        for slot, (
            slot_name,
            defense_delta,
            price,
        ) in CLASS_EQUIPMENT_SLOT_DEFS.items():
            item_id = f"class_{definition['prefix']}_{slot}"
            if slot == "necklace":
                affix_amount = 3
            elif slot in ("ring", "charm"):
                affix_amount = 2
            else:
                affix_amount = 1

            defense = max(
                1,
                int(definition["base_defense"])
                + int(defense_delta),
            )

            ITEMS[item_id] = {
                "name": f"{slot_name} {definition['set_name']}",
                "type": "armor",
                "slot": slot,
                "defense": defense,
                "price": price,
                "currency": "silver",
                "rarity": "crafted",
                "rarity_name": "Klasowy",
                "affix": definition["affix"],
                "affix_amount": affix_amount,
                "required_class": class_name,
                "class_shop_item": True,
                "class_set_name": definition["set_name"],
                "desc": (
                    f"Wyposażenie klasowe dla {class_name}. "
                    f"Wymaga aktywnej klasy {class_name}. "
                    f"Obrona +{defense}."
                ),
            }
            CLASS_EQUIPMENT_ITEM_IDS.add(item_id)
            CLASS_SHOP_ITEMS_BY_ROOM[
                definition["room"]
            ].append(item_id)

_register_class_equipment_shops()

ITEMS["jeweler_pliers"] = {
    "name": "Szczypce Jubilerskie",
    "type": "tool",
    "tool_type": "jewelcrafting",
    "price": 10,
    "currency": "silver",
    "desc": (
        "Podstawowe narzędzie Jubilerstwa. "
        "Ma własny level 1-200, XP i 13 Tierów. "
        "Nie ma trwałości i nie zużywa się."
    ),
}

SHOPS = {
    "fish_market": ["fishing_rod"],
    "market": ["healing_potion", "leather_vest", "lucky_charm"],
    "inn": ["healing_potion", "chef_knife"],
    "forge": [
        "iron_helmet",
        "iron_guard",
        "iron_gauntlets",
        "iron_leggings",
        "iron_boots",
        "forge_charm",
        "crafting_hammer",
    ],
    "cave_entrance": ["pickaxe"],
    "lumberjack_camp": ["saw"],
    "herbalist_hut": ["herbalist_sickle", "alchemy_mortar"],
    "jeweler_workshop": ["jeweler_pliers"],
}
for _room_id, _items in CLASS_SHOP_ITEMS_BY_ROOM.items():
    SHOPS[_room_id] = list(_items)



SHOP_SELLERS = {
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

GUIDE_DESTINATION_ALIASES.update({
    "sklep wojownika": "guild_martial_hall",
    "sklep berserkera": "guild_martial_hall",
    "sklep lotrzyka": "guild_shadow_gallery",
    "sklep łotrzyka": "guild_shadow_gallery",
    "sklep lowcy": "guild_shadow_gallery",
    "sklep łowcy": "guild_shadow_gallery",
    "sklep mnicha": "guild_body_hall",
    "sklep straznika": "guild_body_hall",
    "sklep strażnika": "guild_body_hall",
    "sklep maga": "guild_arcane_chamber",
    "sklep psionika": "guild_arcane_chamber",
    "sklep nekromanty": "guild_dark_chamber",
    "sklep czarownika": "guild_dark_chamber",
    "sklep kaplana": "guild_sanctuary",
    "sklep kapłana": "guild_sanctuary",
    "sklep druida": "guild_sanctuary",
    "sklep kilof": "cave_entrance",
    "sklep kilofa": "cave_entrance",
})

for _room_id in CLASS_SHOP_ITEMS_BY_ROOM:
    ROOMS[_room_id]["desc"] += (
        " W tej sali działa także klasowy sklep "
        "z pełnym ośmioczęściowym wyposażeniem."
    )


CRAFT_RECIPES = {
    "iron_ingot": {
        "name": "Żelazna sztabka", "stations": ("forge",),
        "ingredients": {"iron_ore": 2}, "output": "iron_ingot", "quantity": 1,
        "desc": "Przetop 2 Rudy żelaza w 1 Żelazną sztabkę.",
    },
    "silver_ingot": {
        "name": "Srebrna sztabka", "stations": ("forge",),
        "ingredients": {"silver_ore": 2}, "output": "silver_ingot", "quantity": 1,
        "desc": "Przetop 2 Rudy srebra w 1 Srebrną sztabkę.",
    },
    "gold_ingot": {
        "name": "Złota sztabka", "stations": ("forge",),
        "ingredients": {"gold_ore": 2}, "output": "gold_ingot", "quantity": 1,
        "desc": "Przetop 2 Rudy złota w 1 Złotą sztabkę.",
    },
    "oak_plank": {
        "name": "Deska dębowa", "stations": ("lumberjack_camp",),
        "ingredients": {"oak_log": 2}, "output": "oak_plank", "quantity": 1,
        "desc": "Obrób 2 Pnie dębu w 1 Deskę dębową.",
    },
    "ash_plank": {
        "name": "Deska jesionowa", "stations": ("lumberjack_camp",),
        "ingredients": {"ash_log": 2}, "output": "ash_plank", "quantity": 1,
        "desc": "Obrób 2 Pnie jesionu w 1 Deskę jesionową.",
    },
    "yew_plank": {
        "name": "Deska cisowa", "stations": ("lumberjack_camp",),
        "ingredients": {"yew_log": 2}, "output": "yew_plank", "quantity": 1,
        "desc": "Obrób 2 Pnie cisu w 1 Deskę cisową.",
    },
    "ironwood_plank": {
        "name": "Deska żelaznego drzewa", "stations": ("lumberjack_camp",),
        "ingredients": {"ironwood_log": 2}, "output": "ironwood_plank", "quantity": 1,
        "desc": "Obrób 2 Pnie żelaznego drzewa w 1 Deskę.",
    },
    "spiritwood_plank": {
        "name": "Deska drzewa duchów", "stations": ("lumberjack_camp",),
        "ingredients": {"spiritwood_log": 2}, "output": "spiritwood_plank", "quantity": 1,
        "desc": "Obrób 2 Pnie drzewa duchów w 1 magiczną Deskę.",
    },
    "oak_iron_charm": {
        "name": "Talizman Dębu i Żelaza", "stations": ("forge",),
        "ingredients": {"oak_plank": 2, "iron_ingot": 1},
        "output": "oak_iron_charm", "quantity": 1,
        "desc": "Talizman obronny +2 z drewna dębowego i żelaza.",
    },
    "yew_silver_charm": {
        "name": "Talizman Cisu i Srebra", "stations": ("forge",),
        "ingredients": {"yew_plank": 2, "silver_ingot": 1},
        "output": "yew_silver_charm", "quantity": 1,
        "desc": "Rzadki talizman obronny +3.",
    },
    "spiritwood_gold_charm": {
        "name": "Talizman Drzewa Dusz", "stations": ("forge",),
        "ingredients": {"spiritwood_plank": 2, "gold_ingot": 1},
        "output": "spiritwood_gold_charm", "quantity": 1,
        "desc": "Zaawansowany talizman obronny +5.",
    },
    "runic_guard_charm": {
        "name": "Runiczny Talizman Straży", "stations": ("forge",),
        "ingredients": {"cobalt_ore": 2, "runewood_log": 2},
        "output": "runic_guard_charm", "quantity": 1,
        "min_tool_level": 100, "tool_xp": 24,
        "desc": "Rzemiosło level 100. Obrona +6, Kondycja +2.",
    },
    "dragonforge_charm": {
        "name": "Talizman Smoczej Kuźni", "stations": ("forge",),
        "ingredients": {"runestone_ore": 2, "dragonwood_log": 2},
        "output": "dragonforge_charm", "quantity": 1,
        "min_tool_level": 120, "tool_xp": 28,
        "desc": "Rzemiosło level 120. Obrona +7, Siła +3.",
    },
    "astral_forge_charm": {
        "name": "Astralny Talizman Kuźni", "stations": ("forge",),
        "ingredients": {"dragonsteel_ore": 2, "astralwood_log": 2},
        "output": "astral_forge_charm", "quantity": 1,
        "min_tool_level": 140, "tool_xp": 32,
        "desc": "Rzemiosło level 140. Obrona +8, Inteligencja +3.",
    },
    "void_guard_charm": {
        "name": "Talizman Straży Pustki", "stations": ("forge",),
        "ingredients": {"astral_ore": 2, "voidwood_log": 2},
        "output": "void_guard_charm", "quantity": 1,
        "min_tool_level": 160, "tool_xp": 36,
        "desc": "Rzemiosło level 160. Obrona +9, Siła Woli +4.",
    },
    "worldheart_charm": {
        "name": "Talizman Serca Świata", "stations": ("forge",),
        "ingredients": {"void_ore": 2, "starheart_log": 2},
        "output": "worldheart_charm", "quantity": 1,
        "min_tool_level": 180, "tool_xp": 40,
        "desc": "Rzemiosło level 180. Obrona +10, HP +60.",
    },
    "eternal_soul_charm": {
        "name": "Talizman Wiecznej Duszy", "stations": ("forge",),
        "ingredients": {"eternium_ore": 2, "eternal_worldwood_log": 2},
        "output": "eternal_soul_charm", "quantity": 1,
        "min_tool_level": 200, "tool_xp": 50,
        "desc": "Rzemiosło level 200. Obrona +12, Zręczność +5.",
    },
}

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
            CRAFT_RECIPES[ingot_id] = {
                "name": ITEMS[ingot_id]["name"],
                "stations": ("forge",),
                "ingredients": {
                    tier["ore"]: 2,
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
                    f"Przetop 2 sztuki surowca "
                    f"{ITEMS[tier['ore']]['name']} "
                    f"w 1 sztabkę."
                ),
            }

        for slot, (
            slot_name, _def_delta, ingot_cost
        ) in BLACKSMITH_SLOT_DEFS.items():
            output_id = (
                f"smith_{tier['key']}_{slot}"
            )
            recipe_id = (
                f"forge_{tier['key']}_{slot}"
            )
            CRAFT_RECIPES[recipe_id] = {
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
            }

_register_blacksmith_recipes()

ALCHEMY_RECIPES = {
    "healing_potion": {
        "name": "Mikstura leczenia", "stations": ("herbalist_hut",),
        "ingredients": {"nettle": 1, "chamomile": 1},
        "output": "healing_potion", "quantity": 1,
        "min_tool_level": 5,
        "desc": "Moździerz level 5. Pokrzywa + Rumianek. Przywraca 35 HP.",
    },
    "mana_potion": {
        "name": "Mikstura Many", "stations": ("herbalist_hut",),
        "ingredients": {"mint": 1, "lemon_balm": 1},
        "output": "mana_potion", "quantity": 1,
        "desc": "Mięta + Melisa. Przywraca 35 Many.",
    },
    "greater_healing_potion": {
        "name": "Wielka Mikstura Leczenia", "stations": ("herbalist_hut",),
        "ingredients": {"yarrow": 1, "ginseng": 1, "mandrake": 1},
        "output": "greater_healing_potion", "quantity": 1,
        "desc": "Krwawnik + Żeń-szeń + Mandragora. Przywraca 70 HP.",
    },
    "greater_mana_potion": {
        "name": "Wielka Mikstura Many", "stations": ("herbalist_hut",),
        "ingredients": {"sage": 1, "moonflower": 1, "star_moss": 1},
        "output": "greater_mana_potion", "quantity": 1,
        "desc": "Szałwia + Kwiat księżycowy + Gwiezdny mech. Przywraca 70 Many.",
    },
    "vitality_elixir": {
        "name": "Eliksir Witalności", "stations": ("herbalist_hut",),
        "ingredients": {"ginseng": 1, "soulroot": 1, "phoenix_leaf": 1},
        "output": "vitality_elixir", "quantity": 1,
        "desc": "Przywraca 55 HP i 30 Many.",
    },
    "soul_elixir": {
        "name": "Eliksir Duszy", "stations": ("herbalist_hut",),
        "ingredients": {"soulroot": 2, "astral_lotus": 1},
        "output": "soul_elixir", "quantity": 1,
        "desc": "Daje 80 Soul XP.",
    },
    "supreme_healing_potion": {
        "name": "Najwyższa Mikstura Leczenia", "stations": ("herbalist_hut",),
        "ingredients": {"sunfire_bloom": 2, "phoenix_leaf": 1},
        "output": "supreme_healing_potion", "quantity": 1,
        "min_tool_level": 100, "tool_xp": 24,
        "desc": "Alchemia level 100. Przywraca do 130 HP.",
    },
    "supreme_mana_potion": {
        "name": "Najwyższa Mikstura Many", "stations": ("herbalist_hut",),
        "ingredients": {"dragon_sage": 2, "star_moss": 1},
        "output": "supreme_mana_potion", "quantity": 1,
        "min_tool_level": 120, "tool_xp": 28,
        "desc": "Alchemia level 120. Przywraca do 130 Many.",
    },
    "grand_vitality_elixir": {
        "name": "Wielki Eliksir Witalności", "stations": ("herbalist_hut",),
        "ingredients": {"astral_orchid": 2, "soulroot": 1},
        "output": "grand_vitality_elixir", "quantity": 1,
        "min_tool_level": 140, "tool_xp": 32,
        "desc": "Alchemia level 140. Przywraca do 120 HP i 80 Many.",
    },
    "soul_tonic": {
        "name": "Tonik Duszy", "stations": ("herbalist_hut",),
        "ingredients": {"void_lotus": 2, "astral_lotus": 1},
        "output": "soul_tonic", "quantity": 1,
        "min_tool_level": 160, "tool_xp": 36,
        "desc": "Alchemia level 160. Daje 180 Soul XP.",
    },
    "astral_restoration_elixir": {
        "name": "Astralny Eliksir Odnowy", "stations": ("herbalist_hut",),
        "ingredients": {"phoenix_crown": 2, "sunfire_bloom": 1},
        "output": "astral_restoration_elixir", "quantity": 1,
        "min_tool_level": 180, "tool_xp": 40,
        "desc": "Alchemia level 180. Przywraca do 180 HP i 120 Many.",
    },
    "eternal_soul_elixir": {
        "name": "Eliksir Wiecznej Duszy", "stations": ("herbalist_hut",),
        "ingredients": {"eternal_blossom": 2, "void_lotus": 1},
        "output": "eternal_soul_elixir", "quantity": 1,
        "min_tool_level": 200, "tool_xp": 50,
        "desc": "Alchemia level 200. Daje 400 Soul XP.",
    },
}


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

JEWELCRAFT_RECIPES = {}

def _register_jewelcrafting_recipes():
    for tier in JEWELCRAFTING_TIERS:
        ring_id = f"jewel_{tier['key']}_ring"
        necklace_id = f"jewel_{tier['key']}_necklace"

        ITEMS[ring_id] = {
            "name": f"{tier['label']} Pierścień Jubilerski",
            "type": "armor",
            "slot": "ring",
            "defense": tier["defense"],
            "price": None,
            "rarity": "crafted",
            "rarity_name": "Jubilerski",
            "affix": tier["affix"],
            "affix_amount": tier["affix_amount"],
            "desc": (
                f"Pierścień wykonany przez Jubilerstwo. "
                f"Wymaga Jubilerstwa level {tier['level']}. "
                f"Obrona +{tier['defense']}."
            ),
        }
        ITEMS[necklace_id] = {
            "name": f"{tier['label']} Naszyjnik Jubilerski",
            "type": "armor",
            "slot": "necklace",
            "defense": tier["defense"] + 1,
            "price": None,
            "rarity": "crafted",
            "rarity_name": "Jubilerski",
            "affix": tier["affix"],
            "affix_amount": tier["affix_amount"] + 1,
            "desc": (
                f"Naszyjnik wykonany przez Jubilerstwo. "
                f"Wymaga Jubilerstwa level {tier['level']}. "
                f"Obrona +{tier['defense'] + 1}."
            ),
        }

        base_xp = 12 + tier["level"] // 8

        JEWELCRAFT_RECIPES[ring_id] = {
            "name": ITEMS[ring_id]["name"],
            "stations": ("jeweler_workshop",),
            "ingredients": {tier["material"]: 2},
            "output": ring_id,
            "quantity": 1,
            "min_tool_level": tier["level"],
            "min_profession_level": tier["level"],
            "profession_xp": base_xp,
            "tool_xp": max(8, base_xp - 2),
            "desc": (
                f"Jubilerstwo level {tier['level']}. "
                f"Wykonuje pierścień z 2 sztuk materiału."
            ),
        }
        JEWELCRAFT_RECIPES[necklace_id] = {
            "name": ITEMS[necklace_id]["name"],
            "stations": ("jeweler_workshop",),
            "ingredients": {tier["material"]: 3},
            "output": necklace_id,
            "quantity": 1,
            "min_tool_level": tier["level"],
            "min_profession_level": tier["level"],
            "profession_xp": base_xp + 3,
            "tool_xp": max(9, base_xp),
            "desc": (
                f"Jubilerstwo level {tier['level']}. "
                f"Wykonuje naszyjnik z 3 sztuk materiału."
            ),
        }

_register_jewelcrafting_recipes()

COOK_RECIPES = {
    "grilled_river_fish": {
        "name": "Pieczona ryba rzeczna", "stations": ("inn", "fish_market"),
        "ingredients": {"small_fish": 2},
        "output": "grilled_river_fish", "quantity": 1,
        "min_tool_level": 1, "tool_xp": 8,
        "desc": "Gotowanie level 1. 2 Małe ryby. Przywraca do 30 HP.",
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

NPCS = {
    "fisher_tomas": {
        "name": "Rybak Tomas", "room": "fish_market",
        "dialogue": "Jeśli naprawdę chcesz zostać wędkarzem, przynieś mi trzydzieści ryb.",
        "quest": "fisher_30_fish",
    },
    "lumberjack_bran": {
        "name": "Drwal Bran", "room": "lumberjack_camp",
        "dialogue": "Piłę kupisz tylko tutaj. Jeśli chcesz sprawdzić się jako drwal, przynieś mi trzydzieści sztuk dowolnego drewna.",
        "quest": "lumberjack_30_wood",
    },
    "herbalist_liora": {
        "name": "Zielarka Liora", "room": "herbalist_hut",
        "dialogue": "Kupisz u mnie Sierp Zielarski i Moździerz Alchemiczny. Przynieś mi trzydzieści dowolnych ziół, a wynagrodzę twoją pracę.",
        "quest": "herbalist_30_herbs",
    },
    "miner_toren": {
        "name": "Górnik Toren", "room": "cave_entrance",
        "dialogue": (
            "Dobra ruda nie wydobędzie się sama. "
            "Tylko u mnie kupisz podstawowy Kilof. "
            "Wpisz list albo shop, aby zobaczyć ofertę. "
            "Przynieś mi trzydzieści sztuk dowolnej rudy z kopalni."
        ),
        "quest": "miner_30_ore",
        "shopkeeper": True,
    },
    "specialist_fishing": {
        "name": "Mistrz Wędkarstwa Neris", "room": "fish_market",
        "dialogue": (
            "Specjalizuję się w Wędkarstwie i rozwoju Wędki. "
            "Pokażę ci aktualny level narzędzia, Tier i drogę do następnego progu."
        ),
        "specialist_tool_type": "fishing",
        "specialist_topic": "wedkarstwo",
    },
    "specialist_mining": {
        "name": "Mistrz Górnictwa Kordan", "room": "cave_entrance",
        "dialogue": (
            "Specjalizuję się w Górnictwie i rozwoju Kilofa. "
            "Im wyższy level Kilofa, tym lepsze rudy możesz wydobywać."
        ),
        "specialist_tool_type": "mining",
        "specialist_topic": "gornictwo",
    },
    "specialist_woodcutting": {
        "name": "Mistrz Drwalstwa Oren", "room": "lumberjack_camp",
        "dialogue": (
            "Specjalizuję się w Drwalstwie i rozwoju Piły. "
            "Wyższe levele otwierają dostęp do coraz rzadszych gatunków drewna."
        ),
        "specialist_tool_type": "woodcutting",
        "specialist_topic": "drwalstwo",
    },
    "specialist_crafting": {
        "name": "Mistrz Rzemiosła Haldor", "room": "forge",
        "dialogue": (
            "Specjalizuję się w Kowalstwie, Rzemiośle i Młocie Rzemieślniczym. "
            "W Kuźni możesz przetapiać rudy, kuć pancerze i wykonywać "
            "powtarzalne zlecenia odnawiane co godzinę."
        ),
        "specialist_tool_type": "crafting",
        "specialist_topic": "kowalstwo",
        "specialist_recipes": "receptury kowalstwo",
        "quest": "haldor_crafting_order",
        "specialist_quests": (
            "haldor_crafting_order",
            "haldor_crafting_order_advanced",
            "haldor_crafting_order_master",
        ),
    },
    "specialist_cooking": {
        "name": "Kucharz Marcel", "room": "inn",
        "dialogue": (
            "Jestem Kucharzem Błękitnego Płomienia. "
            "Pomogę ci rozwijać Nóż Kucharski i korzystać z receptur Gotowania."
        ),
        "specialist_tool_type": "cooking",
        "specialist_topic": "gotowanie",
        "specialist_recipes": "receptury cook",
        "quest": "marcel_cooking_order",
        "specialist_quests": (
            "marcel_cooking_order",
            "marcel_cooking_order_advanced",
            "marcel_cooking_order_master",
        ),
    },
    "specialist_herbalism": {
        "name": "Mistrzyni Zielarstwa Sena", "room": "herbalist_hut",
        "dialogue": (
            "Specjalizuję się w Zielarstwie i rozwoju Sierpa Zielarskiego. "
            "Wysoki level Sierpa pozwala zbierać najrzadsze zioła."
        ),
        "specialist_tool_type": "herbalism",
        "specialist_topic": "zielarstwo",
    },
    "specialist_alchemy": {
        "name": "Mistrz Alchemii Orin", "room": "herbalist_hut",
        "dialogue": (
            "Specjalizuję się w Alchemii i Moździerzu Alchemicznym. "
            "Mam jedenaście poziomów zleceń na mikstury i eliksiry, "
            "od podstawowej Many aż do Eliksiru Wiecznej Duszy."
        ),
        "specialist_tool_type": "alchemy",
        "specialist_topic": "alchemia",
        "specialist_recipes": "receptury alchemia",
        "quest": "orin_alchemy_order",
        "specialist_quests": (
            "orin_alchemy_order",
            "orin_alchemy_order_healing",
            "orin_alchemy_order_greater_healing",
            "orin_alchemy_order_greater_mana",
            "orin_alchemy_order_vitality",
            "orin_alchemy_order_advanced",
            "orin_alchemy_order_supreme_mana",
            "orin_alchemy_order_grand_vitality",
            "orin_alchemy_order_soul_tonic",
            "orin_alchemy_order_astral_restoration",
            "orin_alchemy_order_master",
        ),
    },
    "banker_aldren": {
        "name": "Bankier Aldren", "room": "market",
        "dialogue": (
            "Prowadzę Bank Dusz. Możesz zdeponować walutę i "
            "przedmioty, a wszystko pozostanie bezpieczne po wylogowaniu."
        ),
        "quest": None,
        "banker": True,
    },
    "priest_elor": {
        "name": "Kapłan Elor", "room": "temple",
        "dialogue": (
            "Świątynia prowadzi próby Broni Duszy. Tier 2 wymaga Soul Level 25 "
            "i Próby Szkieletów, Tier 3 Soul Level 60 i Próby Upiorów, "
            "Tier 4 Soul Level 120 i pokonania bossa piętra 120 Krypty, "
            "a Tier 5 Soul Level 180 i pokonania bossa piętra 180. "
            "Jeśli nie jesteś jeszcze gotowy, w piwnicy nadal potrzebujemy pomocy ze szczurami."
        ),
        "quest": "temple_rats",
    },
    "captain_arven": {
        "name": "Kapitan Arven", "room": "guard_hall",
        "dialogue": "Gobliny zajęły starą strażnicę. Potrzebujemy kogoś, kto oczyści szlak.",
        "quest": "goblin_problem",
    },
    "watch_commander_roderik": {
        "name": "Dowódca Roderik", "room": "north_watchpost",
        "dialogue": (
            "Bandyci znów zbierają się w obozowisku za Wartownią Pogranicza. "
            "Potrzebujemy regularnych patroli, które ograniczą ich napady."
        ),
        "quest": "bandit_patrol",
    },
    "frontier_guard_anna": {
        "name": "Strażniczka Anna", "room": "frontier_watchpost",
        "dialogue": (
            "Za tą wartownią zaczyna się Obozowisko Bandytów. "
            "Jeśli masz zlecenie od Dowódcy Roderika, trzymaj się na baczności."
        ),
        "quest": None,
    },
    "mira": {
        "name": "Zielarka Mira", "room": "whisper_grove",
        "dialogue": "Wilki Cienia zakłócają równowagę gaju. Ich obecność jest coraz silniejsza.",
        "quest": "shadow_wolves",
    },
    "doran": {
        "name": "Kowal Doran", "room": "forge",
        "dialogue": "Mam pełny żelazny zestaw ochronny. Wpisz list, aby przejrzeć ofertę. Odłamki Duszy z krypty też mnie interesują.",
        "quest": "soul_shards",
    },
    "innkeeper": {
        "name": "Karczmarka Elia", "room": "inn",
        "dialogue": "Witaj w Błękitnym Płomieniu. Na rynku i tutaj kupisz podstawowe mikstury.",
        "quest": None,
    },
    "archivist": {
        "name": "Archiwista Sol", "room": "library",
        "dialogue": "Poziom bohatera jest iluzją. Tutaj mierzymy rozwój czynami i statystykami.",
        "quest": None,
    },
    "teacher_warrior": {
        "name": "Mistrz Garran", "room": "guild_martial_hall",
        "dialogue": "Uczę Wojowników kontroli Miecza Przysięgi i walki frontowej.",
        "teacher_class": "Wojownik",
    },
    "teacher_berserker": {
        "name": "Mistrzyni Brynja", "room": "guild_martial_hall",
        "dialogue": "Uczę Berserkerów kierować furią, zanim furia zacznie kierować nimi.",
        "teacher_class": "Berserker",
    },
    "teacher_rogue": {
        "name": "Mistrz Kael", "room": "guild_shadow_gallery",
        "dialogue": "Uczę Łotrzyków szybkości, precyzji i ataku z cienia.",
        "teacher_class": "Łotrzyk",
    },
    "teacher_hunter": {
        "name": "Mistrzyni Eira", "room": "guild_shadow_gallery",
        "dialogue": "Uczę Łowców wykorzystywać dystans, tempo i Łuk Echa.",
        "teacher_class": "Łowca",
    },
    "teacher_monk": {
        "name": "Mistrz Shen", "room": "guild_body_hall",
        "dialogue": "Uczę Mnichów panowania nad ciałem, oddechem i Rękawicami Ducha.",
        "teacher_class": "Mnich",
    },
    "teacher_guardian": {
        "name": "Mistrz Borin", "room": "guild_body_hall",
        "dialogue": "Uczę Strażników, jak przetrwać uderzenie, które złamałoby innych.",
        "teacher_class": "Strażnik",
    },
    "teacher_mage": {
        "name": "Arcymag Vaelis", "room": "guild_arcane_chamber",
        "dialogue": "Uczę Magów kontroli Many i energii Arkanów.",
        "teacher_class": "Mag",
    },
    "teacher_necromancer": {
        "name": "Mistrzyni Morwen", "room": "guild_dark_chamber",
        "dialogue": "Uczę Nekromantów bezpiecznego obchodzenia się z energią śmierci.",
        "teacher_class": "Nekromanta",
    },
    "teacher_priest": {
        "name": "Mistrz Aureon", "room": "guild_sanctuary",
        "dialogue": "Uczę Kapłanów łączyć świętą moc, leczenie i obronę.",
        "teacher_class": "Kapłan",
    },
    "teacher_warlock": {
        "name": "Mistrzyni Nyra", "room": "guild_dark_chamber",
        "dialogue": "Uczę Czarowników wykorzystywać Otchłań bez oddawania jej całej kontroli.",
        "teacher_class": "Czarownik",
    },
    "teacher_druid": {
        "name": "Mistrz Thalen", "room": "guild_sanctuary",
        "dialogue": "Uczę Druidów czerpać moc z natury, leczenia i burzy.",
        "teacher_class": "Druid",
    },
    "teacher_psion": {
        "name": "Mistrzyni Ilyra", "room": "guild_arcane_chamber",
        "dialogue": "Uczę Psioników dyscypliny umysłu i kontroli energii psionicznej.",
        "teacher_class": "Psionik",
    },
}


NPCS["jeweler_mirella"] = {
    "name": "Jubilerka Mirella",
    "room": "jeweler_workshop",
    "dialogue": (
        "W mojej pracowni kupisz Szczypce Jubilerskie. "
        "Uczę Jubilerstwa od levelu 1 do 200 i prowadzę "
        "dziewięć etapów zleceń na pierścienie oraz naszyjniki."
    ),
    "shopkeeper": True,
    "specialist_tool_type": "jewelcrafting",
    "specialist_topic": "jubilerstwo",
    "specialist_recipes": "receptury jubilerstwo",
    "quest": "mirella_jewel_iron",
    "specialist_quests": (
        "mirella_jewel_iron",
        "mirella_jewel_silver",
        "mirella_jewel_gold",
        "mirella_jewel_cobalt",
        "mirella_jewel_runic",
        "mirella_jewel_dragonsteel",
        "mirella_jewel_astral",
        "mirella_jewel_void",
        "mirella_jewel_eternium",
    ),
}

NPCS.update({
    "guild_quartermaster_martial": {
        "name": "Kwatermistrz Varek",
        "room": "guild_martial_hall",
        "dialogue": (
            "Prowadzę skład wyposażenia Wojowników i Berserkerów. "
            "Wpisz list albo shop, aby przejrzeć klasowy ekwipunek."
        ),
        "shopkeeper": True,
    },
    "guild_quartermaster_shadow": {
        "name": "Kwatermistrzyni Lysa",
        "room": "guild_shadow_gallery",
        "dialogue": (
            "Prowadzę skład wyposażenia Łotrzyków i Łowców. "
            "Wpisz list albo shop, aby przejrzeć klasowy ekwipunek."
        ),
        "shopkeeper": True,
    },
    "guild_quartermaster_body": {
        "name": "Kwatermistrz Omir",
        "room": "guild_body_hall",
        "dialogue": (
            "Prowadzę skład wyposażenia Mnichów i Strażników. "
            "Wpisz list albo shop, aby przejrzeć klasowy ekwipunek."
        ),
        "shopkeeper": True,
    },
    "guild_quartermaster_arcane": {
        "name": "Kwatermistrzyni Selene",
        "room": "guild_arcane_chamber",
        "dialogue": (
            "Prowadzę skład wyposażenia Magów i Psioników. "
            "Wpisz list albo shop, aby przejrzeć klasowy ekwipunek."
        ),
        "shopkeeper": True,
    },
    "guild_quartermaster_dark": {
        "name": "Kwatermistrz Veyran",
        "room": "guild_dark_chamber",
        "dialogue": (
            "Prowadzę skład wyposażenia Nekromantów i Czarowników. "
            "Wpisz list albo shop, aby przejrzeć klasowy ekwipunek."
        ),
        "shopkeeper": True,
    },
    "guild_quartermaster_sanctuary": {
        "name": "Kwatermistrz Elandor",
        "room": "guild_sanctuary",
        "dialogue": (
            "Prowadzę skład wyposażenia Kapłanów i Druidów. "
            "Wpisz list albo shop, aby przejrzeć klasowy ekwipunek."
        ),
        "shopkeeper": True,
    },
})


NPC_DESCRIPTIONS = {
    "fisher_tomas": (
        "Doświadczony rybak z Targu Rybnego. Uczy podstaw Wędkarstwa i nagradza "
        "graczy, którzy udowodnią cierpliwość przy połowie."
    ),
    "lumberjack_bran": (
        "Doświadczony drwal prowadzący Obóz Drwala. "
        "Jako jedyny sprzedaje Piłę potrzebną do Drwalstwa."
    ),
    "miner_toren": (
        "Doświadczony górnik stojący przy wejściu do Kryształowej Jaskini. "
        "Zleca próbę Górnictwa polegającą na dostarczeniu 30 dowolnych rud."
    ),
    "herbalist_liora": (
        "Zielarka i alchemiczka mieszkająca w Chacie Zielarki. "
        "Sprzedaje Sierp Zielarski i Moździerz Alchemiczny oraz zleca próbę Zielarstwa na 30 ziół."
    ),
    "specialist_fishing": (
        "Specjalista Wędkarstwa na Targu Rybnym. Wyjaśnia rozwój Wędki, "
        "Tier narzędzia i dostęp do ryb wysokiego levelu."
    ),
    "specialist_mining": (
        "Specjalista Górnictwa przy wejściu do Kryształowej Jaskini. "
        "Wyjaśnia rozwój Kilofa, Tier narzędzia i progi rud endgame."
    ),
    "specialist_woodcutting": (
        "Specjalista Drwalstwa w Obozie Drwala. Wyjaśnia rozwój Piły "
        "i dostęp do coraz rzadszych gatunków drewna."
    ),
    "specialist_crafting": (
        "Specjalista Rzemiosła w Kuźni Dusz. Pomaga śledzić rozwój "
        "Młota Rzemieślniczego i przypomina komendę receptury craft."
    ),
    "specialist_cooking": (
        "Kucharz w Karczmie Pod Błękitnym Płomieniem. Pomaga rozwijać "
        "Nóż Kucharski i korzystać z receptur Gotowania."
    ),
    "specialist_herbalism": (
        "Specjalistka Zielarstwa w Chacie Zielarki. Wyjaśnia rozwój "
        "Sierpa Zielarskiego i progi rzadkich ziół."
    ),
    "specialist_alchemy": (
        "Specjalista Alchemii w Chacie Zielarki. Pomaga rozwijać "
        "Moździerz Alchemiczny i przypomina receptury Alchemii."
    ),
    "banker_aldren": (
        "Bankier na Rynku. Obsługuje trwałe konto bankowe na srebro, "
        "złoto, mithril i zwykłe przedmioty z inventory."
    ),
    "priest_elor": (
        "Kapłan Świątyni Odrodzenia. Prowadzi próby odblokowania Tier 2, 3, 4 i 5 "
        "Broni Duszy oraz pilnuje bezpieczeństwa świątynnych zapasów."
    ),
    "captain_arven": (
        "Dowódca miejskiej straży. Zleca zadania związane z bezpieczeństwem dróg, "
        "strażnic i okolic Miasta Dusz."
    ),
    "watch_commander_roderik": (
        "Dowódca Wartowni Północnej. Organizuje powtarzalne patrole przeciw bandytom "
        "z Obozowiska Bandytów."
    ),
    "frontier_guard_anna": (
        "Strażniczka z Wartowni Pogranicza. Ostrzega podróżnych przed bandytami "
        "i wskazuje drogę do ich obozowiska."
    ),
    "mira": (
        "Zielarka mieszkająca w Gaju Szeptów. Zna dzicz i reaguje na zagrożenia "
        "naruszające równowagę natury."
    ),
    "doran": (
        "Kowal z Kuźni Dusz. Sprzedaje pełny żelazny zestaw ochronny na głowę, korpus, "
        "dłonie, nogi, stopy i slot talizmanu, a także Kilof. Interesuje się Odłamkami Duszy."
    ),
    "innkeeper": (
        "Karczmarka prowadząca Błękitny Płomień. Sprzedaje podstawowe zapasy i "
        "udziela prostych informacji podróżnym."
    ),
    "archivist": (
        "Archiwista Biblioteki Kronik. Wyjaśnia zasady świata, w którym rozwój "
        "postaci odbywa się przez statystyki, a nie przez level bohatera."
    ),
    "teacher_warrior": "Nauczyciel klasy Wojownik w Sali Gildii.",
    "teacher_berserker": "Nauczycielka klasy Berserker w Sali Gildii.",
    "teacher_rogue": "Nauczyciel klasy Łotrzyk w Sali Gildii.",
    "teacher_hunter": "Nauczycielka klasy Łowca w Sali Gildii.",
    "teacher_monk": "Nauczyciel klasy Mnich w Sali Gildii.",
    "teacher_guardian": "Nauczyciel klasy Strażnik w Sali Gildii.",
    "teacher_mage": "Nauczyciel klasy Mag w Sali Gildii.",
    "teacher_necromancer": "Nauczycielka klasy Nekromanta w Sali Gildii.",
    "teacher_priest": "Nauczyciel klasy Kapłan w Sali Gildii.",
    "teacher_warlock": "Nauczycielka klasy Czarownik w Sali Gildii.",
    "teacher_druid": "Nauczyciel klasy Druid w Sali Gildii.",
    "teacher_psion": "Nauczycielka klasy Psionik w Sali Gildii.",
}

MOB_DESCRIPTIONS = {
    "temple_rat": "Mały, szybki szkodnik z piwnicy świątyni. Dobry pierwszy przeciwnik.",
    "training_dummy": "Magicznie ożywiony manekin przeznaczony do bezpiecznego treningu walki.",
    "goblin": "Lekko uzbrojony goblin nękający drogi i ruiny poza miastem.",
    "goblin_brute": "Silniejszy goblin nastawiony na ciężkie, fizyczne uderzenia.",
    "shadow_wolf": "Drapieżnik skażony energią cienia. Szybszy i groźniejszy od zwykłej bestii.",
    "bandit": "Rozbójnik czatujący na podróżnych na Starym Trakcie.",
    "skeleton": "Nieumarły strażnik krypty. Wytrzymały przeciwnik walczący fizycznie.",
    "crypt_wraith": "Magiczny nieumarły z głębi krypty. Jego ataki sprawdzają obronę magiczną.",
    "crystal_guardian": "Potężny magiczny strażnik Kryształowej Komnaty. Zadaje obrażenia magiczne.",
}

STAT_DESCRIPTIONS = {
    "siła": "Siła zwiększa obrażenia fizyczne postaci.",
    "sila": "Siła zwiększa obrażenia fizyczne postaci.",
    "strength": "Siła zwiększa obrażenia fizyczne postaci.",
    "zręczność": (
        "Zręczność zwiększa Szybkość. Wyższa Szybkość zwiększa szansę uniknięcia "
        "kontrataku. Aktualny limit uniku wynosi 35 procent."
    ),
    "zrecznosc": (
        "Zręczność zwiększa Szybkość. Wyższa Szybkość zwiększa szansę uniknięcia "
        "kontrataku. Aktualny limit uniku wynosi 35 procent."
    ),
    "dexterity": (
        "Zręczność zwiększa Szybkość. Wyższa Szybkość zwiększa szansę uniknięcia kontrataku."
    ),
    "kondycja": "Kondycja zwiększa maksymalne HP. Każdy punkt Kondycji daje 5 maksymalnego HP.",
    "constitution": "Kondycja zwiększa maksymalne HP. Każdy punkt Kondycji daje 5 maksymalnego HP.",
    "inteligencja": "Inteligencja zwiększa maksymalną Manę klas magicznych oraz ich Moc czarów.",
    "intelligence": "Inteligencja zwiększa maksymalną Manę klas magicznych oraz ich Moc czarów.",
    "siła woli": "Siła Woli zwiększa obronę magiczną.",
    "sila woli": "Siła Woli zwiększa obronę magiczną.",
    "willpower": "Siła Woli zwiększa obronę magiczną.",
}

SYSTEM_DESCRIPTIONS = {
    "wędkarstwo": (
        "Wędkarstwo ma własny poziom 1-100. Do połowu potrzebna jest Wędka, która ma "
        "osobny level i osobny XP. Użyj fish albo low. Auto-łowienie: low on i low off."
    ),
    "wedkarstwo": (
        "Wędkarstwo ma własny poziom 1-100. Do połowu potrzebna jest Wędka, która ma "
        "osobny level i osobny XP. Użyj fish albo low. Auto-łowienie: low on i low off."
    ),
    "fishing": "Wędkarstwo ma własny poziom 1-100, a Wędka własny niezależny level 1-100.",
    "górnictwo": (
        "Górnictwo ma własny poziom 1-100. Kilof ma osobny level 1-100. "
        "Użyj mine albo kop. Auto-kopanie: kop on i kop off. "
        "Czysty mithril może zostać wydobyty bezpośrednio dopiero od levelu 80 Kilofa."
    ),
    "gornictwo": (
        "Górnictwo ma własny poziom 1-100. Kilof ma osobny level 1-100. "
        "Czysty mithril może zostać wydobyty bezpośrednio dopiero od levelu 80 Kilofa."
    ),
    "mining": "Górnictwo ma własny poziom 1-100, a Kilof własny niezależny level 1-100.",
    "jubilerstwo": (
        "Jubilerstwo ma własny level 1-200. "
        "Szczypce Jubilerskie mają niezależny level 1-200 i 13 Tierów. "
        "Biżuterię wykonujesz w Pracowni Jubilerskiej u Mirelli."
    ),
    "jewelcrafting": (
        "Jubilerstwo 1-200. Narzędzie: Szczypce Jubilerskie 1-200. "
        "Receptury tworzą pierścienie i naszyjniki."
    ),
    "broń duszy": (
        "Broń Duszy jest na stałe związana z klasą. Ma osobny Soul Level 1-200 i Soul XP. "
        "Tier 2: Soul 25, Tier 3: Soul 60, Tier 4: Soul 120, Tier 5: Soul 180. Każdy wymaga Próby Elora."
    ),
    "bron duszy": "Broń Duszy ma osobny Soul Level 1-200 i pięć Tierów.",
    "soul weapon": "Broń Duszy ma osobny Soul Level 1-200 i pięć Tierów.",
    "srebro": "Srebro jest podstawową walutą. 1000 srebrnych monet można wymienić na 1 złotą monetę.",
    "silver": "Srebro jest podstawową walutą. 1000 srebrnych monet = 1 złota moneta.",
    "złoto": "Złoto jest walutą wyższego rzędu. 1000000 złotych monet można wymienić na 1 mithrilową monetę.",
    "zloto": "Złoto jest walutą wyższego rzędu. 1000000 złotych monet = 1 mithrilowa moneta.",
    "gold": "Złoto jest walutą wyższego rzędu. 1000000 złotych monet = 1 mithrilowa moneta.",
    "mithril": (
        "Mithril jest najrzadszą walutą. 1 mithrilowa moneta = 1000000 złotych monet. "
        "Może być nagrodą lub bardzo rzadkim bezpośrednim wydobyciem wysokopoziomowym Kilofem."
    ),
    "siatka": "Siatka na ryby jest osobnym trwałym magazynem profesji. Komenda siatka/net pokazuje też łączną liczbę ryb, liczbę gatunków i szacowany zarobek ze sprzedaży całej zawartości.",
    "net": "Siatka na ryby przechowuje wszystkie złowione ryby i pokazuje łączną liczbę ryb oraz wartość sprzedaży całej siatki.",
    "sakwa": "Sakwa górnicza przechowuje rudy i pokazuje łączną ilość, liczbę rodzajów oraz szacowany zarobek ze sprzedaży całej zawartości.",
    "bag": "Sakwa górnicza jest magazynem rud; komenda sakwa/bag pokazuje też ilość i wartość sprzedaży.",
    "śmierć": (
        "Po śmierci postać odradza się w Świątyni Odrodzenia i traci 10 procent "
        "każdej posiadanej waluty osobno."
    ),
    "smierc": "Po śmierci postać odradza się w Świątyni Odrodzenia i traci 10 procent każdej waluty.",
    "death": "Po śmierci postać odradza się w Świątyni Odrodzenia i traci część waluty.",
}


LATEST_CHANGES_TITLE = "Soulbound v0.7.37 - Jewelcrafting"
LATEST_CHANGES = [
    "Dodano nową profesję Jubilerstwo level 1-200.",
    "Jubilerstwo ma 13 rang od Ucznia do Wiecznego Mistrza Jubilerstwa.",
    "Dodano Szczypce Jubilerskie level 1-200 z 13 Tierami.",
    "Szczypce Jubilerskie nie mają trwałości ani zużycia.",
    "Dodano nową lokację Pracownia Jubilerska nad Rynkiem.",
    "Dodano NPC Jubilerka Mirella.",
    "Szczypce Jubilerskie kupuje się wyłącznie u Mirelli.",
    "Dodano 18 receptur Jubilerstwa: 9 pierścieni i 9 naszyjników.",
    "Receptury wykorzystują rudy od Żelaza przez Kobalt, Runę, Smoczą Stal, Astral i Pustkę aż po Eternium.",
    "Dodano 9-etapowy łańcuch zleceń Mirelli od levelu 1 do 200.",
    "Wytwarzanie biżuterii rozwija jednocześnie Jubilerstwo i Szczypce Jubilerskie.",
    "Tier Szczypiec może dać dodatkowy produkt receptury.",
    "Dodano komendy jubilerstwo, szczypce, receptury jubilerstwo oraz jub <receptura>.",
    "Poprawiono podpowiedź Kilofa: nadal kupuje się go wyłącznie u Górnika Torena.",
    "Numerowany wybór terenów z v0.7.36 pozostaje.",
    "Brak resetu i brak migracji SQLite.",
]

HELP_TOPIC_ALIASES = {
    "temat": "tematy", "topics": "tematy",
    "all": "wszystko",
    "commands": "komendy", "command": "komendy",
    "basics": "podstawy", "start": "podstawy",
    "movement": "nawigacja", "navigation": "nawigacja",
    "stats": "statystyki", "stat": "statystyki",
    "odmiana": "odmiana_imienia", "przypadki": "odmiana_imienia", "namecases": "odmiana_imienia", "declension": "odmiana_imienia",
    "combat": "walka", "fight": "walka",
    "walk": "walk", "prowadzenie": "walk", "autowalk": "walk",
    "endgameprof": "endgame_profesje", "profesje200": "endgame_profesje", "receptury200": "endgame_profesje",
    "login": "logowanie", "logowanie": "logowanie", "spawn": "logowanie", "start": "logowanie",
    "critical": "krytyki", "crit": "krytyki",
    "statgrowth": "rozwoj_statystyk", "rozwojstatystyk": "rozwoj_statystyk", "rozwoj": "rozwoj_statystyk",
    "uzyjskill": "uzywanie_umiejetnosci", "uzywanieumiejetnosci": "uzywanie_umiejetnosci", "useskill": "uzywanie_umiejetnosci",
    "criticalhits": "krytyki", "krytyk": "krytyki",
    "krytyki": "krytyki",
    "respawn": "respawn", "odrodzenie": "respawn",
    "odradzanie": "respawn",
    "bosses": "bossowie", "boss": "bossowie", "bossowie": "bossowie", "herszt": "bossowie",
    "mobhp": "hp_mobow", "hpmobow": "hp_mobow", "hpprzeciwnikow": "hp_mobow",
    "bosshp": "hp_bossow_lochow", "hpbossow": "hp_bossow_lochow",
    "soul": "dusza", "soulweapon": "dusza",
    "soulxp": "soul_xp_bloki", "duszaexp": "soul_xp_bloki",
    "duszaexp": "soul_xp_bloki", "expsoul": "soul_xp_bloki",
    "money": "pieniadze", "economy": "pieniadze",
    "kurs": "kurs_walut", "waluty": "kurs_walut", "currency": "kurs_walut",
    "wartoscsatki": "wartosc_siatki", "wartoscsiatki": "wartosc_siatki", "netvalue": "wartosc_siatki",
    "equipment": "ekwipunek", "items": "ekwipunek",
    "rarity": "loot_krypty", "rzadkosc": "loot_krypty", "rzadkość": "loot_krypty", "set": "loot_krypty", "sety": "loot_krypty", "lootkrypty": "loot_krypty",
    "quests": "zadania", "quest": "zadania",
    "professions": "profesje",
    "fishing": "wedkarstwo", "fish": "wedkarstwo",
    "laki": "laki", "laka": "laki", "meadows": "laki", "meadow": "laki",
    "atlas": "atlas_kompletny", "atlasy": "atlas_kompletny",
    "codex": "codex_swiata", "kodeks": "codex_swiata",
    "rarezasoby": "rare_resources", "rzadkiezasoby": "rare_resources",
    "atlaszasobow": "atlas_kompletny", "atlaszasobów": "atlas_kompletny",
    "zasobyswiata": "zasoby_swiata", "worldresources": "zasoby_swiata",
    "roslinyswiata": "zasoby_swiata", "rybyswiata": "zasoby_swiata",
    "autooff": "auto_off", "off": "auto_off",
    "autochodzenie": "auto_chodzenie", "automove": "auto_chodzenie",
    "kopalnia": "kopalnia_200", "mine200": "kopalnia_200",
    "water": "woda", "woda": "woda", "lowisko": "woda", "łowisko": "woda",
    "wiecejryb": "wiecej_ryb", "moreryb": "wiecej_ryb", "morefish": "wiecej_ryb",
    "turnin": "oddawanie_zadan", "oddaj": "oddawanie_zadan",
    "mining": "gornictwo", "mine": "gornictwo",
    "woodcutting": "drwalstwo", "drwal": "drwalstwo",
    "crafting": "rzemioslo", "craft": "rzemioslo", "rzemiosło": "rzemioslo",
    "cooking": "gotowanie_rozbudowane", "cook": "gotowanie_rozbudowane",
    "gotowanie": "gotowanie_rozbudowane", "kuchnia": "gotowanie_rozbudowane",
    "herbalism": "zielarstwo", "zielarstwo": "zielarstwo",
    "alchemy": "alchemia", "alchemia": "alchemia",
    "recipes": "receptury", "recipe": "receptury", "przepisy": "receptury",
    "containers": "pojemniki",
    "shops": "sklepy", "shop": "sklepy",
    "multiplayer": "gracze", "players": "gracze",
    "death": "smierc",
    "races": "rasy", "race": "rasy",
    "classes": "klasy", "class": "klasy",
    "descriptions": "opisy", "describe": "opisy",
    "skills": "umiejetnosci", "abilities": "umiejetnosci",
    "skillnames": "nazwy_skilli", "nazwyskilli": "nazwy_skilli",
    "teachers": "nauczyciele", "trainers": "nauczyciele",
    "multiclass": "multiclass", "multiklasa": "multiclass",
    "multiklas": "multiclass", "klasy": "multiclass",
    "changes": "zmiany", "changelog": "zmiany",
    "corpse": "zwloki", "body": "zwloki", "cialo": "zwloki", "ciało": "zwloki",
    "loot": "zwloki", "zwloki": "zwloki", "zwłoki": "zwloki",
    "crypt": "krypta", "krypta": "krypta",
    "portal": "portale", "portals": "portale", "portale": "portale",
    "portalkrypty": "portale", "cryptportal": "portale",
    "checkpoint": "portale", "checkpoints": "portale",
    "punktkrypty": "portale", "punktykrypty": "portale",
    "atlas": "atlas", "atlasy": "atlas",
    "party": "druzyny", "parties": "druzyny", "druzyna": "druzyny", "drużyna": "druzyny",
    "charisma": "charyzma", "charyzma": "charyzma", "haryzma": "charyzma",
}

HELP_TOPICS = {
    "jubilerstwo": [
        "Jubilerstwo jest profesją 1-200 z 13 rangami.",
        "Narzędzie: Szczypce Jubilerskie, level 1-200 i 13 Tierów.",
        "Szczypce nie mają trwałości i nie zużywają się.",
        "Kupisz je wyłącznie u Jubilerki Mirelli w Pracowni Jubilerskiej nad Rynkiem.",
        "Użyj prowadz jubilerka albo prowadz pracownia jubilerska.",
        "Komenda jubilerstwo pokazuje stan profesji.",
        "Komenda szczypce pokazuje stan narzędzia.",
        "Komenda receptury jubilerstwo pokazuje wszystkie receptury.",
        "Komenda jub <receptura> wykonuje biżuterię.",
        "Dodano 18 receptur: 9 pierścieni i 9 naszyjników od Żelaza do Eternium.",
        "Jubilerka Mirella prowadzi 9-etapowy łańcuch zleceń profesyjnych.",
    ],
    "prowadz_wybor": [
        "Gdy prowadz pasuje do kilku lokacji, MUD pokazuje numerowaną listę zamiast zgadywać.",
        "Działa to teraz dla wszystkich terenów, nie tylko dla kopalni.",
        "Po liście wpisujesz tylko sam numer, na przykład 1 albo 2.",
        "Nie ma drugiego pytania ani drugiego wyboru.",
        "Przykłady: prowadz kopalnia, prowadz dzicz, prowadz góry, prowadz podziemia, prowadz gildia, prowadz jaskinia trolli, prowadz krypta, prowadz wieża i prowadz twierdza.",
        "Duże wielopoziomowe lochy są zwijane do czytelnej pozycji zamiast wypisywania dziesiątek lub setek pięter.",
        "Jeżeli chcesz konkretny poziom, nadal działa bezpośrednia nazwa, na przykład prowadz kopalnia 80.",
        "Wpisz anuluj, jeśli chcesz zamknąć oczekujący wybór bez wybierania.",
    ],
    "respawn_mobow": [
        "Czas odradzania mobów został globalnie zwiększony 2 razy.",
        "Zwykłe moby: bazowo 120 sekund, teraz 240 sekund.",
        "Bossowie: bazowo 300 sekund, teraz 600 sekund.",
        "Manekin treningowy: bazowo 60 sekund, teraz 120 sekund.",
        "Jeżeli konkretny mob ma własny respawn_seconds, jego indywidualny czas również jest mnożony razy 2.",
        "HP, obrażenia, Soul XP, nagrody, loot i mechaniki walki nie zostały zmienione.",
    ],
    "bizuteria_klasowa": [
        "Każda z 12 klas ma własny Pierścień i Naszyjnik.",
        "Pierścień zajmuje osobny slot pierścień.",
        "Naszyjnik zajmuje osobny slot naszyjnik.",
        "Biżuteria jest dostępna w tym samym sklepie klasowym co pozostałe części zestawu.",
        "Pierścień daje klasowy bonus +2 do głównej cechy zestawu.",
        "Naszyjnik daje klasowy bonus +3 do głównej cechy zestawu.",
        "Kupno i założenie wymaga aktywnej odpowiedniej klasy.",
        "Multiclass działa także dla pierścieni i naszyjników.",
        "Szybkie komendy: załóż pierścień oraz załóż naszyjnik.",
    ],
    "sklepy_klasowe": [
        "Dodano klasowe sklepy wyposażenia dla wszystkich 12 klas.",
        "Każda klasa ma pełny zestaw 8 części: hełm, pancerz, rękawice, nogawice, buty, talizman, pierścień i naszyjnik.",
        "Wojownik i Berserker kupują wyposażenie w Sali Oręża Gildii.",
        "Łotrzyk i Łowca kupują wyposażenie w Galerii Cieni Gildii.",
        "Mnich i Strażnik kupują wyposażenie w Sali Dyscypliny Gildii.",
        "Mag i Psionik kupują wyposażenie w Komnacie Arkanów Gildii.",
        "Nekromanta i Czarownik kupują wyposażenie w Komnacie Mrocznych Sztuk.",
        "Kapłan i Druid kupują wyposażenie w Sanktuarium Gildii.",
        "Wpisz shop albo list w odpowiedniej sali.",
        "Przedmiot klasowy można kupić i założyć tylko wtedy, gdy wymagana klasa jest aktywna.",
        "Multiclass działa: aktywna klasa dodatkowa również pozwala korzystać z jej wyposażenia.",
        "Możesz użyć prowadz sklep <klasa>, na przykład prowadz sklep maga.",
    ],
    "kilof_u_gornika": [
        "Kilof nie jest już sprzedawany przez Kowala Dorana ani w Górskiej Kuźni.",
        "Podstawowy Kilof sprzedaje wyłącznie Górnik Toren przy Wejściu do Kryształowej Jaskini.",
        "Użyj prowadz jaskinia albo prowadz sklep kilofa.",
        "Na miejscu wpisz shop albo list, a potem kup kilof.",
    ],
    "waluta_auto": [
        "Waluta działa automatycznie bez komendy wymiany.",
        "1000 srebrnych monet = 1 złota moneta.",
        "1 000 000 złotych monet = 1 mithrilowa moneta.",
        "Portfel i Bank Dusz normalizują nominały automatycznie.",
        "Stara ręczna wymiana została usunięta z MUD-a.",
        "Stare salda są zachowywane wartościowo i nie są kasowane.",
    ],
    "przetop": [
        "przetop <metal albo ruda> przetapia rudę na właściwą sztabkę.",
        "Komenda korzysta z istniejących receptur Kowalstwa i nie omija wymagań.",
        "Nadal musisz mieć Młot Rzemieślniczy, odpowiedni level narzędzia, level Kowalstwa, składniki i stać przy właściwej kuźni.",
        "Przykłady: przetop żelazo, przetop srebro, przetop złoto, przetop kobalt.",
        "Obsługiwane są także: runa, smocza stal, astral, pustka i Eternium.",
        "Przetapianie daje XP Kowalstwa i Młota tak samo jak dotychczasowe receptury sztabek.",
    ],
    "assist": [
        "wspieraj <gracz> i assist <gracz> pomagają członkowi drużyny w jego aktualnej walce.",
        "Obaj gracze muszą należeć do tej samej drużyny.",
        "Obaj gracze muszą stać w tej samej lokacji.",
        "Wskazany członek drużyny musi aktualnie walczyć z żywym przeciwnikiem.",
        "Po dołączeniu wykonujesz normalny atak i przeciwnik odpowiada jedną turą.",
        "Jeśli walczysz już z innym mobem, assist nie przełączy celu; najpierw zakończ walkę albo użyj flee.",
        "Działa także jako: druzyna wspieraj <gracz> oraz druzyna assist <gracz>.",
    ],
    "mityczne_od_100": [
        "Mityczna Krypta jest dostępna od Soul Level 100.",
        "Mityczna Wieża Astralna jest dostępna od Soul Level 100.",
        "Oba lochy nie wymagają już ukończenia ich zwykłych wersji do poziomu 200.",
        "Mityczna Krypta nadal ma poziomy 1-200 i bossa co 10 pięter.",
        "Mityczna Wieża Astralna nadal ma poziomy 1-200 i bossa co 10 poziomów.",
        "Soul Level 99 i niższy nie może wejść do żadnego z tych dwóch lochów.",
    ],
    "expowiska": [
        "Komenda expowiska pokazuje listę terenów przeznaczonych do expienia.",
        "Każdy teren ma opis, orientacyjny Soul Level i poziom trudności.",
        "Soul Level jest tylko wskazówką; realna trudność zależy także od statów, klasy i wyposażenia.",
        "expowiska polecane pokazuje tereny pasujące do aktualnego Soul Levelu.",
        "expowiska krypta pokazuje szczegółowy opis Krypty.",
        "expowiska trolle pokazuje szczegółowy opis Jaskini Trolli.",
        "expowiska giganci pokazuje szczegółowy opis Twierdzy Gigantów.",
        "expowiska astral pokazuje szczegółowy opis Wieży Astralnej.",
        "Szczegóły zawierają przeciwników, trudność, opis, uwagi i komendę prowadzenia.",
        "Soulbound nadal nie ma levelu postaci ani Character XP.",
    ],
    "auto_kopalnia_down": [
        "kop on może teraz automatycznie zejść w dół po przebiciu ściany Kopalni Głębinowej.",
        "Automat schodzi tylko przez kierunek down.",
        "Automat schodzi tylko wtedy, gdy następny poziom jest już odblokowany w mine_progress.",
        "Automat sprawdza, czy wyjście down prowadzi dokładnie na następny poziom Kopalni.",
        "Nie przejdzie przez nieprzebitą ścianę.",
        "Nie chodzi po świecie i nie wybiera innych kierunków.",
        "Jeśli włączysz kop on na poziomie z wcześniej przebitą ścianą, zejdzie na odblokowany następny poziom.",
        "Po zejściu kontynuuje kopanie na nowym poziomie.",
    ],
    "sciany_kopalni": [
        "Ściany Kopalni Głębinowej skalują liczbę wymaganych uderzeń Kilofa wraz z głębokością.",
        "Poziomy 1-9 zachowują stary próg 5 uderzeń.",
        "Od poziomu 10 liczba uderzeń jest równa numerowi aktualnego poziomu.",
        "Poziom 10: 10 uderzeń.",
        "Poziom 11: 11 uderzeń.",
        "Poziom 20: 20 uderzeń.",
        "Poziom 50: 50 uderzeń.",
        "Poziom 100: 100 uderzeń.",
        "Poziom 199: 199 uderzeń, aby odblokować poziom 200.",
        "Istniejący zapis wall_hits nie jest resetowany po aktualizacji.",
        "kop on nie chodzi i nie schodzi samodzielnie.",
        "Po przebiciu ściany użyj ręcznie down.",
    ],
    "who": [
        "who pokazuje wszystkich aktualnie zalogowanych graczy.",
        "Dla każdego gracza podaje nazwę, aktywną klasę lub klasy, Soul Level, aktualną lokację i strefę.",
        "Alias po polsku: kto.",
        "Przykładowa linia: Asia. Klasa: Mag. Soul Level 42. Lokalizacja: Rynek. Strefa: Miasto.",
    ],
    "look_skrot": [
        "Skrót l działa dokładnie tak samo jak look.",
        "l bez argumentu opisuje aktualną lokację.",
        "l Asia działa jak look Asia.",
        "l Górski Troll działa jak look Górski Troll.",
        "l Mikstura Leczenia działa jak look Mikstura Leczenia.",
        "l hełm działa jak look hełm.",
        "Skrót obsługuje graczy, NPC, przeciwników i przedmioty.",
    ],
    "look_cel": [
        "look bez argumentu opisuje aktualną lokację jak wcześniej.",
        "look gracz pokazuje gracza w tej samej lokacji.",
        "Przykład: look Asia.",
        "look NPC pokazuje opis NPC stojącego w tej samej lokacji.",
        "look przeciwnik pokazuje aktualne HP, bazowe obrażenia, typ obrażeń i specjalne mechaniki.",
        "look przedmiot pokazuje opis przedmiotu z ekwipunku, założonego sprzętu albo lokalnego sklepu.",
        "Przykład: look Mikstura Leczenia albo look hełm.",
        "Przy częściowej nazwie cel musi być jednoznaczny.",
        "look nie pokazuje graczy, NPC ani mobów z innych lokacji.",
    ],
    "apostrof_say": [
        "Apostrof na początku linii działa jak komenda say.",
        "Przykład: 'Cześć wszystkim",
        "To samo co: say Cześć wszystkim",
        "Nie trzeba wpisywać słowa say.",
        "Sam apostrof bez tekstu pokazuje użycie say.",
        "Wiadomość nadal trafia tylko do graczy w tej samej lokacji.",
    ],
    "say": [
        "say tekst lub apostrof przed tekstem wysyła wiadomość do wszystkich graczy w tej samej lokacji.",
        "Ty otrzymujesz: Mówisz: tekst.",
        "Inni gracze w pokoju otrzymują: nazwa gracza mówi: tekst.",
        "Wiadomość nie jest słyszana w innych lokacjach.",
        "Puste wiadomości i same spacje są odrzucane.",
        "Maksymalna długość jednej wiadomości to 500 znaków.",
        "Aliasy: powiedz, mow, mów.",
        "say nie przerywa odpoczynku.",
    ],
    "kodowanie": [
        "Soulbound domyślnie używa UTF-8 dla całej komunikacji tekstowej.",
        "Serwer wysyła klientowi Telnet negocjację CHARSET z preferowanym UTF-8.",
        "Komenda kodowanie pokazuje bieżący tryb.",
        "kodowanie utf8 przełącza wejście i wyjście sesji na UTF-8.",
        "kodowanie cp1250 przełącza wejście i wyjście sesji na Windows-1250 dla starszych klientów.",
        "Obsługiwane polskie znaki: ą ć ę ł ń ó ś ź ż oraz wielkie odpowiedniki.",
        "Wejście nie używa już errors ignore, więc polskie bajty nie są po cichu usuwane.",
        "Zmiana dotyczy tylko aktualnej sesji i nie zmienia bazy danych.",
    ],
    "mountain_expansion": [
        "Wioska Górska została rozbudowana o Górską Kuźnię, Chatę Łowcy Potworów, Górski Targ Minerałów i Chatę Zielarki Alpejskiej.",
        "Eryk ma dodatkowy Patrol Górskiego Szlaku.",
        "Łowca Potworów Ragna zleca polowanie na Trolli Szamanów i Króla Trolli.",
        "Dagna zleca odzyskanie Skradzionych Skrzyń Rudy oraz serię zadań na konkretne rudy.",
        "Twierdza Gigantów ma 50 prawdziwych poziomów.",
        "Bossowie Twierdzy stoją na poziomach 10, 20, 30, 40 i 50.",
        "Żywy boss blokuje wejście na kolejny poziom.",
        "W Twierdzy występują Ogrzy Miotacze Głazów, Cyklopi Strażnicy i Górskie Giganty.",
        "Prowadzenie: prowadz twierdza gigantow.",
    ],
    "questy_kowalstwa_1_200": [
        "Kowal Górski Brok ma 13-etapowy łańcuch Kowalstwa od levelu 1 do 200.",
        "Questy wymagają jednocześnie odpowiedniego levelu Młota Rzemieślniczego i Kowalstwa.",
        "Po każdym wykutym przedmiocie gra czyta postęp np. 1 z 3.",
        "Finał level 200 wymaga wykucia pełnego sześcioczęściowego Zestawu Eternium.",
        "Każdy etap odnawia się po 60 minutach.",
    ],
    "questy_gotowania_1_200": [
        "Marcel ma 13 etapów z konkretnymi potrawami od levelu 1 do 200.",
        "Wykonanie potraw jest liczone tak samo jak mikstury Orina.",
        "Po każdym gotowaniu słyszysz dokładny postęp.",
        "Każdy etap odnawia się po 60 minutach.",
    ],
    "questy_konkretne_zasoby": [
        "Zielarka Alpejska Ira zleca 10 Lawendy, 8 Żeń-szenia i 5 Księżycowych Kwiatów z osobnych łąk.",
        "Handlarka Dagna ma zadania na konkretne rudy od Miedzi do Eternium.",
        "Mistrz Wędkarstwa Neris ma zadania na konkretne gatunki i rzadkie warianty ryb.",
        "Wśród zleceń Neris są trzy Złote Okazy Pstrąga i jeden Pradawny Tuńczyk.",
        "Stare zapasy nie nabijają licznika zdobywania. Zasób musi zostać pozyskany po przyjęciu questa.",
        "Do oddania nadal trzeba posiadać wymaganą liczbę sztuk.",
        "Każdy quest profesyjny odnawia się co 60 minut.",
    ],
    "rare_trolls_elites": [
        "Górski Troll może przy spawnie zostać zastąpiony rzadkim wariantem.",
        "Rzadkie trolle: Albinos Troll, Kryształowy Troll, Pradawny Troll i Troll Runiczny.",
        "Zwykłe trolle, rzadkie trolle i mieszkańcy Twierdzy mogą pojawić się jako elity.",
        "Affixy elit: Opancerzony, Wampiryczny, Regenerujący, Lodowy, Ognisty i Astralny.",
        "Opancerzony redukuje otrzymywane obrażenia.",
        "Wampiryczny wysysa życie.",
        "Regenerujący odnawia HP.",
        "Lodowy i Ognisty wzmacniają magię.",
        "Astralny zmienia typ obrażeń i częściowo omija obronę.",
        "consider pokazuje affix oraz informację o rzadkim trollu.",
    ],
    "questy_mikstur_orina": [
        "Orin ma teraz 11-etapowy łańcuch zleceń Alchemii od Moździerza level 1 do 200.",
        "Etap I level 1: 3 Mikstury Many.",
        "Etap II level 5: 4 Mikstury Leczenia.",
        "Etap III level 40: 3 Wielkie Mikstury Leczenia.",
        "Etap IV level 60: 3 Wielkie Mikstury Many.",
        "Etap V level 80: 2 Eliksiry Witalności.",
        "Etap VI level 100: 2 Najwyższe Mikstury Leczenia.",
        "Etap VII level 120: 2 Najwyższe Mikstury Many.",
        "Etap VIII level 140: 2 Wielkie Eliksiry Witalności.",
        "Etap IX level 160: 2 Toniki Duszy.",
        "Etap X level 180: 1 Astralny Eliksir Odnowy.",
        "Etap XI level 200: 1 Eliksir Wiecznej Duszy.",
        "Każdy etap śledzi faktycznie uwarzone sztuki i czyta postęp po każdym warzeniu.",
        "Każde zlecenie jest powtarzalne po 60 minutach.",
        "Kolejny etap wymaga ukończenia poprzedniego oraz odpowiedniego levelu Moździerza.",
    ],
    "postep_mikstur": [
        "Questy Alchemii Orina śledzą teraz faktycznie uwarzone mikstury od momentu przyjęcia zadania.",
        "Po każdym warzeniu otrzymujesz komunikat np. Wykonałeś: Mikstura Many. Postęp 1 z 3.",
        "Kolejne warzenie pokazuje 2 z 3, a trzecie 3 z 3.",
        "Bonusowa mikstura z Tieru Moździerza także liczy się jako wykonana, ponieważ rzeczywiście została wytworzona.",
        "Mikstury posiadane przed przyjęciem questa nie zwiększają licznika wykonania.",
        "Po wykonaniu wymaganej liczby nadal musisz posiadać odpowiednią liczbę mikstur, aby oddać je Orinowi.",
        "Jeśli zużyjesz lub sprzedasz miksturę, dziennik pokaże, że wykonanie jest zakończone, ale brakuje sztuk do oddania.",
        "Po ponownym przyjęciu questa po godzinnym cooldownie licznik wykonania wraca do 0.",
        "Dotyczy wszystkich jedenastu zleceń Alchemii Orina.",
    ],
    "wioska_gorska": [
        "Dodano Wioskę Górską w nowym regionie Gór.",
        "Ze Wzgórza Kamiennych Znaków idź na wschód przez Górską Przełęcz.",
        "Na placu Wioski Górskiej są drogi do Domu Straży, Górskiej Gospody i Szlaku Trolli.",
        "Strażnik Górski Eryk w Domu Straży daje zadanie Plaga Trolli.",
        "Zadanie wymaga zabicia 12 trolli w Jaskini Trolli.",
        "Jaskinia Trolli ma wejście, trzy komory i Legowisko Króla Trolli.",
        "W jaskini występują Górskie Trolle, Trolle Osiłki i Trolle Szamani.",
        "Boss: Król Trolli Grum. Jest nieagresywny i walka zaczyna się dopiero po jawnej komendzie ataku.",
        "Prowadzenie: prowadz wioska gorska, prowadz jaskinia trolli, prowadz eryk.",
    ],
    "laki_zielarskie": [
        "Dodano osobne Łąki Zielarskie dla konkretnych ziół.",
        "Łąka Mięty daje Miętę.",
        "Łąka Rumianku daje Rumianek.",
        "Łąka Pokrzywy daje Pokrzywę.",
        "Łąka Melisy daje Melisę.",
        "Łąka Lawendy daje Lawendę.",
        "Łąka Krwawnika daje Krwawnik.",
        "Łąka Szałwii daje Szałwię.",
        "Łąka Waleriany daje Walerianę.",
        "Łąka Żeń-szenia daje Żeń-szeń.",
        "Łąka Księżycowego Kwiatu daje Księżycowy Kwiat.",
        "Wejście do kompleksu Łąk Zielarskich prowadzi na północ z Łąki Kwiatów.",
        "zbieraj i zbieraj on działają na każdej z tych łąk.",
        "Auto-Zielarstwo nie chodzi między łąkami; zbiera tylko tam, gdzie stoisz.",
        "Rzadkie warianty roślin nadal mogą pojawić się przy zbieraniu.",
    ],
    "questy_rzemieslnicze_godzina": [
        "Wszystkie powtarzalne questy profesyjne i rzemieślnicze odnawiają się dokładnie co 60 minut od ukończenia.",
        "Próba Rybaka, Próba Górnika, Próba Drwala i Próba Zielarki: 60 minut.",
        "Trzy zlecenia Haldora: każde 60 minut.",
        "Trzy zlecenia Marcela: każde 60 minut.",
        "Trzy zlecenia Orina: każde 60 minut.",
        "Łącznie 13 questów profesyjno-rzemieślniczych.",
        "Zwykłe questy fabularne nie zostały zmienione.",
    ],
    "kowalstwo": [
        "Kowalstwo jest pełną profesją level 1-200.",
        "Kowalstwo korzysta z istniejącego Młota Rzemieślniczego level 1-200 i nie dodaje nowego narzędzia.",
        "Przetapianie metali i kucie w Kuźni Dusz daje XP Kowalstwa oraz XP Młota Rzemieślniczego.",
        "Receptury przechodzą od Żelaza, Srebra i Złota do Kobaltu, Run, Smoczej Stali, Astralu, Pustki i Eternium.",
        "Każdy metal ma sztabkę oraz sześć elementów wyposażenia: hełm, pancerz, rękawice, nogawice, buty i talizman.",
        "Wyższe receptury wymagają jednocześnie odpowiedniego levelu Kowalstwa i Młota.",
        "Komendy: kowalstwo, kuj <receptura>, craft <receptura>, receptury kowalstwo.",
        "Haldor w Kuźni daje trzy poziomy zleceń Rzemiosła/Kowalstwa.",
        "Zlecenia Haldora są powtarzalne i każde odnawia się dokładnie co 60 minut.",
        "Questy Haldora dają XP Kowalstwa, XP Młota oraz walutę.",
        "Kowalstwo nie ma trwałości, zużycia ani napraw narzędzi.",
    ],
    "rare_resources": [
        "Dodano rzadkie warianty zasobów profesyjnych.",
        "Ryby mogą wypaść jako Albinos, Złoty okaz, Olbrzymi okaz albo Pradawny okaz.",
        "Rzadkie ryby mają większą wartość sprzedaży i są przechowywane jako osobne okazy w Siatce.",
        "Górnictwo losuje jakość żyły przy każdym udanym wydobyciu.",
        "Zwykła żyła daje x1, Bogata x2, Kryształowa x3, a Legendarna x5 tej samej rudy.",
        "Czysty mithril pozostaje osobną bardzo rzadką walutą i nie jest mnożony przez żyłę.",
        "Drewno może być Bujne, Pradawne, Kryształowe albo Legendarne.",
        "Rośliny mogą być Bujne, Lśniące, Pradawne albo Legendarne.",
        "Rzadkie drewno i rośliny są osobnymi cenniejszymi okazami w magazynach profesji.",
        "Szanse na rzadkie warianty poprawiają się wraz z levelem używanego narzędzia.",
        "Questy zbierania kategorii liczą również rzadkie warianty.",
        "Sprzedaj wszystko działa również na rzadkie warianty.",
    ],
    "codex_swiata": [
        "Codex Świata łączy wiedzę o zasobach, mobach, bossach i reliktach.",
        "codex pokazuje podsumowanie wszystkich działów.",
        "codex ryby pokazuje wszystkie bazowe gatunki i zasady rzadkich wariantów.",
        "codex rośliny pokazuje rośliny i warianty.",
        "codex drewno pokazuje drewno i warianty drzew.",
        "codex rudy pokazuje wszystkie rudy i cztery rodzaje żył.",
        "codex moby pokazuje zwykłych przeciwników.",
        "codex bossowie pokazuje bossów świata, Krypty, Wieży oraz Mythic.",
        "codex relikty pokazuje relikty i unikalne trofea.",
        "codex warianty opisuje wszystkie rzadkie warianty profesyjne.",
        "codex <nazwa> wyszukuje konkretny zasób, mob, bossa lub relikt.",
        "Długie listy są dzielone na części przyjazne NVDA.",
    ],
    "astralne_sety": [
        "Astralne zestawy mają teraz pełne bonusy 2/4/6 części.",
        "Każdy Krąg Astralny ma teraz 6 elementów: głowa, korpus, dłonie, nogi, stopy i talizman.",
        "2 części jednego Kręgu: +12 procent maksymalnego HP i Many.",
        "4 części jednego Kręgu: dodatkowo +15 procent wszystkich zadawanych obrażeń.",
        "6 części jednego Kręgu: dodatkowo +20 procent obrony fizycznej i magicznej.",
        "Bonusy Astralne mogą współistnieć z aktywnymi bonusami Zestawu Krypty.",
        "stats i equipment czytają aktywny Zestaw Astralny.",
    ],
    "mythic_endgame": [
        "Mityczna Krypta odblokowuje się od Soul Level 100.",
        "Nie wymaga ukończenia zwykłej Krypty do piętra 200.",
        "Wejście do Mitycznej Krypty znajduje się w Głębi Krypty.",
        "Mityczna Krypta ma 200 poziomów i bossa co 10 pięter.",
        "Mityczna Wieża Astralna odblokowuje się od Soul Level 100.",
        "Nie wymaga ukończenia zwykłej Wieży Astralnej do poziomu 200.",
        "Wejście do Mitycznej Wieży znajduje się przy Astralnej Bramie.",
        "Mityczna Wieża Astralna ma 200 poziomów i bossa co 10 poziomów.",
        "Mityczni bossowie mają znacznie więcej HP, wyższe obrażenia i lepsze nagrody.",
        "Boss Mitycznej Krypty blokuje zejście, a boss Mitycznej Wieży blokuje wejście wyżej.",
        "Mityczna Krypta używa końcowego ekwipunku Krypty, a Mityczna Wieża końcowego Astralnego Kręgu.",
    ],
    "lochy_profesyjne": [
        "Dodano cztery lochy profesyjne po 20 poziomów.",
        "Kopalnia Kryształów zaczyna się w Kryształowej Komnacie i rozwija Górnictwo.",
        "Zatopiona Grota zaczyna się przy Morskim Molo i rozwija Wędkarstwo.",
        "Pradawny Las zaczyna się w Głębi Gaju i rozwija Drwalstwo.",
        "Ogród Alchemika zaczyna się w Chacie Zielarki i rozwija Zielarstwo.",
        "Poziom 1 wymaga podstawowego narzędzia, a kolejne poziomy wymagają coraz wyższego levelu narzędzia.",
        "Poziom 20 wymaga narzędzia level 200.",
        "Im głębiej w lochu profesyjnym, tym wyższy poziom zasobów może wypaść.",
        "Auto-profesja uruchomiona wewnątrz lochu pozostaje w aktualnej komorze i dalej zbiera zasoby.",
        "Prowadzenie: prowadz kopalnia krysztalow, prowadz zatopiona grota, prowadz pradawny las, prowadz ogrod alchemika.",
    ],
    "zasoby_swiata": [
        "World Resources Pack dodaje szeroki przekrój realnych zasobów z całego świata.",
        "Dodano 160 nowych realnych ryb: po 40 do rzeki, jeziora, morza i oceanu.",
        "Dodano 80 nowych roślin, ziół i przypraw.",
        "Dodano 50 nowych rodzajów drewna.",
        "Dodano 40 nowych realnych rud i minerałów.",
        "Nowe ryby są faktycznie łowione przez low i low on.",
        "Nowe rośliny są faktycznie zbierane przez zbieraj i zbieraj on.",
        "Nowe drewna są faktycznie pozyskiwane przez tnij i tnij on.",
        "Nowe rudy są faktycznie wydobywane w Kopalni Głębinowej przez kop i kop on.",
        "Zasoby odblokowują się wraz z levelem narzędzia, a rudy także z głębokością.",
        "atlas ryby, atlas zioła, atlas rośliny, atlas drewno i atlas rudy automatycznie obejmują nowy pakiet.",
        "To duży grywalny przekrój zasobów świata, a nie literalna lista każdej naukowo opisanej species na Ziemi.",
    ],
    "atlas_kompletny": [
        "Atlas zasobów jest teraz kompletny.",
        "atlas ryby pokazuje wszystkie istniejące ryby w grze, a następnie podział na rzekę, jezioro, morze i ocean.",
        "atlas drewno pokazuje wszystkie istniejące rodzaje drewna oraz podział według terenów.",
        "atlas rudy pokazuje wszystkie istniejące rudy, wymagany level Kilofa i minimalną głębokość Kopalni Głębinowej.",
        "atlas zioła i atlas rośliny pokazują wszystkie istniejące zioła i rośliny oraz grupy występowania.",
        "Długie listy są dzielone na krótsze części, żeby NVDA czytał je wygodniej.",
        "Można nadal wpisać atlas <nazwa surowca>, aby usłyszeć informacje o jednym konkretnym zasobie.",
        "Pełne atlasy są bezpośrednio oparte na aktywnych listach RESOURCE_IDS, więc nowy zasób nie powinien wypaść z pełnego spisu.",
    ],
    "kopalnia_200": [
        "Kopalnia Głębinowa ma 200 prawdziwych poziomów.",
        "Kryształowa Komnata prowadzi przez down na poziom 1.",
        "Każde udane kopanie na najgłębszym odblokowanym poziomie daje 1 z 5 uderzeń w ścianę w dół.",
        "Po 5 uderzeniach kolejny poziom zostaje trwale odblokowany w SQLite.",
        "Im głębiej, tym lepsza pula rud.",
        "Level Kilofa nadal ogranicza jakość wydobycia.",
        "1-9: Kamień i Miedź.",
        "10-24: Miedź i Żelazo.",
        "25-49: Żelazo i Srebro.",
        "50-99: Srebro i Złoto.",
        "100-119: Złoto i Kobalt.",
        "120-139: Kobalt i Kamień Runiczny.",
        "140-159: Kamień Runiczny i Smocza Stal.",
        "160-179: Smocza Stal i Ruda Astralna.",
        "180-199: Ruda Astralna i Ruda Pustki.",
        "200: Ruda Pustki i Eternium.",
        "kopalnia pokazuje najgłębszy poziom i postęp ściany.",
        "kop on kopie tylko w aktualnym miejscu i nie schodzi sam po przebiciu ściany.",
    ],
    "auto_chodzenie": [
        "Auto-profesje nie chodzą samodzielnie.",
        "low on łowi tylko w aktualnym łowisku i nie przemieszcza postaci.",
        "zbieraj on zbiera tylko w aktualnym miejscu i nie przemieszcza postaci.",
        "tnij on ścina tylko w aktualnym miejscu i nie przemieszcza postaci.",
        "kop on kopie tylko w aktualnym miejscu; po przebiciu ściany trzeba zejść ręcznie.",
        "Manualny ruch gracza nadal wyłącza aktywne auto.",
        "off nadal dokańcza bieżącą akcję i dopiero potem zatrzymuje automat.",
    ],
    "laki": [
        "Strefa Łąk składa się teraz z czterech lokacji.",
        "Srebrna Łąka jest centralnym punktem strefy.",
        "Łąka Mięty leży na wschód od Srebrnej Łąki i prowadzi dalej do Brzegu Rzeki.",
        "Łąka Kwiatów leży na zachód od Srebrnej Łąki i prowadzi dalej do Gaju Szeptów.",
        "Łąka Nadjeziorna leży na południe od Srebrnej Łąki i prowadzi dalej do Srebrnego Jeziora.",
        "Na wszystkich łąkach działa zbieraj i zbieraj on.",
        "Łąka Mięty częściej daje Miętę i Melisę.",
        "Łąka Kwiatów częściej daje Rumianek, Lawendę i Krwawnik.",
        "Łąka Nadjeziorna ma zioła wilgotnych terenów, a na wyższych poziomach Sierpa może pojawić się Gwiezdny mech.",
        "Użyj prowadz srebrna laka, prowadz laka miety, prowadz laka kwiatow albo prowadz laka nadjeziorna.",
    ],
    "auto_off": [
        "low off, fish off, kop off, mine off, tnij off, woodcut off i zbieraj off zatrzymują automat po dokończeniu bieżącej akcji.",
        "Jeśli akcja już trwa, nie jest anulowana.",
        "Po zakończeniu dostajesz normalnie surowiec, XP profesji i XP używanego narzędzia.",
        "Następna automatyczna akcja już się nie rozpoczyna.",
        "Wymuszone zatrzymanie, na przykład wyjście z gry, podróż albo przełączenie na inną auto-aktywność, nadal może przerwać akcję natychmiast.",
    ],
    "kurs_walut": [
        "Waluta przelicza się automatycznie.",
        "1000 srebrnych monet = 1 złota moneta.",
        "1 000 000 złotych monet = 1 mithrilowa moneta.",
        "Po osiągnięciu progu monety są automatycznie przenoszone do wyższego nominału.",
        "Automatyczne przeliczanie działa w portfelu oraz Banku Dusz.",
        "Stara ręczna komenda wymiany została usunięta.",
        "Istniejący majątek nie jest zerowany; zachowuje pełną wartość.",
    ],
    "wiecej_ryb": [
        "Dodano 40 nowych gatunków ryb: po 10 do rzeki, jeziora, morza i oceanu.",
        "Nowe ryby mają progi Wędki od levelu 1 aż do 200.",
        "Rzeka otrzymała między innymi Ukleję Rzeczną, Pstrąga Potokowego, Tajmienia Rzecznego, Lipienia Duchów i Wiecznego Smoka Rzecznego.",
        "Jezioro otrzymało między innymi Kiełbia Jeziorowego, Złotego Lina, Kryształową Sieję, Astralnego Szczupaka i Wiecznego Węża Jeziora.",
        "Morze otrzymało między innymi Belonę, Prażmę Morską, Kongera, Śledzia Burzy i Wiecznego Smoka Morza.",
        "Ocean otrzymał między innymi Rybę Latającą, Tuńczyka Żółtopłetwego, Marlina Czarnego, Marlina Pustki i Lewiatana Świata.",
        "Komenda woda automatycznie pokazuje nowe ryby po osiągnięciu wymaganego levelu Wędki.",
        "fish losuje z dokładnie tej samej listy, którą pokazuje woda.",
        "Nowe ryby są widoczne w atlasie odpowiedniego łowiska.",
        "Nowe ryby można normalnie przechowywać w Siatce i sprzedawać.",
    ],
    "oddawanie_zadan": [
        "Po wykonaniu celu zadania dziennik pokazuje GOTOWE DO ODDANIA.",
        "Wróć do NPC, który dał zadanie.",
        "oddaj zadanie i oddaj questa automatycznie oddają jedyne gotowe zadanie u NPC w tej lokacji.",
        "oddaj <nazwa zadania> pozwala wybrać konkretne zadanie.",
        "zdaj zadanie oraz turnin są aliasami.",
        "Jeśli kilka zadań jest gotowych u NPC w tej samej lokacji, gra nie zgaduje i prosi o pełną nazwę.",
        "Jeśli zadanie nie jest ukończone, oddaj podaje aktualny postęp.",
        "talk to <NPC> działa tak samo jak talk <NPC>.",
        "Dotychczasowa rozmowa z NPC nadal może przyjąć albo oddać jego zadanie.",
        "Oddawanie collect nadal zabiera wymagane przedmioty dopiero przy rozliczeniu zadania.",
        "Oddawanie collect_category nadal korzysta z właściwego magazynu profesji i inventory.",
    ],
    "woda": [
        "Komenda woda działa w każdym łowisku: rzeka, jezioro, morze i ocean.",
        "Pokazuje typ aktualnego łowiska.",
        "Pokazuje aktualny level Wędki.",
        "Pokazuje dokładną liczbę gatunków, które mogą zostać wylosowane przez fish przy obecnym levelu Wędki.",
        "Czyta również nazwy wszystkich aktualnie dostępnych gatunków.",
        "Jeśli kolejna ryba endgame jest jeszcze zablokowana, woda podaje wymagany level Wędki.",
        "Lista pochodzi z dokładnie tego samego poola co rzeczywiste łowienie.",
        "Liczba oznacza gatunki dostępne do złowienia, a nie skończoną populację sztuk.",
        "Łowiska nie wyczerpują się od łowienia.",
    ],
    "gotowanie_rozbudowane": [
        "Gotowanie korzysta z Noża Kucharskiego level 1-200.",
        "Nie jest osobnym levelem postaci i nie dodaje Character XP.",
        "Gotowanie nie jest osobną profesją; rozwija wyłącznie Nóż Kucharski.",
        "Potrawy przygotowuje się w Karczmie Pod Błękitnym Płomieniem albo na Targu Rybnym.",
        "gotowanie pokazuje stan systemu i aktualny Nóż Kucharski.",
        "gotuj lista pokazuje wszystkie receptury Gotowania.",
        "gotuj <potrawa> przygotowuje wybraną potrawę.",
        "receptury cook nadal działa.",
        "Receptury mają progi Noża: 1,10,20,30,40,50,60,70,80,90,95,99,100,120,140,160,180 i 200.",
        "Dodano Okoń w Ziołowej Skorupce, Zupę ze Srebrnego Pstrąga, Zapiekankę Jeziornego Rybaka, Makrelę Korzenną, Łososia z Ziołami i Rosół z Księżycowego Węgorza.",
        "Każda akcja Gotowania wykorzystuje rzeczywisty czas Noża Kucharskiego.",
        "Na levelu 1 Nóż potrzebuje 12 sekund, a na levelu 200 4 sekundy.",
        "Tier Noża daje szansę na dodatkową porcję.",
        "Gotowanie zużywa składniki z właściwych magazynów profesji oraz inventory.",
        "Potrawy przywracają HP, a część również Manę.",
        "Questy Kucharza Marcela pozostają i nadal wykorzystują Gotowanie.",
    ],
    "hp_bossow_lochow": [
        "Bossowie Krypty i Wieży Astralnej mają teraz HP według numeru piętra.",
        "Wzór: numer piętra razy 1000 HP.",
        "Krypta piętro 10: 10000 HP.",
        "Krypta piętro 20: 20000 HP.",
        "Krypta piętro 100: 100000 HP.",
        "Krypta piętro 200: 200000 HP.",
        "Wieża Astralna poziom 100: 100000 HP.",
        "Wieża Astralna poziom 150: 150000 HP.",
        "Wieża Astralna poziom 200: 200000 HP.",
        "Zwykłe moby nadal mają globalne 2 razy HP z v0.6.94.",
        "Bossowie świata poza Kryptą i Wieżą zachowują swoje 2 razy HP.",
        "Damage i nagrody bossów nie zostały zwiększone.",
        "consider automatycznie korzysta z nowych wartości HP.",
    ],
    "hp_mobow": [
        "Wszystkie moby i bossowie mają teraz globalnie 2 razy więcej maksymalnego HP.",
        "Zmiana obejmuje zwykłych przeciwników, bossów świata, manekina treningowego, Kryptę 1-200 i Wieżę Astralną 100-200.",
        "Obrażenia mobów nie zostały zwiększone.",
        "Nagrody za zabicie, Soul XP, Class XP, stat_progress, waluta i loot pozostają bez zmian.",
        "Mechaniki bossów nadal korzystają z ich aktualnego podwojonego maksymalnego HP.",
        "Respawn pozostaje bez zmian i przywraca pełne nowe maksymalne HP.",
        "consider automatycznie pokazuje i ocenia nowe wartości HP.",
        "Moby i bossowie nadal nie są agresywni.",
        "Walka nadal działa turowo: jedna akcja gracza, jedna odpowiedź przeciwnika.",
    ],
    "soul_xp_bloki": [
        "Wymagane Soul XP podwaja się po każdym pełnym bloku 10 Soul Leveli.",
        "Soul Level 1-10 używa mnożnika x1.",
        "Soul Level 11-20 używa mnożnika x2.",
        "Soul Level 21-30 używa mnożnika x4.",
        "Soul Level 31-40 używa mnożnika x8.",
        "Dalej mnożnik podwaja się analogicznie co 10 leveli aż do Soul Level 200.",
        "Bazowy wzór nadal wynosi 180 + 60 razy Soul Level minus 1, a następnie jest mnożony przez mnożnik bloku.",
        "Przykład: z Soul Level 10 na 11 potrzeba 720 XP.",
        "Przykład: z Soul Level 11 na 12 potrzeba 1560 XP.",
        "Przykład: z Soul Level 21 na 22 potrzeba 5520 XP.",
        "Przykład: z Soul Level 51 na 52 potrzeba 101760 XP.",
        "Nagrody Soul XP z mobów, bossów, drużyny i przedmiotów nie zostały zwiększone.",
        "Już zdobyty Soul XP pozostaje zapisany i nie jest resetowany.",
        "Soul Level nadal ma zakres 1-200.",
    ],
    "consider": [
        "consider <mob>, con <mob> albo ocen <mob> ocenia przeciwnika bez rozpoczynania walki.",
        "Jeśli w lokacji jest dokładnie jeden mob, samo consider oceni właśnie jego.",
        "Przy wielu mobach podaj nazwę przeciwnika.",
        "Ocena może być: bardzo słaby, słaby, korzystny, porównywalny, niebezpieczny, bardzo niebezpieczny albo śmiertelnie groźny.",
        "Consider podaje aktualne HP moba, bazowy atak, typ obrażeń oraz orientacyjny normalny cios gracza.",
        "Podaje również orientacyjną liczbę trafień potrzebnych obu stronom przy obecnym HP gracza.",
        "Uwzględnia obronę fizyczną lub magiczną, unik, redukcje rasowe i klasowe oraz krytyki w średnim wyniku.",
        "Bossowie są oceniani ostrożniej, ponieważ specjalne mechaniki zwiększają ryzyko.",
        "Jeśli boss ma opis mechaniki, consider go przeczyta.",
        "Consider nie angażuje moba, nie wykonuje ataku, nie zużywa Many i nie zajmuje tury.",
    ],
    "wolniejsze_staty": [
        "Rozwój pięciu statystyk został spowolniony dwukrotnie.",
        "Wcześniej wszystkie statystyki rosły o +1 po 50 punktach Postępu Rozwoju.",
        "Teraz potrzeba 100 punktów Postępu Rozwoju.",
        "Po osiągnięciu 100 nadal rosną jednocześnie: Siła +1, Zręczność +1, Kondycja +1, Inteligencja +1 i Siła Woli +1.",
        "Statystyki nadal nie mają maksymalnego limitu.",
        "Nie dodano levelu postaci ani Character XP.",
        "Istniejący zapisany Postęp Rozwoju nie jest zerowany ani przeliczany.",
    ],
    "wieza_astralna": [
        "Wieża Astralna jest drugim lochowym endgame obok Krypty.",
        "Wejście znajduje się przy Zapomnianej Kapliczce. Wpisz prowadz wieza astralna.",
        "Do wejścia na pierwszy poziom potrzebny jest Soul Level 100.",
        "Wieża ma poziomy od 100 do 200, czyli 101 właściwych poziomów.",
        "Boss stoi co 10 poziomów: 100, 110, 120, aż do 200.",
        "Boss blokuje drogę w górę, dopóki żyje.",
        "Pokonanie bossa odblokowuje niezależny Astralny Portal/checkpoint.",
        "Astralny Portal działa wyłącznie przy Astralnej Bramie.",
        "Komenda astralportal pokazuje checkpointy.",
        "Komenda astralportal 150 przenosi na poziom 150, jeśli checkpoint jest odblokowany.",
        "Zwykłe moby zostawiają 1 element Astralnego ekwipunku, bossowie 3.",
        "Każdy z 11 bossów ma unikalny relikt; boss 200 gwarantuje swój relikt.",
        "Wieża ma własne moby, bossów, mechaniki i klimat gwiezdny, niezależny od Krypty.",
        "Moby i bossowie nie atakują automatycznie.",
        "Walka nadal jest turowa: jedna akcja gracza, jedna odpowiedź przeciwnika.",
    ],
    "soul_tier45_krypta200": [
        "Broń Duszy ma teraz 5 Tierów.",
        "Tier 4 wymaga Soul Level 120, posiadania Tier 3 i ukończenia Próby Elora.",
        "Próba Tier 4 wymaga pokonania Królowej Otchłannej Krypty na piętrze 120.",
        "Tier 5 wymaga Soul Level 180, posiadania Tier 4 i ukończenia ostatniej Próby Elora.",
        "Próba Tier 5 wymaga pokonania Cesarza Upiorów na piętrze 180.",
        "Tier 4 zwiększa standardowy bonus specjalizacji Broni Duszy do 20 procent.",
        "Tier 5 zwiększa standardowy bonus specjalizacji Broni Duszy do 25 procent.",
        "Łotrzyk otrzymuje odpowiednio 8 i 10 punktów procentowych bonusu uniku z Broni Duszy.",
        "Strażnik otrzymuje odpowiednio 12 i 15 procent redukcji z Broni Duszy.",
        "Krypta ma teraz 200 pięter.",
        "Boss jest co 10 pięter, czyli łącznie 20 bossów.",
        "Portal Krypty odblokowuje się po każdym bossie i działa aż do piętra 200.",
        "Co 10 pięter zmienia się Tier lootu; Krypa posiada teraz sety Tier 1-20.",
        "Bossowie pięter 110-200 mają własne nazwy, mechaniki i unikalne relikty.",
        "Władca Dwustu Pięter na piętrze 200 jest nowym finałowym bossem Krypty.",
    ],
    "lancuchy_specjalistow": [
        "Haldor, Marcel i Orin mają teraz po 3 osobne etapy zleceń.",
        "Etap 1 jest dostępny od levelu narzędzia 1.",
        "Etap 2 wymaga ukończenia etapu 1 i levelu narzędzia 100.",
        "Etap 3 wymaga ukończenia etapu 2 i levelu narzędzia 200.",
        "Haldor: Żelazne sztabki, Runiczny Talizman Straży, Talizman Wiecznej Duszy.",
        "Marcel: Pieczone ryby rzeczne, Runiczny Półmisek Rybny, Wieczna Uczta Oceanu.",
        "Orin: Mikstury Many, Najwyższe Mikstury Leczenia, Eliksir Wiecznej Duszy.",
        "Rozmowa ze specjalistą podaje stan każdego etapu: aktywne, ukończone, dostępne albo zablokowane.",
        "Po odblokowaniu wyższego etapu specjalista automatycznie proponuje najwyższy dostępny etap.",
        "Każdy etap pozostaje powtarzalny z 30-minutowym cooldownem.",
    ],
    "bank": [
        "Bank Dusz znajduje się na Rynku u Bankiera Aldrena.",
        "prowadz bank prowadzi bezpośrednio na Rynek.",
        "bank pokazuje saldo bankowe oraz przedmioty w skrytce.",
        "bank wplac 100 srebra wpłaca srebro.",
        "bank wplac 5 zlota oraz bank wplac 1 mithril działają analogicznie.",
        "bank wyplac <ile> <waluta> wypłaca walutę.",
        "bank wplac wszystko wpłaca całe srebro, złoto i mithril z portfela.",
        "bank wyplac wszystko wypłaca wszystkie trzy waluty z banku.",
        "bank wloz <przedmiot> [ile] przenosi zwykły przedmiot z inventory do trwałej skrytki.",
        "bank wyjmij <przedmiot> [ile] przenosi przedmiot ze skrytki do inventory.",
        "Założonego elementu wyposażenia nie można schować w banku.",
        "Bank jest trwały w SQLite i nie znika po wylogowaniu ani restarcie serwera.",
        "Bank nie pobiera opłat.",
    ],
    "questy_specjalistow": [
        "Mistrz Rzemiosła Haldor ma 3-etapowy łańcuch powtarzalnych zleceń rzemieślniczych.",
        "Haldor prosi o 3 Żelazne sztabki i nagradza XP Młota Rzemieślniczego oraz srebrem.",
        "Kucharz Marcel ma 3-etapowy łańcuch powtarzalnych zleceń Gotowania.",
        "Marcel prosi o 3 Pieczone ryby rzeczne i nagradza XP Noża Kucharskiego oraz srebrem.",
        "Mistrz Alchemii Orin ma 3-etapowy łańcuch powtarzalnych zleceń Alchemii.",
        "Orin prosi o 3 Mikstury Many i nagradza XP profesji Alchemia, XP Moździerza oraz srebrem.",
        "Każde z tych zleceń ma 30 minut odnowienia po ukończeniu.",
        "Rozmowa ze specjalistą nadal najpierw podaje informacje o jego narzędziu i recepturach.",
    ],
    "sprzedaj_wszystko": [
        "sprzedaj wszystko siatka sprzedaje wszystkie ryby z Siatki.",
        "sprzedaj wszystko sakwa sprzedaje wszystkie rudy z Sakwy.",
        "sprzedaj wszystko stos sprzedaje całe drewno ze Stosu.",
        "sprzedaj wszystko torba sprzedaje wszystkie zioła z Torby Zielarskiej.",
        "Działają też: sprzedaj wszystko ryby, rudy, drewno i ziola.",
        "sprzedaj wszystko przedmioty działa jak sprzedaj przedmioty.",
        "Każda kategoria nadal wymaga właściwego punktu skupu.",
        "Po sprzedaży gra podaje liczbę sztuk, rodzajów i zarobek.",
    ],
    "naturalne_naucz": [
        "U nauczyciela aktywnej klasy możesz uczyć się skilli naturalną nazwą kategorii.",
        "naucz leczenie wybiera najwyżej odblokowane leczenie tej klasy, którego jeszcze nie znasz.",
        "naucz tarcza wybiera najwyżej odblokowaną osłonę.",
        "naucz unik wybiera najwyżej odblokowany unik.",
        "naucz drain albo naucz wysysanie wybiera skill wysysający życie.",
        "naucz dobij wybiera najwyżej odblokowaną umiejętność execute.",
        "Ofensywne przykłady: naucz ciecie, naucz pocisk, naucz ogien, naucz burza, naucz mlot, naucz strzal.",
        "System bierze pod uwagę tylko skille klasy nauczyciela, przy którym aktualnie stoisz.",
        "Najpierw preferuje skill, którego jeszcze nie znasz, a potem najwyższy dostępny próg Soul.",
        "Pełne nazwy i numery skilli nadal działają.",
    ],
    "czas_narzedzi": [
        "Każda czynność narzędzia ma teraz realny czas wykonania.",
        "Na levelu 1: Wędka 15 sekund, Kilof 30 sekund, Piła 24 sekundy, Młot Rzemieślniczy 20 sekund, Nóż Kucharski 12 sekund, Sierp Zielarski 10 sekund, Moździerz Alchemiczny 18 sekund.",
        "Czas skraca się stopniowo wraz z levelem narzędzia.",
        "Na levelu 200: Wędka 5 sekund, Kilof 10 sekund, Piła 8 sekund, Młot 7 sekund, Nóż 4 sekundy, Sierp 3 sekundy, Moździerz 6 sekund.",
        "Po wpisaniu wedka, kilof, pila, mlot, noz, sierp albo mozdzierz gra podaje aktualny czas akcji.",
        "Auto-łowienie, auto-kopanie, auto-Drwalstwo i auto-Zielarstwo używają tego samego realnego czasu.",
        "Crafting, Gotowanie i Alchemia także czekają rzeczywistą liczbę sekund przed ukończeniem receptury.",
    ],
    "nazwy_narzedzi": [
        "Po wpisaniu nazwy narzędzia gra od razu podaje jego aktualną pełną nazwę Tieru.",
        "Przykład: wedka może powiedzieć Aktualna nazwa narzędzia: Wędka Ucznia.",
        "Po awansie Tieru nazwa zmienia się automatycznie, np. na Wędka Rzeczna albo Wędka Srebrnego Haczyka.",
        "Działa dla: wedka, kilof, pila, mlot, noz, sierp i mozdzierz.",
        "Potem gra nadal podaje level, XP, użycia, Tier, bonus i następny Tier.",
        "Komenda narzedzia pokazuje aktualne nazwy wszystkich posiadanych narzędzi.",
    ],
    "odpoczynek_wszystko": [
        "Odpoczynek zawsze regeneruje wszystko, co można regenerować poza walką.",
        "Co 5 sekund odnawia 10 procent maksymalnego HP oraz 10 procent maksymalnej Many.",
        "Postać bez Many regeneruje tylko HP.",
        "odpoczywaj, rest i regen uruchamiają ten sam pełny odpoczynek.",
        "regen mana oraz mana regen również uruchamiają pełny odpoczynek HP i Many.",
        "Nie ma osobnego trybu regenerującego wyłącznie Manę.",
        "Ruch albo aktywna akcja przerywa odpoczynek.",
    ],
    "specjalisci_profesji": [
        "Dodano siedmiu specjalistów odpowiadających wszystkim istniejącym narzędziom i systemom profesji.",
        "Mistrz Wędkarstwa Neris: Targ Rybny.",
        "Mistrz Górnictwa Kordan: Wejście do Kryształowej Jaskini.",
        "Mistrz Drwalstwa Oren: Obóz Drwala.",
        "Mistrz Rzemiosła Haldor: Kuźnia Dusz.",
        "Kucharz Marcel: Karczma Pod Błękitnym Płomieniem.",
        "Mistrzyni Zielarstwa Sena: Chata Zielarki.",
        "Mistrz Alchemii Orin: Chata Zielarki.",
        "Rozmowa ze specjalistą pokazuje twój level narzędzia, XP, Tier i bonus.",
        "Kucharz, Rzemieślnik i Alchemik przypominają również odpowiednią komendę receptur.",
        "Specjaliści są przyjaznymi NPC i nie można ich atakować.",
    ],
    "regen_mana": [
        "Od v0.6.84 regen mana nie jest osobnym trybem.",
        "regen mana i mana regen uruchamiają pełny odpoczynek.",
        "Odpoczynek odnawia jednocześnie HP i Manę co 5 sekund.",
        "mana nadal pokazuje aktualną i maksymalną Manę.",
        "mana stop zatrzymuje aktywny odpoczynek.",
    ],
    "sprzedaz_hurtowa": [
        "sprzedaj ryby siatka sprzedaje wszystkie ryby z Siatki.",
        "sprzedaj rudy sakwa sprzedaje wszystkie rudy z Sakwy.",
        "sprzedaj drewno stos sprzedaje całe drewno ze Stosu.",
        "sprzedaj ziola torba sprzedaje wszystkie zioła z Torby Zielarskiej.",
        "Każda kategoria nadal wymaga właściwej lokacji skupu.",
        "Hurtowa sprzedaż podaje liczbę sztuk, liczbę rodzajów i łączny zarobek.",
        "Charyzma wzrasta o liczbę sprzedanych sztuk, jak przy sprzedaży ręcznej.",
        "sprzedaj przedmioty sprzedaje z inventory tylko rzeczy z jawną ceną sprzedaży i dozwolone w aktualnej lokacji.",
        "sprzedaj przedmioty nie sprzedaje narzędzi, mikstur, założonego wyposażenia ani rzeczy bez ceny.",
    ],
    "mana_stats_eq": [
        "stats zawsze pokazuje Mana: aktualna z maksymalnej.",
        "Klasa bez Many zobaczy Mana: 0 z 0.",
        "Klasa magiczna albo multiclass magiczny zobaczy aktualną i maksymalną Manę.",
        "eq działa jak equipment.",
    ],
    "wartosc_magazynow": [
        "Wszystkie cztery magazyny profesji pokazują teraz podsumowanie ilości i wartości.",
        "siatka/net: łączna liczba ryb, liczba gatunków i wartość sprzedaży.",
        "sakwa/bag: łączna liczba rud, liczba rodzajów i wartość sprzedaży.",
        "drewno/stos/woodpile: łączna liczba sztuk drewna, liczba rodzajów i wartość sprzedaży.",
        "ziola/herbs: łączna liczba ziół, liczba rodzajów i wartość sprzedaży.",
        "Srebro, złoto i mithril są liczone osobno.",
        "Podsumowania obejmują tylko zawartość danego magazynu, nie zwykły inventory.",
        "Sprawdzenie magazynu niczego nie sprzedaje ani nie usuwa.",
    ],
    "wartosc_siatki": [
        "Komenda siatka albo net pokazuje każdą rybę i jej ilość.",
        "Na końcu podaje łączną liczbę wszystkich ryb w siatce.",
        "Podaje też liczbę różnych gatunków ryb.",
        "Szacowany zarobek jest liczony z aktualnych cen sprzedaży każdej ryby pomnożonych przez jej ilość.",
        "Srebro, złoto i mithril są podawane osobno, bez automatycznej wymiany między walutami.",
        "Wartość obejmuje tylko ryby aktualnie znajdujące się w Siatce, nie ryby w zwykłym inventory.",
        "Podsumowanie nie sprzedaje ryb. To tylko informacja przed sprzedażą.",
    ],
    "tempo_profesji": [
        "Wędkarstwo, Górnictwo, Drwalstwo, Zielarstwo i Alchemia levelują teraz wolniej.",
        "Każda akcja i nagroda daje 2 razy więcej XP profesji niż wcześniej.",
        "Jednocześnie każdy kolejny level profesji wymaga 4 razy więcej XP niż wcześniej.",
        "Efektywnie profesje rozwijają się około 2 razy wolniej.",
        "Przykład level 1: dawniej potrzeba było 80 XP, teraz potrzeba 320 XP.",
        "Typowa akcja dawała wcześniej 10-15 XP, teraz daje 20-30 XP.",
        "Quest profesyjny dający dawniej 1000 XP daje teraz 2000 XP.",
        "Maksymalny level profesji pozostaje 100.",
        "XP narzędzi nie jest tu zmieniane; narzędzia zachowują tempo z v0.6.78.",
    ],
    "zakladanie_lootu": [
        "Ekwipunek zabrany z ciał mobów i bossów można zakładać bez wpisywania pełnej długiej nazwy.",
        "Skróty: załóż hełm, załóż zbroja, załóż rękawice, załóż nogi, załóż buty, załóż talizman.",
        "Działają też warianty bez polskich znaków, np. zaloz helm, zaloz rekawice.",
        "Jeśli masz kilka przedmiotów w tym samym slocie, skrót wybiera najlepszy według obrony, potem rzadkości i bonusu.",
        "Pełna nazwa konkretnego dropu nadal działa i pozwala wymusić dokładnie wybrany przedmiot.",
        "Po przeszukaniu ciała gra podaje skróty zakładania dla zdobytych slotów.",
        "Zmiana ekwipunku podczas aktywnej walki nadal jest zablokowana.",
    ],
    "skill200": [
        "Wszystkie umiejętności mają teraz Skill Level od 1 do 200.",
        "Skill XP zdobywasz nadal przez używanie nauczonej umiejętności.",
        "Wymagany Skill XP pozostaje według tej samej rosnącej formuły i działa dalej powyżej levelu 100.",
        "Moc skilla rośnie również od levelu 101 do 200.",
        "Maksymalna redukcja cooldownu pozostaje ograniczona do 30 procent.",
        "Na Skill Level 200 XP zostaje wyzerowane i skill osiąga maksymalny poziom.",
    ],
    "wolniejszy_xp_narzedzi": [
        "Narzędzia nadal mają level 1-200 i 13 Tierów.",
        "Od v0.6.78 każdy kolejny level narzędzia wymaga 2 razy więcej XP niż wcześniej.",
        "XP przyznawane za łowienie, kopanie, Drwalstwo, crafting, gotowanie, Zielarstwo, Alchemię i nagrody pozostaje bez zmian.",
        "Przykład: dawniej przejście z levelu 1 wymagało 60 XP, teraz wymaga 120 XP.",
        "Nieużywane narzędzia nadal nie zdobywają XP ani użyć.",
    ],
    "skille100_200": [
        "Każda z 12 klas dostała 4 nowe umiejętności endgame.",
        "Nowe progi odblokowania to Soul Level 100, 140, 180 i 200.",
        "Łącznie dodano 48 nowych skilli.",
        "Nowe skille trzeba nauczyć się u właściwego nauczyciela klasy, tak jak wcześniejsze.",
        "Skill Level każdego skilla rozwija się teraz osobno od 1 do 200.",
        "Cooldown, Mana, Skill XP, krytyki i walka turowa pozostają zgodne z istniejącym systemem.",
        "Wpisz skills, skillnames albo porozmawiaj z nauczycielem klasy.",
    ],
    "naturalne_uzyj": [
        "Komenda użyj obsługuje naturalne intencje skilli.",
        "Przykłady: użyj heal, użyj tarcza, użyj unik, użyj drain, użyj dobij goblin.",
        "Ofensywne skróty: użyj ciecie goblin, użyj pocisk goblin, użyj ogien goblin, użyj burza goblin, użyj strzal goblin.",
        "Gra wybiera najwyżej odblokowany i nauczony skill pasujący do intencji.",
        "Jeśli dwa skille mają taki sam najlepszy wynik w multiclassie, gra nie wybierze losowo. Użyj pełnej nazwy.",
        "Pełne komendy skill, cast, użyj umiejętność oraz użyj czar nadal działają.",
    ],
    "prowadz_most": [
        "Komenda prowadz most prowadzi bezpośrednio do lokacji Kamienny Most.",
        "Działa też walk most, idz most, go most oraz prowadz kamienny most.",
        "Prowadzenie wykorzystuje ten sam bezpieczny system wyznaczania trasy co pozostałe cele.",
    ],
    "uzyj_skilla": [
        "Komenda użyj może uruchamiać nauczone umiejętności i czary.",
        "Przykład Wojownika: użyj ciecie goblin uruchamia Potężne Cięcie, jeśli skrót jest jednoznaczny i skill jest nauczony.",
        "Przykład Maga: użyj pocisk goblin może uruchomić Pocisk Arkanów.",
        "Przykład Czarownika: użyj plomien goblin może uruchomić Płomień Otchłani.",
        "Działa też użyj czar <nazwa> [cel], use spell <name> [target], skill <nazwa> [cel] i cast <nazwa> [cel].",
        "Jeżeli krótka nazwa pasuje do kilku aktywnych skilli, użyj pełnej nazwy.",
        "Cooldown, Mana, Skill Level i Skill XP pozostają bez zmian.",
    ],
    "kup_narzedzia": [
        "Narzędzia można kupować krótkimi nazwami bez polskich znaków.",
        "Przykłady: kup wedka, kup kilof, kup pila, kup mlot, kup noz, kup sierp, kup mozdzierz.",
        "Narzędzie nadal trzeba kupić u właściwego sprzedawcy. Gra poda właściwą lokację, jeśli jesteś w złym miejscu.",
        "Kupienie narzędzia nie daje mu XP ani levelu.",
    ],
    "xp_narzedzi": [
        "XP dostaje wyłącznie narzędzie faktycznie użyte w danej akcji.",
        "Łowienie rozwija tylko Wędkę.",
        "Kopanie rozwija tylko Kilof.",
        "Drwalstwo rozwija tylko Piłę.",
        "Crafting rozwija tylko Młot Rzemieślniczy.",
        "Gotowanie rozwija tylko Nóż Kucharski.",
        "Zielarstwo rozwija tylko Sierp Zielarski.",
        "Alchemia rozwija tylko Moździerz Alchemiczny.",
        "Pozostałe narzędzia nie dostają XP, użyć ani leveli od tej akcji.",
    ],
    "endgame_profesje": [
        "Dodano progresję surowców i receptur dla leveli narzędzi 100, 120, 140, 160, 180 i 200.",
        "Wędka odblokowuje nowe ryby endgame; część zależy od typu łowiska: rzeka, jezioro, morze albo ocean.",
        "Kilof odblokowuje: Ruda Kobaltu 100, Kamień Runiczny 120, Smocza Stal 140, Ruda Astralna 160, Ruda Pustki 180 i Eternium 200.",
        "Piła w Głębi Gaju odblokowuje nowe drewna na levelach 100, 120, 140, 160, 180 i 200.",
        "Sierp w Głębi Gaju odblokowuje nowe zioła na levelach 100, 120, 140, 160, 180 i 200.",
        "Rzemiosło, Gotowanie i Alchemia mają po 6 nowych receptur wymagających odpowiednio levelu 100, 120, 140, 160, 180 i 200 narzędzia.",
        "Receptury są twardo zablokowane levelem narzędzia. Samo posiadanie składników nie wystarcza.",
        "Wpisz receptury, receptury craft, receptury cook albo receptury alchemia, aby usłyszeć wymagany level.",
    ],
    "walk": [
        "Prowadzenie obsługuje teraz krótką składnię walk <cel> bez słowa to.",
        "Przykłady: walk targ, walk kuznia, walk swiatynia, walk port, walk karczma, walk jaskinia, walk bandyci.",
        "Polskie warianty: prowadz <cel> oraz idz <cel>.",
        "Działa też starsza składnia walk to <location>.",
        "Można podawać krótkie nazwy NPC, np. walk doran, walk elor, walk roderik, walk liora, walk tomas.",
        "Krypta zachowuje skróty pięter, np. walk krypta 50.",
        "Prowadzenie nadal zatrzyma się przed żywym bossem Krypty blokującym zejście.",
    ],
    "logowanie": [
        "Po każdym zalogowaniu postać rozpoczyna sesję w Świątyni Odrodzenia.",
        "Nie ma znaczenia, gdzie postać wylogowała się poprzednio.",
        "Zapisana lokacja z poprzedniej sesji nie jest miejscem startowym następnego logowania.",
        "Po wejściu do świata HP i Mana są ustawiane jak dotychczas przy logowaniu.",
        "Portale Krypty, questy, ekwipunek i cała trwała progresja pozostają zapisane.",
    ],
    "soul_level_hp": [
        "Każdy awans Soul Level Broni Duszy natychmiast odnawia postać do 100 procent HP.",
        "Działa niezależnie od źródła Soul XP, między innymi z przeciwników oraz Eliksiru Duszy.",
        "Jeżeli Soul XP nie wbije nowego Soul Levelu, HP nie jest odnawiane.",
        "Odnowienie dotyczy tylko HP. Mana nie jest automatycznie odnawiana.",
        "Soul Level nadal ma zakres 1-200.",
    ],
    "rozwoj_statystyk": [
        "Statystyki rosną automatycznie przez Postęp Rozwoju.",
        "Próg wzrostu został zmniejszony do 50 Postępu Rozwoju.",
        "Każde pełne 50 Postępu Rozwoju daje jednocześnie: Siła +1, Zręczność +1, Kondycja +1, Inteligencja +1 i Siła Woli +1.",
        "To oznacza dwa razy szybszy wzrost statystyk niż przy starym progu 100.",
        "Nie ma ręcznego rozdawania punktów.",
        "Levelu postaci nadal nie ma.",
        "Bonus rasy Człowiek do Postępu Rozwoju nadal działa.",
    ],
    "uzywanie_umiejetnosci": [
        "Umiejętności można używać dotychczasową komendą skill <nazwa lub numer> [cel].",
        "Działa też umiejętność <nazwa> [cel], zdolność <nazwa> [cel] oraz cast <nazwa> [cel].",
        "Dodano składnię użyj umiejętność <nazwa> [cel].",
        "Angielska wersja to use skill <name> [target].",
        "Jeżeli po use/użyj podasz bezpośrednio rozpoznawalną nazwę skilla, gra także spróbuje go użyć.",
        "Ofensywne umiejętności nadal rozpoczynają walkę tylko na wyraźną akcję gracza.",
        "Cooldown, Mana, Skill Level i zdobywanie Skill XP działają dokładnie tak jak przy komendzie skill.",
    ],
    "soul200": [
        "Broń Duszy ma teraz Soul Level 1-200.",
        "Wymagane Soul XP podwaja się po każdym pełnym bloku 10 leveli; wpisz help soulxp.",
        "Tier 2 nadal odblokowuje się przez próbę od Soul Level 25.",
        "Tier 3 odblokowuje się przez próbę od Soul Level 60.",
        "Tier 4 odblokowuje się od Soul Level 120 po Próbie Elora na bossie piętra 120 Krypty.",
        "Tier 5 odblokowuje się od Soul Level 180 po Próbie Elora na bossie piętra 180 Krypty.",
        "Po Soul Level 100 Broń Duszy rozwija się dalej aż do 200.",
        "Soul Level nadal zwiększa bazową moc Broni Duszy.",
        "Nie ma levelu postaci.",
    ],
    "narzedzia200": [
        "Wszystkie 7 narzędzi ma level 1-200 i 13 Tierów.",
        "Wędka, Kilof, Piła, Młot Rzemieślniczy, Nóż Kucharski, Sierp Zielarski i Moździerz Alchemiczny rozwijają się do 200.",
        "Tier 8: level 100-119, bonus 15 procent.",
        "Tier 9: level 120-139, bonus 18 procent.",
        "Tier 10: level 140-159, bonus 21 procent.",
        "Tier 11: level 160-179, bonus 24 procent.",
        "Tier 12: level 180-199, bonus 27 procent.",
        "Tier 13: level 200, bonus 30 procent.",
        "Każdy Tier 9-13 ma osobną nazwę dla każdego rodzaju narzędzia.",
        "tools, tiers oraz bezpośrednie komendy narzędzi pokazują aktualny Tier i następny próg.",
    ],
    "krytyki": [
        "Trafienia krytyczne zależą od efektywnej Zręczności, czyli także od bonusów ekwipunku.",
        "Przy Zręczności 10 bazowa szansa na krytyk wynosi 5 procent.",
        "Każdy punkt Zręczności ponad 10 dodaje 0,5 punktu procentowego szansy.",
        "Zręczność poniżej 10 obniża szansę o 0,5 punktu procentowego za punkt.",
        "Minimalna szansa wynosi 1 procent, maksymalna 35 procent.",
        "Trafienie krytyczne zadaje 150 procent normalnych obrażeń.",
        "Krytyki działają dla zwykłego ataku i ofensywnych umiejętności klasowych.",
        "Mechaniki obronne bossów nadal mogą zredukować albo anulować krytyk.",
        "stats pokazuje aktualną szansę na krytyk i mnożnik.",
    ],
    "respawn": [
        "Zwykłe moby odradzają się po 120 sekundach od śmierci.",
        "Bossowie Krypty i Herszt Bandytów odradzają się po 300 sekundach.",
        "Żywy Manekin treningowy odradza się po 60 sekundach.",
        "Po respawnie boss Krypty ponownie blokuje zejście na następne piętro.",
    ],
    "bossowie": [
        "Bossowie nadal działają w walce turowej: jedna akcja gracza, potem jedna odpowiedź przeciwnika.",
        "Bossowie i zwykłe moby nie są agresywne; nie zaczynają walki sami.",
        "Kościany Egzekutor: co trzeci kontratak używa Kościanego Miażdżenia.",
        "Krwawy Kurator: co trzeci kontratak używa Krwawego Drenażu i leczy się częścią zadanych obrażeń.",
        "Rycerz Grobowca: co trzecie trafienie gracza redukuje Tarczą Grobowca o połowę.",
        "Wiedźma Popiołu: co trzeci kontratak używa Klątwy Popiołu, która omija połowę obrony magicznej.",
        "Pan Katakumb: co czwarty kontratak używa Echa Katakumb.",
        "Widmowy Tytan: naprzemiennie zmienia kontratak fizyczny i magiczny.",
        "Nekromantyczny Kolos: co czwarty kontratak regeneruje 7 procent maksymalnego HP.",
        "Arcyupiór Otchłani: ma 25 procent szansy na eteryczny unik przeciw trafieniu gracza.",
        "Król Kości: poniżej 50 procent HP zadaje 50 procent więcej obrażeń.",
        "Władca Stu Pięter: poniżej połowy HP wchodzi w drugą fazę; co trzeci kontratak używa Załamania Duszy, a co czwarte trafienie gracza osłabia Pieczęcią Stu Pięter.",
        "Strażnik Pękniętej Duszy, piętro 110: co trzeci kontratak używa Rozdarcia Duszy.",
        "Królowa Otchłannej Krypty, piętro 120: co czwarty kontratak używa Drenażu Otchłani i jest celem Próby Tier 4.",
        "Tytan Żelaznych Kości, piętro 130: co trzecie trafienie gracza jest silnie redukowane.",
        "Prorok Czarnego Płomienia, piętro 140: co trzeci kontratak omija połowę obrony magicznej.",
        "Władca Bezdennych Katakumb, piętro 150: co czwarty kontratak używa Bezdennego Echa.",
        "Astralny Żniwiarz, piętro 160: zmienia fizyczną i magiczną fazę.",
        "Kolos Pustki, piętro 170: regeneruje 8 procent HP co czwartą turę.",
        "Cesarz Upiorów, piętro 180: ma Widmowy Unik i jest celem Próby Tier 5.",
        "Strażnik Końca, piętro 190: poniżej połowy HP zadaje 60 procent więcej obrażeń.",
        "Władca Dwustu Pięter, piętro 200: finałowa druga faza, Bariera Końca i Załamanie Wieczności.",
        "Każdy boss Krypty ma własny unikalny relikt. Boss piętra 200 gwarantuje relikt, pozostałe mają 45 procent szansy.",
        "W Obozowisku Bandytów pojawia się Herszt Bandytów. Co trzeci kontratak wykonuje Brutalną Kombinację.",
        "Herszt Bandytów może upuścić unikalny Sygnet Herszta Bandytów.",
        "Król Goblinów pojawia się w Obozie Goblinów i co trzeci kontratak wykonuje Królewską Szarżę.",
        "Alfa Wilków Cienia pojawia się w Głębi Gaju i poniżej połowy HP wpada w Szał Cienia.",
        "Strażnik Ruin pojawia się przy Zrujnowanej Wieży i co czwarty kontratak używa Runicznego Wybuchu.",
        "Kryształowy Władca pojawia się w Kryształowej Komnacie; używa Kryształowego Promienia i Kryształowej Bariery.",
        "Każdy z nowych bossów świata ma własny unikalny przedmiot z 45 procent szansy.",
    ],
    "loot_krypty": [
        "Ekwipunek z Krypty ma 5 rzadkości: Zwykły, Rzadki, Epicki, Legendarny i Mityczny.",
        "Wyższa rzadkość daje większą obronę i mocniejszy losowy affix.",
        "Losowe affixy to: Siła, Zręczność, Kondycja, Inteligencja, Siła Woli, HP albo Mana.",
        "Zwykłe moby częściej dają Zwykły lub Rzadki loot.",
        "Bossowie mają dużo lepszą szansę na Epicki, Legendarny i Mityczny loot.",
        "Każdy element Krypty należy do Zestawu Krypty swojego Tieru 1-20.",
        "Dominujący set to Tier, którego masz założonych najwięcej części; przy remisie wygrywa wyższy Tier.",
        "2 części jednego setu: +10 procent maksymalnego HP i Many.",
        "4 części jednego setu: dodatkowo +10 procent wszystkich zadawanych obrażeń.",
        "6 części jednego setu: dodatkowo +15 procent obrony fizycznej i magicznej.",
        "Komenda equipment pokazuje rarity, affix oraz aktywny bonus setu.",
        "Komenda stats pokazuje statystyki bazowe, statystyki z wyposażeniem oraz bonusy setu.",
        "Stare przedmioty Krypty pozostają działające i liczą się do odpowiedniego setu jako Zwykłe bez affixu.",
    ],
    "portale": [
        "Portal Krypty odblokowuje się po pokonaniu bossa co 10 pięter.",
        "Portale prowadzą co 10 pięter od 10 aż do 200.",
        "Odblokowanie portalu zapisuje się trwale w SQLite.",
        "portal pokazuje wszystkie odblokowane cele.",
        "portal 30 przenosi z Sali Krypty lub Przedsionka Krypty bezpośrednio na piętro 30.",
        "Portal służy tylko do szybkiego powrotu i nie wyłącza bossa.",
        "Jeśli boss na piętrze portalu żyje, nadal blokuje zejście na następne piętro.",
        "Po zabiciu bossa przejście jest otwarte do respawnu; po respawnie boss znowu blokuje.",
        "Portalu nie można używać podczas walki.",
        "Stare komendy checkpoint nadal działają jako alias portalu dla zgodności.",
    ],
    "krypta": [
        "Loot Krypty ma rarity, losowe affixy statystyk i bonusy setowe 2/4/6 części.",
        "Wpisz help loot_krypty, help rarity albo help sety po szczegóły.",
        "Krypta ma 200 realnych pięter połączonych up i down.",
        "Na każdym piętrze znajduje się skalowany przeciwnik.",
        "Moby nie są agresywne i nie rozpoczynają walki same.",
        "Bossowie są co 10 pięter od 10 aż do 200.",
        "Każdy żywy boss zawsze blokuje zejście na następne piętro.",
        "Po zabiciu bossa przejście jest otwarte do czasu jego respawnu.",
        "Po respawnie boss ponownie blokuje przejście.",
        "Pokonanie bossa odblokowuje trwały Portal Krypty do jego piętra.",
        "portal pokazuje odblokowane cele; portal 50 przenosi na piętro 50.",
        "Portal nie omija żywego bossa.",
        "Zwykły mob Krypty daje 100 + piętro*10 Soul XP.",
        "Boss Krypty daje 600 + piętro*20 Soul XP.",
        "Zwykły mob zostawia 1 element ekwipunku na ciele, boss 3.",
        "prowadz krypta 25 prowadzi normalną trasą i zatrzyma się na żywym bossie.",
        "Co 10 pięter zmienia się Tier ekwipunku znajdowanego na ciałach.",
    ],
    "multiclass": [
        "Multiclass jest całkowicie opcjonalny.",
        "Każda postać ma jedną klasę główną i może włączyć maksymalnie dwie dodatkowe klasy, czyli 3 aktywne łącznie.",
        "multiclass pokazuje aktywne klasy i ich Biegłość.",
        "multiclass add <klasa> włącza klasę dodatkową.",
        "multiclass remove <klasa> wyłącza klasę dodatkową. Klasy głównej nie można wyłączyć.",
        "Klasa główna zachowuje swoją Broń Duszy. Jej bonus klasowy także zawsze wzmacnia klasę główną; dodatkowe klasy nie dostają osobnej Broni Duszy.",
        "Dodatkowe klasy aktywują swoje pasywy i dają dostęp do własnych nauczycieli oraz skilli.",
        "Class XP z zabitego moba jest jedną pulą dzieloną równo między wszystkie aktywne klasy.",
        "Każda klasa ma własną Biegłość 1-100 i własny Class XP. To nie jest level postaci.",
        "Wyłączenie klasy nie kasuje jej Biegłości ani wcześniej nauczonych skilli, ale skilli nie można używać, gdy klasa jest nieaktywna.",
        "Jeśli włączysz klasę magiczną jako dodatkową, postać otrzymuje pulę Many i może używać jej magicznych skilli.",
    ],
    "opisy": [
        "Komenda opis bez argumentu opisuje aktualną lokację.",
        "opis <przedmiot> pokazuje działanie, typ i ceny.",
        "opis <NPC> pokazuje rolę, lokację i powiązane zadanie.",
        "NPC-e pomocni, handlowi, zadaniowi i nauczyciele są pokojowi oraz chronieni przed walką.",
        "opis <przeciwnik> pokazuje HP, obrażenia, typ ataku i nagrody.",
        "opis <lokacja> pokazuje strefę, opis, wyjścia i specjalne funkcje.",
        "opis <zadanie>, opis <rasa>, opis <klasa>, opis <statystyka> i opis <waluta> także działają.",
    ],
    "zmiany": [
        "changes, zmiany albo changelog pokazuje pełną historię wszystkich wersji.",
        "Najnowsza wersja jest na górze, starsze wersje są niżej.",
        "Historia jest czytana z CHANGELOG_PL.txt linia po linii dla NVDA.",
    ],
}

QUESTS = {
    "mirella_jewel_iron": {
        "name": "Zlecenie Mirelli I: Żelazne Pierścienie",
        "giver": "Jubilerka Mirella",
        "kind": "collect",
        "track_craft_progress": True,
        "target": "jewel_iron_ring",
        "needed": 2,
        "description": (
            "Wykonaj 2 Żelazne Pierścienie Jubilerskie "
            "i przynieś je Mirelli."
        ),
        "specialist_tool_type": "jewelcrafting",
        "min_tool_level": 1,
        "reward_profession": "Jubilerstwo",
        "reward_profession_xp": 600,
        "reward_tool_type": "jewelcrafting",
        "reward_tool_xp": 500,
        "reward_silver": 120,
        "reward_gold": 0,
        "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "mirella_jewel_silver": {
        "name": "Zlecenie Mirelli II: Srebrny Naszyjnik",
        "giver": "Jubilerka Mirella",
        "kind": "collect",
        "track_craft_progress": True,
        "target": "jewel_silver_necklace",
        "needed": 1,
        "description": "Wykonaj Srebrny Naszyjnik Jubilerski.",
        "specialist_tool_type": "jewelcrafting",
        "min_tool_level": 20,
        "requires_quest": "mirella_jewel_iron",
        "reward_profession": "Jubilerstwo",
        "reward_profession_xp": 900,
        "reward_tool_type": "jewelcrafting",
        "reward_tool_xp": 750,
        "reward_silver": 180,
        "reward_gold": 0,
        "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "mirella_jewel_gold": {
        "name": "Zlecenie Mirelli III: Złoty Pierścień",
        "giver": "Jubilerka Mirella",
        "kind": "collect",
        "track_craft_progress": True,
        "target": "jewel_gold_ring",
        "needed": 1,
        "description": "Wykonaj Złoty Pierścień Jubilerski.",
        "specialist_tool_type": "jewelcrafting",
        "min_tool_level": 40,
        "requires_quest": "mirella_jewel_silver",
        "reward_profession": "Jubilerstwo",
        "reward_profession_xp": 1200,
        "reward_tool_type": "jewelcrafting",
        "reward_tool_xp": 1000,
        "reward_silver": 240,
        "reward_gold": 1,
        "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "mirella_jewel_cobalt": {
        "name": "Zlecenie Mirelli IV: Kobaltowy Naszyjnik",
        "giver": "Jubilerka Mirella",
        "kind": "collect",
        "track_craft_progress": True,
        "target": "jewel_cobalt_necklace",
        "needed": 1,
        "description": "Wykonaj Kobaltowy Naszyjnik Jubilerski.",
        "specialist_tool_type": "jewelcrafting",
        "min_tool_level": 100,
        "requires_quest": "mirella_jewel_gold",
        "reward_profession": "Jubilerstwo",
        "reward_profession_xp": 1800,
        "reward_tool_type": "jewelcrafting",
        "reward_tool_xp": 1700,
        "reward_silver": 350,
        "reward_gold": 1,
        "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "mirella_jewel_runic": {
        "name": "Zlecenie Mirelli V: Runiczny Pierścień",
        "giver": "Jubilerka Mirella",
        "kind": "collect",
        "track_craft_progress": True,
        "target": "jewel_runic_ring",
        "needed": 1,
        "description": "Wykonaj Runiczny Pierścień Jubilerski.",
        "specialist_tool_type": "jewelcrafting",
        "min_tool_level": 120,
        "requires_quest": "mirella_jewel_cobalt",
        "reward_profession": "Jubilerstwo",
        "reward_profession_xp": 2300,
        "reward_tool_type": "jewelcrafting",
        "reward_tool_xp": 2200,
        "reward_silver": 450,
        "reward_gold": 2,
        "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "mirella_jewel_dragonsteel": {
        "name": "Zlecenie Mirelli VI: Naszyjnik Smoczej Stali",
        "giver": "Jubilerka Mirella",
        "kind": "collect",
        "track_craft_progress": True,
        "target": "jewel_dragonsteel_necklace",
        "needed": 1,
        "description": "Wykonaj Naszyjnik Jubilerski Smoczej Stali.",
        "specialist_tool_type": "jewelcrafting",
        "min_tool_level": 140,
        "requires_quest": "mirella_jewel_runic",
        "reward_profession": "Jubilerstwo",
        "reward_profession_xp": 2800,
        "reward_tool_type": "jewelcrafting",
        "reward_tool_xp": 2700,
        "reward_silver": 550,
        "reward_gold": 2,
        "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "mirella_jewel_astral": {
        "name": "Zlecenie Mirelli VII: Astralny Pierścień",
        "giver": "Jubilerka Mirella",
        "kind": "collect",
        "track_craft_progress": True,
        "target": "jewel_astral_ring",
        "needed": 1,
        "description": "Wykonaj Astralny Pierścień Jubilerski.",
        "specialist_tool_type": "jewelcrafting",
        "min_tool_level": 160,
        "requires_quest": "mirella_jewel_dragonsteel",
        "reward_profession": "Jubilerstwo",
        "reward_profession_xp": 3400,
        "reward_tool_type": "jewelcrafting",
        "reward_tool_xp": 3300,
        "reward_silver": 650,
        "reward_gold": 3,
        "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "mirella_jewel_void": {
        "name": "Zlecenie Mirelli VIII: Naszyjnik Pustki",
        "giver": "Jubilerka Mirella",
        "kind": "collect",
        "track_craft_progress": True,
        "target": "jewel_void_necklace",
        "needed": 1,
        "description": "Wykonaj Naszyjnik Jubilerski Pustki.",
        "specialist_tool_type": "jewelcrafting",
        "min_tool_level": 180,
        "requires_quest": "mirella_jewel_astral",
        "reward_profession": "Jubilerstwo",
        "reward_profession_xp": 4100,
        "reward_tool_type": "jewelcrafting",
        "reward_tool_xp": 4000,
        "reward_silver": 800,
        "reward_gold": 4,
        "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "mirella_jewel_eternium": {
        "name": "Zlecenie Mirelli IX: Wieczny Klejnot",
        "giver": "Jubilerka Mirella",
        "kind": "collect",
        "track_craft_progress": True,
        "target": "jewel_eternium_necklace",
        "needed": 1,
        "description": (
            "Wykonaj Naszyjnik Jubilerski Eternium "
            "jako próbę mistrzowskiego Jubilerstwa."
        ),
        "specialist_tool_type": "jewelcrafting",
        "min_tool_level": 200,
        "requires_quest": "mirella_jewel_void",
        "reward_profession": "Jubilerstwo",
        "reward_profession_xp": 5000,
        "reward_tool_type": "jewelcrafting",
        "reward_tool_xp": 5000,
        "reward_silver": 1000,
        "reward_gold": 5,
        "reward_mithril": 1,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "haldor_crafting_order": {
        "name": "Zlecenie Haldora: Żelazne Sztabki",
        "giver": "Mistrz Rzemiosła Haldor",
        "specialist_tool_type": "crafting",
        "min_tool_level": 1,
        "kind": "collect", "target": "iron_ingot", "needed": 3,
        "description": (
            "Wytwórz 3 Żelazne sztabki i przynieś je "
            "Mistrzowi Rzemiosła Haldorowi w Kuźni Dusz."
        ),
        "reward_profession": "Kowalstwo",
        "reward_profession_xp": 600,
        "reward_tool_type": "crafting",
        "reward_tool_xp": 500,
        "reward_silver": 120,
        "reward_gold": 0,
        "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": BLACKSMITH_QUEST_COOLDOWN_SECONDS,
    },
    "haldor_crafting_order_advanced": {
        "name": "Zlecenie Haldora II: Runiczna Straż",
        "giver": "Mistrz Rzemiosła Haldor",
        "kind": "collect", "target": "runic_guard_charm", "needed": 1,
        "description": (
            "Wytwórz Runiczny Talizman Straży i przynieś go "
            "Haldorowi w Kuźni Dusz."
        ),
        "specialist_tool_type": "crafting",
        "min_tool_level": 100,
        "requires_quest": "haldor_crafting_order",
        "reward_profession": "Kowalstwo",
        "reward_profession_xp": 1800,
        "reward_tool_type": "crafting",
        "reward_tool_xp": 1800,
        "reward_silver": 350,
        "reward_gold": 1,
        "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": BLACKSMITH_QUEST_COOLDOWN_SECONDS,
    },
    "haldor_crafting_order_master": {
        "name": "Zlecenie Haldora III: Wieczna Dusza",
        "giver": "Mistrz Rzemiosła Haldor",
        "kind": "collect", "target": "eternal_soul_charm", "needed": 1,
        "description": (
            "Wytwórz Talizman Wiecznej Duszy i przynieś go "
            "Haldorowi jako dowód mistrzostwa Rzemiosła."
        ),
        "specialist_tool_type": "crafting",
        "min_tool_level": 200,
        "requires_quest": "haldor_crafting_order_advanced",
        "reward_profession": "Kowalstwo",
        "reward_profession_xp": 5000,
        "reward_tool_type": "crafting",
        "reward_tool_xp": 5000,
        "reward_silver": 1000,
        "reward_gold": 5,
        "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": BLACKSMITH_QUEST_COOLDOWN_SECONDS,
    },
    "marcel_cooking_order": {
        "name": "Zlecenie Marcela: Pieczone Ryby",
        "giver": "Kucharz Marcel",
        "specialist_tool_type": "cooking",
        "min_tool_level": 1,
        "kind": "collect", "target": "grilled_river_fish", "needed": 3,
        "description": (
            "Przygotuj 3 Pieczone ryby rzeczne i przynieś je "
            "Kucharzowi Marcelowi w Karczmie."
        ),
        "reward_tool_type": "cooking",
        "reward_tool_xp": 450,
        "reward_silver": 100,
        "reward_gold": 0,
        "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "marcel_cooking_order_advanced": {
        "name": "Zlecenie Marcela II: Runiczny Półmisek",
        "giver": "Kucharz Marcel",
        "kind": "collect", "target": "runic_fish_plate", "needed": 1,
        "description": (
            "Przygotuj Runiczny Półmisek Rybny i przynieś go "
            "Kucharzowi Marcelowi."
        ),
        "specialist_tool_type": "cooking",
        "min_tool_level": 100,
        "requires_quest": "marcel_cooking_order",
        "reward_tool_type": "cooking",
        "reward_tool_xp": 1600,
        "reward_silver": 300,
        "reward_gold": 1,
        "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "marcel_cooking_order_master": {
        "name": "Zlecenie Marcela III: Wieczna Uczta",
        "giver": "Kucharz Marcel",
        "kind": "collect", "target": "eternal_ocean_banquet", "needed": 1,
        "description": (
            "Przygotuj Wieczną Ucztę Oceanu i przynieś ją "
            "Marcelowi jako potrawę mistrzowską."
        ),
        "specialist_tool_type": "cooking",
        "min_tool_level": 200,
        "requires_quest": "marcel_cooking_order_advanced",
        "reward_tool_type": "cooking",
        "reward_tool_xp": 4500,
        "reward_silver": 900,
        "reward_gold": 5,
        "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "orin_alchemy_order": {
        "name": "Zlecenie Orina I: Mikstury Many",
        "giver": "Mistrz Alchemii Orin",
        "specialist_tool_type": "alchemy",
        "min_tool_level": 1,
        "kind": "collect",
        "track_craft_progress": True, "target": "mana_potion", "needed": 3,
        "description": (
            "Uwarz 3 Mikstury Many i przynieś je "
            "Mistrzowi Alchemii Orinowi w Chacie Zielarki."
        ),
        "reward_profession": "Alchemia",
        "reward_profession_xp": 600,
        "reward_tool_type": "alchemy",
        "reward_tool_xp": 500,
        "reward_silver": 120,
        "reward_gold": 0,
        "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "orin_alchemy_order_healing": {
        "name": "Zlecenie Orina II: Mikstury Leczenia",
        "giver": "Mistrz Alchemii Orin",
        "kind": "collect",
        "track_craft_progress": True,
        "target": "healing_potion",
        "needed": 4,
        "description": (
            "Uwarz 4 Mikstury Leczenia i przynieś je "
            "Mistrzowi Alchemii Orinowi."
        ),
        "specialist_tool_type": "alchemy",
        "min_tool_level": 5,
        "requires_quest": "orin_alchemy_order",
        "reward_profession": "Alchemia",
        "reward_profession_xp": 900,
        "reward_tool_type": "alchemy",
        "reward_tool_xp": 750,
        "reward_silver": 180,
        "reward_gold": 0,
        "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "orin_alchemy_order_greater_healing": {
        "name": "Zlecenie Orina III: Wielkie Mikstury Leczenia",
        "giver": "Mistrz Alchemii Orin",
        "kind": "collect",
        "track_craft_progress": True,
        "target": "greater_healing_potion",
        "needed": 3,
        "description": (
            "Uwarz 3 Wielkie Mikstury Leczenia i przynieś je Orinowi."
        ),
        "specialist_tool_type": "alchemy",
        "min_tool_level": 40,
        "requires_quest": "orin_alchemy_order_healing",
        "reward_profession": "Alchemia",
        "reward_profession_xp": 1200,
        "reward_tool_type": "alchemy",
        "reward_tool_xp": 1000,
        "reward_silver": 240,
        "reward_gold": 0,
        "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "orin_alchemy_order_greater_mana": {
        "name": "Zlecenie Orina IV: Wielkie Mikstury Many",
        "giver": "Mistrz Alchemii Orin",
        "kind": "collect",
        "track_craft_progress": True,
        "target": "greater_mana_potion",
        "needed": 3,
        "description": (
            "Uwarz 3 Wielkie Mikstury Many i przynieś je Orinowi."
        ),
        "specialist_tool_type": "alchemy",
        "min_tool_level": 60,
        "requires_quest": "orin_alchemy_order_greater_healing",
        "reward_profession": "Alchemia",
        "reward_profession_xp": 1500,
        "reward_tool_type": "alchemy",
        "reward_tool_xp": 1300,
        "reward_silver": 300,
        "reward_gold": 1,
        "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "orin_alchemy_order_vitality": {
        "name": "Zlecenie Orina V: Eliksiry Witalności",
        "giver": "Mistrz Alchemii Orin",
        "kind": "collect",
        "track_craft_progress": True,
        "target": "vitality_elixir",
        "needed": 2,
        "description": (
            "Uwarz 2 Eliksiry Witalności i przynieś je Orinowi."
        ),
        "specialist_tool_type": "alchemy",
        "min_tool_level": 80,
        "requires_quest": "orin_alchemy_order_greater_mana",
        "reward_profession": "Alchemia",
        "reward_profession_xp": 1800,
        "reward_tool_type": "alchemy",
        "reward_tool_xp": 1600,
        "reward_silver": 360,
        "reward_gold": 1,
        "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "orin_alchemy_order_advanced": {
        "name": "Zlecenie Orina VI: Najwyższa Mikstura Leczenia",
        "giver": "Mistrz Alchemii Orin",
        "kind": "collect",
        "track_craft_progress": True, "target": "supreme_healing_potion", "needed": 2,
        "description": (
            "Uwarz 2 Najwyższe Mikstury Leczenia i przynieś je "
            "Mistrzowi Alchemii Orinowi."
        ),
        "specialist_tool_type": "alchemy",
        "min_tool_level": 100,
        "requires_quest": "orin_alchemy_order_vitality",
        "reward_profession": "Alchemia",
        "reward_profession_xp": 1800,
        "reward_tool_type": "alchemy",
        "reward_tool_xp": 1800,
        "reward_silver": 350,
        "reward_gold": 1,
        "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "orin_alchemy_order_supreme_mana": {
        "name": "Zlecenie Orina VII: Najwyższe Mikstury Many",
        "giver": "Mistrz Alchemii Orin",
        "kind": "collect",
        "track_craft_progress": True,
        "target": "supreme_mana_potion",
        "needed": 2,
        "description": (
            "Uwarz 2 Najwyższe Mikstury Many i przynieś je Orinowi."
        ),
        "specialist_tool_type": "alchemy",
        "min_tool_level": 120,
        "requires_quest": "orin_alchemy_order_advanced",
        "reward_profession": "Alchemia",
        "reward_profession_xp": 2300,
        "reward_tool_type": "alchemy",
        "reward_tool_xp": 2200,
        "reward_silver": 450,
        "reward_gold": 2,
        "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "orin_alchemy_order_grand_vitality": {
        "name": "Zlecenie Orina VIII: Wielkie Eliksiry Witalności",
        "giver": "Mistrz Alchemii Orin",
        "kind": "collect",
        "track_craft_progress": True,
        "target": "grand_vitality_elixir",
        "needed": 2,
        "description": (
            "Uwarz 2 Wielkie Eliksiry Witalności i przynieś je Orinowi."
        ),
        "specialist_tool_type": "alchemy",
        "min_tool_level": 140,
        "requires_quest": "orin_alchemy_order_supreme_mana",
        "reward_profession": "Alchemia",
        "reward_profession_xp": 2800,
        "reward_tool_type": "alchemy",
        "reward_tool_xp": 2700,
        "reward_silver": 550,
        "reward_gold": 2,
        "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "orin_alchemy_order_soul_tonic": {
        "name": "Zlecenie Orina IX: Toniki Duszy",
        "giver": "Mistrz Alchemii Orin",
        "kind": "collect",
        "track_craft_progress": True,
        "target": "soul_tonic",
        "needed": 2,
        "description": (
            "Uwarz 2 Toniki Duszy i przynieś je Orinowi."
        ),
        "specialist_tool_type": "alchemy",
        "min_tool_level": 160,
        "requires_quest": "orin_alchemy_order_grand_vitality",
        "reward_profession": "Alchemia",
        "reward_profession_xp": 3400,
        "reward_tool_type": "alchemy",
        "reward_tool_xp": 3300,
        "reward_silver": 650,
        "reward_gold": 3,
        "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "orin_alchemy_order_astral_restoration": {
        "name": "Zlecenie Orina X: Astralne Eliksiry Odnowy",
        "giver": "Mistrz Alchemii Orin",
        "kind": "collect",
        "track_craft_progress": True,
        "target": "astral_restoration_elixir",
        "needed": 1,
        "description": (
            "Uwarz Astralny Eliksir Odnowy i przynieś go Orinowi."
        ),
        "specialist_tool_type": "alchemy",
        "min_tool_level": 180,
        "requires_quest": "orin_alchemy_order_soul_tonic",
        "reward_profession": "Alchemia",
        "reward_profession_xp": 4100,
        "reward_tool_type": "alchemy",
        "reward_tool_xp": 4000,
        "reward_silver": 800,
        "reward_gold": 4,
        "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "orin_alchemy_order_master": {
        "name": "Zlecenie Orina XI: Eliksir Wiecznej Duszy",
        "giver": "Mistrz Alchemii Orin",
        "kind": "collect",
        "track_craft_progress": True, "target": "eternal_soul_elixir", "needed": 1,
        "description": (
            "Uwarz Eliksir Wiecznej Duszy i przynieś go "
            "Orinowi jako próbę mistrzowskiej Alchemii."
        ),
        "specialist_tool_type": "alchemy",
        "min_tool_level": 200,
        "requires_quest": "orin_alchemy_order_astral_restoration",
        "reward_profession": "Alchemia",
        "reward_profession_xp": 5000,
        "reward_tool_type": "alchemy",
        "reward_tool_xp": 5000,
        "reward_silver": 1000,
        "reward_gold": 5,
        "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "fisher_30_fish": {
        "name": "Próba Rybaka",
        "giver": "Rybak Tomas",
        "kind": "collect_category", "target": "fish", "needed": 30,
        "description": "Przynieś Rybakowi Tomasowi 30 dowolnych ryb.",
        "reward_profession": "Wędkarstwo",
        "reward_profession_xp": 1000,
        "reward_tool_type": "fishing",
        "reward_tool_xp": 1000,
        "reward_silver": 50, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "miner_30_ore": {
        "name": "Próba Górnika",
        "giver": "Górnik Toren",
        "kind": "collect_category", "target": "ore", "needed": 30,
        "description": "Przynieś Górnikowi Torenowi 30 dowolnych rud.",
        "reward_profession": "Górnictwo",
        "reward_profession_xp": 1000,
        "reward_tool_type": "mining",
        "reward_tool_xp": 1000,
        "reward_silver": 50, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "lumberjack_30_wood": {
        "name": "Próba Drwala",
        "giver": "Drwal Bran",
        "kind": "collect_category", "target": "wood", "needed": 30,
        "description": "Przynieś Drwalowi Branowi 30 sztuk dowolnego drewna.",
        "reward_profession": "Drwalstwo",
        "reward_profession_xp": 1000,
        "reward_tool_type": "woodcutting",
        "reward_tool_xp": 1000,
        "reward_silver": 50, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "herbalist_30_herbs": {
        "name": "Próba Zielarki",
        "giver": "Zielarka Liora",
        "kind": "collect_category", "target": "herb", "needed": 30,
        "description": "Przynieś Zielarce Liorze 30 dowolnych ziół.",
        "reward_profession": "Zielarstwo",
        "reward_profession_xp": 1000,
        "reward_tool_type": "herbalism",
        "reward_tool_xp": 1000,
        "reward_silver": 50, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
    },
    "soul_tier_2_trial": {
        "name": "Próba Broni Duszy: Tier 2",
        "giver": "Kapłan Elor",
        "kind": "kill", "target": "skeleton", "needed": 5,
        "description": (
            "Pokonaj 5 Szkieletów Strażników, wróć do Kapłana Elora "
            "w Świątyni Odrodzenia i potwierdź gotowość Broni Duszy."
        ),
        "required_soul_level": 25,
        "required_soul_tier": 1,
        "unlocks_soul_tier": 2,
        "reward_silver": 100, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {},
    },
    "soul_tier_3_trial": {
        "name": "Próba Broni Duszy: Tier 3",
        "giver": "Kapłan Elor",
        "kind": "kill", "target": "crypt_wraith", "needed": 3,
        "description": (
            "Pokonaj 3 Upiory Krypty, wróć do Kapłana Elora "
            "w Świątyni Odrodzenia i potwierdź pełnię mocy Broni Duszy."
        ),
        "required_soul_level": 60,
        "required_soul_tier": 2,
        "unlocks_soul_tier": 3,
        "reward_silver": 250, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {},
    },
    "soul_tier_4_trial": {
        "name": "Próba Broni Duszy: Tier 4",
        "giver": "Kapłan Elor",
        "kind": "kill", "target": "crypt_tier4_trial_boss", "needed": 1,
        "description": (
            "Zejdź na piętro 120 Krypty i pokonaj Królową Otchłannej Krypty. "
            "Następnie wróć do Kapłana Elora w Świątyni Odrodzenia."
        ),
        "required_soul_level": 120,
        "required_soul_tier": 3,
        "unlocks_soul_tier": 4,
        "reward_silver": 600, "reward_gold": 2, "reward_mithril": 0,
        "reward_items": {},
    },
    "soul_tier_5_trial": {
        "name": "Próba Broni Duszy: Tier 5",
        "giver": "Kapłan Elor",
        "kind": "kill", "target": "crypt_tier5_trial_boss", "needed": 1,
        "description": (
            "Zejdź na piętro 180 Krypty i pokonaj Cesarza Upiorów. "
            "Następnie wróć do Kapłana Elora i zakończ ostatnią Próbę Broni Duszy."
        ),
        "required_soul_level": 180,
        "required_soul_tier": 4,
        "unlocks_soul_tier": 5,
        "reward_silver": 1200, "reward_gold": 5, "reward_mithril": 0,
        "reward_items": {},
    },
    "temple_rats": {
        "name": "Szczury pod świątynią",
        "giver": "Kapłan Elor",
        "kind": "kill", "target": "temple_rat", "needed": 10,
        "description": "Zejdź do piwnicy Świątyni Odrodzenia i zabij 10 szczurów.",
        "reward_stat_progress": 120,
        "reward_silver": 75, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {"healing_potion": 1},
    },
    "goblin_problem": {
        "name": "Problem goblinów",
        "giver": "Kapitan Arven",
        "kind": "kill", "target": "goblin", "needed": 3,
        "description": "Pokonaj 3 gobliny w ruinach i obozie.",
        "reward_silver": 100, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {"healing_potion": 2},
    },
    "bandit_patrol": {
        "name": "Patrol przeciw bandytom",
        "giver": "Dowódca Roderik",
        "kind": "kill", "target": "bandit", "needed": 10,
        "description": (
            "Pokonaj 10 bandytów w Obozowisku Bandytów i wróć "
            "do Dowódcy Roderika w Wartowni Północnej."
        ),
        "reward_stat_progress": 150,
        "reward_silver": 250, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {"healing_potion": 2},
        "repeatable": True,
        "repeat_cooldown": 60 * 60,
    },
    "shadow_wolves": {
        "name": "Cienie w gaju",
        "giver": "Zielarka Mira",
        "kind": "kill", "target": "shadow_wolf", "needed": 2,
        "description": "Pokonaj 2 Wilki Cienia w Gaju Szeptów.",
        "reward_silver": 120, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {"healing_potion": 1},
    },
    "soul_shards": {
        "name": "Odłamki dla kowala",
        "giver": "Kowal Doran",
        "kind": "collect", "target": "soul_shard", "needed": 3,
        "description": "Przynieś 3 Odłamki Duszy z krypty.",
        "reward_silver": 300, "reward_gold": 0, "reward_mithril": 0,
        "reward_items": {"soul_elixir": 1},
    },
}

MOB_TEMPLATES = {
    "temple_rat": {
        "name": "Szczur Świątynny", "max_hp": 28, "damage": 3, "damage_type": "physical",
        "silver": 6, "gold": 0, "mithril": 0,
        "stat_reward": 8, "soul_reward": 80,
        "drops": {}, "quest_target": "temple_rat",
    },
    "training_dummy": {
        "name": "Żywy Manekin", "max_hp": 45, "damage": 4, "damage_type": "physical",
        "silver": 12, "gold": 0, "mithril": 0, "stat_reward": 18, "soul_reward": 100,
        "drops": {}, "quest_target": None,
        "training_dummy": True,
    },
    "goblin": {
        "name": "Goblin", "max_hp": 60, "damage": 7, "damage_type": "physical",
        "silver": 28, "gold": 0, "mithril": 0, "stat_reward": 30, "soul_reward": 140,
        "drops": {"healing_potion": 0.08}, "quest_target": "goblin",
    },
    "goblin_brute": {
        "name": "Gobliński Osiłek", "max_hp": 85, "damage": 10, "damage_type": "physical",
        "silver": 45, "gold": 1, "mithril": 0, "stat_reward": 38, "soul_reward": 180,
        "drops": {"healing_potion": 0.12}, "quest_target": "goblin",
    },
    "shadow_wolf": {
        "name": "Wilk Cienia", "max_hp": 70, "damage": 9, "damage_type": "physical",
        "silver": 32, "gold": 0, "mithril": 0, "stat_reward": 34, "soul_reward": 160,
        "drops": {"wolf_fang": 0.45}, "quest_target": "shadow_wolf",
    },
    "bandit": {
        "name": "Bandyta", "max_hp": 75, "damage": 9, "damage_type": "physical",
        "silver": 40, "gold": 0, "mithril": 0, "stat_reward": 35, "soul_reward": 170,
        "drops": {"healing_potion": 0.10}, "quest_target": "bandit",
    },
    "bandit_marauder": {
        "name": "Bandycki Maruder", "max_hp": 105, "damage": 12, "damage_type": "physical",
        "silver": 65, "gold": 0, "mithril": 0, "stat_reward": 48, "soul_reward": 220,
        "drops": {"healing_potion": 0.14}, "quest_target": "bandit",
    },
    "bandit_chief": {
        "name": "Herszt Bandytów",
        "max_hp": 320,
        "damage": 24,
        "damage_type": "physical",
        "silver": 420,
        "gold": 0,
        "mithril": 0,
        "stat_reward": 180,
        "class_xp_reward": 2200,
        "soul_reward": 650,
        "drops": {
            "healing_potion": 0.60,
            "bandit_chief_signet": 0.45,
        },
        "quest_target": "bandit",
        "boss_mechanic": "bandit_combo",
        "world_boss": True,
        "corpse_equipment_pool": [
            "iron_helmet", "iron_guard", "iron_gauntlets",
            "iron_leggings", "iron_boots", "lucky_charm"
        ],
        "corpse_equipment_guaranteed": 2,
    },
    "goblin_king": {
        "name": "Król Goblinów",
        "max_hp": 360,
        "damage": 25,
        "damage_type": "physical",
        "silver": 500,
        "gold": 1,
        "mithril": 0,
        "stat_reward": 200,
        "class_xp_reward": 2600,
        "soul_reward": 720,
        "drops": {
            "healing_potion": 0.65,
            "goblin_king_crown": 0.45,
        },
        "quest_target": "goblin",
        "boss_mechanic": "goblin_king",
        "world_boss": True,
        "corpse_equipment_pool": [
            "iron_helmet", "iron_gauntlets", "iron_boots", "lucky_charm"
        ],
        "corpse_equipment_guaranteed": 2,
    },
    "shadow_alpha": {
        "name": "Alfa Wilków Cienia",
        "max_hp": 390,
        "damage": 27,
        "damage_type": "physical",
        "silver": 480,
        "gold": 1,
        "mithril": 0,
        "stat_reward": 215,
        "class_xp_reward": 2900,
        "soul_reward": 780,
        "drops": {
            "wolf_fang": 1.0,
            "shadow_alpha_fang": 0.45,
        },
        "quest_target": "shadow_wolf",
        "boss_mechanic": "shadow_alpha",
        "world_boss": True,
        "corpse_equipment_pool": [
            "leather_vest", "lucky_charm", "iron_boots"
        ],
        "corpse_equipment_guaranteed": 2,
    },
    "ruin_warden": {
        "name": "Strażnik Ruin",
        "max_hp": 430,
        "damage": 29,
        "damage_type": "physical",
        "silver": 550,
        "gold": 2,
        "mithril": 0,
        "stat_reward": 235,
        "class_xp_reward": 3300,
        "soul_reward": 860,
        "drops": {
            "soul_shard": 0.80,
            "ruin_warden_plate": 0.45,
        },
        "quest_target": None,
        "boss_mechanic": "ruin_warden",
        "world_boss": True,
        "corpse_equipment_pool": [
            "iron_helmet", "iron_guard", "iron_gauntlets",
            "iron_leggings", "iron_boots"
        ],
        "corpse_equipment_guaranteed": 2,
    },
    "crystal_lord": {
        "name": "Kryształowy Władca",
        "max_hp": 500,
        "damage": 32,
        "damage_type": "magic",
        "silver": 0,
        "gold": 8,
        "mithril": 1,
        "stat_reward": 270,
        "class_xp_reward": 4000,
        "soul_reward": 1000,
        "drops": {
            "soul_elixir": 0.35,
            "crystal_lord_core": 0.45,
        },
        "quest_target": None,
        "boss_mechanic": "crystal_lord",
        "world_boss": True,
        "corpse_equipment_pool": [
            "iron_guard", "iron_leggings", "forge_charm", "lucky_charm"
        ],
        "corpse_equipment_guaranteed": 2,
    },
    "skeleton": {
        "name": "Szkielet Strażnik", "max_hp": 90, "damage": 11, "damage_type": "physical",
        "silver": 30, "gold": 1, "mithril": 0, "stat_reward": 42, "soul_reward": 240,
        "drops": {"soul_shard": 0.55}, "quest_target": "skeleton",
    },
    "crypt_wraith": {
        "name": "Upiór Krypty", "max_hp": 120, "damage": 14, "damage_type": "magic",
        "silver": 0, "gold": 2, "mithril": 1, "stat_reward": 55, "soul_reward": 280,
        "drops": {"soul_shard": 0.85}, "quest_target": "crypt_wraith",
    },
    "crystal_guardian": {
        "name": "Kryształowy Strażnik", "max_hp": 140, "damage": 15, "damage_type": "magic",
        "silver": 0, "gold": 4, "mithril": 1, "stat_reward": 60, "soul_reward": 320,
        "drops": {"soul_elixir": 0.08}, "quest_target": None,
    },
}

# room_id, template_id
MOB_SPAWNS = [
    ("temple_basement", "temple_rat"),
    ("temple_basement", "temple_rat"),
    ("temple_basement", "temple_rat"),
    ("temple_basement", "temple_rat"),
    ("training", "training_dummy"),
    ("old_road", "bandit"),
    ("bandit_camp", "bandit"),
    ("bandit_camp", "bandit"),
    ("bandit_camp", "bandit"),
    ("bandit_camp", "bandit"),
    ("bandit_camp", "bandit_marauder"),
    ("bandit_camp", "bandit_marauder"),
    ("bandit_camp", "bandit_chief"),
    ("goblin_camp", "goblin_king"),
    ("deep_grove", "shadow_alpha"),
    ("ruined_watchtower", "ruin_warden"),
    ("crystal_chamber", "crystal_lord"),
    ("deep_grove", "shadow_wolf"),
    ("whisper_grove", "shadow_wolf"),
    ("ruined_watchtower", "goblin"),
    ("goblin_camp", "goblin"),
    ("goblin_camp", "goblin_brute"),
    ("crypt_hall", "skeleton"),
    ("crypt_depths", "crypt_wraith"),
    ("crystal_chamber", "crystal_guardian"),
]


CRYPT_MAX_FLOOR = 200
CRYPT_BOSS_FLOORS = tuple(range(10, CRYPT_MAX_FLOOR + 1, 10))
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
    60: "Widmowy Tytan zmienia typ obrażeń między fizycznym i magicznym co turę.",
    70: "Co czwarty kontratak: Nekroregeneracja odnawia 7 procent maksymalnego HP bossa.",
    80: "Arcyupiór ma 25 procent szansy na eteryczny unik przeciw trafieniu gracza.",
    90: "Poniżej połowy HP Król Kości wpada w furię i zadaje 50 procent więcej obrażeń.",
    100: "Poniżej połowy HP Władca Stu Pięter wzmacnia się; co trzeci kontratak używa Załamania Duszy.",
    110: "Co trzeci kontratak: Rozdarcie Duszy, magiczne obrażenia częściowo omijające obronę.",
    120: "Co czwarty kontratak: Drenaż Otchłani, magiczne obrażenia leczące Królową.",
    130: "Co trzecie trafienie gracza rozbija się o Żelazne Kości i zostaje mocno zredukowane.",
    140: "Co trzeci kontratak: Czarny Płomień, silny atak magiczny ignorujący połowę obrony.",
    150: "Co czwarty kontratak: Bezdenne Echo, jedna bardzo silna odpowiedź bossa.",
    160: "Astralny Żniwiarz zmienia typ obrażeń co turę i co piątą turę wzmacnia atak.",
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
    m = re.fullmatch(r"crypt_floor_(\d+)", str(room_id))
    if not m: return None
    floor=int(m.group(1))
    return floor if 1 <= floor <= CRYPT_MAX_FLOOR else None


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
    ITEMS[_item_id] = {
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
    }

ITEMS["bandit_chief_signet"] = {
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
}

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
ITEMS.update(WORLD_BOSS_UNIQUES)

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
    base_ids = [
        item_id
        for item_id, item in list(ITEMS.items())
        if re.fullmatch(r"crypt_t\d+_(?:head|body|hands|legs|feet|charm)", item_id)
    ]

    for base_item_id in base_ids:
        base_item = ITEMS[base_item_id]
        m = re.fullmatch(
            r"crypt_t(\d+)_(head|body|hands|legs|feet|charm)",
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
                ITEMS[variant_id] = {
                    "name": variant_name,
                    "type": "armor",
                    "slot": slot,
                    "defense": defense,
                    "price": None,
                    "desc": (
                        f"Ekwipunek z Krypty. Tier {tier}. "
                        f"Rzadkość: {rarity['name']}. "
                        f"Obrona +{defense}. "
                        f"Bonus: {affix_name} +{amount}. "
                        f"Zestaw Krypty Tier {tier}."
                    ),
                    "rarity": rarity_key,
                    "rarity_name": rarity["name"],
                    "crypt_set_tier": tier,
                    "crypt_base_item": base_item_id,
                    "affix": affix_key,
                    "affix_amount": amount,
                }

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
    match = re.fullmatch(r"astral_floor_(\d+)", str(room_id))
    if not match:
        return None
    floor = int(match.group(1))
    if ASTRAL_MIN_FLOOR <= floor <= ASTRAL_MAX_FLOOR:
        return floor
    return None

for _floor, (_item_id, _name, _defense, _affix, _amount) in ASTRAL_BOSS_RELICS.items():
    ITEMS[_item_id] = {
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
    }

MYTHIC_MIN_FLOOR = 1
MYTHIC_MAX_FLOOR = 200
MYTHIC_CRYPT_MIN_SOUL_LEVEL = 100
MYTHIC_ASTRAL_MIN_SOUL_LEVEL = 100
MYTHIC_BOSS_FLOORS = set(range(10, MYTHIC_MAX_FLOOR + 1, 10))
PROF_DUNGEON_MAX_FLOOR = 20

def mythic_crypt_floor_id(floor):
    return f"mythic_crypt_floor_{int(floor)}"

def mythic_crypt_floor_number(room_id):
    match = re.fullmatch(
        r"mythic_crypt_floor_(\d+)", str(room_id or "")
    )
    if not match:
        return None
    floor = int(match.group(1))
    if MYTHIC_MIN_FLOOR <= floor <= MYTHIC_MAX_FLOOR:
        return floor
    return None

def mythic_astral_floor_id(floor):
    return f"mythic_astral_floor_{int(floor)}"

def mythic_astral_floor_number(room_id):
    match = re.fullmatch(
        r"mythic_astral_floor_(\d+)", str(room_id or "")
    )
    if not match:
        return None
    floor = int(match.group(1))
    if MYTHIC_MIN_FLOOR <= floor <= MYTHIC_MAX_FLOOR:
        return floor
    return None

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
        if raw.isdigit():
            floor = int(raw)
            if 1 <= floor <= PROF_DUNGEON_MAX_FLOOR:
                return dungeon, floor
    return None, None

def profession_dungeon_room_id(dungeon, floor):
    return f"{PROF_DUNGEON_PREFIXES[dungeon]}{int(floor)}"

def profession_dungeon_required_tool_level(floor):
    floor = max(1, min(PROF_DUNGEON_MAX_FLOOR, int(floor)))
    if floor == 1:
        return 1
    return min(200, floor * 10)

def build_astral_tower():
    ROOMS["shrine"]["exits"]["east"] = "astral_gate"
    ROOMS["astral_gate"] = {
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
    }

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
        )
        affix = stat_cycle[(tier_index - 1) % len(stat_cycle)]
        affix_amount = 5 + tier_index // 2
        for slot, label, defense in defs:
            item_id = f"astral_t{tier_index}_{slot}"
            ITEMS[item_id] = {
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
            }

    for floor in range(ASTRAL_MIN_FLOOR, ASTRAL_MAX_FLOOR + 1):
        room_id = astral_floor_id(floor)
        exits = {}
        if floor == ASTRAL_MIN_FLOOR:
            exits["down"] = "astral_gate"
        else:
            exits["down"] = astral_floor_id(floor - 1)
        if floor < ASTRAL_MAX_FLOOR:
            exits["up"] = astral_floor_id(floor + 1)

        if floor in ASTRAL_BOSS_FLOORS and floor < ASTRAL_MAX_FLOOR:
            note = " Strażnik tego poziomu blokuje drogę w górę."
        elif floor == ASTRAL_MAX_FLOOR:
            note = " To szczyt Wieży Astralnej. Czeka tutaj Astralny Suweren."
        else:
            note = ""

        ROOMS[room_id] = {
            "zone": "Wieża Astralna",
            "name": f"Wieża Astralna, poziom {floor}",
            "desc": (
                f"Poziom {floor}. Przez przezroczyste ściany widać gwiazdy, "
                f"mgławice i odległe pasma światła.{note}"
            ),
            "exits": exits,
        }

        tier_index = min(
            11,
            (floor - ASTRAL_MIN_FLOOR) // 10 + 1,
        )
        gear = [
            f"astral_t{tier_index}_{slot}"
            for slot in (
                "head", "body", "hands", "legs", "feet", "charm"
            )
        ]

        regular_id = f"astral_floor_mob_{floor}"
        regular_name = ASTRAL_REGULAR_NAMES[
            (floor - ASTRAL_MIN_FLOOR) % len(ASTRAL_REGULAR_NAMES)
        ]
        relative = floor - ASTRAL_MIN_FLOOR
        MOB_TEMPLATES[regular_id] = {
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
        }
        MOB_SPAWNS.append((room_id, regular_id))

        if floor in ASTRAL_BOSS_FLOORS:
            boss_id = f"astral_boss_{floor}"
            pool = list(gear)
            relic_id = ASTRAL_BOSS_RELICS[floor][0]
            MOB_TEMPLATES[boss_id] = {
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
            }
            MOB_SPAWNS.append((room_id, boss_id))


def build_crypt_200_floors():
    ROOMS["crypt_hall"]["exits"]["down"] = crypt_floor_id(1)
    ROOMS["crypt_hall"]["exits"]["east"] = "crypt_depths"
    ROOMS["crypt_depths"]["exits"] = {"west": "crypt_hall"}

    for tier in range(1, CRYPT_MAX_FLOOR // 10 + 1):
        defs=(
            ("head","Hełm Krypty",1+tier//2),
            ("body","Napierśnik Krypty",2+tier),
            ("hands","Rękawice Krypty",1+tier//3),
            ("legs","Nogawice Krypty",2+tier//2),
            ("feet","Buty Krypty",1+tier//3),
        )
        for slot,label,defense in defs:
            item_id=f"crypt_t{tier}_{slot}"
            ITEMS[item_id]={
                "name":f"{label} Tier {tier}","type":"armor","slot":slot,
                "defense":defense,"price":None,
                "desc":f"Ekwipunek z Krypty. Tier {tier}. Obrona +{defense}.",
            }
        charm=f"crypt_t{tier}_charm"; defense=1+tier//2
        ITEMS[charm]={
            "name":f"Talizman Bossa Krypty Tier {tier}","type":"armor","slot":"charm",
            "defense":defense,"price":None,
            "desc":f"Talizman po bossie Krypty. Tier {tier}. Obrona +{defense}.",
        }

    for floor in range(1, CRYPT_MAX_FLOOR+1):
        room_id=crypt_floor_id(floor); exits={}
        exits["up"]="crypt_hall" if floor==1 else crypt_floor_id(floor-1)
        if floor<CRYPT_MAX_FLOOR: exits["down"]=crypt_floor_id(floor+1)
        if floor in CRYPT_BOSS_FLOORS and floor < CRYPT_MAX_FLOOR:
            note=" Przy zejściu czeka boss blokujący drogę niżej."
        elif floor == CRYPT_MAX_FLOOR:
            note=" To ostatnie piętro. Czeka tutaj finałowy boss Krypty."
        else:
            note=""
        ROOMS[room_id]={
            "zone":f"Krypta 1-{CRYPT_MAX_FLOOR}","name":f"Krypta, piętro {floor}",
            "desc":(
                f"Piętro {floor} z {CRYPT_MAX_FLOOR}. "
                f"Kamienne korytarze stają się coraz bardziej niebezpieczne.{note}"
            ),
            "exits":exits,
        }
        tier=min(CRYPT_MAX_FLOOR // 10,(floor-1)//10+1)
        gear=[f"crypt_t{tier}_{x}" for x in ("head","body","hands","legs","feet")]
        tid=f"crypt_floor_mob_{floor}"
        name=CRYPT_REGULAR_NAMES[(floor-1)%len(CRYPT_REGULAR_NAMES)]
        MOB_TEMPLATES[tid]={
            "name":f"{name}, piętro {floor}",
            "max_hp":70+floor*9,"damage":6+floor//3,
            "damage_type":"magic" if (floor%3==0 or floor%4==0) else "physical",
            "silver":8+floor,"gold":0,"mithril":0,
            "stat_reward":20+floor*2,
            "class_xp_reward":450+floor*60,
            "soul_reward":100+floor*10,
            "drops":{"soul_shard":min(0.30,0.08+floor*0.002)},"quest_target":None,
            "crypt_floor":floor,"corpse_equipment_pool":gear,"corpse_equipment_guaranteed":1,
        }
        MOB_SPAWNS.append((room_id,tid))
        if floor in CRYPT_BOSS_FLOORS:
            bid=f"crypt_boss_{floor}"; pool=gear+[f"crypt_t{tier}_charm"]
            MOB_TEMPLATES[bid]={
                "name":CRYPT_BOSS_NAMES[floor],"max_hp":350+floor*25,
                "damage":16+floor//2,"damage_type":"magic" if floor%20==0 else "physical",
                "silver":300+floor*12,"gold":0,"mithril":0,
                "stat_reward":350+floor*6,
                "class_xp_reward":3000+floor*160,
                "soul_reward":600+floor*20,
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
            }
            MOB_SPAWNS.append((room_id,bid))

def build_mythic_endgame():
    # Mythic Crypt opens from the old Crypt depths after floor 200 completion.
    ROOMS["crypt_depths"]["exits"]["east"] = "mythic_crypt_gate"
    ROOMS["mythic_crypt_gate"] = {
        "zone": "Mityczna Krypta",
        "name": "Brama Mitycznej Krypty",
        "desc": (
            "Czarna brama rezonuje mityczną energią Krypty. "
            "Wejście wymaga Soul Level 100."
        ),
        "exits": {
            "west": "crypt_depths",
            "down": mythic_crypt_floor_id(1),
        },
    }

    # Mythic Astral opens from the ordinary Astral Gate.
    ROOMS["astral_gate"]["exits"]["east"] = "mythic_astral_gate"
    ROOMS["mythic_astral_gate"] = {
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
    }

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
        if floor < MYTHIC_MAX_FLOOR:
            c_exits["down"] = mythic_crypt_floor_id(floor + 1)
        c_note = (
            " Mityczny boss blokuje zejście niżej."
            if floor in MYTHIC_BOSS_FLOORS
            and floor < MYTHIC_MAX_FLOOR
            else (
                " To finał Mitycznej Krypty."
                if floor == MYTHIC_MAX_FLOOR
                else ""
            )
        )
        ROOMS[c_room] = {
            "zone": "Mityczna Krypta",
            "name": f"Mityczna Krypta, piętro {floor}",
            "desc": (
                f"Mityczne piętro {floor} z {MYTHIC_MAX_FLOOR}. "
                f"Ściany są przesycone ciemną energią.{c_note}"
            ),
            "exits": c_exits,
        }

        c_regular = f"mythic_crypt_mob_{floor}"
        MOB_TEMPLATES[c_regular] = {
            "name": (
                f"{crypt_names[(floor - 1) % len(crypt_names)]}, "
                f"piętro {floor}"
            ),
            "max_hp": 4000 + floor * 100,
            "damage": 120 + floor,
            "damage_type": "magic" if floor % 2 else "physical",
            "silver": 800 + floor * 8,
            "gold": 5 + floor // 20,
            "mithril": 0,
            "stat_reward": 800 + floor * 5,
            "class_xp_reward": 20000 + floor * 300,
            "soul_reward": 4000 + floor * 25,
            "drops": {"soul_shard": 0.55},
            "quest_target": None,
            "mythic_crypt_floor": floor,
            "corpse_equipment_pool": [
                f"crypt_t20_{slot}"
                for slot in (
                    "head", "body", "hands", "legs", "feet", "charm"
                )
            ],
            "corpse_equipment_guaranteed": 1,
        }
        MOB_SPAWNS.append((c_room, c_regular))

        if floor in MYTHIC_BOSS_FLOORS:
            c_boss = f"mythic_crypt_boss_{floor}"
            MOB_TEMPLATES[c_boss] = {
                "name": f"Mityczny Władca Krypty, piętro {floor}",
                "max_hp": 100000,
                "damage": 240 + floor * 2,
                "damage_type": "magic" if floor % 20 else "physical",
                "silver": 8000 + floor * 40,
                "gold": 60 + floor // 5,
                "mithril": 1 if floor >= 100 else 0,
                "stat_reward": 3000 + floor * 12,
                "class_xp_reward": 60000 + floor * 700,
                "soul_reward": 9000 + floor * 50,
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
                    f"crypt_t20_{slot}"
                    for slot in (
                        "head", "body", "hands",
                        "legs", "feet", "charm"
                    )
                ],
                "corpse_equipment_guaranteed": 3,
            }
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
            " Mityczny boss blokuje drogę w górę."
            if floor in MYTHIC_BOSS_FLOORS
            and floor < MYTHIC_MAX_FLOOR
            else (
                " To szczyt Mitycznej Wieży Astralnej."
                if floor == MYTHIC_MAX_FLOOR
                else ""
            )
        )
        ROOMS[a_room] = {
            "zone": "Mityczna Wieża Astralna",
            "name": f"Mityczna Wieża Astralna, poziom {floor}",
            "desc": (
                f"Mityczny poziom {floor} z {MYTHIC_MAX_FLOOR}. "
                f"Gwiazdy wydają się nienaturalnie blisko.{a_note}"
            ),
            "exits": a_exits,
        }

        a_regular = f"mythic_astral_mob_{floor}"
        MOB_TEMPLATES[a_regular] = {
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
                for slot in (
                    "head", "body", "hands",
                    "legs", "feet", "charm"
                )
            ],
            "corpse_equipment_guaranteed": 1,
        }
        MOB_SPAWNS.append((a_room, a_regular))

        if floor in MYTHIC_BOSS_FLOORS:
            a_boss = f"mythic_astral_boss_{floor}"
            MOB_TEMPLATES[a_boss] = {
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
                    for slot in (
                        "head", "body", "hands",
                        "legs", "feet", "charm"
                    )
                ],
                "corpse_equipment_guaranteed": 3,
            }
            MOB_SPAWNS.append((a_room, a_boss))


def build_profession_dungeons():
    # 1. Kopalnia Kryształów - mining
    ROOMS["crystal_chamber"]["exits"]["east"] = (
        profession_dungeon_room_id("crystal_mine", 1)
    )
    # 2. Zatopiona Grota - fishing
    ROOMS["sea_pier"]["exits"]["down"] = (
        profession_dungeon_room_id("sunken_grotto", 1)
    )
    # 3. Pradawny Las - woodcutting
    ROOMS["deep_grove"]["exits"]["south"] = (
        profession_dungeon_room_id("ancient_forest", 1)
    )
    # 4. Ogród Alchemika - herbalism
    ROOMS["herbalist_hut"]["exits"]["east"] = (
        profession_dungeon_room_id("alchemy_garden", 1)
    )

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
        ROOMS[rid] = {
            "zone": "Loch Profesyjny - Kopalnia Kryształów",
            "name": f"Kopalnia Kryształów, poziom {floor}",
            "desc": (
                f"Profesyjny poziom górniczy {floor} z 20. "
                f"Zalecany Kilof level {required}. "
                "Im głębiej, tym lepsze rudy i minerały."
            ),
            "exits": exits,
        }
        MINING_ROOMS.add(rid)

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
        ROOMS[rid] = {
            "zone": "Loch Profesyjny - Zatopiona Grota",
            "name": f"Zatopiona Grota, głębokość {floor}",
            "desc": (
                f"Podwodne łowisko {floor} z 20. "
                f"Zalecana Wędka level {required}. "
                "Niższe komory prowadzą do coraz rzadszych ryb."
            ),
            "exits": exits,
        }
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
        ROOMS[rid] = {
            "zone": "Loch Profesyjny - Pradawny Las",
            "name": f"Pradawny Las, ostęp {floor}",
            "desc": (
                f"Pradawny ostęp {floor} z 20. "
                f"Zalecana Piła level {required}. "
                "Głębsze ostępy dają dostęp do rzadszego drewna."
            ),
            "exits": exits,
        }
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
        ROOMS[rid] = {
            "zone": "Loch Profesyjny - Ogród Alchemika",
            "name": f"Ogród Alchemika, sektor {floor}",
            "desc": (
                f"Alchemiczny sektor {floor} z 20. "
                f"Zalecany Sierp level {required}. "
                "Głębsze sektory zawierają coraz rzadsze rośliny."
            ),
            "exits": exits,
        }
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

def build_mountain_region_and_herb_meadows():
    # -----------------------------
    # Wioska Górska i góry
    # -----------------------------
    ROOMS["hill"]["exits"]["east"] = "mountain_pass"

    ROOMS["mountain_pass"] = {
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
    }

    ROOMS["mountain_village"] = {
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
    }

    ROOMS["mountain_guard_house"] = {
        "zone": "Wioska Górska",
        "name": "Dom Straży Górskiej",
        "desc": (
            "Prosty kamienny budynek służy strażnikom wioski. "
            "Na stole leżą mapy szlaków prowadzących do Jaskini Trolli."
        ),
        "exits": {"south": "mountain_village"},
    }

    ROOMS["mountain_inn"] = {
        "zone": "Wioska Górska",
        "name": "Górska Gospoda",
        "desc": (
            "Ciepła gospoda daje schronienie przed górskim wiatrem. "
            "Podróżnicy opowiadają o potężnym Królu Trolli."
        ),
        "exits": {"west": "mountain_village"},
    }

    ROOMS["mountain_troll_trail"] = {
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
    }

    ROOMS["troll_cave_entrance"] = {
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
    }

    ROOMS["troll_cave_1"] = {
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
    }

    ROOMS["troll_cave_2"] = {
        "zone": "Jaskinia Trolli",
        "name": "Jaskinia Trolli - Wilgotny Tunel",
        "desc": (
            "Woda ścieka po ścianach, a ciężkie kroki odbijają się echem."
        ),
        "exits": {
            "west": "troll_cave_1",
            "east": "troll_cave_3",
        },
    }

    ROOMS["troll_cave_3"] = {
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
    }

    ROOMS["troll_king_den"] = {
        "zone": "Jaskinia Trolli",
        "name": "Legowisko Króla Trolli",
        "desc": (
            "Największa komora jaskini. Pośrodku stoi kamienny tron "
            "otoczony stosami kości i zdobytego żelaza."
        ),
        "exits": {"west": "troll_cave_3"},
    }

    # -----------------------------
    # NPC + quest na trolle
    # -----------------------------
    QUESTS["mountain_troll_hunt"] = {
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
    }

    NPCS["mountain_guard_eryk"] = {
        "name": "Strażnik Górski Eryk",
        "room": "mountain_guard_house",
        "dialogue": (
            "Trolle z południowej jaskini coraz częściej schodzą "
            "pod samą wioskę. Potrzebujemy kogoś, kto przerzedzi ich szeregi."
        ),
        "quest": "mountain_troll_hunt",
    }

    # -----------------------------
    # Trolle i boss
    # Wartości bazowe są potem mnożone przez globalne x2 HP.
    # -----------------------------
    ITEMS["troll_king_tusk"] = {
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
    }

    MOB_TEMPLATES["mountain_troll"] = {
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
    }

    MOB_TEMPLATES["troll_brute"] = {
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
    }

    MOB_TEMPLATES["troll_shaman"] = {
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
    }

    MOB_TEMPLATES["troll_king"] = {
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
    }

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
    ROOMS["flower_meadow"]["exits"]["north"] = "herb_meadow_hub"

    ROOMS["herb_meadow_hub"] = {
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
    }

    ROOMS["chamomile_meadow"] = {
        "zone": "Łąki Zielarskie",
        "name": "Łąka Rumianku",
        "desc": "Białe kwiaty rumianku pokrywają niemal całą łąkę.",
        "exits": {
            "south": "herb_meadow_hub",
            "north": "nettle_meadow",
        },
    }
    ROOMS["nettle_meadow"] = {
        "zone": "Łąki Zielarskie",
        "name": "Łąka Pokrzywy",
        "desc": "Gęste kępy pokrzywy rosną między niskimi kamieniami.",
        "exits": {
            "south": "chamomile_meadow",
            "north": "lemon_balm_meadow",
        },
    }
    ROOMS["lemon_balm_meadow"] = {
        "zone": "Łąki Zielarskie",
        "name": "Łąka Melisy",
        "desc": "Powietrze wypełnia łagodny cytrynowy zapach melisy.",
        "exits": {"south": "nettle_meadow"},
    }

    ROOMS["lavender_meadow"] = {
        "zone": "Łąki Zielarskie",
        "name": "Łąka Lawendy",
        "desc": "Fioletowe pasy lawendy ciągną się po łagodnym zboczu.",
        "exits": {
            "west": "herb_meadow_hub",
            "east": "sage_meadow",
        },
    }
    ROOMS["sage_meadow"] = {
        "zone": "Łąki Zielarskie",
        "name": "Łąka Szałwii",
        "desc": "Srebrzystozielone liście szałwii rosną w suchszej części łąk.",
        "exits": {
            "west": "lavender_meadow",
            "east": "valerian_meadow",
        },
    }
    ROOMS["valerian_meadow"] = {
        "zone": "Łąki Zielarskie",
        "name": "Łąka Waleriany",
        "desc": "Wysokie łodygi waleriany rosną w spokojnej kotlinie.",
        "exits": {"west": "sage_meadow"},
    }

    ROOMS["yarrow_meadow"] = {
        "zone": "Łąki Zielarskie",
        "name": "Łąka Krwawnika",
        "desc": "Drobne białe kwiaty krwawnika tworzą szerokie skupiska.",
        "exits": {
            "east": "herb_meadow_hub",
            "west": "ginseng_meadow",
        },
    }
    ROOMS["ginseng_meadow"] = {
        "zone": "Łąki Zielarskie",
        "name": "Łąka Żeń-szenia",
        "desc": "W zacienionych zagłębieniach rośnie dziki żeń-szeń.",
        "exits": {
            "east": "yarrow_meadow",
            "west": "moonflower_meadow",
        },
    }
    ROOMS["moonflower_meadow"] = {
        "zone": "Łąki Zielarskie",
        "name": "Łąka Księżycowego Kwiatu",
        "desc": (
            "Blade kwiaty rosną na chłodnej łące, a ich płatki "
            "lekko połyskują nawet w cieniu."
        ),
        "exits": {"east": "ginseng_meadow"},
    }

    # Istniejąca Łąka Mięty jest także pełną łąką tematyczną.
    ROOMS["mint_meadow"]["zone"] = "Łąki Zielarskie"
    ROOMS["mint_meadow"]["desc"] = (
        "Mięta dominuje na tej łące. Zbieranie tutaj daje Miętę "
        "jako podstawowy plon."
    )

    for room_id in HERB_SPECIFIC_MEADOWS:
        HERBALISM_ROOMS.add(room_id)
        MEADOW_HERBALISM_ROOMS.add(room_id)

    # Prowadzenie do nowej zawartości.
    GUIDE_DESTINATION_ALIASES.update({
        "gory": "mountain_pass",
        "gorska przelecz": "mountain_pass",
        "wioska gorska": "mountain_village",
        "wioska w gorach": "mountain_village",
        "straznik eryk": "mountain_guard_house",
        "eryk": "mountain_guard_house",
        "jaskinia trolli": "troll_cave_entrance",
        "trolle": "troll_cave_entrance",
        "krol trolli": "troll_king_den",
        "lak zielarskich": "herb_meadow_hub",
        "laki zielarskie": "herb_meadow_hub",
        "laka rumianku": "chamomile_meadow",
        "laka pokrzywy": "nettle_meadow",
        "laka melisy": "lemon_balm_meadow",
        "laka lawendy": "lavender_meadow",
        "laka krwawnika": "yarrow_meadow",
        "laka szalwii": "sage_meadow",
        "laka waleriany": "valerian_meadow",
        "laka zen szenia": "ginseng_meadow",
        "laka zenszenia": "ginseng_meadow",
        "laka ksiezycowego kwiatu": "moonflower_meadow",
    })


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
        r"giant_fortress_(\d+)",
        str(room_id),
    )
    if not match:
        return None
    floor = int(match.group(1))
    if 1 <= floor <= GIANT_FORTRESS_MAX_FLOOR:
        return floor
    return None

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
            MOB_TEMPLATES[elite_id] = elite

def resolve_world_spawn_template(template_id):
    resolved = template_id

    if (
        resolved == "mountain_troll"
        and random.random() < 0.18
    ):
        resolved = random.choices(
            RARE_TROLL_VARIANTS,
            weights=(45, 30, 7, 18),
            k=1,
        )[0]

    template = MOB_TEMPLATES.get(resolved, {})
    if (
        template.get("elite_eligible")
        and random.random() < 0.22
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
        "name": "Odzyskaj Skradzione Rudy",
        "giver": "Handlarka Minerałów Dagna",
        "kind": "collect",
        "target": "stolen_mountain_ore",
        "needed": 6,
        "description": (
            "Odzyskaj 6 Skradzionych Skrzyń Rudy "
            "z trolli i przynieś je Dagnie."
        ),
        "specialist_tool_type": "mining",
        "min_tool_level": 1,
        "reward_profession": "Górnictwo",
        "reward_profession_xp": 700,
        "reward_tool_type": "mining",
        "reward_tool_xp": 600,
        "reward_silver": 300,
        "reward_gold": 1,
        "reward_mithril": 0,
        "reward_items": {},
        "repeatable": True,
        "repeat_cooldown": QUEST_REPEAT_COOLDOWN_SECONDS,
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
        "name": "Zlecenie Marcela I: Pieczone Ryby",
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
    mining_chain = ["stolen_mountain_ores"]
    previous = "stolen_mountain_ores"
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
            "Trolle kradną nasze skrzynie, a ja płacę "
            "za konkretne rudy od miedzi aż po Eternium."
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
        (1, "river_carp", 5, "Karp Rzeczny"),
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

    GUIDE_DESTINATION_ALIASES.update({
        "gorska kuznia": "mountain_forge",
        "kowal gorski": "mountain_forge",
        "brok": "mountain_forge",
        "chata lowcy": "hunter_lodge",
        "lowca potworow": "hunter_lodge",
        "ragna": "hunter_lodge",
        "gorski targ mineralow": "mountain_market",
        "dagna": "mountain_market",
        "zielarka alpejska": "alpine_herbalist_hut",
        "ira": "alpine_herbalist_hut",
        "twierdza gigantow": "giant_fortress_gate",
        "brama twierdzy gigantow": "giant_fortress_gate",
    })

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

build_crypt_200_floors()
build_crypt_loot_variants()
build_astral_tower()
build_mythic_endgame()
build_profession_dungeons()
build_mountain_region_and_herb_meadows()
build_mountain_crafting_expansion()
configure_base_mob_corpse_equipment()

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
        template["max_hp"] = floor * 1000
        template["scaled_boss_hp_rule"] = "floor_x_1000"

    for floor in ASTRAL_BOSS_FLOORS:
        template = MOB_TEMPLATES[f"astral_boss_{floor}"]
        template["max_hp"] = floor * 1000
        template["scaled_boss_hp_rule"] = "floor_x_1000"

    for floor in MYTHIC_BOSS_FLOORS:
        crypt_template = MOB_TEMPLATES[
            f"mythic_crypt_boss_{floor}"
        ]
        crypt_template["max_hp"] = 300000 + floor * 5000
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

IAC = 255
DONT = 254
DO = 253
WONT = 252
WILL = 251
SB = 250
SE = 240


TELNET_CHARSET = 42
TELNET_CHARSET_REQUEST = 1
TELNET_CHARSET_ACCEPTED = 2
TELNET_CHARSET_REJECTED = 3

DEFAULT_TEXT_ENCODING = "utf-8"
POLISH_LEGACY_ENCODING = "cp1250"
SUPPORTED_TEXT_ENCODINGS = (
    DEFAULT_TEXT_ENCODING,
    POLISH_LEGACY_ENCODING,
)


def telnet_charset_offer_bytes():
    # RFC 2066: TELNET CHARSET option 42.
    # UTF-8 jest preferowane, Windows-1250 jest fallbackiem.
    return (
        bytes((
            IAC, WILL, TELNET_CHARSET,
            IAC, SB, TELNET_CHARSET,
            TELNET_CHARSET_REQUEST,
            ord(";"),
        ))
        + b"UTF-8;WINDOWS-1250"
        + bytes((IAC, SE))
    )


def strip_telnet_commands(data: bytes) -> bytes:
    out = bytearray()
    i = 0

    while i < len(data):
        byte = data[i]

        if byte != IAC:
            out.append(byte)
            i += 1
            continue

        i += 1
        if i >= len(data):
            break

        command = data[i]
        i += 1

        if command in (DO, DONT, WILL, WONT):
            if i < len(data):
                i += 1
            continue

        if command == SB:
            while i < len(data):
                if (
                    data[i] == IAC
                    and i + 1 < len(data)
                    and data[i + 1] == SE
                ):
                    i += 2
                    break
                i += 1
            continue

        if command == IAC:
            out.append(IAC)

    return bytes(out)


def decode_polish_telnet_text(
    data: bytes,
    preferred_encoding=DEFAULT_TEXT_ENCODING,
) -> str:
    payload = strip_telnet_commands(data)

    preferred = str(
        preferred_encoding or DEFAULT_TEXT_ENCODING
    ).lower()

    attempts = []
    for encoding in (
        preferred,
        DEFAULT_TEXT_ENCODING,
        POLISH_LEGACY_ENCODING,
    ):
        if encoding not in attempts:
            attempts.append(encoding)

    for encoding in attempts:
        try:
            return payload.decode(
                encoding,
                errors="strict",
            )
        except UnicodeDecodeError:
            pass

    # Nie gubimy bajtów po cichu.
    return payload.decode(
        DEFAULT_TEXT_ENCODING,
        errors="replace",
    )


def clean_telnet(
    data: bytes,
    preferred_encoding=DEFAULT_TEXT_ENCODING,
) -> str:
    return decode_polish_telnet_text(
        data,
        preferred_encoding,
    )



def mob_respawn_seconds(template):
    if template.get("respawn_seconds") is not None:
        base_seconds = max(
            1,
            int(template["respawn_seconds"]),
        )
    elif (
        template.get("crypt_boss")
        or template.get("world_boss")
        or template.get("mythic_crypt_boss")
        or template.get("mythic_astral_boss")
        or template.get("giant_fortress_boss")
    ):
        base_seconds = BOSS_RESPAWN_SECONDS
    elif template.get("training_dummy"):
        base_seconds = TRAINING_DUMMY_RESPAWN_SECONDS
    else:
        base_seconds = REGULAR_MOB_RESPAWN_SECONDS

    return max(
        1,
        int(round(
            base_seconds
            * GLOBAL_MOB_RESPAWN_MULTIPLIER
        )),
    )

def safe_name(name: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9_-]{3,20}", name))


def hash_password(password: str, salt: Optional[bytes] = None) -> tuple[str, str]:
    if salt is None:
        salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS)
    return salt.hex(), digest.hex()


def verify_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    salt = bytes.fromhex(salt_hex)
    _, candidate = hash_password(password, salt)
    return hmac.compare_digest(candidate, hash_hex)


def normalize_lookup_text(value):
    text = str(value or "").strip().lower()
    text = text.replace("ł", "l")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        ch for ch in text
        if not unicodedata.combining(ch)
    )
    text = text.replace("_", " ").replace("-", " ")
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return " ".join(text.split())


def find_by_name(mapping, query, name_field="name"):
    q = normalize_lookup_text(query)
    if not q:
        return None
    exact = []
    partial = []
    for key, value in mapping.items():
        key_name = normalize_lookup_text(key)
        name = normalize_lookup_text(value[name_field])
        if q == key_name or q == name:
            exact.append((key, value))
        elif q in name or q in key_name:
            partial.append((key, value))
    if exact:
        return exact[0]
    if len(partial) == 1:
        return partial[0]
    return None


class Database:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.create_schema()
        self.migrate_schema()

    def create_schema(self):
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS characters (
                account_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                name_nom TEXT NOT NULL DEFAULT '',
                name_gen TEXT NOT NULL DEFAULT '',
                name_dat TEXT NOT NULL DEFAULT '',
                name_acc TEXT NOT NULL DEFAULT '',
                name_ins TEXT NOT NULL DEFAULT '',
                name_loc TEXT NOT NULL DEFAULT '',
                name_voc TEXT NOT NULL DEFAULT '',
                race TEXT NOT NULL,
                class_name TEXT NOT NULL,
                class_type TEXT NOT NULL,
                soul_weapon TEXT NOT NULL,
                weapon_base INTEGER NOT NULL,
                strength INTEGER NOT NULL,
                dexterity INTEGER NOT NULL,
                constitution INTEGER NOT NULL,
                intelligence INTEGER NOT NULL,
                willpower INTEGER NOT NULL,
                stat_progress INTEGER NOT NULL DEFAULT 0,
                soul_level INTEGER NOT NULL DEFAULT 1,
                soul_xp INTEGER NOT NULL DEFAULT 0,
                soul_tier INTEGER NOT NULL DEFAULT 1,
                room_id TEXT NOT NULL DEFAULT 'square',
                silver INTEGER NOT NULL DEFAULT 250,
                gold INTEGER NOT NULL DEFAULT 2,
                mithril INTEGER NOT NULL DEFAULT 0,
                charisma INTEGER NOT NULL DEFAULT 0,
                deaths INTEGER NOT NULL DEFAULT 0,
                crypt_checkpoint INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS inventory (
                account_id INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(account_id, item_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS equipment (
                account_id INTEGER NOT NULL,
                slot TEXT NOT NULL,
                item_id TEXT NOT NULL,
                PRIMARY KEY(account_id, slot),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS quests (
                account_id INTEGER NOT NULL,
                quest_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                progress INTEGER NOT NULL DEFAULT 0,
                completed_at INTEGER NOT NULL DEFAULT 0,
                completion_count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(account_id, quest_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS professions (
                account_id INTEGER NOT NULL,
                profession TEXT NOT NULL,
                level INTEGER NOT NULL DEFAULT 1,
                xp INTEGER NOT NULL DEFAULT 0,
                actions INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(account_id, profession),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS tools (
                account_id INTEGER NOT NULL,
                tool_type TEXT NOT NULL,
                level INTEGER NOT NULL DEFAULT 1,
                xp INTEGER NOT NULL DEFAULT 0,
                uses INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(account_id, tool_type),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS profession_storage (
                account_id INTEGER NOT NULL,
                container TEXT NOT NULL,
                item_id TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(account_id, container,item_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS bank_balances (
                account_id INTEGER PRIMARY KEY,
                silver INTEGER NOT NULL DEFAULT 0,
                gold INTEGER NOT NULL DEFAULT 0,
                mithril INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS bank_items (
                account_id INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(account_id,item_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS astral_progress (
                account_id INTEGER PRIMARY KEY,
                checkpoint INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS mine_progress (
                account_id INTEGER PRIMARY KEY,
                max_floor_unlocked INTEGER NOT NULL DEFAULT 1,
                wall_hits INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS class_progress (
                account_id INTEGER NOT NULL,
                class_name TEXT NOT NULL,
                level INTEGER NOT NULL DEFAULT 1,
                xp INTEGER NOT NULL DEFAULT 0,
                active_slot INTEGER,
                PRIMARY KEY(account_id, class_name),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS learned_skills (
                account_id INTEGER NOT NULL,
                skill_id TEXT NOT NULL,
                learned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(account_id, skill_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS skill_progress (
                account_id INTEGER NOT NULL,
                skill_id TEXT NOT NULL,
                level INTEGER NOT NULL DEFAULT 1,
                xp INTEGER NOT NULL DEFAULT 0,
                uses INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY(account_id, skill_id),
                FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
            );
            """
        )
        self.conn.commit()

    def migrate_schema(self):
        cols = {r["name"] for r in self.conn.execute("PRAGMA table_info(characters)")}
        additions = {
            "silver": "INTEGER NOT NULL DEFAULT 30",
            "gold": "INTEGER NOT NULL DEFAULT 2",
            "mithril": "INTEGER NOT NULL DEFAULT 0",
            "charisma": "INTEGER NOT NULL DEFAULT 0",
            "deaths": "INTEGER NOT NULL DEFAULT 0",
            "crypt_checkpoint": "INTEGER NOT NULL DEFAULT 0",
            "name_nom": "TEXT NOT NULL DEFAULT ''",
            "name_gen": "TEXT NOT NULL DEFAULT ''",
            "name_dat": "TEXT NOT NULL DEFAULT ''",
            "name_acc": "TEXT NOT NULL DEFAULT ''",
            "name_ins": "TEXT NOT NULL DEFAULT ''",
            "name_loc": "TEXT NOT NULL DEFAULT ''",
            "name_voc": "TEXT NOT NULL DEFAULT ''",
        }
        for name, decl in additions.items():
            if name not in cols:
                self.conn.execute(f"ALTER TABLE characters ADD COLUMN {name} {decl}")

        # Zgodność ze starymi postaciami: jeśli nie mają jeszcze odmiany,
        # dotychczasowe imię staje się bezpieczną formą we wszystkich przypadkach.
        for column in (
            "name_nom", "name_gen", "name_dat", "name_acc",
            "name_ins", "name_loc", "name_voc",
        ):
            self.conn.execute(
                f"UPDATE characters SET {column}=name "
                f"WHERE {column} IS NULL OR TRIM({column})=''"
            )
        quest_cols = {
            r["name"] for r in self.conn.execute("PRAGMA table_info(quests)")
        }
        quest_additions = {
            "completed_at": "INTEGER NOT NULL DEFAULT 0",
            "completion_count": "INTEGER NOT NULL DEFAULT 0",
        }
        for name, decl in quest_additions.items():
            if name not in quest_cols:
                self.conn.execute(
                    f"ALTER TABLE quests ADD COLUMN {name} {decl}"
                )

        self.conn.commit()

    def account_by_name(self, username):
        return self.conn.execute(
            "SELECT * FROM accounts WHERE username=? COLLATE NOCASE", (username,)
        ).fetchone()

    def create_account(self, username, password):
        salt, digest = hash_password(password)
        cur = self.conn.execute(
            "INSERT INTO accounts(username,password_salt,password_hash) VALUES(?,?,?)",
            (username, salt, digest),
        )
        self.conn.commit()
        return cur.lastrowid

    def character_for_account(self, account_id):
        return self.conn.execute(
            "SELECT * FROM characters WHERE account_id=?", (account_id,)
        ).fetchone()

    def character_name_exists(self, name):
        return self.conn.execute(
            "SELECT 1 FROM characters WHERE name=? COLLATE NOCASE", (name,)
        ).fetchone() is not None

    def create_character(self, account_id, name, race, cls, name_cases):
        rname, _, strength, dexterity, constitution, intelligence, willpower = race
        cname, ctype, soul_weapon, weapon_base = cls
        self.conn.execute(
            """
            INSERT INTO characters(
                account_id,name,
                name_nom,name_gen,name_dat,name_acc,name_ins,name_loc,name_voc,
                race,class_name,class_type,soul_weapon,weapon_base,
                strength,dexterity,constitution,intelligence,willpower,
                stat_progress,soul_level,soul_xp,soul_tier,room_id,silver,gold,mithril,deaths
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,1,0,1,'square',30,2,0,0)
            """,
            (
                account_id, name,
                name_cases["nom"], name_cases["gen"], name_cases["dat"],
                name_cases["acc"], name_cases["ins"], name_cases["loc"],
                name_cases["voc"],
                rname, cname, ctype, soul_weapon, weapon_base,
                strength, dexterity, constitution, intelligence, willpower,
            ),
        )
        self.conn.execute(
            "INSERT OR REPLACE INTO inventory(account_id,item_id,quantity) VALUES(?,?,?)",
            (account_id, "healing_potion", 2),
        )
        self.conn.execute(
            "INSERT OR IGNORE INTO class_progress(account_id,class_name,level,xp,active_slot) "
            "VALUES(?,?,1,0,1)",
            (account_id, cname),
        )
        self.conn.execute(
            "UPDATE class_progress SET active_slot=1 "
            "WHERE account_id=? AND class_name=?",
            (account_id, cname),
        )
        self.conn.commit()

    def save_character(self, c):
        (
            c.silver,
            c.gold,
            c.mithril,
        ) = normalize_currency_values(
            c.silver,
            c.gold,
            c.mithril,
        )

        self.conn.execute(
            """
            UPDATE characters SET
                strength=?, dexterity=?, constitution=?, intelligence=?, willpower=?,
                stat_progress=?, soul_level=?, soul_xp=?, soul_tier=?, room_id=?,
                silver=?, gold=?, mithril=?, charisma=?, deaths=?
            WHERE account_id=?
            """,
            (
                c.strength, c.dexterity, c.constitution, c.intelligence, c.willpower,
                c.stat_progress, c.soul_level, c.soul_xp, c.soul_tier, c.room_id,
                c.silver, c.gold, c.mithril, c.charisma, c.deaths, c.account_id,
            ),
        )
        self.conn.commit()

    def crypt_checkpoint(self, account_id):
        row = self.conn.execute(
            "SELECT crypt_checkpoint FROM characters WHERE account_id=?",
            (account_id,),
        ).fetchone()
        return int(row["crypt_checkpoint"] or 0) if row else 0

    def unlock_crypt_checkpoint(self, account_id, floor):
        floor = int(floor)
        if floor not in CRYPT_BOSS_FLOORS:
            return self.crypt_checkpoint(account_id)

        current = self.crypt_checkpoint(account_id)
        new_value = max(current, floor)
        if new_value != current:
            self.conn.execute(
                "UPDATE characters SET crypt_checkpoint=? "
                "WHERE account_id=?",
                (new_value, account_id),
            )
            self.conn.commit()
        return new_value

    def sync_legacy_crypt_checkpoint(self, account_id, room_id):
        floor = crypt_floor_number(room_id)
        if floor is None:
            return self.crypt_checkpoint(account_id)

        # Stara postać stojąca na piętrze N musiała wcześniej przejść
        # wszystkie bossy poniżej N. Nie zaliczamy bossa bieżącego piętra.
        safe_floor = ((max(1, floor) - 1) // 10) * 10
        if safe_floor >= 10:
            return self.unlock_crypt_checkpoint(account_id, safe_floor)
        return self.crypt_checkpoint(account_id)

    def crypt_portal(self, account_id):
        return self.crypt_checkpoint(account_id)

    def unlock_crypt_portal(self, account_id, floor):
        return self.unlock_crypt_checkpoint(account_id, floor)

    def astral_checkpoint(self, account_id):
        row = self.conn.execute(
            "SELECT checkpoint FROM astral_progress WHERE account_id=?",
            (account_id,),
        ).fetchone()
        return int(row["checkpoint"] or 0) if row else 0

    def unlock_astral_checkpoint(self, account_id, floor):
        floor = int(floor)
        if floor not in ASTRAL_BOSS_FLOORS:
            return self.astral_checkpoint(account_id)

        current = self.astral_checkpoint(account_id)
        new_value = max(current, floor)
        if new_value != current:
            self.conn.execute(
                """
                INSERT INTO astral_progress(account_id,checkpoint)
                VALUES(?,?)
                ON CONFLICT(account_id)
                DO UPDATE SET checkpoint=excluded.checkpoint
                """,
                (account_id, new_value),
            )
            self.conn.commit()
        return new_value

    def astral_portal(self, account_id):
        return self.astral_checkpoint(account_id)

    def unlock_astral_portal(self, account_id, floor):
        return self.unlock_astral_checkpoint(account_id, floor)

    def ensure_mine_progress(self, account_id):
        self.conn.execute(
            """
            INSERT OR IGNORE INTO mine_progress(
                account_id,max_floor_unlocked,wall_hits
            ) VALUES(?,1,0)
            """,
            (account_id,),
        )
        self.conn.commit()

    def mine_progress(self, account_id):
        self.ensure_mine_progress(account_id)
        row = self.conn.execute(
            """
            SELECT max_floor_unlocked,wall_hits
            FROM mine_progress
            WHERE account_id=?
            """,
            (account_id,),
        ).fetchone()
        return {
            "max_floor_unlocked": max(
                MINE_MIN_FLOOR,
                min(MINE_MAX_FLOOR, int(row["max_floor_unlocked"])),
            ),
            "wall_hits": max(0, int(row["wall_hits"])),
        }

    def add_mine_wall_hit(self, account_id, floor):
        floor = int(floor)
        progress = self.mine_progress(account_id)
        highest = progress["max_floor_unlocked"]
        hits = progress["wall_hits"]

        if floor != highest or floor >= MINE_MAX_FLOOR:
            return {
                "max_floor_unlocked": highest,
                "wall_hits": hits,
                "unlocked_floor": None,
            }

        hits += 1
        required_hits = mine_wall_hits_required(floor)
        unlocked_floor = None
        if hits >= required_hits:
            highest = min(MINE_MAX_FLOOR, highest + 1)
            hits = 0
            unlocked_floor = highest

        self.conn.execute(
            """
            UPDATE mine_progress
            SET max_floor_unlocked=?, wall_hits=?
            WHERE account_id=?
            """,
            (highest, hits, account_id),
        )
        self.conn.commit()
        return {
            "max_floor_unlocked": highest,
            "wall_hits": hits,
            "unlocked_floor": unlocked_floor,
        }

    def ensure_bank(self, account_id):
        self.conn.execute(
            "INSERT OR IGNORE INTO bank_balances("
            "account_id,silver,gold,mithril"
            ") VALUES(?,0,0,0)",
            (account_id,),
        )
        self.conn.commit()

    def bank_balance(self, account_id):
        self.ensure_bank(account_id)
        row = self.conn.execute(
            "SELECT silver,gold,mithril FROM bank_balances "
            "WHERE account_id=?",
            (account_id,),
        ).fetchone()

        silver, gold, mithril = normalize_currency_values(
            row["silver"],
            row["gold"],
            row["mithril"],
        )

        if (
            silver != int(row["silver"])
            or gold != int(row["gold"])
            or mithril != int(row["mithril"])
        ):
            self.conn.execute(
                "UPDATE bank_balances "
                "SET silver=?, gold=?, mithril=? "
                "WHERE account_id=?",
                (silver, gold, mithril, account_id),
            )
            self.conn.commit()
            row = self.conn.execute(
                "SELECT silver,gold,mithril FROM bank_balances "
                "WHERE account_id=?",
                (account_id,),
            ).fetchone()

        return row

    def change_bank_currency(self, account_id, currency, amount):
        if currency not in ("silver", "gold", "mithril"):
            raise ValueError("Nieznana waluta bankowa.")

        row = self.bank_balance(account_id)
        values = {
            "silver": int(row["silver"]),
            "gold": int(row["gold"]),
            "mithril": int(row["mithril"]),
        }
        values[currency] += int(amount)

        if values[currency] < 0:
            return False

        silver, gold, mithril = normalize_currency_values(
            values["silver"],
            values["gold"],
            values["mithril"],
        )

        self.conn.execute(
            "UPDATE bank_balances "
            "SET silver=?, gold=?, mithril=? "
            "WHERE account_id=?",
            (silver, gold, mithril, account_id),
        )
        self.conn.commit()
        return True

    def bank_items(self, account_id):
        return self.conn.execute(
            "SELECT item_id,quantity FROM bank_items "
            "WHERE account_id=? AND quantity>0 ORDER BY item_id",
            (account_id,),
        ).fetchall()

    def bank_item_qty(self, account_id, item_id):
        row = self.conn.execute(
            "SELECT quantity FROM bank_items "
            "WHERE account_id=? AND item_id=?",
            (account_id, item_id),
        ).fetchone()
        return int(row["quantity"]) if row else 0

    def add_bank_item(self, account_id, item_id, qty=1):
        qty = max(1, int(qty))
        self.conn.execute(
            """
            INSERT INTO bank_items(account_id,item_id,quantity)
            VALUES(?,?,?)
            ON CONFLICT(account_id,item_id)
            DO UPDATE SET quantity=quantity+excluded.quantity
            """,
            (account_id, item_id, qty),
        )
        self.conn.commit()

    def remove_bank_item(self, account_id, item_id, qty=1):
        qty = max(1, int(qty))
        current = self.bank_item_qty(account_id, item_id)
        if current < qty:
            return False
        new_qty = current - qty
        if new_qty <= 0:
            self.conn.execute(
                "DELETE FROM bank_items "
                "WHERE account_id=? AND item_id=?",
                (account_id, item_id),
            )
        else:
            self.conn.execute(
                "UPDATE bank_items SET quantity=? "
                "WHERE account_id=? AND item_id=?",
                (new_qty, account_id, item_id),
            )
        self.conn.commit()
        return True

    def inventory(self, account_id):
        return self.conn.execute(
            "SELECT item_id,quantity FROM inventory WHERE account_id=? AND quantity>0 ORDER BY item_id",
            (account_id,),
        ).fetchall()

    def item_qty(self, account_id, item_id):
        row = self.conn.execute(
            "SELECT quantity FROM inventory WHERE account_id=? AND item_id=?",
            (account_id, item_id),
        ).fetchone()
        return int(row["quantity"]) if row else 0

    def add_item(self, account_id, item_id, qty=1):
        self.conn.execute(
            """
            INSERT INTO inventory(account_id,item_id,quantity) VALUES(?,?,?)
            ON CONFLICT(account_id,item_id)
            DO UPDATE SET quantity=quantity+excluded.quantity
            """,
            (account_id, item_id, qty),
        )
        self.conn.commit()

    def remove_item(self, account_id, item_id, qty=1):
        current = self.item_qty(account_id, item_id)
        if current < qty:
            return False
        new_qty = current - qty
        if new_qty <= 0:
            self.conn.execute(
                "DELETE FROM inventory WHERE account_id=? AND item_id=?",
                (account_id, item_id),
            )
        else:
            self.conn.execute(
                "UPDATE inventory SET quantity=? WHERE account_id=? AND item_id=?",
                (new_qty, account_id, item_id),
            )
        self.conn.commit()
        return True

    def ensure_class_progress(self, account_id, class_name):
        self.conn.execute(
            "INSERT OR IGNORE INTO class_progress(account_id,class_name,level,xp,active_slot) "
            "VALUES(?,?,1,0,NULL)",
            (account_id, class_name),
        )
        self.conn.commit()

    def ensure_primary_class(self, account_id, class_name):
        self.ensure_class_progress(account_id, class_name)
        self.conn.execute(
            "UPDATE class_progress SET active_slot=NULL "
            "WHERE account_id=? AND active_slot=1 AND class_name<>?",
            (account_id, class_name),
        )
        self.conn.execute(
            "UPDATE class_progress SET active_slot=1 "
            "WHERE account_id=? AND class_name=?",
            (account_id, class_name),
        )
        self.conn.commit()

    def class_progress_row(self, account_id, class_name):
        self.ensure_class_progress(account_id, class_name)
        return self.conn.execute(
            "SELECT class_name,level,xp,active_slot FROM class_progress "
            "WHERE account_id=? AND class_name=?",
            (account_id, class_name),
        ).fetchone()

    def active_class_rows(self, account_id, primary_class):
        self.ensure_primary_class(account_id, primary_class)
        return self.conn.execute(
            "SELECT class_name,level,xp,active_slot FROM class_progress "
            "WHERE account_id=? AND active_slot IS NOT NULL "
            "ORDER BY active_slot",
            (account_id,),
        ).fetchall()

    def active_class_names(self, account_id, primary_class):
        return [
            row["class_name"]
            for row in self.active_class_rows(account_id, primary_class)
        ]

    def activate_secondary_class(self, account_id, primary_class, class_name):
        self.ensure_primary_class(account_id, primary_class)
        rows = self.active_class_rows(account_id, primary_class)
        active_names = [row["class_name"] for row in rows]

        if class_name in active_names:
            return False, "Ta klasa jest już aktywna."
        if len(active_names) >= MULTICLASS_MAX_ACTIVE:
            return False, "Masz już maksymalnie 3 aktywne klasy."

        used_slots = {
            int(row["active_slot"])
            for row in rows
            if row["active_slot"] is not None
        }
        slot = next(
            number for number in range(2, MULTICLASS_MAX_ACTIVE + 1)
            if number not in used_slots
        )

        self.ensure_class_progress(account_id, class_name)
        self.conn.execute(
            "UPDATE class_progress SET active_slot=? "
            "WHERE account_id=? AND class_name=?",
            (slot, account_id, class_name),
        )
        self.conn.commit()
        return True, slot

    def deactivate_secondary_class(self, account_id, primary_class, class_name):
        self.ensure_primary_class(account_id, primary_class)
        if class_name == primary_class:
            return False, "Nie można wyłączyć klasy głównej."

        row = self.conn.execute(
            "SELECT active_slot FROM class_progress "
            "WHERE account_id=? AND class_name=?",
            (account_id, class_name),
        ).fetchone()
        if not row or row["active_slot"] is None:
            return False, "Ta klasa nie jest aktywna."

        self.conn.execute(
            "UPDATE class_progress SET active_slot=NULL "
            "WHERE account_id=? AND class_name=?",
            (account_id, class_name),
        )
        self.conn.commit()
        return True, None

    def add_class_mastery_xp(self, account_id, class_name, amount):
        self.ensure_class_progress(account_id, class_name)
        row = self.class_progress_row(account_id, class_name)
        level = int(row["level"])
        xp = int(row["xp"])
        gain = max(0, int(amount))
        xp += gain
        level_ups = 0

        while level < CLASS_MASTERY_MAX_LEVEL:
            needed = class_mastery_xp_to_next(level)
            if needed <= 0 or xp < needed:
                break
            xp -= needed
            level += 1
            level_ups += 1

        if level >= CLASS_MASTERY_MAX_LEVEL:
            level = CLASS_MASTERY_MAX_LEVEL
            xp = 0

        self.conn.execute(
            "UPDATE class_progress SET level=?,xp=? "
            "WHERE account_id=? AND class_name=?",
            (level, xp, account_id, class_name),
        )
        self.conn.commit()
        return {
            "class_name": class_name,
            "level": level,
            "xp": xp,
            "level_ups": level_ups,
            "next_xp": class_mastery_xp_to_next(level),
            "gain": gain,
        }

    def learned_skill_ids(self, account_id):
        rows = self.conn.execute(
            "SELECT skill_id FROM learned_skills WHERE account_id=? ORDER BY learned_at, skill_id",
            (account_id,),
        ).fetchall()
        return {row["skill_id"] for row in rows}

    def knows_skill(self, account_id, skill_id):
        return self.conn.execute(
            "SELECT 1 FROM learned_skills WHERE account_id=? AND skill_id=?",
            (account_id, skill_id),
        ).fetchone() is not None

    def learn_skill(self, account_id, skill_id):
        before = self.conn.total_changes
        self.conn.execute(
            "INSERT OR IGNORE INTO learned_skills(account_id,skill_id) VALUES(?,?)",
            (account_id, skill_id),
        )
        self.conn.commit()
        learned_now = self.conn.total_changes > before
        self.ensure_skill_progress(account_id, skill_id)
        return learned_now

    def ensure_skill_progress(self, account_id, skill_id):
        self.conn.execute(
            "INSERT OR IGNORE INTO skill_progress(account_id,skill_id,level,xp,uses) VALUES(?,?,1,0,0)",
            (account_id, skill_id),
        )
        self.conn.commit()

    def skill_progress(self, account_id, skill_id):
        self.ensure_skill_progress(account_id, skill_id)
        return self.conn.execute(
            "SELECT level,xp,uses FROM skill_progress WHERE account_id=? AND skill_id=?",
            (account_id, skill_id),
        ).fetchone()

    def add_skill_xp(self, account_id, skill_id, amount):
        self.ensure_skill_progress(account_id, skill_id)
        row = self.skill_progress(account_id, skill_id)
        level = int(row["level"])
        xp = int(row["xp"]) + max(0, int(amount))
        uses = int(row["uses"]) + 1
        level_ups = 0

        while level < SKILL_MAX_LEVEL:
            needed = skill_xp_to_next(level)
            if needed <= 0 or xp < needed:
                break
            xp -= needed
            level += 1
            level_ups += 1

        if level >= SKILL_MAX_LEVEL:
            level = SKILL_MAX_LEVEL
            xp = 0

        self.conn.execute(
            "UPDATE skill_progress SET level=?,xp=?,uses=? WHERE account_id=? AND skill_id=?",
            (level, xp, uses, account_id, skill_id),
        )
        self.conn.commit()
        return {
            "level": level,
            "xp": xp,
            "uses": uses,
            "level_ups": level_ups,
            "next_xp": skill_xp_to_next(level),
        }

    def equipment(self, account_id):
        return self.conn.execute(
            "SELECT slot,item_id FROM equipment WHERE account_id=? ORDER BY slot",
            (account_id,),
        ).fetchall()

    def equipped_item(self, account_id, slot):
        row = self.conn.execute(
            "SELECT item_id FROM equipment WHERE account_id=? AND slot=?",
            (account_id, slot),
        ).fetchone()
        return row["item_id"] if row else None

    def equip(self, account_id, slot, item_id):
        self.conn.execute(
            """
            INSERT INTO equipment(account_id,slot,item_id) VALUES(?,?,?)
            ON CONFLICT(account_id,slot) DO UPDATE SET item_id=excluded.item_id
            """,
            (account_id, slot, item_id),
        )
        self.conn.commit()

    def ensure_profession(self, account_id, profession):
        self.conn.execute(
            "INSERT OR IGNORE INTO professions(account_id,profession,level,xp,actions) VALUES(?,?,1,0,0)",
            (account_id, profession),
        )
        self.conn.commit()

    def profession(self, account_id, profession):
        self.ensure_profession(account_id, profession)
        return self.conn.execute(
            "SELECT * FROM professions WHERE account_id=? AND profession=?",
            (account_id, profession),
        ).fetchone()

    def save_profession(self, account_id, profession, level, xp, actions):
        self.conn.execute(
            "UPDATE professions SET level=?,xp=?,actions=? WHERE account_id=? AND profession=?",
            (level, xp, actions, account_id, profession),
        )
        self.conn.commit()

    def ensure_tool(self, account_id, tool_type):
        self.conn.execute(
            "INSERT OR IGNORE INTO tools(account_id,tool_type,level,xp,uses) VALUES(?,?,1,0,0)",
            (account_id, tool_type),
        )
        self.conn.commit()

    def tool(self, account_id, tool_type):
        self.ensure_tool(account_id, tool_type)
        return self.conn.execute(
            "SELECT * FROM tools WHERE account_id=? AND tool_type=?",
            (account_id, tool_type),
        ).fetchone()

    def save_tool(self, account_id, tool_type, level, xp, uses):
        self.conn.execute(
            "UPDATE tools SET level=?,xp=?,uses=? WHERE account_id=? AND tool_type=?",
            (level, xp, uses, account_id, tool_type),
        )
        self.conn.commit()

    def storage_rows(self, account_id, container):
        return self.conn.execute(
            "SELECT item_id,quantity FROM profession_storage "
            "WHERE account_id=? AND container=? AND quantity>0 ORDER BY item_id",
            (account_id, container),
        ).fetchall()

    def storage_qty(self, account_id, container, item_id):
        row = self.conn.execute(
            "SELECT quantity FROM profession_storage "
            "WHERE account_id=? AND container=? AND item_id=?",
            (account_id, container, item_id),
        ).fetchone()
        return int(row["quantity"]) if row else 0

    def add_storage_item(self, account_id, container, item_id, qty=1):
        self.conn.execute(
            """
            INSERT INTO profession_storage(account_id,container,item_id,quantity)
            VALUES(?,?,?,?)
            ON CONFLICT(account_id,container,item_id)
            DO UPDATE SET quantity=quantity+excluded.quantity
            """,
            (account_id, container, item_id, qty),
        )
        self.conn.commit()

    def remove_storage_item(self, account_id, container, item_id, qty=1):
        current = self.storage_qty(account_id, container, item_id)
        if current < qty:
            return False
        new_qty = current - qty
        if new_qty <= 0:
            self.conn.execute(
                "DELETE FROM profession_storage "
                "WHERE account_id=? AND container=? AND item_id=?",
                (account_id, container, item_id),
            )
        else:
            self.conn.execute(
                "UPDATE profession_storage SET quantity=? "
                "WHERE account_id=? AND container=? AND item_id=?",
                (new_qty, account_id, container, item_id),
            )
        self.conn.commit()
        return True

    def total_items_across_storage_and_inventory(self, account_id, item_ids, container=None):
        total = 0
        for item_id in item_ids:
            total += self.item_qty(account_id, item_id)
            if container:
                total += self.storage_qty(account_id, container, item_id)
        return total

    def consume_items_across_storage_and_inventory(self, account_id, item_ids, needed, container=None):
        remaining = needed

        if container:
            for item_id in sorted(item_ids):
                if remaining <= 0:
                    break
                qty = self.storage_qty(account_id, container, item_id)
                take = min(qty, remaining)
                if take > 0:
                    self.remove_storage_item(account_id, container, item_id, take)
                    remaining -= take

        for item_id in sorted(item_ids):
            if remaining <= 0:
                break
            qty = self.item_qty(account_id, item_id)
            take = min(qty, remaining)
            if take > 0:
                self.remove_item(account_id, item_id, take)
                remaining -= take

        return remaining == 0

    def quest(self, account_id, quest_id):
        return self.conn.execute(
            "SELECT * FROM quests WHERE account_id=? AND quest_id=?",
            (account_id, quest_id),
        ).fetchone()

    def start_quest(self, account_id, quest_id):
        self.conn.execute(
            "INSERT OR IGNORE INTO quests("
            "account_id,quest_id,status,progress,completed_at,completion_count"
            ") VALUES(?,?, 'active',0,0,0)",
            (account_id, quest_id),
        )
        self.conn.commit()

    def restart_quest(self, account_id, quest_id):
        self.conn.execute(
            "UPDATE quests SET status='active',progress=0 "
            "WHERE account_id=? AND quest_id=?",
            (account_id, quest_id),
        )
        self.conn.commit()

    def repeat_quest_seconds_remaining(self, account_id, quest_id, cooldown):
        row = self.quest(account_id, quest_id)
        if not row or row["status"] != "completed":
            return 0
        completed_at = int(row["completed_at"] or 0)
        if completed_at <= 0:
            return 0
        elapsed = max(0, int(time.time()) - completed_at)
        return max(0, int(cooldown) - elapsed)

    def quest_rows(self, account_id):
        return self.conn.execute(
            "SELECT * FROM quests WHERE account_id=? ORDER BY status,quest_id",
            (account_id,),
        ).fetchall()

    def increment_quest(self, account_id, target):
        rows = self.conn.execute(
            "SELECT * FROM quests WHERE account_id=? AND status='active'",
            (account_id,),
        ).fetchall()
        changed = []
        for row in rows:
            q = QUESTS.get(row["quest_id"])
            if not q or q["kind"] != "kill" or q["target"] != target:
                continue
            new_progress = min(q["needed"], row["progress"] + 1)
            self.conn.execute(
                "UPDATE quests SET progress=? WHERE account_id=? AND quest_id=?",
                (new_progress, account_id, row["quest_id"]),
            )
            changed.append((row["quest_id"], new_progress))
        self.conn.commit()
        return changed

    def increment_craft_quest(
        self, account_id, item_id, amount=1
    ):
        amount = max(0, int(amount))
        if amount <= 0:
            return []

        rows = self.conn.execute(
            "SELECT * FROM quests "
            "WHERE account_id=? AND status='active'",
            (account_id,),
        ).fetchall()

        changed = []
        for row in rows:
            quest = QUESTS.get(row["quest_id"])
            if not quest or not quest.get(
                "track_craft_progress"
            ):
                continue

            if quest.get("kind") == "collect":
                if quest.get("target") != item_id:
                    continue
                needed = max(
                    1, int(quest.get("needed", 1))
                )
                old_progress = int(row["progress"])
                new_progress = min(
                    needed,
                    old_progress + amount,
                )
                self.conn.execute(
                    "UPDATE quests SET progress=? "
                    "WHERE account_id=? AND quest_id=?",
                    (
                        new_progress,
                        account_id,
                        row["quest_id"],
                    ),
                )
                changed.append(
                    (
                        row["quest_id"],
                        new_progress,
                        needed,
                    )
                )
                continue

            if quest.get("kind") == "craft_set":
                targets = tuple(
                    quest.get("targets") or ()
                )
                if item_id not in targets:
                    continue

                index = targets.index(item_id)
                old_mask = int(row["progress"])
                new_mask = old_mask | (1 << index)
                if new_mask == old_mask:
                    continue

                self.conn.execute(
                    "UPDATE quests SET progress=? "
                    "WHERE account_id=? AND quest_id=?",
                    (
                        new_mask,
                        account_id,
                        row["quest_id"],
                    ),
                )
                changed.append(
                    (
                        row["quest_id"],
                        int(new_mask).bit_count(),
                        len(targets),
                    )
                )

        self.conn.commit()
        return changed

    def increment_resource_quest(
        self, account_id, item_id, amount=1
    ):
        amount = max(0, int(amount))
        if amount <= 0:
            return []

        rows = self.conn.execute(
            "SELECT * FROM quests "
            "WHERE account_id=? AND status='active'",
            (account_id,),
        ).fetchall()

        changed = []
        for row in rows:
            quest = QUESTS.get(row["quest_id"])
            if (
                not quest
                or quest.get("kind") != "collect_resource"
                or not quest.get("track_resource_progress")
                or quest.get("target") != item_id
            ):
                continue

            needed = max(
                1, int(quest.get("needed", 1))
            )
            old_progress = int(row["progress"])
            new_progress = min(
                needed,
                old_progress + amount,
            )
            self.conn.execute(
                "UPDATE quests SET progress=? "
                "WHERE account_id=? AND quest_id=?",
                (
                    new_progress,
                    account_id,
                    row["quest_id"],
                ),
            )
            changed.append(
                (
                    row["quest_id"],
                    new_progress,
                    needed,
                )
            )

        self.conn.commit()
        return changed

    def complete_quest(self, account_id, quest_id):
        self.conn.execute(
            "UPDATE quests SET status='completed',completed_at=?,"
            "completion_count=completion_count+1 "
            "WHERE account_id=? AND quest_id=?",
            (int(time.time()), account_id, quest_id),
        )
        self.conn.commit()


@dataclass
class Character:
    account_id: int
    name: str
    name_nom: str
    name_gen: str
    name_dat: str
    name_acc: str
    name_ins: str
    name_loc: str
    name_voc: str
    race: str
    class_name: str
    class_type: str
    soul_weapon: str
    weapon_base: int
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    willpower: int
    stat_progress: int
    soul_level: int
    soul_xp: int
    soul_tier: int
    room_id: str
    silver: int
    gold: int
    mithril: int
    charisma: int
    deaths: int

    @classmethod
    def from_row(cls, row):
        return cls(
            account_id=row["account_id"], name=row["name"],
            name_nom=row["name_nom"], name_gen=row["name_gen"],
            name_dat=row["name_dat"], name_acc=row["name_acc"],
            name_ins=row["name_ins"], name_loc=row["name_loc"],
            name_voc=row["name_voc"], race=row["race"],
            class_name=row["class_name"], class_type=row["class_type"],
            soul_weapon=row["soul_weapon"], weapon_base=row["weapon_base"],
            strength=row["strength"], dexterity=row["dexterity"],
            constitution=row["constitution"], intelligence=row["intelligence"],
            willpower=row["willpower"], stat_progress=row["stat_progress"],
            soul_level=row["soul_level"], soul_xp=row["soul_xp"],
            soul_tier=row["soul_tier"], room_id=row["room_id"],
            silver=row["silver"], gold=row["gold"], mithril=row["mithril"],
            charisma=row["charisma"], deaths=row["deaths"],
        )

    def name_case(self, case):
        mapping = {
            "nom": self.name_nom, "mianownik": self.name_nom,
            "gen": self.name_gen, "dopelniacz": self.name_gen, "dopełniacz": self.name_gen,
            "dat": self.name_dat, "celownik": self.name_dat,
            "acc": self.name_acc, "biernik": self.name_acc,
            "ins": self.name_ins, "narzednik": self.name_ins, "narzędnik": self.name_ins,
            "loc": self.name_loc, "miejscownik": self.name_loc,
            "voc": self.name_voc, "wolacz": self.name_voc, "wołacz": self.name_voc,
        }
        return mapping.get(str(case).strip().lower(), self.name_nom or self.name)

    def max_hp(self):
        # Kondycja bezpośrednio zwiększa maksymalne HP.
        base = 40 + self.constitution * 5
        return max(1, int(round(base * self.racial_max_hp_multiplier())))

    def physical_power(self):
        # Siła odpowiada za obrażenia fizyczne.
        return self.strength

    def speed(self):
        # Zręczność odpowiada za szybkość.
        return 10 + self.dexterity * 2

    def dodge_chance(self):
        # Szybkość przekłada się na szansę uniknięcia kontrataku.
        # Bonusy klasy i rasy mogą się łączyć.
        base = max(0.0, (self.speed() - 20) / 300.0)
        return min(
            0.45,
            base + self.class_dodge_bonus() + self.racial_dodge_bonus()
        )

    def active_class_names(self):
        names = list(getattr(self, "_active_classes", []) or [])
        if self.class_name not in names:
            names.insert(0, self.class_name)
        result = []
        for name in names:
            if name not in result:
                result.append(name)
        return result[:MULTICLASS_MAX_ACTIVE]

    def has_active_class(self, class_name):
        return class_name in self.active_class_names()

    def max_mana(self):
        if not any(
            class_type_for_name(name) == "magic"
            for name in self.active_class_names()
        ):
            return 0
        # Multiclass fizyczny może korzystać z Many, jeśli ma aktywną klasę magiczną.
        base = 20 + self.intelligence * 5
        return max(0, int(round(base * self.racial_max_mana_multiplier())))

    def spell_power(self):
        return self.intelligence

    def class_passive_text_for(self, class_name):
        return {
            "Wojownik": "+10 procent obrażeń fizycznych",
            "Berserker": "+12 procent obrażeń fizycznych",
            "Łotrzyk": "+5 punktów procentowych do uniku",
            "Łowca": "+8 procent obrażeń fizycznych",
            "Mnich": "+8 procent mocy klasowego leczenia",
            "Strażnik": "10 procent redukcji wszystkich otrzymywanych obrażeń",
            "Mag": "+10 procent obrażeń magicznych",
            "Nekromanta": "+15 procent leczenia z wysysania życia",
            "Kapłan": "+10 procent mocy klasowego leczenia",
            "Czarownik": "+12 procent obrażeń magicznych",
            "Druid": "+10 procent mocy klasowego leczenia",
            "Psionik": "+10 procent obrony magicznej",
        }.get(class_name, "brak")

    def class_passive_text(self):
        return self.class_passive_text_for(self.class_name)

    def class_physical_damage_multiplier(self):
        multiplier = 1.0
        bonuses = {"Wojownik": 1.10, "Berserker": 1.12, "Łowca": 1.08}
        for name in self.active_class_names():
            multiplier *= bonuses.get(name, 1.0)

        if self.class_name in ("Wojownik", "Berserker", "Łowca"):
            multiplier *= 1.0 + self.soul_weapon_bonus_percent() / 100.0
        return multiplier

    def class_magic_damage_multiplier(self):
        multiplier = 1.0
        bonuses = {"Mag": 1.10, "Czarownik": 1.12}
        for name in self.active_class_names():
            multiplier *= bonuses.get(name, 1.0)

        if self.class_name in ("Mag", "Czarownik"):
            multiplier *= 1.0 + self.soul_weapon_bonus_percent() / 100.0
        return multiplier

    def class_healing_multiplier(self):
        multiplier = 1.0
        bonuses = {"Mnich": 1.08, "Kapłan": 1.10, "Druid": 1.10}
        for name in self.active_class_names():
            multiplier *= bonuses.get(name, 1.0)

        if self.class_name in ("Mnich", "Kapłan", "Druid"):
            multiplier *= 1.0 + self.soul_weapon_bonus_percent() / 100.0
        return multiplier

    def class_drain_healing_multiplier(self):
        multiplier = 1.15 if self.has_active_class("Nekromanta") else 1.0
        if self.class_name == "Nekromanta":
            multiplier *= 1.0 + self.soul_weapon_bonus_percent() / 100.0
        return multiplier

    def class_dodge_bonus(self):
        bonus = 0.05 if self.has_active_class("Łotrzyk") else 0.0
        if self.class_name == "Łotrzyk":
            bonus += self.soul_weapon_dodge_bonus()
        return bonus

    def class_damage_reduction_percent(self):
        percent = 10 if self.has_active_class("Strażnik") else 0
        if self.class_name == "Strażnik":
            percent += self.soul_weapon_guardian_reduction_percent()
        return percent

    def class_magic_defense_multiplier(self):
        multiplier = 1.10 if self.has_active_class("Psionik") else 1.0
        if self.class_name == "Psionik":
            multiplier *= 1.0 + self.soul_weapon_bonus_percent() / 100.0
        return multiplier

    def apply_class_damage_reduction(self, damage):
        damage = max(1, int(damage))
        percent = self.class_damage_reduction_percent()
        if percent <= 0:
            return damage, 0
        reduced = max(1, int(round(damage * (1.0 - percent / 100.0))))
        return reduced, max(0, damage - reduced)

    def racial_passive_text(self):
        return {
            "Człowiek": "+10 procent Postępu Rozwoju statystyk",
            "Ogr": "+12 procent obrażeń fizycznych",
            "Elf": "+5 punktów procentowych do uniku",
            "Krasnolud": "10 procent redukcji wszystkich otrzymywanych obrażeń",
            "Ork": "+10 procent maksymalnego HP",
            "Niziołek": "+3 punkty procentowe szansy na bonusowy połów, rudę lub drewno",
            "Mroczny Elf": "+10 procent obrażeń magicznych",
            "Gnom": "+15 procent maksymalnej Many",
            "Smoczy": "+8 procent wszystkich zadawanych obrażeń",
            "Troll": "12 procent redukcji otrzymywanych obrażeń fizycznych",
            "Diablę": "+10 procent zdobywanego Soul XP",
            "Aasimar": "+12 procent obrony magicznej",
            "Driada": "+15 procent mocy klasowego leczenia",
        }.get(self.race, "brak")

    def racial_stat_progress_multiplier(self):
        return 1.10 if self.race == "Człowiek" else 1.0

    def racial_physical_damage_multiplier(self):
        return 1.12 if self.race == "Ogr" else 1.0

    def racial_dodge_bonus(self):
        return 0.05 if self.race == "Elf" else 0.0

    def racial_max_hp_multiplier(self):
        return 1.10 if self.race == "Ork" else 1.0

    def racial_profession_bonus_chance(self):
        return 0.03 if self.race == "Niziołek" else 0.0

    def racial_magic_damage_multiplier(self):
        return 1.10 if self.race == "Mroczny Elf" else 1.0

    def racial_max_mana_multiplier(self):
        return 1.15 if self.race == "Gnom" else 1.0

    def racial_all_damage_multiplier(self):
        return 1.08 if self.race == "Smoczy" else 1.0

    def racial_physical_damage_reduction_percent(self):
        return 12 if self.race == "Troll" else 0

    def racial_soul_xp_multiplier(self):
        return 1.10 if self.race == "Diablę" else 1.0

    def racial_magic_defense_multiplier(self):
        return 1.12 if self.race == "Aasimar" else 1.0

    def racial_healing_multiplier(self):
        # Driada jest rasą specjalizującą się w leczeniu.
        if self.race == "Driada":
            return 1.15
        return 1.0

    def racial_healing_bonus_percent(self):
        return int(round((self.racial_healing_multiplier() - 1.0) * 100))

    def racial_damage_reduction_percent(self):
        # Krasnolud ma stałą rasową odporność na każde otrzymane trafienie.
        if self.race == "Krasnolud":
            return 10
        return 0

    def apply_racial_damage_reduction(self, damage):
        damage = max(1, int(damage))
        percent = self.racial_damage_reduction_percent()
        if percent <= 0:
            return damage, 0
        reduced = max(1, int(round(damage * (1.0 - percent / 100.0))))
        prevented = max(0, damage - reduced)
        return reduced, prevented

    def magic_defense(self):
        # Siła Woli odpowiada wyłącznie za obronę magiczną.
        base = max(0, self.willpower // 2)
        return max(
            0,
            int(
                round(
                    base
                    * self.class_magic_defense_multiplier()
                    * self.racial_magic_defense_multiplier()
                )
            )
        )

    def shop_discount_percent(self):
        return min(
            CHARISMA_MAX_DISCOUNT,
            max(0, self.charisma // CHARISMA_DISCOUNT_STEP),
        )

    def party_capacity(self):
        # Startowo 8 osób łącznie z liderem.
        # Co 25 Charyzmy lider otrzymuje jedno kolejne miejsce.
        return PARTY_BASE_CAPACITY + max(0, self.charisma // PARTY_CHARISMA_STEP)

    def charisma_to_next_discount(self):
        if self.shop_discount_percent() >= CHARISMA_MAX_DISCOUNT:
            return 0
        next_value = (self.shop_discount_percent() + 1) * CHARISMA_DISCOUNT_STEP
        return max(0, next_value - self.charisma)

    def charisma_to_next_party_slot(self):
        next_value = (
            (max(0, self.charisma) // PARTY_CHARISMA_STEP) + 1
        ) * PARTY_CHARISMA_STEP
        return max(0, next_value - self.charisma)

    def soul_xp_multiplier(self):
        if self.soul_level >= SOUL_MAX_LEVEL:
            return 0
        # Co pełne 10 Soul Leveli wymaganie podwaja się:
        # 1-10 x1, 11-20 x2, 21-30 x4, 31-40 x8 itd.
        completed_ten_level_blocks = max(
            0,
            (self.soul_level - 1) // 10,
        )
        return 2 ** completed_ten_level_blocks

    def soul_xp_to_next(self):
        if self.soul_level >= SOUL_MAX_LEVEL:
            return 0
        base = 180 + (self.soul_level - 1) * 60
        return base * self.soul_xp_multiplier()

    def soul_weapon_bonus_percent(self):
        # Broń Duszy klasy głównej wzmacnia jej specjalizację.
        # Tier 1-5: 5 / 10 / 15 / 20 / 25 procent.
        return {
            1: 5, 2: 10, 3: 15, 4: 20, 5: 25
        }.get(self.soul_tier, 5)

    def soul_weapon_dodge_bonus(self):
        # Unik jest liczony w punktach procentowych i ma globalny cap 45%.
        return {
            1: 0.02, 2: 0.04, 3: 0.06, 4: 0.08, 5: 0.10
        }.get(self.soul_tier, 0.02)

    def soul_weapon_guardian_reduction_percent(self):
        # Redukcja Strażnika rośnie wolniej niż standardowy bonus specjalizacji.
        return {
            1: 3, 2: 6, 3: 9, 4: 12, 5: 15
        }.get(self.soul_tier, 3)

    def soul_weapon_class_bonus_text(self):
        percent = self.soul_weapon_bonus_percent()
        if self.class_name in ("Wojownik", "Berserker", "Łowca"):
            return (
                f"+{percent} procent obrażeń fizycznych z Broni Duszy "
                f"klasy {self.class_name}"
            )
        if self.class_name == "Łotrzyk":
            pp = int(round(self.soul_weapon_dodge_bonus() * 100))
            return f"+{pp} punkty procentowe uniku z Broni Duszy Łotrzyka"
        if self.class_name in ("Mag", "Czarownik"):
            return (
                f"+{percent} procent obrażeń magicznych z Broni Duszy "
                f"klasy {self.class_name}"
            )
        if self.class_name in ("Mnich", "Kapłan", "Druid"):
            return (
                f"+{percent} procent mocy leczenia z Broni Duszy "
                f"klasy {self.class_name}"
            )
        if self.class_name == "Nekromanta":
            return (
                f"+{percent} procent leczenia z wysysania życia "
                "z Broni Duszy Nekromanty"
            )
        if self.class_name == "Strażnik":
            return (
                f"+{self.soul_weapon_guardian_reduction_percent()} procent "
                "redukcji wszystkich obrażeń z Broni Duszy Strażnika"
            )
        if self.class_name == "Psionik":
            return (
                f"+{percent} procent obrony magicznej "
                "z Broni Duszy Psionika"
            )
        return f"+{percent} procent do specjalizacji klasy głównej"

    def soul_power(self):
        tier_bonus = {
            1: 0,
            2: 12,
            3: 30,
            4: 55,
            5: 85,
        }.get(self.soul_tier, 0)
        return self.weapon_base + self.soul_level - 1 + tier_bonus

    def can_unlock(self):
        if self.soul_tier == 1 and self.soul_level >= TIER2_LEVEL:
            return 2
        if self.soul_tier == 2 and self.soul_level >= TIER3_LEVEL:
            return 3
        if self.soul_tier == 3 and self.soul_level >= TIER4_LEVEL:
            return 4
        if self.soul_tier == 4 and self.soul_level >= TIER5_LEVEL:
            return 5
        return None

    def add_stat_progress(self, amount):
        base_amount = max(0, int(amount))
        amount = max(
            0,
            int(round(base_amount * self.racial_stat_progress_multiplier()))
        )
        messages = [f"Postęp rozwoju statystyk +{amount}."]
        if amount > base_amount:
            messages.append(
                f"Bonus rasy {self.race}: +{amount - base_amount} Postępu Rozwoju."
            )
        self.stat_progress += amount
        while self.stat_progress >= STAT_GROWTH_THRESHOLD:
            self.stat_progress -= STAT_GROWTH_THRESHOLD

            # Każda klasa rozwija wszystkie pięć statystyk.
            self.strength += 1
            self.dexterity += 1
            self.constitution += 1
            self.intelligence += 1
            self.willpower += 1

            messages.append(
                "Statystyki wzrosły: Siła +1, Zręczność +1, Kondycja +1, "
                "Inteligencja +1, Siła Woli +1."
            )
        return messages

    def add_soul_xp(self, amount):
        if self.soul_level >= SOUL_MAX_LEVEL:
            return [f"Broń Duszy ma już Soul Level {SOUL_MAX_LEVEL}."]
        base_amount = max(0, int(amount))
        amount = max(
            0,
            int(round(base_amount * self.racial_soul_xp_multiplier()))
        )
        messages = [f"Broń Duszy otrzymuje {amount} Soul XP."]
        if amount > base_amount:
            messages.append(
                f"Bonus rasy {self.race}: +{amount - base_amount} Soul XP."
            )
        self.soul_xp += amount
        while self.soul_level < SOUL_MAX_LEVEL:
            needed = self.soul_xp_to_next()
            if self.soul_xp < needed:
                break
            self.soul_xp -= needed
            self.soul_level += 1
            messages.append(f"Broń Duszy osiąga Soul Level {self.soul_level}.")
            if self.soul_level == TIER2_LEVEL and self.soul_tier == 1:
                messages.append("Osiągnięto Soul Level 25. Idź do Kapłana Elora w Świątyni Odrodzenia po Próbę Broni Duszy na Tier 2.")
            if self.soul_level == TIER3_LEVEL and self.soul_tier == 2:
                messages.append("Osiągnięto Soul Level 60. Idź do Kapłana Elora w Świątyni Odrodzenia po Próbę Broni Duszy na Tier 3.")
            if self.soul_level == TIER4_LEVEL and self.soul_tier == 3:
                messages.append(
                    "Osiągnięto Soul Level 120. Idź do Kapłana Elora "
                    "po Próbę Broni Duszy na Tier 4."
                )
            if self.soul_level == TIER5_LEVEL and self.soul_tier == 4:
                messages.append(
                    "Osiągnięto Soul Level 180. Idź do Kapłana Elora "
                    "po Próbę Broni Duszy na Tier 5."
                )
        if self.soul_level >= SOUL_MAX_LEVEL:
            self.soul_level = SOUL_MAX_LEVEL
            self.soul_xp = 0
            messages.append(f"Osiągnięto maksymalny Soul Level {SOUL_MAX_LEVEL}.")
        return messages


@dataclass
class CorpseState:
    key: str
    room_id: str
    mob_name: str
    items: list
    created_at: float
    expires_at: float


@dataclass
class MobState:
    key: str
    room_id: str
    template_id: str
    hp: int
    alive: bool = True
    respawn_at: float = 0.0
    engaged_by: Optional[str] = None
    combat_turn: int = 0
    player_hits: int = 0


class World:
    def __init__(self):
        self.mobs = {}
        self.corpses = {}
        self.corpse_counter = 0
        counts = {}
        for room_id, template_id in MOB_SPAWNS:
            template_id = resolve_world_spawn_template(
                template_id
            )
            counts[(room_id, template_id)] = counts.get((room_id, template_id), 0) + 1
            n = counts[(room_id, template_id)]
            key = f"{room_id}:{template_id}:{n}"
            self.mobs[key] = MobState(
                key=key, room_id=room_id, template_id=template_id,
                hp=MOB_TEMPLATES[template_id]["max_hp"],
            )

    def refresh(self):
        now = time.time()
        for corpse_key, corpse in list(self.corpses.items()):
            if corpse.expires_at <= now:
                self.corpses.pop(corpse_key, None)
        for mob in self.mobs.values():
            if not mob.alive and mob.respawn_at <= now:
                mob.alive = True
                mob.hp = MOB_TEMPLATES[mob.template_id]["max_hp"]
                mob.engaged_by = None
                mob.combat_turn = 0
                mob.player_hits = 0

    def live_crypt_boss(self, room_id):
        self.refresh()
        for mob in self.mobs.values():
            if mob.alive and mob.room_id == room_id and MOB_TEMPLATES[mob.template_id].get("crypt_boss"):
                return mob
        return None

    def crypt_descent_blocked(self, room_id, direction="down"):
        if direction != "down": return False
        floor=crypt_floor_number(room_id)
        if floor is None or floor not in CRYPT_BOSS_FLOORS: return False
        return self.live_crypt_boss(room_id) is not None

    def live_astral_boss(self, room_id):
        self.refresh()
        for mob in self.mobs.values():
            if (
                mob.alive
                and mob.room_id == room_id
                and MOB_TEMPLATES[mob.template_id].get("astral_boss")
            ):
                return mob
        return None

    def astral_ascent_blocked(self, room_id, direction="up"):
        if direction != "up":
            return False
        floor = astral_floor_number(room_id)
        if floor is None or floor not in ASTRAL_BOSS_FLOORS:
            return False
        return self.live_astral_boss(room_id) is not None

    def live_mythic_crypt_boss(self, room_id):
        self.refresh()
        for mob in self.mobs.values():
            if (
                mob.alive
                and mob.room_id == room_id
                and MOB_TEMPLATES[mob.template_id].get(
                    "mythic_crypt_boss"
                )
            ):
                return mob
        return None

    def mythic_crypt_descent_blocked(
        self, room_id, direction="down"
    ):
        if direction != "down":
            return False
        floor = mythic_crypt_floor_number(room_id)
        if floor is None or floor not in MYTHIC_BOSS_FLOORS:
            return False
        return self.live_mythic_crypt_boss(room_id) is not None

    def live_mythic_astral_boss(self, room_id):
        self.refresh()
        for mob in self.mobs.values():
            if (
                mob.alive
                and mob.room_id == room_id
                and MOB_TEMPLATES[mob.template_id].get(
                    "mythic_astral_boss"
                )
            ):
                return mob
        return None

    def mythic_astral_ascent_blocked(
        self, room_id, direction="up"
    ):
        if direction != "up":
            return False
        floor = mythic_astral_floor_number(room_id)
        if floor is None or floor not in MYTHIC_BOSS_FLOORS:
            return False
        return self.live_mythic_astral_boss(room_id) is not None

    def live_giant_fortress_boss(self, room_id):
        self.refresh()
        for mob in self.mobs.values():
            if (
                mob.alive
                and mob.room_id == room_id
                and MOB_TEMPLATES[
                    mob.template_id
                ].get("giant_fortress_boss")
            ):
                return mob
        return None

    def giant_fortress_ascent_blocked(
        self, room_id, direction="up"
    ):
        if direction != "up":
            return False
        floor = giant_fortress_floor_number(
            room_id
        )
        if (
            floor is None
            or floor not in GIANT_FORTRESS_BOSS_FLOORS
        ):
            return False
        return (
            self.live_giant_fortress_boss(
                room_id
            )
            is not None
        )

    def create_corpse(self, mob):
        template=MOB_TEMPLATES[mob.template_id]
        if template.get("leave_corpse", True) is False: return None
        pool=list(template.get("corpse_equipment_pool",()))
        guaranteed=min(len(pool),max(0,int(template.get("corpse_equipment_guaranteed",0))))
        items=random.sample(pool,guaranteed) if guaranteed else []
        if items:
            is_crypt_boss = bool(
                template.get("crypt_boss")
                or template.get("mythic_crypt_boss")
            )
            items = [
                roll_crypt_loot_item(
                    item_id, is_boss=is_crypt_boss
                )
                for item_id in items
            ]
        self.corpse_counter += 1; now=time.time()
        corpse=CorpseState(
            key=f"corpse:{self.corpse_counter}", room_id=mob.room_id,
            mob_name=template["name"], items=items, created_at=now,
            expires_at=now+CORPSE_LIFETIME_SECONDS,
        )
        self.corpses[corpse.key]=corpse
        return corpse

    def room_corpses(self, room_id):
        self.refresh()
        return [c for c in self.corpses.values() if c.room_id==room_id]

    def find_corpse(self, room_id, query=""):
        corpses=self.room_corpses(room_id); q=str(query).strip().lower()
        for prefix in ("ciało ","cialo ","zwłoki ","zwloki ","body ","corpse "):
            if q.startswith(prefix): q=q[len(prefix):].strip(); break
        if not q: return corpses[0] if len(corpses)==1 else None
        exact=[c for c in corpses if q==c.mob_name.lower()]
        if exact: return exact[0]
        partial=[c for c in corpses if q in c.mob_name.lower()]
        return partial[0] if partial else None

    def room_mobs(self, room_id):
        self.refresh()
        return [m for m in self.mobs.values() if m.room_id == room_id and m.alive]

    def find_mob(self, room_id, query):
        mobs = self.room_mobs(room_id)
        q = query.strip().lower()
        if not q and len(mobs) == 1:
            return mobs[0]
        exact = []
        partial = []
        for mob in mobs:
            name = MOB_TEMPLATES[mob.template_id]["name"].lower()
            if q == name or q == mob.template_id:
                exact.append(mob)
            elif q and (q in name or q in mob.template_id):
                partial.append(mob)
        if exact:
            return exact[0]
        if len(partial) == 1:
            return partial[0]
        return None


class Session:
    def __init__(self, server, reader, writer):
        self.server = server
        self.reader = reader
        self.writer = writer
        self.input_encoding = DEFAULT_TEXT_ENCODING
        self.output_encoding = DEFAULT_TEXT_ENCODING
        self.account_id = None
        self.character = None
        self.closed = False
        self.current_hp = 0
        self.current_mana = 0
        self.combat_mob_key = None
        self.last_profession_action = 0.0
        self.auto_fishing = False
        self.auto_fishing_task = None
        self.auto_mining = False
        self.auto_mining_task = None
        self.auto_woodcutting = False
        self.auto_woodcutting_task = None
        self.auto_herbalism = False
        self.auto_herbalism_task = None
        self.guiding = False
        self.guide_choice_state = None
        self.skill_cooldowns = {}
        self.skill_guard = 0
        self.skill_evade = False
        self.skill_damage_boost = 1.0
        self.resting = False
        self.rest_task = None

    def mine_progress(self):
        return self.server.db.mine_progress(self.account_id)

    def mine_descent_blocked_for_player(self, room_id, direction="down"):
        if direction != "down":
            return False
        floor = mine_floor_number(room_id)
        if floor is None or floor >= MINE_MAX_FLOOR:
            return False
        return (
            floor + 1
            > self.mine_progress()["max_floor_unlocked"]
        )

    async def auto_mine_descend_if_unlocked(self):
        if not self.auto_mining or self.closed:
            return False
        if self.combat_mob_key:
            return False

        current_room = self.character.room_id
        floor = mine_floor_number(current_room)

        if floor is None or floor >= MINE_MAX_FLOOR:
            return False

        target = ROOMS[current_room]["exits"].get("down")
        expected_target = mine_floor_id(floor + 1)

        if target != expected_target:
            return False

        progress = self.mine_progress()
        if progress["max_floor_unlocked"] < floor + 1:
            return False

        if self.mine_descent_blocked_for_player(
            current_room,
            "down",
        ):
            return False

        old = current_room
        await self.server.broadcast_room(
            old,
            f"{self.character.name} odchodzi.",
            exclude=self,
        )

        self.character.room_id = target
        self.server.db.save_character(
            self.character
        )

        await self.server.broadcast_room(
            target,
            f"{self.character.name} przychodzi.",
            exclude=self,
        )

        await self.send(
            f"Ściana w dół jest przebita. "
            f"Auto-kopanie schodzi na poziom {floor + 1}."
        )
        return True

    def nearest_auto_target(self, route):
        best = None
        best_len = None
        for room_id in route:
            path = self.shortest_path(
                self.character.room_id, room_id
            )
            if path is None:
                continue
            if best is None or len(path) < best_len:
                best = room_id
                best_len = len(path)
        return best

    def next_auto_target(self, route):
        current = self.character.room_id
        dungeon, _floor = profession_dungeon_floor(current)
        if dungeon in {
            "sunken_grotto", "ancient_forest", "alchemy_garden"
        }:
            return current
        if current not in route:
            return self.nearest_auto_target(route)
        index = route.index(current)
        return route[(index + 1) % len(route)]

    async def auto_walk_to_target(self, target, label, flag_attr):
        path = self.shortest_path(
            self.character.room_id, target
        )
        if path is None:
            await self.send(
                f"{label}: nie udało się znaleźć drogi."
            )
            return False

        for direction, next_room in path:
            if self.closed or not getattr(self, flag_attr, False):
                return False
            if self.combat_mob_key:
                await self.send(
                    f"{label} zatrzymane: rozpoczęła się walka."
                )
                return False
            if self.mythic_entry_error(next_room):
                return False
            if self.profession_dungeon_access_error(next_room):
                return False
            if self.astral_entry_blocked(next_room):
                return False
            if self.mythic_crypt_descent_blocked_for_player(
                self.character.room_id, direction
            ):
                return False
            if self.mythic_astral_ascent_blocked_for_player(
                self.character.room_id, direction
            ):
                return False
            if self.giant_fortress_ascent_blocked_for_player(
                self.character.room_id, direction
            ):
                return False
            if self.crypt_descent_blocked_for_player(
                self.character.room_id, direction
            ):
                return False
            if self.astral_ascent_blocked_for_player(
                self.character.room_id, direction
            ):
                return False
            if self.mine_descent_blocked_for_player(
                self.character.room_id, direction
            ):
                await self.send(
                    f"{label}: ściana kopalni blokuje zejście."
                )
                return False

            old = self.character.room_id
            await self.server.broadcast_room(
                old,
                f"{self.character.name} odchodzi.",
                exclude=self,
            )
            self.character.room_id = next_room
            self.server.db.save_character(self.character)
            await self.server.broadcast_room(
                next_room,
                f"{self.character.name} przychodzi.",
                exclude=self,
            )
            await self.send(
                f"{label}: {direction} -> "
                f"{ROOMS[next_room]['name']}."
            )
            await asyncio.sleep(0.12)

        return self.character.room_id == target

    async def show_mine_info(self):
        progress = self.mine_progress()
        floor = mine_floor_number(self.character.room_id)
        await self.send("KOPALNIA GŁĘBINOWA")
        await self.send(
            f"Odblokowane poziomy: 1-"
            f"{progress['max_floor_unlocked']} z {MINE_MAX_FLOOR}."
        )
        if floor is not None:
            await self.send(
                f"Aktualny poziom kopalni: {floor}."
            )
            if floor < MINE_MAX_FLOOR:
                if floor == progress["max_floor_unlocked"]:
                    required_hits = mine_wall_hits_required(floor)
                    await self.send(
                        f"Ściana w dół: {progress['wall_hits']} z "
                        f"{required_hits} uderzeń."
                    )
                else:
                    await self.send(
                        "Zejście niżej z tego poziomu jest już przebite."
                    )
            else:
                await self.send(
                    "Jesteś na najgłębszym poziomie 200."
                )
        await self.send(
            "Im głębiej, tym lepsze złoża. "
            "Kilof nadal musi mieć odpowiedni level."
        )
        await self.send(
            "kop on nie chodzi po świecie. "
            "Może zejść tylko o jeden poziom przez wyjście down, "
            "jeśli ściana do następnego poziomu jest już przebita."
        )

    def mythic_entry_error(self, target_room):
        if target_room == "mythic_crypt_gate":
            if self.character.soul_level < MYTHIC_CRYPT_MIN_SOUL_LEVEL:
                return (
                    "Mityczna Krypta jest zablokowana. "
                    f"Wymaga Soul Level {MYTHIC_CRYPT_MIN_SOUL_LEVEL}. "
                    f"Masz Soul Level {self.character.soul_level}."
                )

        if target_room == "mythic_astral_gate":
            if self.character.soul_level < MYTHIC_ASTRAL_MIN_SOUL_LEVEL:
                return (
                    "Mityczna Wieża Astralna jest zablokowana. "
                    f"Wymaga Soul Level {MYTHIC_ASTRAL_MIN_SOUL_LEVEL}. "
                    f"Masz Soul Level {self.character.soul_level}."
                )

        return None

    def profession_dungeon_access_error(self, target_room):
        dungeon, floor = profession_dungeon_floor(target_room)
        if not dungeon:
            return None

        tool_type, item_id, tool_name = PROF_DUNGEON_TOOL[dungeon]
        if self.server.db.item_qty(self.account_id, item_id) <= 0:
            return (
                f"Ten loch profesyjny wymaga narzędzia: {tool_name}."
            )

        tool = self.server.db.tool(self.account_id, tool_type)
        level = int(tool["level"])
        required = profession_dungeon_required_tool_level(floor)
        if level < required:
            return (
                f"Ten poziom lochu profesyjnego wymaga "
                f"{tool_name} level {required}. Masz level {level}."
            )
        return None

    def giant_fortress_ascent_blocked_for_player(
        self, room_id, direction="up"
    ):
        return (
            self.server.world.giant_fortress_ascent_blocked(
                room_id, direction
            )
        )

    def mythic_crypt_descent_blocked_for_player(
        self, room_id, direction="down"
    ):
        return self.server.world.mythic_crypt_descent_blocked(
            room_id, direction
        )

    def mythic_astral_ascent_blocked_for_player(
        self, room_id, direction="up"
    ):
        return self.server.world.mythic_astral_ascent_blocked(
            room_id, direction
        )

    def crypt_portal(self):
        return self.server.db.crypt_portal(self.account_id)

    def crypt_portal_floors(self):
        highest = self.crypt_portal()
        return [
            floor for floor in CRYPT_BOSS_FLOORS
            if floor <= highest
        ]

    def crypt_descent_blocked_for_player(self, room_id, direction="down"):
        # Żywy boss zawsze blokuje zejście.
        # Portal tylko skraca podróż i nie zmienia tej zasady.
        return self.server.world.crypt_descent_blocked(
            room_id, direction
        )

    def astral_portal(self):
        return self.server.db.astral_portal(self.account_id)

    def astral_portal_floors(self):
        highest = self.astral_portal()
        return [
            floor for floor in ASTRAL_BOSS_FLOORS
            if floor <= highest
        ]

    def astral_ascent_blocked_for_player(self, room_id, direction="up"):
        return self.server.world.astral_ascent_blocked(
            room_id, direction
        )

    def astral_entry_blocked(self, target_room):
        return (
            target_room == astral_floor_id(ASTRAL_MIN_FLOOR)
            and self.character.soul_level < ASTRAL_MIN_SOUL_LEVEL
        )

    async def grant_soul_xp(self, amount):
        old_level = self.character.soul_level

        messages = self.character.add_soul_xp(amount)
        for message in messages:
            await self.send(message)

        if self.character.soul_level > old_level:
            self.current_hp = self.max_hp()
            await self.send(
                f"Awans Soul Level odnawia całe HP. "
                f"HP: {self.current_hp} z {self.max_hp()}."
            )

        return self.character.soul_level > old_level

    async def show_astral_portal_status(self):
        if self.character.soul_level < ASTRAL_MIN_SOUL_LEVEL:
            await self.send(
                f"Wieża Astralna wymaga Soul Level {ASTRAL_MIN_SOUL_LEVEL}. "
                f"Masz Soul Level {self.character.soul_level}."
            )
            return

        highest = self.astral_portal()
        unlocked = self.astral_portal_floors()
        if not highest:
            await self.send(
                "Astralny Portal nie ma jeszcze odblokowanych checkpointów. "
                "Pokonaj Strażnika Gwiezdnej Bramy na poziomie 100."
            )
            return

        await self.send(
            f"Najwyższy checkpoint Wieży Astralnej: poziom {highest}."
        )
        await self.send(
            "Odblokowane Astralne Portale: "
            + ", ".join(str(floor) for floor in unlocked)
            + "."
        )
        await self.send(
            f"Użycie: astralportal <100/110/.../{ASTRAL_MAX_FLOOR}>. "
            "Portal uruchamia się przy Astralnej Bramie."
        )

    async def use_astral_portal(self, raw):
        if self.combat_mob_key:
            await self.send(
                "Nie możesz użyć Astralnego Portalu podczas walki."
            )
            return

        if self.character.soul_level < ASTRAL_MIN_SOUL_LEVEL:
            await self.send(
                f"Wieża Astralna wymaga Soul Level {ASTRAL_MIN_SOUL_LEVEL}. "
                f"Masz {self.character.soul_level}."
            )
            return

        value = self.normalize_room_query(raw)
        if not value or value in ("status", "lista", "list"):
            await self.show_astral_portal_status()
            return

        match = re.search(r"(\d+)", value)
        if not match:
            await self.send(
                f"Użycie: astralportal 100, 110, ... {ASTRAL_MAX_FLOOR}."
            )
            return

        floor = int(match.group(1))
        if floor not in ASTRAL_BOSS_FLOORS:
            await self.send(
                f"Checkpointy Wieży są co 10 poziomów od "
                f"{ASTRAL_MIN_FLOOR} do {ASTRAL_MAX_FLOOR}."
            )
            return

        highest = self.astral_portal()
        if floor > highest:
            await self.send(
                f"Checkpoint poziomu {floor} jest zablokowany. "
                f"Najwyższy odblokowany: {highest if highest else 'brak'}."
            )
            return

        if self.character.room_id != "astral_gate":
            await self.send(
                "Astralny Portal działa tylko przy Astralnej Bramie. "
                "Wpisz prowadz wieza astralna."
            )
            return

        target = astral_floor_id(floor)
        old = self.character.room_id
        await self.server.broadcast_room(
            old,
            f"{self.character.name} wchodzi w Astralny Portal.",
            exclude=self,
        )
        self.character.room_id = target
        self.server.db.save_character(self.character)
        await self.server.broadcast_room(
            target,
            f"{self.character.name} wychodzi z Astralnego Portalu.",
            exclude=self,
        )
        await self.send(
            f"Astralny Portal przenosi cię na poziom {floor}."
        )
        await self.look()

    async def show_portal_status(self):
        highest = self.crypt_portal()
        unlocked = self.crypt_portal_floors()
        if not unlocked:
            await self.send(
                "Portale Krypty: brak. "
                "Pokonaj bossa piętra 10, aby odblokować pierwszy portal."
            )
            return

        await self.send(
            f"Najwyższy odblokowany Portal Krypty: piętro {highest}."
        )
        await self.send(
            "Odblokowane Portale Krypty: "
            + ", ".join(str(floor) for floor in unlocked)
            + "."
        )
        await self.send(
            f"Użycie: portal <10/20/.../{CRYPT_MAX_FLOOR}>. "
            "Portal można uruchomić w Sali Krypty albo w Przedsionku Krypty."
        )

    async def use_crypt_portal(self, raw):
        if self.combat_mob_key:
            await self.send(
                "Nie możesz użyć Portalu Krypty podczas walki."
            )
            return

        value = self.normalize_room_query(raw)
        if not value or value in ("status", "lista", "list"):
            await self.show_portal_status()
            return

        match = re.search(r"(\d+)", value)
        if not match:
            await self.send(
                f"Użycie: portal 10, portal 20, ... portal {CRYPT_MAX_FLOOR}."
            )
            return

        floor = int(match.group(1))
        if floor not in CRYPT_BOSS_FLOORS:
            await self.send(
                f"Portale są co 10 pięter: 10, 20, ... "
                f"{CRYPT_MAX_FLOOR}."
            )
            return

        highest = self.crypt_portal()
        if floor > highest:
            await self.send(
                f"Portal piętra {floor} jest jeszcze zablokowany. "
                f"Najwyższy odblokowany portal: "
                f"{highest if highest else 'brak'}."
            )
            return

        if self.character.room_id not in ("crypt_hall", "crypt_entrance"):
            await self.send(
                "Portal Krypty można uruchomić tylko w Sali Krypty "
                "albo w Przedsionku Krypty. Użyj prowadz Sala Krypty."
            )
            return

        if self.resting or self.rest_task:
            await self.stop_rest(announce=False)
        if self.auto_fishing or self.auto_fishing_task:
            await self.stop_auto_fishing(announce=False)
        if self.auto_mining or self.auto_mining_task:
            await self.stop_auto_mining(announce=False)
        if self.auto_woodcutting or self.auto_woodcutting_task:
            await self.stop_auto_woodcutting(announce=False)
        if self.auto_herbalism or self.auto_herbalism_task:
            await self.stop_auto_herbalism(announce=False)

        target = crypt_floor_id(floor)
        old = self.character.room_id

        await self.server.broadcast_room(
            old,
            f"{self.character.name} wchodzi w Portal Krypty.",
            exclude=self,
        )
        self.character.room_id = target
        self.server.db.save_character(self.character)
        await self.server.broadcast_room(
            target,
            f"{self.character.name} wychodzi z Portalu Krypty.",
            exclude=self,
        )
        await self.send(
            f"Portal Krypty przenosi cię na piętro {floor}."
        )
        await self.look()


    def rest_status_text(self):
        if not self.character:
            return "Brak postaci."
        max_hp = self.max_hp()
        max_mana = self.max_mana()
        if max_mana > 0:
            return (
                f"HP {self.current_hp} z {max_hp}. "
                f"Mana {self.current_mana} z {max_mana}. "
                f"Odpoczynek: {'aktywny' if self.resting else 'wyłączony'}."
            )
        return (
            f"HP {self.current_hp} z {max_hp}. "
            f"Odpoczynek: {'aktywny' if self.resting else 'wyłączony'}."
        )

    def rest_needs_regeneration(self):
        if not self.character:
            return False

        if self.current_hp < self.max_hp():
            return True

        max_mana = self.max_mana()
        return (
            max_mana > 0
            and self.current_mana < max_mana
        )

    async def rest_tick(self):
        if not self.character:
            return False

        max_hp = self.max_hp()
        max_mana = self.max_mana()

        hp_before = self.current_hp
        mana_before = self.current_mana

        hp_gain = max(
            1,
            (max_hp * REST_REGEN_PERCENT + 99) // 100,
        )
        self.current_hp = min(
            max_hp,
            self.current_hp + hp_gain,
        )

        if max_mana > 0:
            mana_gain = max(
                1,
                (max_mana * REST_REGEN_PERCENT + 99) // 100,
            )
            self.current_mana = min(
                max_mana,
                self.current_mana + mana_gain,
            )
        else:
            self.current_mana = 0

        if (
            self.current_hp != hp_before
            or self.current_mana != mana_before
        ):
            if max_mana > 0:
                await self.send(
                    f"Regeneracja: HP {self.current_hp} z {max_hp}. "
                    f"Mana {self.current_mana} z {max_mana}."
                )
            else:
                await self.send(
                    f"Regeneracja: HP {self.current_hp} z {max_hp}."
                )

        return self.rest_needs_regeneration()

    async def rest_loop(self):
        try:
            while self.resting and not self.closed:
                await asyncio.sleep(REST_TICK_SECONDS)

                if (
                    not self.resting
                    or self.closed
                    or self.combat_mob_key
                ):
                    break

                needs_more = await self.rest_tick()
                if not needs_more:
                    self.resting = False
                    await self.send(
                        "Odpoczynek zakończony. "
                        "HP i Mana są pełne."
                    )
                    break
        except asyncio.CancelledError:
            pass
        finally:
            self.resting = False
            if self.rest_task is asyncio.current_task():
                self.rest_task = None

    async def stop_rest(self, announce=True, reason=None):
        was_resting = self.resting or (
            self.rest_task is not None
            and not self.rest_task.done()
        )

        self.resting = False
        task = self.rest_task
        self.rest_task = None

        if (
            task
            and task is not asyncio.current_task()
            and not task.done()
        ):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        if announce and was_resting:
            if reason:
                await self.send(
                    f"Odpoczynek przerwany: {reason}."
                )
            else:
                await self.send(
                    "Odpoczynek przerwany."
                )

        return was_resting

    async def start_rest(self):
        if self.combat_mob_key:
            await self.send(
                "Nie możesz odpoczywać podczas walki. "
                "Najpierw pokonaj przeciwnika albo użyj flee."
            )
            return

        if self.resting:
            await self.send(self.rest_status_text())
            return

        if not self.rest_needs_regeneration():
            await self.send(
                "Nie musisz odpoczywać. "
                "HP i Mana są już pełne."
            )
            return

        if self.auto_fishing or self.auto_fishing_task:
            await self.stop_auto_fishing(announce=False)
        if self.auto_mining or self.auto_mining_task:
            await self.stop_auto_mining(announce=False)
        if self.auto_woodcutting or self.auto_woodcutting_task:
            await self.stop_auto_woodcutting(announce=False)
        if self.auto_herbalism or self.auto_herbalism_task:
            await self.stop_auto_herbalism(announce=False)

        self.resting = True
        self.rest_task = asyncio.create_task(
            self.rest_loop()
        )

        await self.send(
            "Rozpoczynasz odpoczynek. "
            "Co 5 sekund regenerujesz HP i Manę."
        )
        await self.send(self.rest_status_text())

    async def start_mana_regen(self):
        # v0.6.84: nie ma już osobnego trybu tylko Many.
        # Każdy regen prowadzi do pełnego odpoczynku HP + Mana.
        await self.start_rest()

    async def handle_mana_command(self, raw):
        action = normalize_lookup_text(raw)

        if action in ("", "status", "stan"):
            await self.send(
                f"Mana: {self.current_mana} z {self.max_mana()}."
            )
            if self.resting:
                await self.send(
                    "Odpoczynek: włączony. "
                    "Regenerujesz HP i Manę."
                )
            return

        if action in (
            "regen",
            "regeneruj",
            "on",
            "start",
        ):
            await self.start_rest()
            return

        if action in (
            "off",
            "stop",
            "koniec",
            "przerwij",
        ):
            if not await self.stop_rest(announce=True):
                await self.send(
                    "Odpoczynek nie jest włączony."
                )
            return

        await self.send(
            "Użycie: mana, mana regen, mana stop. "
            "Mana regen uruchamia pełny odpoczynek HP i Many."
        )

    async def handle_rest(self, raw):
        action = normalize_lookup_text(raw)

        if action in ("status", "stan"):
            await self.send(self.rest_status_text())
            return

        # regen mana i odpoczywaj mana również regenerują wszystko.
        if action in (
            "mana",
            "mana on",
            "mana start",
            "mana regen",
        ):
            await self.start_rest()
            return

        if action in (
            "mana off",
            "mana stop",
            "off",
            "stop",
            "koniec",
            "przerwij",
        ):
            if not await self.stop_rest(announce=True):
                await self.send("Nie odpoczywasz.")
            return

        if action in ("", "on", "start"):
            await self.start_rest()
            return

        await self.send(
            "Użycie: odpoczywaj, regen, regen mana, "
            "odpoczywaj status, odpoczywaj stop."
        )

    def refresh_active_classes(self):
        if not self.character or not self.account_id:
            return []
        names = self.server.db.active_class_names(
            self.account_id, self.character.class_name
        )
        self.character._active_classes = list(names)
        return list(names)

    def active_class_names(self):
        self.refresh_active_classes()
        return self.character.active_class_names()

    def find_class_name(self, query):
        wanted = self.normalize_description_query(query)
        if not wanted:
            return None
        exact = []
        partial = []
        for class_name, class_type, weapon, base_power in CLASSES:
            normalized = self.normalize_description_query(class_name)
            if wanted == normalized:
                exact.append(class_name)
            elif wanted in normalized:
                partial.append(class_name)
        if exact:
            return exact[0]
        if len(partial) == 1:
            return partial[0]
        return None

    def skill_class_name(self, skill):
        skill_id = skill["id"] if isinstance(skill, dict) else str(skill)
        for class_name, skills in CLASS_SKILLS.items():
            if any(entry["id"] == skill_id for entry in skills):
                return class_name
        return self.character.class_name

    def teacher_here_for_active_class(self):
        active = set(self.active_class_names())
        for npc_id, npc in NPCS.items():
            if (
                npc.get("room") == self.character.room_id
                and npc.get("teacher_class") in active
            ):
                return npc_id, npc
        return None, None

    async def show_multiclass(self):
        active = self.active_class_names()
        await self.send(
            f"MULTICLASS: {len(active)} z {MULTICLASS_MAX_ACTIVE} aktywnych klas."
        )
        await self.send(
            f"Klasa główna: {self.character.class_name}. "
            f"Broń Duszy pozostaje: {self.character.soul_weapon}."
        )
        rows = self.server.db.active_class_rows(
            self.account_id, self.character.class_name
        )
        for row in rows:
            level = int(row["level"])
            xp = int(row["xp"])
            slot = int(row["active_slot"])
            role = "główna" if slot == 1 else f"dodatkowa, slot {slot}"
            if level >= CLASS_MASTERY_MAX_LEVEL:
                progress = "Biegłość 100, maksimum."
            else:
                needed = class_mastery_xp_to_next(level)
                progress = (
                    f"Biegłość {level}, XP {xp} z {needed}, "
                    f"brakuje {max(0, needed - xp)} XP."
                )
            await self.send(
                f"{row['class_name']}: {role}. {progress} "
                f"Pasyw: {self.character.class_passive_text_for(row['class_name'])}."
            )

        await self.send(
            "Dodanie klas jest opcjonalne. Użyj: multiclass add <klasa>. "
            "Usunięcie: multiclass remove <klasa>."
        )
        await self.send(
            "Maksymalnie 3 klasy łącznie. Class XP z każdego zabitego moba "
            "jest dzielony równo między wszystkie aktywne klasy."
        )
        await self.send(
            "Klasa główna i jej Broń Duszy nie zmieniają się. "
            "Dodatkowe klasy dają swoje pasywy i dostęp do skilli ich nauczycieli."
        )

    async def handle_multiclass(self, raw):
        if self.combat_mob_key:
            await self.send("Nie możesz zmieniać multiclass podczas walki.")
            return

        parts = raw.strip().split(maxsplit=1)
        if not parts:
            await self.show_multiclass()
            return

        action = self.normalize_description_query(parts[0])
        query = parts[1] if len(parts) > 1 else ""

        if action in ("status", "show", "lista", "list"):
            await self.show_multiclass()
            return

        if action in ("add", "dodaj", "wlacz", "włącz"):
            class_name = self.find_class_name(query)
            if not class_name:
                await self.send(
                    "Nie rozpoznaję klasy. Dostępne: "
                    + ", ".join(cls[0] for cls in CLASSES) + "."
                )
                return
            if class_name == self.character.class_name:
                await self.send("To już jest twoja klasa główna.")
                return

            old_max_mana = self.max_mana()
            ok, result = self.server.db.activate_secondary_class(
                self.account_id, self.character.class_name, class_name
            )
            if not ok:
                await self.send(str(result))
                return

            self.refresh_active_classes()
            new_max_mana = self.max_mana()
            if new_max_mana > old_max_mana:
                self.current_mana = new_max_mana
            else:
                self.current_mana = min(self.current_mana, new_max_mana)

            await self.send(
                f"Aktywowano dodatkową klasę: {class_name}. "
                f"Masz teraz {len(self.active_class_names())} aktywne klasy."
            )
            await self.send(
                "Jej pasyw działa od razu. Skilli nauczysz się u nauczyciela "
                f"klasy {class_name}."
            )
            return

        if action in ("remove", "usun", "usuń", "wylacz", "wyłącz"):
            class_name = self.find_class_name(query)
            if not class_name:
                await self.send("Nie rozpoznaję klasy do wyłączenia.")
                return

            old_max_mana = self.max_mana()
            ok, result = self.server.db.deactivate_secondary_class(
                self.account_id, self.character.class_name, class_name
            )
            if not ok:
                await self.send(str(result))
                return

            self.refresh_active_classes()
            new_max_mana = self.max_mana()
            self.current_mana = min(self.current_mana, new_max_mana)

            await self.send(
                f"Wyłączono dodatkową klasę: {class_name}. "
                "Jej Biegłość i nauczenie skille pozostają zapisane, "
                "ale nie można ich używać, dopóki klasa znów nie będzie aktywna."
            )
            return

        await self.send(
            "Użycie: multiclass, multiclass add <klasa>, "
            "multiclass remove <klasa>."
        )

    async def grant_class_xp(self, total_xp):
        active = self.active_class_names()
        if not active:
            return
        total_xp = max(0, int(total_xp))
        if total_xp <= 0:
            return

        base_share, remainder = divmod(total_xp, len(active))
        await self.send(
            f"EXP klas: {total_xp}. Aktywne klasy: {len(active)}. "
            "Pula jest dzielona między aktywne klasy."
        )

        for index, class_name in enumerate(active):
            share = base_share + (1 if index < remainder else 0)
            result = self.server.db.add_class_mastery_xp(
                self.account_id, class_name, share
            )
            if result["level_ups"]:
                await self.send(
                    f"{class_name}: Biegłość rośnie do {result['level']}."
                )
            if result["level"] >= CLASS_MASTERY_MAX_LEVEL:
                await self.send(
                    f"{class_name}: +{share} EXP klasy. "
                    "Biegłość 100, maksimum."
                )
            else:
                await self.send(
                    f"{class_name}: +{share} EXP klasy. "
                    f"Biegłość {result['level']}, XP {result['xp']} z "
                    f"{result['next_xp']}."
                )

    def encode_session_text(self, value):
        value = str(value)
        try:
            return value.encode(
                self.output_encoding,
                errors="strict",
            )
        except UnicodeEncodeError:
            return value.encode(
                self.output_encoding,
                errors="replace",
            )

    async def negotiate_polish_charset(self):
        if self.closed:
            return
        try:
            self.writer.write(
                telnet_charset_offer_bytes()
            )
            await self.writer.drain()
        except (ConnectionError, BrokenPipeError):
            self.closed = True

    async def show_encoding(self):
        label = (
            "UTF-8"
            if self.output_encoding == "utf-8"
            else "Windows-1250"
        )
        await self.send(
            f"Kodowanie sesji: {label}."
        )
        await self.send(
            "Zmiana: kodowanie utf8 albo kodowanie cp1250."
        )

    async def set_encoding(self, raw):
        value = normalize_lookup_text(raw)

        if not value:
            await self.show_encoding()
            return

        if value in {"utf8", "utf 8", "unicode"}:
            self.input_encoding = "utf-8"
            self.output_encoding = "utf-8"
            await self.send(
                "Kodowanie przełączone na UTF-8. "
                "Test: ą ć ę ł ń ó ś ź ż."
            )
            return

        if value in {
            "cp1250",
            "windows1250",
            "windows 1250",
            "win1250",
        }:
            self.input_encoding = "cp1250"
            self.output_encoding = "cp1250"
            await self.send(
                "Kodowanie przełączone na Windows-1250. "
                "Test: ą ć ę ł ń ó ś ź ż."
            )
            return

        await self.send(
            "Nieznane kodowanie. Użyj: "
            "kodowanie utf8 albo kodowanie cp1250."
        )

    async def send(self, text=""):
        if self.closed:
            return
        try:
            self.writer.write(
                self.encode_session_text(
                    str(text) + "\r\n"
                )
            )
            await self.writer.drain()
        except (ConnectionError, BrokenPipeError):
            self.closed = True

    async def prompt(self, text):
        if self.closed:
            return
        try:
            self.writer.write(
                self.encode_session_text(text)
            )
            await self.writer.drain()
        except (ConnectionError, BrokenPipeError):
            self.closed = True

    async def read_line(self):
        try:
            while True:
                data = await self.reader.readline()
                if not data:
                    return None
                text = clean_telnet(
                    data,
                    self.input_encoding,
                )
                text = (
                    text.replace("\r", "")
                    .replace("\n", "")
                    .strip()
                )
                if text:
                    return text
        except (
            ConnectionError,
            asyncio.IncompleteReadError,
        ):
            return None

    async def ask(self, text):
        await self.prompt(text)
        return await self.read_line()

    async def login_flow(self):
        await self.negotiate_polish_charset()
        await self.send(f"SOULBOUND ONLINE v{VERSION}")
        await self.send("ENCODING: UTF-8")
        await self.send(
            "Jeśli polskie znaki są błędne, wpisz: "
            "kodowanie cp1250"
        )
        await self.send("Wpisz: login albo new")
        while True:
            cmd = await self.ask("> ")
            if cmd is None:
                return False
            cmd = cmd.lower()
            if cmd in ("login", "zaloguj"):
                if await self.do_login():
                    return True
            elif cmd in ("new", "nowe", "konto"):
                if await self.do_new_account():
                    return True
            elif cmd in ("quit", "wyjdz", "wyjdź"):
                return False
            else:
                await self.send("Dostępne: login, new, quit")

    async def do_login(self):
        username = await self.ask("Nazwa konta: ")
        if username is None:
            return False
        row = self.server.db.account_by_name(username)
        if not row:
            await self.send("Nie ma takiego konta.")
            return False
        password = await self.ask("Hasło: ")
        if password is None:
            return False
        if not verify_password(password, row["password_salt"], row["password_hash"]):
            await self.send("Nieprawidłowe hasło.")
            return False
        if self.server.account_online(row["id"]):
            await self.send("To konto jest już zalogowane.")
            return False
        self.account_id = row["id"]
        char_row = self.server.db.character_for_account(self.account_id)
        if char_row:
            self.character = Character.from_row(char_row)
            if self.character.room_id not in ROOMS:
                self.character.room_id = "square"
        else:
            if not await self.character_creator():
                return False
        return True

    async def do_new_account(self):
        await self.send("Tworzenie nowego konta.")
        while True:
            username = await self.ask("Nazwa konta, 3-20 znaków: ")
            if username is None:
                return False
            username = username.strip()
            if not safe_name(username):
                await self.send("Dozwolone są litery, cyfry, _ i -. Długość 3-20.")
                continue
            if self.server.db.account_by_name(username):
                await self.send("Taka nazwa konta już istnieje.")
                continue
            break
        while True:
            password = await self.ask("Hasło, minimum 6 znaków: ")
            if password is None:
                return False
            if len(password) < 6:
                await self.send("Hasło jest za krótkie.")
                continue
            confirm = await self.ask("Powtórz hasło: ")
            if confirm is None:
                return False
            if password != confirm:
                await self.send("Hasła się różnią.")
                continue
            break
        self.account_id = self.server.db.create_account(username, password)
        await self.send("Konto utworzone.")
        return await self.character_creator()

    async def choose_number(self, items, prompt_text):
        while True:
            raw = await self.ask(prompt_text)
            if raw is None:
                return None
            try:
                n = int(raw)
                if 1 <= n <= len(items):
                    return items[n - 1]
            except ValueError:
                pass
            await self.send("Nieprawidłowy numer.")

    def valid_name_case_form(self, value):
        value = value.strip()
        if not (1 <= len(value) <= 40):
            return False
        return not any(ord(ch) < 32 for ch in value)

    async def ask_name_declension(self, base_name):
        await self.send("ODMIANA IMIENIA POSTACI")
        await self.send(
            "Mianownik jest nazwą wybraną na początku kreatora. "
            "Teraz podaj pozostałe sześć form."
        )
        result = {"nom": base_name}
        await self.send(f"Mianownik. Kto? Co?: {base_name}.")

        prompts = (
            ("gen", "Dopełniacz. Kogo? Czego?"),
            ("dat", "Celownik. Komu? Czemu?"),
            ("acc", "Biernik. Kogo? Co?"),
            ("ins", "Narzędnik. Z kim? Z czym?"),
            ("loc", "Miejscownik. O kim? O czym?"),
            ("voc", "Wołacz. O!"),
        )
        for key, label in prompts:
            while True:
                raw = await self.ask(f"{label}: ")
                if raw is None:
                    return None
                value = raw.strip()
                if self.valid_name_case_form(value):
                    result[key] = value
                    break
                await self.send("Nieprawidłowa forma. Użyj od 1 do 40 znaków.")

        await self.send("Zapisana odmiana imienia:")
        await self.send(f"Mianownik: {result['nom']}.")
        await self.send(f"Dopełniacz: {result['gen']}.")
        await self.send(f"Celownik: {result['dat']}.")
        await self.send(f"Biernik: {result['acc']}.")
        await self.send(f"Narzędnik: {result['ins']}.")
        await self.send(f"Miejscownik: {result['loc']}.")
        await self.send(f"Wołacz: {result['voc']}.")
        return result

    async def character_creator(self):
        await self.send("KREATOR POSTACI")
        while True:
            name = await self.ask("Nazwa postaci, 3-20 znaków: ")
            if name is None:
                return False
            name = name.strip()
            if not safe_name(name) or self.server.db.character_name_exists(name):
                await self.send("Nieprawidłowa lub zajęta nazwa.")
                continue
            break
        await self.send("Wybierz rasę:")
        await self.send(
            "Znaczenie statystyk: Siła zwiększa atak fizyczny; "
            "Zręczność zwiększa szybkość i unik; Kondycja zwiększa HP; "
            "Inteligencja zwiększa Manę i moc czarów; "
            "Siła Woli zwiększa obronę magiczną."
        )
        for i, race in enumerate(RACES, 1):
            rname, desc, s, d, c, inte, w = race
            await self.send(
                f"{i}. {rname}. {desc} Siła {s}, Zręczność {d}, Kondycja {c}, "
                f"Inteligencja {inte}, Siła Woli {w}."
            )
        race = await self.choose_number(RACES, "Numer rasy: ")
        if race is None:
            return False
        await self.send("Wybierz klasę:")
        for i, cls in enumerate(CLASSES, 1):
            cname, ctype, weapon, _ = cls
            kind = "fizyczna" if ctype == "physical" else "magiczna"
            desc = CLASS_DESCRIPTIONS.get(cname, "")
            growth = (
                "Rozwój: wszystkie statystyki automatycznie: Siła, Zręczność, "
                "Kondycja, Inteligencja i Siła Woli."
            )
            skills = CLASS_SKILLS.get(cname, [])
            skill_text = "; ".join(
                f"{s['name']} do nauki od Soul Level {s['unlock']}" for s in skills
            )
            await self.send(
                f"{i}. {cname}. Typ {kind}. {desc} "
                f"{growth} Broń Duszy: {weapon}. Umiejętności: {skill_text}."
            )
        cls = await self.choose_number(CLASSES, "Numer klasy: ")
        if cls is None:
            return False

        name_cases = await self.ask_name_declension(name)
        if name_cases is None:
            return False

        self.server.db.create_character(
            self.account_id, name, race, cls, name_cases
        )
        self.character = Character.from_row(
            self.server.db.character_for_account(self.account_id)
        )
        await self.send(f"Utworzono postać {self.character.name}.")
        await self.send(
            "Postać nie posiada levelu. Wszystkie pięć statystyk rośnie automatycznie."
        )
        await self.send("Na start otrzymujesz 30 srebra, 2 złota i 2 Mikstury leczenia.")
        return True

    async def enter_world(self):
        self.refresh_active_classes()

        # Najpierw zachowaj zgodność starego mechanizmu portali Krypty
        # na podstawie lokacji zapisanej przy poprzednim wylogowaniu.
        self.server.db.sync_legacy_crypt_checkpoint(
            self.account_id, self.character.room_id
        )

        # Każde wejście do świata zaczyna się w Świątyni Odrodzenia.
        # Nie ma znaczenia, gdzie postać wylogowała się poprzednio.
        self.character.room_id = "temple"
        self.server.db.save_character(self.character)

        self.current_hp = self.max_hp()
        self.current_mana = self.max_mana()

        await self.server.broadcast_room(
            self.character.room_id,
            f"{self.character.name} pojawia się w Świątyni Odrodzenia.",
            exclude=self,
        )
        await self.send(
            f"Witaj, {self.character.name_case('voc')}. "
            f"Soulbound v{VERSION} World Core."
        )
        await self.send(
            "Rozpoczynasz sesję w Świątyni Odrodzenia."
        )
        await self.send("Wpisz help, aby poznać komendy.")
        await self.look()

    def equipped_item_rows(self):
        return list(self.server.db.equipment(self.account_id))

    def equipment_bonus_totals(self):
        totals = {
            "strength": 0,
            "dexterity": 0,
            "constitution": 0,
            "intelligence": 0,
            "willpower": 0,
            "hp": 0,
            "mana": 0,
        }
        for row in self.equipped_item_rows():
            item = ITEMS.get(row["item_id"])
            if not item:
                continue
            affix = item.get("affix")
            if affix in totals:
                totals[affix] += int(item.get("affix_amount", 0))
        return totals

    def dominant_crypt_set(self):
        counts = {}
        for row in self.equipped_item_rows():
            item = ITEMS.get(row["item_id"])
            if not item:
                continue
            tier = item.get("crypt_set_tier")
            if tier:
                tier = int(tier)
                counts[tier] = counts.get(tier, 0) + 1

        if not counts:
            return 0, 0

        tier, count = sorted(
            counts.items(),
            key=lambda entry: (entry[1], entry[0]),
            reverse=True,
        )[0]
        return tier, count

    def crypt_set_hp_mana_multiplier(self):
        _tier, count = self.dominant_crypt_set()
        return 1.10 if count >= 2 else 1.0

    def crypt_set_damage_multiplier(self):
        _tier, count = self.dominant_crypt_set()
        return 1.10 if count >= 4 else 1.0

    def crypt_set_defense_multiplier(self):
        _tier, count = self.dominant_crypt_set()
        return 1.15 if count >= 6 else 1.0

    def crypt_set_bonus_text(self):
        tier, count = self.dominant_crypt_set()
        if not tier:
            return "Brak aktywnego zestawu Krypty."

        active = []
        if count >= 2:
            active.append("2 części: +10 procent maksymalnego HP i Many")
        if count >= 4:
            active.append("4 części: +10 procent wszystkich obrażeń")
        if count >= 6:
            active.append("6 części: +15 procent obrony fizycznej i magicznej")

        if not active:
            active_text = "brak aktywnego progu; potrzeba 2 części"
        else:
            active_text = "; ".join(active)

        return (
            f"Zestaw Krypty Tier {tier}: {count} z 6 części. "
            f"{active_text}."
        )

    def dominant_astral_set(self):
        counts = {}
        for row in self.equipped_item_rows():
            item = ITEMS.get(row["item_id"])
            if not item:
                continue
            tier = item.get("astral_set_tier")
            if tier:
                tier = int(tier)
                counts[tier] = counts.get(tier, 0) + 1

        if not counts:
            return 0, 0

        tier, count = sorted(
            counts.items(),
            key=lambda entry: (entry[1], entry[0]),
            reverse=True,
        )[0]
        return tier, count

    def astral_set_hp_mana_multiplier(self):
        _tier, count = self.dominant_astral_set()
        return 1.12 if count >= 2 else 1.0

    def astral_set_damage_multiplier(self):
        _tier, count = self.dominant_astral_set()
        return 1.15 if count >= 4 else 1.0

    def astral_set_defense_multiplier(self):
        _tier, count = self.dominant_astral_set()
        return 1.20 if count >= 6 else 1.0

    def total_set_hp_mana_multiplier(self):
        return (
            self.crypt_set_hp_mana_multiplier()
            * self.astral_set_hp_mana_multiplier()
        )

    def total_set_damage_multiplier(self):
        return (
            self.crypt_set_damage_multiplier()
            * self.astral_set_damage_multiplier()
        )

    def total_set_defense_multiplier(self):
        return (
            self.crypt_set_defense_multiplier()
            * self.astral_set_defense_multiplier()
        )

    def astral_set_bonus_text(self):
        tier, count = self.dominant_astral_set()
        if not tier:
            return "Brak aktywnego Zestawu Astralnego."

        active = []
        if count >= 2:
            active.append(
                "2 części: +12 procent maksymalnego HP i Many"
            )
        if count >= 4:
            active.append(
                "4 części: +15 procent wszystkich obrażeń"
            )
        if count >= 6:
            active.append(
                "6 części: +20 procent obrony fizycznej i magicznej"
            )

        if not active:
            active_text = "brak aktywnego progu; potrzeba 2 części"
        else:
            active_text = "; ".join(active)

        return (
            f"Zestaw Astralny Krąg {tier}: {count} z 6 części. "
            f"{active_text}."
        )

    def effective_strength(self):
        return (
            self.character.strength
            + self.equipment_bonus_totals()["strength"]
        )

    def effective_dexterity(self):
        return (
            self.character.dexterity
            + self.equipment_bonus_totals()["dexterity"]
        )

    def critical_chance(self):
        dexterity = self.effective_dexterity()
        chance = 0.05 + (dexterity - 10) * 0.005
        return max(0.01, min(0.35, chance))

    def critical_multiplier(self):
        return 1.50

    def roll_critical_hit(self, damage):
        damage = max(0, int(damage))
        if damage <= 0:
            return damage, False
        if random.random() < self.critical_chance():
            return (
                max(
                    1,
                    int(round(
                        damage * self.critical_multiplier()
                    )),
                ),
                True,
            )
        return damage, False

    def effective_constitution(self):
        return (
            self.character.constitution
            + self.equipment_bonus_totals()["constitution"]
        )

    def effective_intelligence(self):
        return (
            self.character.intelligence
            + self.equipment_bonus_totals()["intelligence"]
        )

    def effective_willpower(self):
        return (
            self.character.willpower
            + self.equipment_bonus_totals()["willpower"]
        )

    def max_hp(self):
        bonuses = self.equipment_bonus_totals()
        base = 40 + self.effective_constitution() * 5
        value = int(
            round(
                (base + bonuses["hp"])
                * self.character.racial_max_hp_multiplier()
                * self.total_set_hp_mana_multiplier()
            )
        )
        return max(1, value)

    def max_mana(self):
        if not any(
            class_type_for_name(name) == "magic"
            for name in self.active_class_names()
        ):
            return 0

        bonuses = self.equipment_bonus_totals()
        base = 20 + self.effective_intelligence() * 5
        value = int(
            round(
                (base + bonuses["mana"])
                * self.character.racial_max_mana_multiplier()
                * self.total_set_hp_mana_multiplier()
            )
        )
        return max(0, value)

    def physical_power(self):
        return self.effective_strength()

    def speed(self):
        return 10 + self.effective_dexterity() * 2

    def dodge_chance(self):
        base = max(0.0, (self.speed() - 20) / 300.0)
        return min(
            0.45,
            base
            + self.character.class_dodge_bonus()
            + self.character.racial_dodge_bonus(),
        )

    def spell_power(self):
        return self.effective_intelligence()

    def magic_defense(self):
        base = max(0, self.effective_willpower() // 2)
        value = int(
            round(
                base
                * self.character.class_magic_defense_multiplier()
                * self.character.racial_magic_defense_multiplier()
                * self.total_set_defense_multiplier()
            )
        )
        return max(0, value)

    def defense(self):
        total = 0
        for row in self.server.db.equipment(self.account_id):
            item = ITEMS.get(row["item_id"])
            if item:
                total += int(item.get("defense", 0))
        return max(
            0,
            int(round(total * self.total_set_defense_multiplier()))
        )

    def visible_player_for_look(self, query):
        wanted = self.normalize_description_query(query)
        if not wanted:
            return None

        exact = []
        partial = []
        for session in self.server.sessions:
            if (
                not session.character
                or session.character.room_id != self.character.room_id
            ):
                continue
            normalized = self.normalize_description_query(
                session.character.name
            )
            if wanted == normalized:
                exact.append(session)
            elif wanted in normalized:
                partial.append(session)

        if exact:
            return exact[0]
        if len(partial) == 1:
            return partial[0]
        return None

    def visible_npc_for_look(self, query):
        current = {
            npc_id: npc
            for npc_id, npc in NPCS.items()
            if npc.get("room") == self.character.room_id
        }
        return self.find_description_entry(current, query)

    def visible_mob_for_look(self, query):
        wanted = self.normalize_description_query(query)
        if not wanted:
            return None

        exact = []
        partial = []
        for mob in self.server.world.room_mobs(
            self.character.room_id
        ):
            template = MOB_TEMPLATES[mob.template_id]
            name = self.normalize_description_query(
                template["name"]
            )
            template_id = self.normalize_description_query(
                mob.template_id
            )
            entry = (mob, template)
            if wanted in {name, template_id}:
                exact.append(entry)
            elif wanted in name or wanted in template_id:
                partial.append(entry)

        if exact:
            return exact[0]
        if len(partial) == 1:
            return partial[0]
        return None

    def visible_item_for_look(self, query):
        wanted = self.normalize_description_query(query)
        if not wanted:
            return None

        candidates = {}

        for row in self.server.db.inventory(self.account_id):
            item_id = row["item_id"]
            item = ITEMS.get(item_id)
            if not item:
                continue
            entry = candidates.setdefault(
                item_id,
                {
                    "item": item,
                    "quantity": 0,
                    "equipped": [],
                    "shop": False,
                },
            )
            entry["quantity"] += int(row["quantity"])

        for row in self.server.db.equipment(self.account_id):
            item_id = row["item_id"]
            item = ITEMS.get(item_id)
            if not item:
                continue
            entry = candidates.setdefault(
                item_id,
                {
                    "item": item,
                    "quantity": 0,
                    "equipped": [],
                    "shop": False,
                },
            )
            entry["equipped"].append(row["slot"])

        for item_id in SHOPS.get(self.character.room_id, ()):
            item = ITEMS.get(item_id)
            if not item:
                continue
            entry = candidates.setdefault(
                item_id,
                {
                    "item": item,
                    "quantity": 0,
                    "equipped": [],
                    "shop": False,
                },
            )
            entry["shop"] = True

        exact = []
        partial = []
        for item_id, entry in candidates.items():
            item = entry["item"]
            normalized_id = self.normalize_description_query(item_id)
            normalized_name = self.normalize_description_query(
                item.get("name", item_id)
            )
            result = (item_id, entry)

            if wanted in {normalized_id, normalized_name}:
                exact.append(result)
            elif (
                wanted in normalized_id
                or wanted in normalized_name
            ):
                partial.append(result)

        if exact:
            return exact[0]
        if len(partial) == 1:
            return partial[0]
        return None

    async def look_at_player(self, session):
        character = session.character
        classes = character.active_class_names()
        await self.send(f"{character.name}. Gracz.")
        await self.send(
            f"Rasa: {character.race}. "
            f"Klasa: {', '.join(classes)}. "
            f"Soul Level {character.soul_level}. "
            f"Soul Tier {character.soul_tier}."
        )
        await self.send(
            f"Broń Duszy: {character.soul_weapon}."
        )

    async def look_at_npc(self, npc_id, npc):
        await self.send(f"{npc['name']}. NPC.")
        desc = NPC_DESCRIPTIONS.get(
            npc_id,
            npc.get("dialogue", ""),
        )
        if desc:
            await self.send(desc)

        quest_ids = []
        if npc.get("quest"):
            quest_ids.append(npc["quest"])
        quest_ids.extend(npc.get("quest_chain") or ())
        quest_ids.extend(npc.get("specialist_quests") or ())
        quest_ids = list(dict.fromkeys(quest_ids))

        if quest_ids:
            names = [
                QUESTS[qid]["name"]
                for qid in quest_ids
                if qid in QUESTS
            ]
            if names:
                await self.send(
                    "Powiązane zadania: "
                    + ", ".join(names)
                    + "."
                )

    async def look_at_mob(self, mob, template):
        dtype = (
            "magiczne"
            if template.get("damage_type") == "magic"
            else "fizyczne"
        )
        await self.send(
            f"{template['name']}. Przeciwnik."
        )
        await self.send(
            f"HP: {mob.hp} z {template['max_hp']}. "
            f"Bazowe obrażenia: {template.get('damage', 0)}. "
            f"Typ obrażeń: {dtype}."
        )

        if template.get("rare_troll"):
            await self.send("Rzadki wariant trolla.")

        if template.get("elite_affix_text"):
            await self.send(
                "Elitarny affix: "
                + template["elite_affix_text"]
            )

        if template.get("boss_mechanic_text"):
            await self.send(
                "Mechanika: "
                + template["boss_mechanic_text"]
            )

    async def look_at_item(self, item_id, entry):
        item = entry["item"]
        await self.send(
            self.format_item_description(item_id, item)
        )

        context = []
        quantity = int(entry.get("quantity", 0))
        if quantity > 0:
            context.append(f"Masz {quantity} szt.")

        for slot in entry.get("equipped", ()):
            context.append(
                "Założony: "
                + EQUIPMENT_SLOT_NAMES.get(slot, slot)
            )

        if entry.get("shop"):
            context.append(
                "Dostępny w sklepie tej lokacji"
            )

        if context:
            await self.send(". ".join(context) + ".")

    async def look(self, query=""):
        query = str(query or "").strip()

        if query:
            player = self.visible_player_for_look(query)
            if player:
                await self.look_at_player(player)
                return

            npc = self.visible_npc_for_look(query)
            if npc:
                npc_id, npc_data = npc
                await self.look_at_npc(npc_id, npc_data)
                return

            mob = self.visible_mob_for_look(query)
            if mob:
                mob_state, template = mob
                await self.look_at_mob(mob_state, template)
                return

            item = self.visible_item_for_look(query)
            if item:
                item_id, entry = item
                await self.look_at_item(item_id, entry)
                return

            await self.send(
                "Nie widzisz tutaj takiego gracza, "
                "NPC, przeciwnika ani przedmiotu."
            )
            return

        room = ROOMS[self.character.room_id]
        await self.send(
            f"{room['name']}. Strefa: {room['zone']}."
        )
        await self.send(room["desc"])

        npcs = [
            value["name"]
            for value in NPCS.values()
            if value["room"] == self.character.room_id
        ]
        if npcs:
            await self.send(
                "NPC: " + ", ".join(npcs) + "."
            )

        mobs = self.server.world.room_mobs(
            self.character.room_id
        )
        if mobs:
            names = [
                MOB_TEMPLATES[mob.template_id]["name"]
                for mob in mobs
            ]
            await self.send(
                "Przeciwnicy: "
                + ", ".join(names)
                + "."
            )

        corpses = self.server.world.room_corpses(
            self.character.room_id
        )
        if corpses:
            await self.send(
                "Ciała: "
                + ", ".join(
                    corpse.mob_name
                    for corpse in corpses
                )
                + ". Wpisz ciało, aby sprawdzić ekwipunek."
            )

        if self.crypt_descent_blocked_for_player(
            self.character.room_id
        ):
            boss = self.server.world.live_crypt_boss(
                self.character.room_id
            )
            if boss:
                await self.send(
                    f"Zejście niżej blokuje boss: "
                    f"{MOB_TEMPLATES[boss.template_id]['name']}."
                )

        others = [
            session.character.name
            for session in self.server.sessions
            if (
                session is not self
                and session.character
                and session.character.room_id
                == self.character.room_id
            )
        ]
        if others:
            await self.send(
                "Gracze tutaj: "
                + ", ".join(
                    sorted(others, key=str.lower)
                )
                + "."
            )

        await self.show_exits()

    async def show_exits(self):
        room = ROOMS[self.character.room_id]
        if not room["exits"]:
            await self.send("Wyjścia: brak.")
            return
        exits=[]
        for direction in room["exits"].keys():
            if self.giant_fortress_ascent_blocked_for_player(
                self.character.room_id, direction
            ):
                exits.append(
                    f"{direction}, zablokowane przez bossa Twierdzy Gigantów"
                )
            elif self.crypt_descent_blocked_for_player(
                self.character.room_id, direction
            ):
                exits.append(f"{direction}, zablokowane przez bossa Krypty")
            elif self.astral_ascent_blocked_for_player(
                self.character.room_id, direction
            ):
                exits.append(f"{direction}, zablokowane przez bossa Wieży")
            elif self.astral_entry_blocked(
                room["exits"].get(direction)
            ):
                exits.append(
                    f"{direction}, wymaga Soul Level {ASTRAL_MIN_SOUL_LEVEL}"
                )
            else:
                exits.append(direction)
        await self.send("Wyjścia: " + ", ".join(exits) + ".")

    async def show_map(self):
        current = self.character.room_id
        await self.send("MAPA ODKRYTEGO ŚWIATA")

        zones = {}
        for room_id, room in ROOMS.items():
            if (
                room_id.startswith("crypt_floor_")
                or room_id.startswith("astral_floor_")
                or room_id.startswith("mine_floor_")
            ):
                continue
            zones.setdefault(room["zone"], []).append(
                (room_id, room["name"])
            )

        for zone in sorted(zones):
            await self.send(zone + ":")
            entries = []
            for room_id, name in sorted(
                zones[zone], key=lambda entry: entry[1].lower()
            ):
                marker = " [TU]" if room_id == current else ""
                entries.append(name + marker)
            await self.send("; ".join(entries) + ".")

        floor = crypt_floor_number(current)
        marker = f" [TU: piętro {floor}]" if floor else ""
        await self.send(
            f"Krypta 1-{CRYPT_MAX_FLOOR}: "
            f"piętra 1-{CRYPT_MAX_FLOOR}{marker}."
        )
        astral_floor = astral_floor_number(current)
        astral_marker = (
            f" [TU: poziom {astral_floor}]"
            if astral_floor is not None else ""
        )
        await self.send(
            f"Wieża Astralna {ASTRAL_MIN_FLOOR}-{ASTRAL_MAX_FLOOR}: "
            f"poziomy {ASTRAL_MIN_FLOOR}-{ASTRAL_MAX_FLOOR}"
            f"{astral_marker}."
        )
        await self.send(
            "Każdą nazwę z mapy można podać do prowadz. "
            "Wpisz prowadz lista, aby dostać pełną listę celów."
        )


    async def show_crypt_info(self):
        floor = crypt_floor_number(self.character.room_id)
        await self.send(
            f"KRYPTA: {CRYPT_MAX_FLOOR} pięter. "
            f"Bossowie są co 10 pięter od 10 do {CRYPT_MAX_FLOOR}."
        )
        await self.send(
            "Żywy boss zawsze blokuje zejście na następne piętro."
        )
        await self.send(
            "Po zabiciu bossa przejście jest otwarte tylko do jego respawnu. "
            "Gdy boss odrodzi się, ponownie blokuje zejście."
        )
        await self.send(
            "Pokonanie bossa odblokowuje trwały Portal Krypty do jego piętra. "
            "Portal skraca podróż, ale nie wyłącza żywego bossa."
        )
        await self.send(
            "Portal uruchamiasz komendą portal <piętro> w Sali Krypty "
            "albo w Przedsionku Krypty."
        )
        await self.send(
            "Zwykłe moby Krypty zostawiają 1 element ekwipunku na ciele, "
            "bossowie 3."
        )
        await self.send(
            "Moby nie są agresywne. Nie atakują gracza same."
        )

        highest = self.crypt_portal()
        if highest:
            await self.send(
                f"Najwyższy odblokowany Portal Krypty: piętro {highest}."
            )
        else:
            await self.send("Portale Krypty: jeszcze brak.")

        if floor:
            await self.send(
                f"Aktualne piętro Krypty: {floor} z {CRYPT_MAX_FLOOR}."
            )
            boss = self.server.world.live_crypt_boss(
                self.character.room_id
            )
            if boss:
                await self.send(
                    f"Boss żyje i blokuje zejście: "
                    f"{MOB_TEMPLATES[boss.template_id]['name']}."
                )
            elif floor in CRYPT_BOSS_FLOORS:
                await self.send(
                    "Boss tego piętra jest obecnie pokonany. "
                    "Możesz zejść niżej do czasu jego respawnu."
                )


    async def show_astral_info(self):
        floor = astral_floor_number(self.character.room_id)
        await self.send(
            f"WIEŻA ASTRALNA: poziomy {ASTRAL_MIN_FLOOR}-{ASTRAL_MAX_FLOOR}. "
            f"Wejście wymaga Soul Level {ASTRAL_MIN_SOUL_LEVEL}."
        )
        await self.send(
            "Klimat Wieży to gwiezdne szkło, mgławice, konstelacje i astralna energia."
        )
        await self.send(
            "Boss stoi co 10 poziomów i blokuje drogę w górę, dopóki żyje."
        )
        await self.send(
            "Pokonanie bossa odblokowuje trwały Astralny Portal do jego poziomu."
        )
        await self.send(
            "Astralny Portal działa przy Astralnej Bramie komendą "
            "astralportal <poziom>."
        )
        await self.send(
            "Zwykłe moby Wieży zostawiają 1 element Astralnego ekwipunku, "
            "bossowie 3. Bossowie mają także własne unikalne relikty."
        )
        await self.send(
            "Moby i bossowie Wieży nie są agresywni."
        )

        highest = self.astral_portal()
        if highest:
            await self.send(
                f"Najwyższy checkpoint Wieży: poziom {highest}."
            )
        else:
            await self.send("Checkpointy Wieży: jeszcze brak.")

        if floor is not None:
            await self.send(
                f"Aktualny poziom Wieży Astralnej: {floor}."
            )
            boss = self.server.world.live_astral_boss(
                self.character.room_id
            )
            if boss:
                await self.send(
                    f"Boss żyje i blokuje drogę w górę: "
                    f"{MOB_TEMPLATES[boss.template_id]['name']}."
                )

    async def show_corpses(self, query=""):
        corpses=self.server.world.room_corpses(self.character.room_id)
        if not corpses:
            await self.send("Nie ma tutaj żadnych ciał."); return
        if query.strip():
            corpse=self.server.world.find_corpse(self.character.room_id,query)
            if not corpse: await self.send("Nie widzę takiego ciała."); return
            corpses=[corpse]
        for number,corpse in enumerate(corpses,1):
            names=", ".join(ITEMS[i]["name"] for i in corpse.items) if corpse.items else "brak ekwipunku"
            await self.send(f"{number}. Ciało: {corpse.mob_name}. Ekwipunek na ciele: {names}.")
        await self.send("Aby zabrać ekwipunek wpisz: przeszukaj ciało albo przeszukaj <nazwa moba>.")

    async def loot_corpse(self, query=""):
        corpses=self.server.world.room_corpses(self.character.room_id)
        if not corpses:
            await self.send("Nie ma tutaj żadnych ciał do przeszukania."); return
        corpse=self.server.world.find_corpse(self.character.room_id,query)
        if corpse is None:
            if not query.strip() and len(corpses)>1:
                await self.send("Jest tutaj kilka ciał. Wpisz ciało, potem przeszukaj <nazwa moba>.")
            else: await self.send("Nie widzę takiego ciała.")
            return
        if not corpse.items:
            await self.send(f"Przeszukujesz ciało: {corpse.mob_name}. Nie ma już na nim ekwipunku."); return
        looted=list(corpse.items); corpse.items.clear()
        for item_id in looted:
            self.server.db.add_item(self.account_id,item_id,1)

        await self.send(
            f"Przeszukujesz ciało: {corpse.mob_name}. Zabierasz: "
            + ", ".join(ITEMS[i]["name"] for i in looted) + "."
        )

        armor_slots = sorted({
            ITEMS[item_id].get("slot")
            for item_id in looted
            if ITEMS.get(item_id, {}).get("type") == "armor"
        })
        if armor_slots:
            commands = {
                "head": "załóż hełm",
                "body": "załóż zbroja",
                "hands": "załóż rękawice",
                "legs": "załóż nogi",
                "feet": "załóż buty",
                "charm": "załóż talizman",
            }
            quick = [
                commands[slot]
                for slot in armor_slots
                if slot in commands
            ]
            await self.send(
                "Zdobyty pancerz możesz założyć. Skróty: "
                + ", ".join(quick) + "."
            )

    async def show_where(self):
        room = ROOMS[self.character.room_id]
        await self.send(f"Jesteś tutaj: {room['name']}. Strefa: {room['zone']}.")

    def help_commands(self):
        return [
            "help [temat] / pomoc [temat] - pomoc; help tematy pokazuje działy",
            "changes / zmiany / changelog - pokaż najnowsze zmiany",
            "opis [nazwa] / describe [name] - szczegółowy opis elementu świata",
            "look lub l - opis aktualnej lokacji",
            "exits - dostępne kierunki",
            "map - lista lokacji świata; Krypta 1-200 jest pokazana skrótowo",
            "krypta / crypt - informacje o Krypcie 1-200, bossach i checkpointach",
            "wieza / astral - informacje o Wieży Astralnej 100-200",
            "astralportal [poziom] - checkpointy Wieży Astralnej",
            "portal [piętro] - pokaż lub uruchom odblokowany Portal Krypty",
            "atlas [ryby|drewno|rudy|surowiec] - atlas pozyskiwania surowców",
            "where - aktualna lokacja",
            "location / lokalizacja - lokacja, strefa i wyjścia",
            "north/south/east/west/up/down lub n/s/e/w/u/d - ruch",
            "prowadz lokacja / walk lokacja / walk to location - automatyczne prowadzenie; np. walk targ, walk kuznia, walk port",
            "prowadz lista - wszystkie dostępne cele prowadzenia",
            "who - gracze online",
            "say tekst - rozmowa lokalna",
            "tell gracz tekst - wiadomość prywatna",
            "druzyna / party - zarządzanie drużyną",
            "pc tekst - czat drużyny",
            "charyzma / charisma - rabat sklepowy i limit drużyny",
            "multiclass / klasy - opcjonalne 1-3 aktywne klasy i Biegłość klas",
            "multiclass add klasa / remove klasa - dodaj lub wyłącz klasę dodatkową",
            "stats - statystyki",
            "odmiana / przypadki - pokaż 7 form imienia postaci",
            "skills / umiejetnosci - lista umiejętności twojej klasy",
            "skillnames / nazwyskilli - wszystkie nazwy skilli wszystkich klas",
            "skill / umiejetnosc / cast <nazwa lub numer> [cel] - użyj umiejętności",
            "użyj umiejętność <nazwa> [cel] / use skill <name> [target] - alternatywne użycie skilla",
            "learn / naucz / ucz <nazwa, numer lub naturalna kategoria> - np. naucz leczenie, tarcza, ciecie, pocisk, ogien",
            "soul - Broń Duszy, Soul Level 1-200",
            "money - srebro, złoto i mithril",
            "bank - Bank Dusz na Rynku; waluta i trwała skrytka przedmiotów",
            "money - automatyczne nominały waluty i kurs",
            "professions / profesje - Wędkarstwo, Górnictwo i Drwalstwo",
            "rangi / ranks - pełna lista rang trzech profesji",
            "tools / narzedzia - skrót wszystkich 7 narzędzi",
            "wedka / kilof / pila / mlot / noz / sierp / mozdzierz - pełne informacje o wybranym narzędziu",
            "tiers / tiery / nazwytierow - pełna lista Tierów wszystkich 7 narzędzi",
            "fish / wedkuj / low - pojedynczy połów",
            "low on / fish on - auto-łowienie",
            "low off / fish off - wyłącz auto-łowienie",
            "mine / kop - pojedyncze wydobycie",
            "kop on / mine on - auto-kopanie",
            "kop off / mine off - wyłącz auto-kopanie",
            "tnij / drwal / woodcut - pojedyncze pozyskanie drewna",
            "tnij on / woodcut on - auto-Drwalstwo",
            "tnij off / woodcut off - wyłącz auto-Drwalstwo",
            "zbieraj / zielarstwo - pojedynczy zbiór ziół",
            "zbieraj on / zbieraj off - auto-Zielarstwo",
            "ziola / herbs - Torba Zielarska; pokazuje ilość ziół i szacowany zarobek",
            "alchemia / warz receptura - warzenie mikstur",
            "net / siatka - Siatka na ryby; pokazuje liczbę ryb i szacowany zarobek ze sprzedaży",
            "bag / sakwa - Sakwa górnicza; pokazuje ilość rud i szacowany zarobek",
            "drewno / stos / woodpile - Stos drewna; pokazuje ilość drewna i szacowany zarobek",
            "put fish net / wloz ryba siatka - przenieś ryby do Siatki",
            "put ore bag / wloz ruda sakwa - przenieś rudy do Sakwy",
            "take przedmiot net/bag / wyjmij przedmiot siatka/sakwa - wyjmij surowiec",
            "sell / sprzedaj - pojedynczo albo hurtowo: sprzedaj wszystko siatka, wszystko sakwa, wszystko stos, wszystko torba, wszystko przedmioty",
            "receptury / przepisy / recipes [craft|cook] - lista receptur",
            "craft / stworz / wytworz receptura - rzemiosło z rud i drewna",
            "cook / gotuj receptura - przygotuj potrawę z ryb",
            "inventory / i - zwykły ekwipunek",
            "equipment / eq - założone wyposażenie, rarity, affix i bonus setu",
            "help loot_krypty - rarity, losowe statystyki i sety Krypty",
            "equip / załóż przedmiot albo slot - np. załóż buty, hełm, zbroja, rękawice, nogi, talizman",
            "use / użyj - przedmioty, skille i czary; np. użyj ciecie goblin albo użyj pocisk goblin",
            "shop / sklep / list / lista - oferta sprzedawcy",
            "buy / kup przedmiot - kup przedmiot",
            "talk npc - rozmowa, zadania i lekcje nauczycieli klasowych",
            "teachers / nauczyciele - lista nauczycieli w Sali Gildii",
            "quests - dziennik zadań",
            "consider / con / ocen <mob> - oceń siłę przeciwnika bez rozpoczynania walki",
            "attack / atakuj / zabij / kill przeciwnik - tura walki",
            "ciało / zwloki / corpse - pokaż ciała i ich ekwipunek",
            "przeszukaj ciało / loot - zabierz ekwipunek z ciała moba",
            "flee / uciekaj - ucieczka",
            "unlock - odblokuj gotowy Soul Tier",
            "save - zapis",
            "quit - wyjście",
        ]

    def full_changelog_lines(self):
        module_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = (
            os.path.join(module_dir, "CHANGELOG_PL.txt"),
            os.path.join(os.getcwd(), "CHANGELOG_PL.txt"),
        )

        for changelog_path in candidates:
            try:
                if not os.path.exists(changelog_path):
                    continue
                with open(changelog_path, "r", encoding="utf-8") as handle:
                    lines = [line.rstrip("\r\n") for line in handle]
                if any(line.strip() for line in lines):
                    return lines
            except (OSError, UnicodeError):
                continue

        lines = [LATEST_CHANGES_TITLE]
        lines.extend("- " + line for line in LATEST_CHANGES)
        return lines

    async def show_latest_changes(self):
        await self.send("PEŁNA HISTORIA ZMIAN SOULBOUND")
        await self.send(
            "Najnowsze wersje są na górze. Poniżej znajduje się "
            "cały dostępny CHANGELOG_PL.txt."
        )
        for line in self.full_changelog_lines():
            if line.strip():
                await self.send(line)

    async def show_help(self, topic=""):
        raw = topic.strip().lower()
        key = HELP_TOPIC_ALIASES.get(raw, raw)

        if not key:
            await self.send("POMOC GŁÓWNA")
            await self.send(
                "Użyj help <temat>. Tematy: podstawy, komendy, nawigacja, statystyki, "
                "walka, krytyki, bossowie, respawn, odpoczynek, dusza, pieniadze, ekwipunek, loot_krypty, zadania, profesje, wedkarstwo, "
                "gornictwo, drwalstwo, zielarstwo, alchemia, rzemioslo, gotowanie, receptury, atlas, "
                "charyzma, druzyny, multiclass, krypta, portale, zwloki, pojemniki, sklepy, gracze, smierc, rasy, klasy, "
                "umiejetnosci, nazwy_skilli, nauczyciele, opisy, zmiany."
            )
            await self.send("help tematy - lista tematów.")
            await self.send("help wszystko - pełny przewodnik.")
            await self.send("opis <nazwa> - szczegółowy opis dowolnego elementu.")
            await self.send("changes / zmiany / changelog - pełna historia wszystkich wersji i zmian, najnowsze na górze.")
            await self.send("Na start: look, exits, stats, inventory, quests, help podstawy.")
            return

        if key == "tematy":
            await self.send("TEMATY POMOCY")
            for name in HELP_TOPICS:
                await self.send(name)
            await self.send("Dodatkowo: komendy, wszystko.")
            return

        if key == "komendy":
            await self.send("WSZYSTKIE KOMENDY")
            for line in self.help_commands():
                await self.send(line)
            return

        if key == "wszystko":
            await self.send("PEŁNY PRZEWODNIK SOULBOUND")
            for name, lines in HELP_TOPICS.items():
                await self.send(name.upper())
                for line in lines:
                    await self.send(line)
            await self.send("KOMENDY")
            for line in self.help_commands():
                await self.send(line)
            return

        lines = HELP_TOPICS.get(key)
        if not lines:
            await self.send("Nie znam takiego tematu pomocy. Wpisz help tematy albo help komendy.")
            return

        await self.send("POMOC: " + key.upper())
        for line in lines:
            await self.send(line)



    def format_item_description(self, item_id, item):
        parts = [f"{item['name']}. Typ: {item.get('type', 'przedmiot')}.", item.get("desc", "")]

        if item.get("type") == "armor":
            parts.append(
                f"Slot: {EQUIPMENT_SLOT_NAMES.get(item.get('slot'), item.get('slot', 'brak'))}. "
                f"Obrona fizyczna: +{item.get('defense', 0)}."
            )
            if item.get("rarity_name"):
                parts.append(
                    f"Rzadkość: {item['rarity_name']}."
                )
            if item.get("required_class"):
                parts.append(
                    f"Wymagana aktywna klasa: "
                    f"{item['required_class']}."
                )
            if item.get("affix"):
                affix_name = CRYPT_AFFIXES.get(
                    item["affix"], item["affix"]
                )
                parts.append(
                    f"Losowy bonus: {affix_name} "
                    f"+{item.get('affix_amount', 0)}."
                )
            if item.get("crypt_set_tier"):
                parts.append(
                    f"Zestaw Krypty Tier "
                    f"{item['crypt_set_tier']}."
                )
        elif item.get("type") == "tool":
            tool = "Wędka" if item.get("tool_type") == "fishing" else "Kilof"
            parts.append(f"Narzędzie profesji: {tool}. Ma własny level 1-100 i osobny XP.")
        elif "heal" in item:
            parts.append(f"Leczenie: {item['heal']} HP.")
        elif "soul_xp" in item:
            parts.append(f"Po użyciu daje {item['soul_xp']} Soul XP.")

        if item.get("price") is not None:
            currency = item.get("currency", "gold")
            names = {"silver": "srebra", "gold": "złota", "mithril": "mithrilu"}
            parts.append(f"Cena kupna: {item['price']} {names.get(currency, currency)}.")

        sell_parts = []
        if item.get("sell_silver"):
            sell_parts.append(f"{item['sell_silver']} srebra")
        if item.get("sell_gold"):
            sell_parts.append(f"{item['sell_gold']} złota")
        if item.get("sell_mithril"):
            sell_parts.append(f"{item['sell_mithril']} mithrilu")
        if sell_parts:
            parts.append("Wartość sprzedaży: " + ", ".join(sell_parts) + ".")

        return " ".join(p for p in parts if p)

    def room_special_features(self, room_id):
        features = []
        if room_id in RIVER_FISHING_ROOMS:
            features.append("łowisko rzeczne")
        if room_id in LAKE_FISHING_ROOMS:
            features.append("łowisko jeziorowe")
        if room_id in SEA_FISHING_ROOMS:
            features.append("łowisko morskie")
        if room_id in OCEAN_FISHING_ROOMS:
            features.append("łowisko oceaniczne")
        if room_id in MINING_ROOMS:
            features.append("miejsce wydobycia")
            floor = mine_floor_number(room_id)
            if floor is not None:
                features.append(
                    f"Kopalnia Głębinowa poziom {floor} z "
                    f"{MINE_MAX_FLOOR}"
                )
        if room_id in SHOPS:
            features.append("sklep")
        if any(npc["room"] == room_id for npc in NPCS.values()):
            features.append("NPC")
        if any(spawn_room == room_id for spawn_room, _ in MOB_SPAWNS):
            features.append("przeciwnicy")
        return features

    def normalize_description_query(self, value):
        table = str.maketrans(
            "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ",
            "acelnoszzACELNOSZZ"
        )
        return value.strip().lower().translate(table)

    def find_description_entry(self, mapping, query, name_field="name"):
        q = self.normalize_description_query(query)
        if not q:
            return None
        exact = []
        partial = []
        for key, value in mapping.items():
            name = value[name_field] if isinstance(value, dict) else str(value)
            nk = self.normalize_description_query(str(key))
            nn = self.normalize_description_query(name)
            if q == nk or q == nn:
                exact.append((key, value))
            elif q in nk or q in nn:
                partial.append((key, value))
        if exact:
            return exact[0]
        if len(partial) == 1:
            return partial[0]
        return None

    def atlas_item_locations(self, item_id):
        item = ITEMS.get(item_id, {})
        item_id = item.get("base_resource_id", item_id)
        locations = []

        if item_id in RIVER_FISH_ATLAS:
            locations.extend(ROOMS[r]["name"] for r in sorted(RIVER_FISHING_ROOMS))
        if item_id in LAKE_FISH_ATLAS:
            locations.extend(ROOMS[r]["name"] for r in sorted(LAKE_FISHING_ROOMS))
        if item_id in SEA_FISH_ATLAS:
            locations.extend(ROOMS[r]["name"] for r in sorted(SEA_FISHING_ROOMS))
        if item_id in OCEAN_FISH_ATLAS:
            locations.extend(ROOMS[r]["name"] for r in sorted(OCEAN_FISHING_ROOMS))

        if item_id in WOOD_BEGINNER_ATLAS:
            locations.extend(
                ROOMS[r]["name"] for r in ("lumberjack_camp", "meadow")
            )
        if item_id in WOOD_FOREST_ATLAS:
            locations.extend(
                ROOMS[r]["name"] for r in ("whisper_grove", "old_road")
            )
        if item_id in WOOD_DEEP_ATLAS:
            locations.append(ROOMS["deep_grove"]["name"])

        if item_id in ORE_STORAGE_IDS:
            locations.extend((
                ROOMS["cave_entrance"]["name"],
                ROOMS["cave_tunnel"]["name"],
                ROOMS["crystal_chamber"]["name"],
            ))
            minimum_floor = ORE_MINE_FLOOR_MINIMUMS.get(
                item_id, 1
            )
            locations.append(
                f"Kopalnia Głębinowa od poziomu {minimum_floor}"
            )
        if item_id in HERB_MEADOW_ATLAS:
            locations.extend(
                ROOMS[r]["name"]
                for r in (
                    "herbalist_hut", "meadow", "mint_meadow",
                    "flower_meadow", "lakeside_meadow",
                )
            )
        if item_id in HERB_FOREST_ATLAS:
            locations.extend(ROOMS[r]["name"] for r in ("whisper_grove", "old_road"))
        if item_id in HERB_WATER_ATLAS:
            locations.extend(
                ROOMS[r]["name"]
                for r in ("riverbank", "lake_shore", "lakeside_meadow")
            )
        if item_id in HERB_DEEP_ATLAS:
            locations.append(ROOMS["deep_grove"]["name"])

        result = []
        seen = set()
        for value in locations:
            if value not in seen:
                seen.add(value)
                result.append(value)
        return result

    def atlas_names(self, item_ids):
        return ", ".join(
            sorted(
                (ITEMS[item_id]["name"] for item_id in item_ids),
                key=str.lower,
            )
        )

    async def send_complete_atlas_list(
        self, title, item_ids, chunk_size=20
    ):
        names = sorted(
            (ITEMS[item_id]["name"] for item_id in item_ids),
            key=self.normalize_description_query,
        )
        await self.send(
            f"{title}. Łącznie pozycji: {len(names)}."
        )
        if not names:
            await self.send("Brak pozycji.")
            return

        chunk_size = max(1, int(chunk_size))
        total_parts = (
            len(names) + chunk_size - 1
        ) // chunk_size

        for index in range(0, len(names), chunk_size):
            part = index // chunk_size + 1
            chunk = names[index:index + chunk_size]
            await self.send(
                f"Część {part} z {total_parts}: "
                + ", ".join(chunk)
                + "."
            )

    async def show_atlas(self, query=""):
        q = self.normalize_description_query(query)

        if not q:
            await self.send("ATLAS SUROWCÓW")
            await self.send("Działy: ryby, drewno, rudy, zioła.")
            await self.send(
                "Użycie: atlas ryby, atlas drewno, atlas rudy, "
                "atlas zioła, atlas rośliny albo atlas <nazwa surowca>."
            )
            await self.send(
                "Każdy dział pokazuje teraz pełny spis wszystkich "
                "zasobów istniejących w tej kategorii."
            )
            return

        if q in ("ryby", "fish", "wedkarstwo"):
            await self.send("ATLAS RYB")
            await self.send_complete_atlas_list(
                "WSZYSTKIE RYBY",
                FISH_ATLAS_ALL,
                chunk_size=20,
            )
            groups = (
                ("Rzeka", RIVER_FISHING_ROOMS, RIVER_FISH_ATLAS),
                ("Jezioro", LAKE_FISHING_ROOMS, LAKE_FISH_ATLAS),
                ("Morze", SEA_FISHING_ROOMS, SEA_FISH_ATLAS),
                ("Ocean", OCEAN_FISHING_ROOMS, OCEAN_FISH_ATLAS),
            )
            for title, rooms, items in groups:
                places = ", ".join(
                    ROOMS[r]["name"] for r in sorted(rooms)
                )
                await self.send(
                    f"{title}. Łowiska: {places}. "
                    f"Liczba gatunków w tej grupie: {len(items)}."
                )
                await self.send(
                    "Gatunki: "
                    + self.atlas_names(items)
                    + "."
                )
            return

        fish_groups = {
            "rzeka": ("Rzeka", RIVER_FISHING_ROOMS, RIVER_FISH_ATLAS),
            "river": ("Rzeka", RIVER_FISHING_ROOMS, RIVER_FISH_ATLAS),
            "jezioro": ("Jezioro", LAKE_FISHING_ROOMS, LAKE_FISH_ATLAS),
            "lake": ("Jezioro", LAKE_FISHING_ROOMS, LAKE_FISH_ATLAS),
            "morze": ("Morze", SEA_FISHING_ROOMS, SEA_FISH_ATLAS),
            "sea": ("Morze", SEA_FISHING_ROOMS, SEA_FISH_ATLAS),
            "ocean": ("Ocean", OCEAN_FISHING_ROOMS, OCEAN_FISH_ATLAS),
        }
        if q in fish_groups:
            title, rooms, items = fish_groups[q]
            await self.send(f"ATLAS: {title.upper()}")
            await self.send(
                "Łowiska: "
                + ", ".join(ROOMS[r]["name"] for r in sorted(rooms))
                + "."
            )
            await self.send("Gatunki: " + self.atlas_names(items) + ".")
            return

        if q in ("drewno", "wood", "drwalstwo"):
            await self.send("ATLAS DREWNA")
            await self.send_complete_atlas_list(
                "WSZYSTKIE DREWNA",
                WOOD_ATLAS_ALL,
                chunk_size=15,
            )
            await self.send(
                "Obóz Drwala i Srebrna Łąka: "
                + self.atlas_names(WOOD_BEGINNER_ATLAS)
                + "."
            )
            await self.send(
                "Gaj Szeptów i Stary Trakt: "
                + self.atlas_names(WOOD_FOREST_ATLAS)
                + "."
            )
            await self.send(
                "Głębia Gaju: "
                + self.atlas_names(WOOD_DEEP_ATLAS)
                + "."
            )
            return

        if q in ("rudy", "ruda", "ore", "gornictwo"):
            await self.send("ATLAS RUD")
            await self.send_complete_atlas_list(
                "WSZYSTKIE RUDY",
                ORE_ATLAS_ALL,
                chunk_size=20,
            )
            await self.send(
                "Miejsca wydobycia: Kryształowa Jaskinia oraz "
                f"Kopalnia Głębinowa poziomy 1-{MINE_MAX_FLOOR}."
            )
            for item_id in sorted(
                ORE_ATLAS_ALL,
                key=lambda value: (
                    ORE_MINE_FLOOR_MINIMUMS.get(value, 1),
                    self.normalize_description_query(
                        ITEMS[value]["name"]
                    ),
                ),
            ):
                minimum = ORE_ATLAS_LEVELS.get(item_id, 1)
                floor_min = ORE_MINE_FLOOR_MINIMUMS.get(
                    item_id, 1
                )
                await self.send(
                    f"{ITEMS[item_id]['name']}: około levelu "
                    f"{minimum} Kilofa; w Kopalni Głębinowej od "
                    f"poziomu {floor_min}."
                )
            await self.send(
                "Czysty mithril nie jest rudą w Sakwie. "
                "To bardzo rzadka waluta trafiająca bezpośrednio "
                "do portfela, możliwa od efektywnej głębokości "
                "i levelu Kilofa 80."
            )
            return

        if q in ("ziola", "zioła", "herbs", "herb", "zielarstwo", "rosliny", "rośliny", "plants"):
            await self.send("ATLAS ZIÓŁ I ROŚLIN")
            await self.send_complete_atlas_list(
                "WSZYSTKIE ZIOŁA I ROŚLINY",
                HERB_ATLAS_ALL,
                chunk_size=15,
            )
            await self.send(
                "Łąki i Chata Zielarki: "
                + self.atlas_names(HERB_MEADOW_ATLAS)
                + "."
            )
            await self.send(
                "Gaj Szeptów i Stary Trakt: "
                + self.atlas_names(HERB_FOREST_ATLAS)
                + "."
            )
            await self.send(
                "Brzeg Rzeki, Brzeg Srebrnego Jeziora i "
                "Łąka Nadjeziorna: "
                + self.atlas_names(HERB_WATER_ATLAS)
                + "."
            )
            await self.send(
                "Głębia Gaju i zioła endgame: "
                + self.atlas_names(HERB_DEEP_ATLAS)
                + "."
            )
            return

        resources = {
            item_id: ITEMS[item_id]
            for item_id in (
                FISH_STORAGE_IDS
                | ORE_STORAGE_IDS
                | WOOD_STORAGE_IDS
                | HERB_STORAGE_IDS
            )
        }
        found = find_by_name(resources, query)
        if not found:
            await self.send(
                "Atlas nie rozpoznaje tego surowca. "
                "Wpisz atlas ryby, atlas drewno albo atlas rudy."
            )
            return

        item_id, item = found
        await self.send(f"ATLAS: {item['name']}.")
        if item_id in FISH_STORAGE_IDS:
            await self.send("Typ: ryba. Trafia do Siatki na ryby.")
        elif item_id in WOOD_RESOURCE_IDS:
            await self.send("Typ: drewno. Trafia na Stos drewna.")
        elif item_id in HERB_RESOURCE_IDS:
            await self.send("Typ: zioło. Trafia do Torby Zielarskiej.")
        else:
            await self.send("Typ: ruda. Trafia do Sakwy górniczej.")

        places = self.atlas_item_locations(item_id)
        if places:
            await self.send("Występowanie: " + ", ".join(places) + ".")

        if item_id in ORE_ATLAS_LEVELS:
            await self.send(
                f"Orientacyjny minimalny level Kilofa: "
                f"{ORE_ATLAS_LEVELS[item_id]}."
            )

    def codex_boss_ids(self):
        result = set()
        for mob_id, mob in MOB_TEMPLATES.items():
            if (
                mob_id.startswith("crypt_boss_")
                or mob_id.startswith("astral_boss_")
                or mob_id.startswith("mythic_crypt_boss_")
                or mob_id.startswith("mythic_astral_boss_")
                or mob.get("world_boss")
                or mob.get("boss_mechanic")
            ):
                result.add(mob_id)
        return result

    def codex_relic_ids(self):
        result = set()
        for item_id, item in ITEMS.items():
            if (
                item.get("boss_relic_floor") is not None
                or item_id.startswith("astral_relic_")
                or item.get("rarity") == "unique"
            ):
                result.add(item_id)
        return result

    async def send_codex_name_list(
        self, title, names, chunk_size=20
    ):
        names = sorted(
            set(names),
            key=self.normalize_description_query,
        )
        await self.send(
            f"{title}. Łącznie: {len(names)}."
        )
        if not names:
            await self.send("Brak wpisów.")
            return

        chunk_size = max(1, int(chunk_size))
        total = (
            len(names) + chunk_size - 1
        ) // chunk_size
        for index in range(0, len(names), chunk_size):
            part = index // chunk_size + 1
            await self.send(
                f"Część {part} z {total}: "
                + ", ".join(
                    names[index:index + chunk_size]
                )
                + "."
            )

    async def show_world_codex(self, query=""):
        q = self.normalize_description_query(query)
        bosses = self.codex_boss_ids()
        normal_mobs = set(MOB_TEMPLATES) - bosses
        relics = self.codex_relic_ids()

        if not q:
            await self.send("CODEX ŚWIATA")
            await self.send(
                f"Ryby: {len(FISH_RESOURCE_IDS)} gatunków bazowych. "
                f"Rzadkie warianty ryb: "
                f"{len(RARE_FISH_VARIANT_IDS)}."
            )
            await self.send(
                f"Rośliny i zioła: {len(HERB_RESOURCE_IDS)} bazowych. "
                f"Rzadkie warianty roślin: "
                f"{len(RARE_HERB_VARIANT_IDS)}."
            )
            await self.send(
                f"Drewno: {len(WOOD_RESOURCE_IDS)} bazowych rodzajów. "
                f"Rzadkie warianty drewna: "
                f"{len(RARE_WOOD_VARIANT_IDS)}."
            )
            await self.send(
                f"Rudy i minerały: {len(ORE_RESOURCE_IDS)}. "
                f"Rodzaje żył: {len(MINING_VEINS)}."
            )
            await self.send(
                f"Zwykłe moby: {len(normal_mobs)}. "
                f"Bossowie: {len(bosses)}. "
                f"Relikty i unikalne trofea: {len(relics)}."
            )
            await self.send(
                "Działy: codex ryby, codex rośliny, codex drewno, "
                "codex rudy, codex warianty, codex moby, "
                "codex bossowie, codex relikty."
            )
            await self.send(
                "Możesz też wpisać codex <nazwa>, aby wyszukać "
                "konkretny zasób, mob, bossa albo relikt."
            )
            return

        if q in ("ryby", "ryba", "fish"):
            await self.send_complete_atlas_list(
                "CODEX RYB - GATUNKI BAZOWE",
                FISH_RESOURCE_IDS,
                chunk_size=20,
            )
            await self.send(
                "Rzadkie warianty każdego gatunku: "
                "Albinos x2 wartości, Złoty okaz x4, "
                "Olbrzymi okaz x3, Pradawny okaz x8."
            )
            await self.send(
                "Szansa na rzadki wariant rośnie wraz z levelem "
                "Wędki: około 8 do 12 procent."
            )
            return

        if q in (
            "rosliny", "rośliny", "ziola", "zioła",
            "herbs", "plants",
        ):
            await self.send_complete_atlas_list(
                "CODEX ROŚLIN I ZIÓŁ - BAZOWE",
                HERB_RESOURCE_IDS,
                chunk_size=20,
            )
            await self.send(
                "Rzadkie warianty: Bujna x2 wartości, "
                "Lśniąca x4, Pradawna x6, Legendarna x10."
            )
            await self.send(
                "Szansa na wariant rośnie z levelem Sierpa."
            )
            return

        if q in ("drewno", "wood", "drzewa", "drzewo"):
            await self.send_complete_atlas_list(
                "CODEX DREWNA - BAZOWE",
                WOOD_RESOURCE_IDS,
                chunk_size=20,
            )
            await self.send(
                "Rzadkie warianty drzew: Bujne x2 wartości, "
                "Pradawne x4, Kryształowe x6, Legendarne x10."
            )
            await self.send(
                "Szansa na wariant rośnie z levelem Piły."
            )
            return

        if q in ("rudy", "ruda", "ore", "mineral", "mineraly"):
            await self.send_complete_atlas_list(
                "CODEX RUD I MINERAŁÓW",
                ORE_RESOURCE_IDS,
                chunk_size=20,
            )
            await self.send(
                "Rodzaje żył: Zwykła x1, Bogata x2, "
                "Kryształowa x3, Legendarna x5 urobku."
            )
            await self.send(
                "Im wyższy level Kilofa, tym większa szansa na "
                "Bogate, Kryształowe i Legendarne żyły."
            )
            return

        if q in ("warianty", "rare", "rzadkie"):
            await self.send("CODEX RZADKICH WARIANTÓW")
            await self.send(
                "Ryby: Albinos, Złoty okaz, Olbrzymi okaz, "
                "Pradawny okaz."
            )
            await self.send(
                "Drzewa i drewno: Bujne, Pradawne, "
                "Kryształowe, Legendarne."
            )
            await self.send(
                "Rośliny: Bujna, Lśniąca, Pradawna, Legendarna."
            )
            await self.send(
                "Górnictwo: Zwykła, Bogata, Kryształowa "
                "i Legendarna żyła."
            )
            return

        if q in ("moby", "mob", "potwory", "przeciwnicy"):
            await self.send_codex_name_list(
                "CODEX MOBÓW",
                (
                    MOB_TEMPLATES[mob_id]["name"]
                    for mob_id in normal_mobs
                ),
                chunk_size=20,
            )
            return

        if q in ("bossowie", "boss", "bosses"):
            await self.send_codex_name_list(
                "CODEX BOSSÓW",
                (
                    MOB_TEMPLATES[mob_id]["name"]
                    for mob_id in bosses
                ),
                chunk_size=20,
            )
            return

        if q in ("relikty", "relikt", "relic", "relics"):
            await self.send_codex_name_list(
                "CODEX RELIKTÓW I TROFEÓW",
                (
                    ITEMS[item_id]["name"]
                    for item_id in relics
                ),
                chunk_size=20,
            )
            return

        searchable_items = {
            item_id: item
            for item_id, item in ITEMS.items()
            if (
                item_id in FISH_STORAGE_IDS
                or item_id in ORE_STORAGE_IDS
                or item_id in WOOD_STORAGE_IDS
                or item_id in HERB_STORAGE_IDS
                or item_id in relics
            )
        }
        found = find_by_name(searchable_items, query)
        if found:
            item_id, item = found
            await self.send(f"CODEX: {item['name']}.")
            await self.send(item.get("desc", "Brak opisu."))
            if item.get("rare_resource_variant"):
                base_id = item.get("base_resource_id")
                base_name = ITEMS.get(
                    base_id, {"name": base_id}
                )["name"]
                await self.send(
                    f"Rzadki wariant: "
                    f"{item.get('rare_resource_label')}. "
                    f"Bazowy zasób: {base_name}. "
                    f"Mnożnik wartości: x"
                    f"{item.get('rare_value_multiplier', 1)}."
                )
            places = self.atlas_item_locations(item_id)
            if places:
                await self.send(
                    "Występowanie: "
                    + ", ".join(places)
                    + "."
                )
            return

        found_mob = find_by_name(MOB_TEMPLATES, query)
        if found_mob:
            mob_id, mob = found_mob
            kind = (
                "boss"
                if mob_id in bosses
                else "zwykły mob"
            )
            dtype = (
                "magiczne"
                if mob.get("damage_type") == "magic"
                else "fizyczne"
            )
            await self.send(
                f"CODEX: {mob['name']}. Typ: {kind}."
            )
            await self.send(
                f"HP: {mob.get('max_hp', 0)}. "
                f"Bazowe obrażenia: {mob.get('damage', 0)}. "
                f"Typ obrażeń: {dtype}."
            )
            if mob.get("boss_mechanic_text"):
                await self.send(
                    "Mechanika: "
                    + mob["boss_mechanic_text"]
                )
            return

        await self.send(
            "Codex nie znalazł takiego wpisu. "
            "Wpisz codex bez argumentu, aby usłyszeć działy."
        )

    async def describe_target(self, query):
        q = query.strip()

        if not q:
            room = ROOMS[self.character.room_id]
            await self.send(f"{room['name']}. Strefa: {room['zone']}. {room['desc']}")
            features = self.room_special_features(self.character.room_id)
            if features:
                await self.send("Funkcje lokacji: " + ", ".join(features) + ".")
            await self.show_exits()
            return

        normalized = self.normalize_description_query(q)

        normalized_systems = {
            self.normalize_description_query(k): v
            for k, v in SYSTEM_DESCRIPTIONS.items()
        }
        normalized_stats = {
            self.normalize_description_query(k): v
            for k, v in STAT_DESCRIPTIONS.items()
        }
        if normalized in normalized_stats:
            await self.send(normalized_stats[normalized])
            return
        if normalized in normalized_systems:
            await self.send(normalized_systems[normalized])
            return

        found = self.find_description_entry(ITEMS, q)
        if found:
            item_id, item = found
            await self.send(self.format_item_description(item_id, item))
            return

        found = self.find_description_entry(NPCS, q)
        if found:
            npc_id, npc = found
            room = ROOMS[npc["room"]]
            desc = NPC_DESCRIPTIONS.get(npc_id, npc.get("dialogue", ""))
            await self.send(f"{npc['name']}. {desc}")
            await self.send(f"Stała lokacja: {room['name']}.")
            if npc.get("quest"):
                quest = QUESTS[npc["quest"]]
                await self.send(f"Powiązane zadanie: {quest['name']}. {quest['description']}")
            return

        found = self.find_description_entry(MOB_TEMPLATES, q)
        if found:
            mob_id, mob = found
            dtype = "magiczne" if mob.get("damage_type") == "magic" else "fizyczne"
            await self.send(f"{mob['name']}. {MOB_DESCRIPTIONS.get(mob_id, '')}")
            await self.send(
                f"HP: {mob['max_hp']}. Bazowe obrażenia: {mob['damage']}. Typ obrażeń: {dtype}."
            )
            await self.send(
                f"Nagroda podstawowa: {mob.get('silver',0)} srebra, "
                f"{mob.get('gold',0)} złota, {mob.get('mithril',0)} mithrilu; "
                f"Rozwój statystyk +{mob.get('stat_reward',0)}; "
                f"Soul XP +{mob.get('soul_reward',0)}."
            )
            drops = []
            for item_id, chance in mob.get("drops", {}).items():
                item = ITEMS.get(item_id, {"name": item_id})
                drops.append(f"{item['name']} około {int(chance * 100)} procent")
            if drops:
                await self.send("Możliwe dropy: " + ", ".join(drops) + ".")
            return

        found = self.find_description_entry(ROOMS, q)
        if found:
            room_id, room = found
            await self.send(f"{room['name']}. Strefa: {room['zone']}. {room['desc']}")
            exits = ", ".join(room["exits"].keys()) if room["exits"] else "brak"
            await self.send("Wyjścia: " + exits + ".")
            features = self.room_special_features(room_id)
            if features:
                await self.send("Funkcje lokacji: " + ", ".join(features) + ".")
            return

        found = self.find_description_entry(QUESTS, q)
        if found:
            quest_id, quest = found
            await self.send(
                f"Zadanie: {quest['name']}. Zleca: {quest['giver']}. {quest['description']}"
            )
            rewards = []
            if quest.get("reward_stat_progress"):
                rewards.append(f"{quest['reward_stat_progress']} EXP rozwoju")
            if quest.get("reward_profession_xp"):
                rewards.append(
                    f"{quest['reward_profession_xp']} XP profesji {quest.get('reward_profession','')}"
                )
            if quest.get("reward_tool_xp"):
                tool = "Wędki" if quest.get("reward_tool_type") == "fishing" else "Kilofa"
                rewards.append(f"{quest['reward_tool_xp']} XP {tool}")
            if quest.get("reward_silver"):
                rewards.append(f"{quest['reward_silver']} srebra")
            if quest.get("reward_gold"):
                rewards.append(f"{quest['reward_gold']} złota")
            if quest.get("reward_mithril"):
                rewards.append(f"{quest['reward_mithril']} mithrilu")
            for item_id, qty in quest.get("reward_items", {}).items():
                rewards.append(f"{ITEMS.get(item_id, {'name': item_id})['name']} x{qty}")
            if rewards:
                await self.send("Nagrody: " + ", ".join(rewards) + ".")
            return

        race_map = {
            race[0]: {
                "name": race[0], "desc": race[1],
                "strength": race[2], "dexterity": race[3],
                "constitution": race[4], "intelligence": race[5],
                "willpower": race[6],
            }
            for race in RACES
        }
        found = self.find_description_entry(race_map, q)
        if found:
            _, race = found
            await self.send(f"Rasa: {race['name']}. {race['desc']}")
            await self.send(
                f"Startowe statystyki: Siła {race['strength']}, "
                f"Zręczność {race['dexterity']}, Kondycja {race['constitution']}, "
                f"Inteligencja {race['intelligence']}, Siła Woli {race['willpower']}."
            )
            return

        class_map = {
            cls[0]: {"name": cls[0], "type": cls[1], "weapon": cls[2], "base": cls[3]}
            for cls in CLASSES
        }
        found = self.find_description_entry(class_map, q)
        if found:
            _, cls = found
            kind = "fizyczna" if cls["type"] == "physical" else "magiczna"
            await self.send(
                f"Klasa: {cls['name']}. Typ: {kind}. {CLASS_DESCRIPTIONS.get(cls['name'], '')}"
            )
            await self.send(
                f"Broń Duszy: {cls['weapon']}. Bazowa moc Broni Duszy: {cls['base']}."
            )
            await self.send("Rozwój klasy: wszystkie pięć statystyk rośnie automatycznie.")
            skills = CLASS_SKILLS.get(cls["name"], [])
            if skills:
                await self.send(
                    "Umiejętności: " + "; ".join(
                        f"{s['name']} do nauki od Soul Level {s['unlock']}" for s in skills
                    ) + "."
                )
            return

        help_key = HELP_TOPIC_ALIASES.get(normalized, normalized)
        if help_key in HELP_TOPICS:
            await self.show_help(help_key)
            return

        await self.send(
            "Nie znalazłem takiego opisu. Spróbuj dokładniejszej nazwy albo wpisz help opisy."
        )


    async def show_name_declension(self):
        await self.send(f"ODMIANA IMIENIA: {self.character.name_nom}")
        await self.send(f"Mianownik: {self.character.name_nom}.")
        await self.send(f"Dopełniacz: {self.character.name_gen}.")
        await self.send(f"Celownik: {self.character.name_dat}.")
        await self.send(f"Biernik: {self.character.name_acc}.")
        await self.send(f"Narzędnik: {self.character.name_ins}.")
        await self.send(f"Miejscownik: {self.character.name_loc}.")
        await self.send(f"Wołacz: {self.character.name_voc}.")

    async def show_stats(self):
        c = self.character
        active_classes = self.active_class_names()
        await self.send(
            f"{c.name}. Rasa: {c.race}. Klasa główna: {c.class_name}. "
            f"Aktywne klasy: {', '.join(active_classes)}."
        )
        await self.send("Poziom postaci: nie istnieje.")
        bonuses = self.equipment_bonus_totals()
        await self.send(
            f"Statystyki bazowe: Siła {c.strength}, Zręczność {c.dexterity}, "
            f"Kondycja {c.constitution}, Inteligencja {c.intelligence}, "
            f"Siła Woli {c.willpower}."
        )
        await self.send(
            f"Z wyposażeniem: Siła {self.effective_strength()}, "
            f"Zręczność {self.effective_dexterity()}, "
            f"Kondycja {self.effective_constitution()}, "
            f"Inteligencja {self.effective_intelligence()}, "
            f"Siła Woli {self.effective_willpower()}."
        )
        if any(bonuses.values()):
            await self.send(
                "Bonusy ekwipunku: "
                f"Siła +{bonuses['strength']}, "
                f"Zręczność +{bonuses['dexterity']}, "
                f"Kondycja +{bonuses['constitution']}, "
                f"Inteligencja +{bonuses['intelligence']}, "
                f"Siła Woli +{bonuses['willpower']}, "
                f"HP +{bonuses['hp']}, Mana +{bonuses['mana']}."
            )
        await self.send(f"Rozwój statystyk: {c.stat_progress} z {STAT_GROWTH_THRESHOLD}.")
        await self.send(
            f"Życie: {self.current_hp} z {self.max_hp()}. "
            f"Mana: {self.current_mana} z {self.max_mana()}. "
            f"Obrona fizyczna: {self.defense()}. "
            f"Obrona magiczna: {self.magic_defense()}."
        )
        await self.send(
            f"Siła ataku fizycznego: {self.physical_power()}. "
            f"Szybkość: {self.speed()}. "
            f"Unik: {int(self.dodge_chance() * 100)} procent. "
            f"Krytyk: {int(round(self.critical_chance() * 100))} procent. "
            f"Mnożnik krytyka: "
            f"{int(self.critical_multiplier() * 100)} procent."
        )
        await self.send(
            f"Pasyw rasy {c.race}: {c.racial_passive_text()}."
        )
        for class_name in active_classes:
            await self.send(
                f"Pasyw klasy {class_name}: "
                f"{c.class_passive_text_for(class_name)}."
            )
        await self.send(
            f"Bonus klasowy Broni Duszy klasy głównej: "
            f"{c.soul_weapon_class_bonus_text()}."
        )
        if self.max_mana() > 0:
            await self.send(
                f"Moc czarów: {self.spell_power()}."
            )
        await self.send(self.crypt_set_bonus_text())
        await self.send(self.astral_set_bonus_text())
        await self.send(
            f"Waluta: {c.silver} srebrnych monet, {c.gold} złotych monet, {c.mithril} mithrilowych monet. "
            f"Śmierci: {c.deaths}."
        )
        await self.send(
            f"Charyzma handlowa: {c.charisma}. "
            f"Rabat: {c.shop_discount_percent()} procent. "
            f"Limit drużyny jako lider: {c.party_capacity()}."
        )

    async def show_soul(self):
        c = self.character
        await self.send(f"Broń Duszy: {c.soul_weapon}.")
        await self.send(
            f"Soul Level: {c.soul_level} z {SOUL_MAX_LEVEL}. "
            f"Tier: {c.soul_tier} z {SOUL_MAX_TIER}."
        )
        if c.soul_level < SOUL_MAX_LEVEL:
            await self.send(
                f"Soul XP: {c.soul_xp} z {c.soul_xp_to_next()}. "
                f"Mnożnik wymaganego XP dla tego bloku: "
                f"x{c.soul_xp_multiplier()}."
            )
        await self.send(f"Moc Broni Duszy: {c.soul_power()}.")
        await self.send(
            f"Bonus klasowy Broni Duszy: {c.soul_weapon_class_bonus_text()}."
        )
        nxt = c.can_unlock()
        if nxt:
            if self.soul_tier_quest_completed(nxt):
                await self.send(
                    f"Tier {nxt}: wymagany Soul Level i Próba Broni Duszy "
                    "ukończone. Wpisz unlock."
                )
            else:
                await self.send(
                    f"Tier {nxt}: wymagany Soul Level osiągnięty. "
                    "Idź do Kapłana Elora w Świątyni Odrodzenia "
                    "i ukończ Próbę Broni Duszy."
                )
        elif c.soul_tier == 1:
            await self.send(
                f"Tier 2 wymaga Soul Level {TIER2_LEVEL} oraz Próby "
                "Broni Duszy w Świątyni Odrodzenia."
            )
        elif c.soul_tier == 2:
            await self.send(
                f"Tier 3 wymaga Soul Level {TIER3_LEVEL} oraz Próby "
                "Broni Duszy w Świątyni Odrodzenia."
            )
        elif c.soul_tier == 3:
            await self.send(
                f"Tier 4 wymaga Soul Level {TIER4_LEVEL} oraz Próby "
                "na bossie piętra 120 Krypty."
            )
        elif c.soul_tier == 4:
            await self.send(
                f"Tier 5 wymaga Soul Level {TIER5_LEVEL} oraz Próby "
                "na bossie piętra 180 Krypty."
            )

    async def move(self, direction):
        if self.resting or self.rest_task:
            await self.stop_rest(
                announce=True, reason="ruszasz się"
            )
        if self.auto_fishing or self.auto_fishing_task:
            await self.stop_auto_fishing(announce=False)
            await self.send("Auto-łowienie wyłączone z powodu ruchu.")
        if self.auto_mining or self.auto_mining_task:
            await self.stop_auto_mining(announce=False)
            await self.send("Auto-kopanie wyłączone z powodu ruchu.")
        if self.auto_woodcutting or self.auto_woodcutting_task:
            await self.stop_auto_woodcutting(announce=False)
            await self.send("Auto-Drwalstwo wyłączone z powodu ruchu.")
        if self.auto_herbalism or self.auto_herbalism_task:
            await self.stop_auto_herbalism(announce=False)
            await self.send("Auto-Zielarstwo wyłączone z powodu ruchu.")
        if self.combat_mob_key:
            await self.send("Jesteś w walce. Najpierw użyj flee albo pokonaj przeciwnika.")
            return
        target = ROOMS[self.character.room_id]["exits"].get(direction)
        if not target:
            await self.send("Nie możesz iść w tym kierunku.")
            return
        mythic_error = self.mythic_entry_error(target)
        if mythic_error:
            await self.send(mythic_error)
            return

        profession_error = self.profession_dungeon_access_error(
            target
        )
        if profession_error:
            await self.send(profession_error)
            return

        if self.astral_entry_blocked(target):
            await self.send(
                f"Wieża Astralna wymaga Soul Level "
                f"{ASTRAL_MIN_SOUL_LEVEL}. "
                f"Masz Soul Level {self.character.soul_level}."
            )
            return
        if self.mine_descent_blocked_for_player(
            self.character.room_id, direction
        ):
            progress = self.mine_progress()
            floor = mine_floor_number(
                self.character.room_id
            )
            required_hits = mine_wall_hits_required(
                floor if floor is not None else MINE_MIN_FLOOR
            )
            await self.send(
                f"Nie możesz zejść niżej. Ściana kopalni nie jest "
                f"przebita. Postęp: {progress['wall_hits']} z "
                f"{required_hits}. Użyj kop albo kop on."
            )
            return
        if self.mythic_crypt_descent_blocked_for_player(
            self.character.room_id, direction
        ):
            boss = self.server.world.live_mythic_crypt_boss(
                self.character.room_id
            )
            boss_name = (
                MOB_TEMPLATES[boss.template_id]["name"]
                if boss else "mityczny boss Krypty"
            )
            await self.send(
                f"Nie możesz zejść niżej. Drogę blokuje "
                f"{boss_name}."
            )
            return

        if self.mythic_astral_ascent_blocked_for_player(
            self.character.room_id, direction
        ):
            boss = self.server.world.live_mythic_astral_boss(
                self.character.room_id
            )
            boss_name = (
                MOB_TEMPLATES[boss.template_id]["name"]
                if boss else "mityczny boss Wieży Astralnej"
            )
            await self.send(
                f"Nie możesz wejść wyżej. Drogę blokuje "
                f"{boss_name}."
            )
            return

        if self.giant_fortress_ascent_blocked_for_player(
            self.character.room_id, direction
        ):
            boss = self.server.world.live_giant_fortress_boss(
                self.character.room_id
            )
            boss_name = (
                MOB_TEMPLATES[boss.template_id]["name"]
                if boss
                else "boss Twierdzy Gigantów"
            )
            await self.send(
                f"Nie możesz wejść wyżej. Drogę blokuje "
                f"{boss_name}. Najpierw pokonaj bossa."
            )
            return

        if self.crypt_descent_blocked_for_player(
            self.character.room_id, direction
        ):
            boss = self.server.world.live_crypt_boss(
                self.character.room_id
            )
            boss_name = (
                MOB_TEMPLATES[boss.template_id]["name"]
                if boss else "boss Krypty"
            )
            await self.send(
                f"Nie możesz zejść niżej. Drogę blokuje {boss_name}. "
                "Najpierw pokonaj bossa."
            )
            return
        if self.astral_ascent_blocked_for_player(
            self.character.room_id, direction
        ):
            boss = self.server.world.live_astral_boss(
                self.character.room_id
            )
            boss_name = (
                MOB_TEMPLATES[boss.template_id]["name"]
                if boss else "boss Wieży Astralnej"
            )
            await self.send(
                f"Nie możesz wejść wyżej. Drogę blokuje {boss_name}. "
                "Najpierw pokonaj bossa."
            )
            return
        old = self.character.room_id
        await self.server.broadcast_room(old, f"{self.character.name} odchodzi.", exclude=self)
        self.character.room_id = target
        self.server.db.save_character(self.character)
        await self.server.broadcast_room(target, f"{self.character.name} przychodzi.", exclude=self)
        await self.look()

    def party_key(self):
        return self.server.party_key_for_account(self.account_id)

    async def show_party(self):
        key = self.party_key()
        if key is None:
            await self.send("Nie należysz do drużyny.")
            await self.send(
                f"Twój limit jako przyszłego lidera: "
                f"{self.character.party_capacity()} osób."
            )
            return

        leader = self.server.session_by_account(key)
        leader_name = leader.character.name if leader else f"konto {key}"
        capacity = (
            leader.character.party_capacity()
            if leader else PARTY_BASE_CAPACITY
        )
        members = sorted(
            self.server.party_sessions(self.account_id),
            key=lambda s: s.character.name.lower(),
        )
        await self.send(
            f"DRUŻYNA. Lider: {leader_name}. "
            f"Członkowie: {len(members)} z {capacity}."
        )
        for number, session in enumerate(members, 1):
            marker = " Lider." if session.account_id == key else ""
            await self.send(
                f"{number}. {session.character.name}. "
                f"Lokacja: {ROOMS[session.character.room_id]['name']}.{marker}"
            )

    async def leave_party(self, announce=True):
        key = self.party_key()
        if key is None:
            if announce:
                await self.send("Nie należysz do drużyny.")
            return False

        members = self.server.parties.get(key, set())
        members.discard(self.account_id)

        if self.account_id == key:
            if members:
                candidates = [
                    self.server.session_by_account(member_id)
                    for member_id in members
                ]
                candidates = [s for s in candidates if s]
                if candidates:
                    new_leader = sorted(
                        candidates,
                        key=lambda s: s.character.name.lower(),
                    )[0]
                    self.server.parties[new_leader.account_id] = set(members)
                    self.server.parties.pop(key, None)
                    await self.server.party_broadcast(
                        new_leader.account_id,
                        f"{new_leader.character.name} zostaje nowym liderem drużyny."
                    )
                else:
                    self.server.parties.pop(key, None)
            else:
                self.server.parties.pop(key, None)
        else:
            self.server.parties[key] = members
            await self.server.party_broadcast(
                key,
                f"{self.character.name} opuszcza drużynę.",
                exclude=self,
            )

        for target_id, leader_id in list(self.server.party_invites.items()):
            if target_id == self.account_id or leader_id == self.account_id:
                self.server.party_invites.pop(target_id, None)

        if announce:
            await self.send("Opuszczasz drużynę.")
        return True

    async def disband_party(self):
        key = self.party_key()
        if key is None:
            await self.send("Nie należysz do drużyny.")
            return
        if key != self.account_id:
            await self.send("Tylko lider może rozwiązać drużynę.")
            return

        members = list(self.server.parties.get(key, set()))
        for member_id in members:
            session = self.server.session_by_account(member_id)
            if session:
                await session.send(
                    "Drużyna została rozwiązana przez lidera."
                )
        self.server.parties.pop(key, None)
        for target_id, leader_id in list(self.server.party_invites.items()):
            if leader_id == key:
                self.server.party_invites.pop(target_id, None)

    async def party_invite(self, name):
        target = self.server.find_character_session(name.strip())
        if not target:
            await self.send("Ten gracz nie jest online.")
            return
        if target is self:
            await self.send("Nie możesz zaprosić samego siebie.")
            return
        if self.server.party_key_for_account(target.account_id) is not None:
            await self.send("Ten gracz już należy do drużyny.")
            return

        key = self.party_key()
        if key is None:
            key = self.account_id
            self.server.parties[key] = {self.account_id}
        elif key != self.account_id:
            await self.send("Tylko lider drużyny może zapraszać.")
            return

        capacity = self.character.party_capacity()
        if len(self.server.parties[key]) >= capacity:
            await self.send(
                f"Drużyna jest pełna. Limit lidera: {capacity} osób."
            )
            return

        self.server.party_invites[target.account_id] = key
        await target.send(
            f"{self.character.name} zaprasza cię do drużyny. "
            f"Wpisz druzyna dolacz albo druzyna odrzuc."
        )
        await self.send(
            f"Zapraszasz {target.character.name} do drużyny."
        )

    async def party_accept(self):
        leader_id = self.server.party_invites.get(self.account_id)
        if leader_id is None:
            await self.send("Nie masz aktywnego zaproszenia do drużyny.")
            return

        leader = self.server.session_by_account(leader_id)
        members = self.server.parties.get(leader_id)
        if not leader or members is None:
            self.server.party_invites.pop(self.account_id, None)
            await self.send("Ta drużyna nie jest już dostępna.")
            return
        if self.party_key() is not None:
            self.server.party_invites.pop(self.account_id, None)
            await self.send("Już należysz do drużyny.")
            return

        capacity = leader.character.party_capacity()
        if len(members) >= capacity:
            self.server.party_invites.pop(self.account_id, None)
            await self.send("Drużyna osiągnęła limit lidera.")
            return

        members.add(self.account_id)
        self.server.party_invites.pop(self.account_id, None)
        await self.server.party_broadcast(
            leader_id,
            f"{self.character.name} dołącza do drużyny."
        )

    async def party_decline(self):
        leader_id = self.server.party_invites.pop(self.account_id, None)
        if leader_id is None:
            await self.send("Nie masz aktywnego zaproszenia.")
            return
        leader = self.server.session_by_account(leader_id)
        if leader:
            await leader.send(
                f"{self.character.name} odrzuca zaproszenie do drużyny."
            )
        await self.send("Odrzucasz zaproszenie do drużyny.")

    async def party_kick(self, name):
        key = self.party_key()
        if key is None:
            await self.send("Nie należysz do drużyny.")
            return
        if key != self.account_id:
            await self.send("Tylko lider może wyrzucać członków.")
            return

        target = self.server.find_character_session(name.strip())
        if not target or target.account_id not in self.server.parties[key]:
            await self.send("Nie ma takiego członka w twojej drużynie.")
            return
        if target is self:
            await self.send(
                "Lider używa druzyna opusc albo druzyna rozwiaz."
            )
            return

        self.server.parties[key].discard(target.account_id)
        await target.send(
            f"{self.character.name} usuwa cię z drużyny."
        )
        await self.server.party_broadcast(
            key,
            f"{target.character.name} zostaje usunięty z drużyny.",
            exclude=target,
        )

    async def party_chat(self, message):
        if not message.strip():
            await self.send("Użycie: pc <tekst>.")
            return
        if self.party_key() is None:
            await self.send("Nie należysz do drużyny.")
            return
        await self.server.party_broadcast(
            self.account_id,
            f"[Drużyna] {self.character.name}: {message.strip()}"
        )

    async def assist_party_member(self, name):
        name = str(name or "").strip()

        if not name:
            await self.send(
                "Użycie: wspieraj <gracz> albo assist <gracz>."
            )
            return False

        if self.party_key() is None:
            await self.send(
                "Nie należysz do drużyny."
            )
            return False

        target = self.server.find_character_session(name)
        if not target:
            await self.send(
                "Ten gracz nie jest online."
            )
            return False

        if target is self:
            await self.send(
                "Nie możesz wspierać samego siebie."
            )
            return False

        if not self.server.same_party(
            self.account_id,
            target.account_id,
        ):
            await self.send(
                f"{target.character.name} nie należy do twojej drużyny."
            )
            return False

        if (
            target.character.room_id
            != self.character.room_id
        ):
            await self.send(
                f"{target.character.name} nie jest w tej samej lokacji."
            )
            return False

        target_mob_key = target.combat_mob_key
        if not target_mob_key:
            await self.send(
                f"{target.character.name} z nikim teraz nie walczy."
            )
            return False

        mob = self.server.world.mobs.get(
            target_mob_key
        )
        if (
            not mob
            or not mob.alive
            or mob.room_id != self.character.room_id
        ):
            await self.send(
                "Cel walki tego gracza nie jest już dostępny."
            )
            return False

        if (
            self.combat_mob_key
            and self.combat_mob_key != mob.key
        ):
            current = self.server.world.mobs.get(
                self.combat_mob_key
            )
            current_name = (
                MOB_TEMPLATES[current.template_id]["name"]
                if current and current.alive
                else "inny przeciwnik"
            )
            await self.send(
                f"Już walczysz z: {current_name}. "
                "Najpierw zakończ tę walkę albo użyj flee."
            )
            return False

        if self.combat_mob_key == mob.key:
            await self.send(
                f"Już wspierasz {target.character.name} "
                f"przeciw {MOB_TEMPLATES[mob.template_id]['name']}."
            )
            return False

        if not self.server.engagement_allowed(
            self,
            mob,
        ):
            await self.send(
                "Nie możesz dołączyć do tej walki."
            )
            return False

        self.combat_mob_key = mob.key

        mob_name = MOB_TEMPLATES[
            mob.template_id
        ]["name"]

        await self.send(
            f"Wspierasz {target.character.name} "
            f"przeciw {mob_name}."
        )

        await self.server.broadcast_room(
            self.character.room_id,
            f"{self.character.name} wspiera "
            f"{target.character.name} przeciw {mob_name}.",
            exclude=self,
        )

        await self.attack("")
        return True

    async def handle_party(self, args):
        parts = args.strip().split(maxsplit=1)
        if not parts:
            await self.show_party()
            return

        action = self.normalize_description_query(parts[0])
        value = parts[1] if len(parts) > 1 else ""

        if action in ("status", "lista", "list", "sklad"):
            await self.show_party()
        elif action in ("zapros", "invite"):
            if not value:
                await self.send("Użycie: druzyna zapros <gracz>.")
            else:
                await self.party_invite(value)
        elif action in ("dolacz", "accept"):
            await self.party_accept()
        elif action in ("odrzuc", "decline"):
            await self.party_decline()
        elif action in ("opusc", "leave"):
            await self.leave_party(announce=True)
        elif action in ("wyrzuc", "kick"):
            if not value:
                await self.send("Użycie: druzyna wyrzuc <gracz>.")
            else:
                await self.party_kick(value)
        elif action in ("rozwiaz", "disband"):
            await self.disband_party()
        elif action in ("wspieraj", "assist", "pomagaj"):
            if not value:
                await self.send(
                    "Użycie: druzyna wspieraj <gracz>."
                )
            else:
                await self.assist_party_member(value)
        elif action in ("limit", "capacity"):
            key = self.party_key()
            leader = self.server.session_by_account(key) if key else self
            leader = leader or self
            await self.send(
                f"Limit drużyny: {leader.character.party_capacity()} osób. "
                f"Startowo 8; +1 miejsce co 25 Charyzmy lidera."
            )
        else:
            await self.send(
                "Drużyna: status, zapros <gracz>, dolacz, odrzuc, "
                "opusc, wyrzuc <gracz>, rozwiaz, wspieraj <gracz>, "
                "limit. Czat: pc <tekst>."
            )

    def exp_area_recommended(self, area):
        soul_level = int(self.character.soul_level)
        return (
            int(area["soul_min"])
            <= soul_level
            <= int(area["soul_max"])
        )

    def find_exp_area(self, query):
        wanted = self.normalize_description_query(query)
        if not wanted:
            return None

        exact = []
        partial = []

        for area in EXP_AREAS:
            names = (
                area["id"],
                area["name"],
                *area.get("aliases", ()),
            )
            normalized = {
                self.normalize_description_query(name)
                for name in names
            }

            if wanted in normalized:
                exact.append(area)
            elif any(
                wanted in name
                for name in normalized
            ):
                partial.append(area)

        if exact:
            return exact[0]
        if len(partial) == 1:
            return partial[0]
        return None

    def exp_area_soul_text(self, area):
        minimum = int(area["soul_min"])
        maximum = int(area["soul_max"])

        if minimum == maximum:
            return f"orientacyjnie Soul Level {minimum}"
        return (
            f"orientacyjnie Soul Level "
            f"{minimum}-{maximum}"
        )

    async def show_exp_area_details(self, area):
        recommended = (
            " Polecane dla ciebie."
            if self.exp_area_recommended(area)
            else ""
        )

        await self.send(
            f"{area['name']}. "
            f"{self.exp_area_soul_text(area)}. "
            f"Trudność: {area['difficulty']}."
            f"{recommended}"
        )
        await self.send(
            f"Opis: {area['description']}"
        )
        await self.send(
            f"Przeciwnicy: {area['enemies']}."
        )
        await self.send(
            f"Uwagi: {area['note']}"
        )
        await self.send(
            f"Prowadzenie: prowadz {area['guide']}."
        )

    async def show_exp_areas(self, query=""):
        query = str(query or "").strip()
        normalized = (
            self.normalize_description_query(query)
            if query
            else ""
        )

        if normalized in {
            "polecane", "recommended", "dla mnie",
        }:
            areas = [
                area
                for area in EXP_AREAS
                if self.exp_area_recommended(area)
            ]
            await self.send(
                f"POLECANE EXPOWISKA. "
                f"Twój Soul Level: "
                f"{self.character.soul_level}."
            )
            if not areas:
                await self.send(
                    "Brak terenu dokładnie w twoim "
                    "orientacyjnym zakresie. "
                    "Wpisz expowiska, aby zobaczyć wszystko."
                )
                return
            for area in areas:
                await self.send(
                    f"{area['name']}. "
                    f"{self.exp_area_soul_text(area)}. "
                    f"{area['description']}"
                )
            return

        if query:
            area = self.find_exp_area(query)
            if not area:
                await self.send(
                    "Nie rozpoznaję expowiska. "
                    "Wpisz expowiska, aby usłyszeć pełną listę."
                )
                return
            await self.show_exp_area_details(area)
            return

        await self.send(
            f"EXPOWISKA. Twój Soul Level: "
            f"{self.character.soul_level}."
        )
        await self.send(
            "Zakres Soul Level jest wskazówką, "
            "nie wymaganiem. Trudność zależy też "
            "od statów, klasy i wyposażenia."
        )

        for number, area in enumerate(
            EXP_AREAS,
            1,
        ):
            marker = (
                " Polecane dla ciebie."
                if self.exp_area_recommended(area)
                else ""
            )
            await self.send(
                f"{number}. {area['name']}. "
                f"{self.exp_area_soul_text(area)}. "
                f"Trudność: {area['difficulty']}. "
                f"{area['description']}"
                f"{marker}"
            )

        await self.send(
            "Szczegóły: expowiska nazwa. "
            "Tylko polecane: expowiska polecane."
        )

    async def who(self):
        online = [
            session
            for session in self.server.sessions
            if session.character
        ]
        online.sort(
            key=lambda session: session.character.name.lower()
        )

        await self.send(
            f"Gracze online: {len(online)}."
        )

        if not online:
            return

        for session in online:
            character = session.character
            room = ROOMS.get(
                character.room_id,
                {
                    "name": character.room_id,
                    "zone": "Nieznana strefa",
                },
            )

            classes = character.active_class_names()
            class_text = (
                ", ".join(classes)
                if classes
                else character.class_name
            )

            await self.send(
                f"{character.name}. "
                f"Klasa: {class_text}. "
                f"Soul Level {character.soul_level}. "
                f"Lokalizacja: {room['name']}. "
                f"Strefa: {room['zone']}."
            )

    async def say(self, text):
        message = str(text or "").strip()

        if not message:
            await self.send("Użycie: say tekst")
            return

        if len(message) > 500:
            message = message[:500]
            await self.send(
                "Wiadomość skrócono do 500 znaków."
            )

        await self.send(
            f"Mówisz: {message}"
        )
        await self.server.broadcast_room(
            self.character.room_id,
            f"{self.character.name} mówi: {message}",
            exclude=self,
        )

    async def tell(self, args):
        parts = args.split(maxsplit=1)
        if len(parts) != 2:
            await self.send("Użycie: tell gracz tekst")
            return
        target = self.server.find_character_session(parts[0])
        if not target:
            await self.send("Ten gracz nie jest online.")
            return
        await target.send(f"{self.character.name} mówi ci prywatnie: {parts[1]}")
        await self.send(f"Do {target.character.name}: {parts[1]}")

    def shop_item_base_value_silver(self, item):
        price = int(item.get("price") or 0)
        currency = item.get("currency", "gold")
        if currency == "silver":
            return price
        if currency == "gold":
            return price * SILVER_PER_GOLD
        if currency == "mithril":
            return price * GOLD_PER_MITHRIL * SILVER_PER_GOLD
        return 0

    def shop_cashback_silver(self, item):
        base = self.shop_item_base_value_silver(item)
        return (base * self.character.shop_discount_percent()) // 100

    async def show_charisma(self):
        c = self.character
        await self.send(f"Charyzma handlowa: {c.charisma}.")
        await self.send(
            f"Rabat sklepowy: {c.shop_discount_percent()} procent "
            f"z maksymalnych {CHARISMA_MAX_DISCOUNT} procent."
        )
        if c.shop_discount_percent() < CHARISMA_MAX_DISCOUNT:
            await self.send(
                f"Do następnego 1 procent rabatu: "
                f"{c.charisma_to_next_discount()} Charyzmy."
            )
        else:
            await self.send("Rabat sklepowy osiągnął maksimum.")
        await self.send(
            f"Limit drużyny jako lider: {c.party_capacity()} osób."
        )
        await self.send(
            f"Do następnego miejsca w drużynie: "
            f"{c.charisma_to_next_party_slot()} Charyzmy."
        )
        await self.send(
            "Każda udana sprzedaż surowca zwiększa Charyzmę o 1."
        )

    async def gain_charisma_from_sale(self):
        old_discount = self.character.shop_discount_percent()
        old_capacity = self.character.party_capacity()
        self.character.charisma += 1
        await self.send(
            f"Charyzma handlowa +1. Masz teraz {self.character.charisma}."
        )
        new_discount = self.character.shop_discount_percent()
        new_capacity = self.character.party_capacity()
        if new_discount > old_discount:
            await self.send(
                f"Nowy rabat sklepowy: {new_discount} procent."
            )
        if new_capacity > old_capacity:
            await self.send(
                f"Nowy limit drużyny jako lider: {new_capacity} osób."
            )

    def bank_here(self):
        return self.character.room_id == BANK_ROOM

    def bank_currency_name(self, currency):
        return {
            "silver": "srebra",
            "gold": "złota",
            "mithril": "mithrilu",
        }[currency]

    def normalize_bank_currency(self, raw):
        value = normalize_lookup_text(raw)
        mapping = {
            "silver": "silver",
            "srebro": "silver",
            "srebra": "silver",
            "srebrnych": "silver",
            "gold": "gold",
            "zloto": "gold",
            "zlota": "gold",
            "mithril": "mithril",
            "mithrilu": "mithril",
        }
        return mapping.get(value)

    async def show_bank(self):
        if not self.bank_here():
            await self.send(
                "Bank Dusz obsługuje Bankier Aldren na Rynku. "
                "Wpisz prowadz bank."
            )
            return

        row = self.server.db.bank_balance(
            self.account_id
        )
        await self.send("BANK DUSZ")
        await self.send(
            f"Saldo: {row['silver']} srebrnych monet, "
            f"{row['gold']} złotych monet, "
            f"{row['mithril']} mithrilowych monet."
        )

        items = self.server.db.bank_items(
            self.account_id
        )
        if not items:
            await self.send(
                "Skrytka przedmiotów: pusta."
            )
        else:
            await self.send("Skrytka przedmiotów:")
            for item_row in items:
                item = ITEMS.get(
                    item_row["item_id"],
                    {"name": item_row["item_id"]},
                )
                await self.send(
                    f"{item['name']} x"
                    f"{item_row['quantity']}."
                )

        await self.send(
            "Komendy: bank wplac <ile> <waluta>, "
            "bank wyplac <ile> <waluta>, "
            "bank wplac wszystko, bank wyplac wszystko, "
            "bank wloz <przedmiot> [ile], "
            "bank wyjmij <przedmiot> [ile]."
        )

    async def bank_deposit_currency(self, amount, currency):
        amount = int(amount)
        if amount <= 0:
            await self.send(
                "Kwota wpłaty musi być większa od zera."
            )
            return False

        wallet = int(getattr(self.character, currency))
        if wallet < amount:
            await self.send(
                f"Nie masz tyle {self.bank_currency_name(currency)}. "
                f"Masz {wallet}."
            )
            return False

        if not self.server.db.change_bank_currency(
            self.account_id, currency, amount
        ):
            await self.send("Nie udało się wykonać wpłaty.")
            return False

        setattr(
            self.character,
            currency,
            wallet - amount,
        )
        self.server.db.save_character(self.character)
        await self.send(
            f"Wpłacasz {amount} "
            f"{self.bank_currency_name(currency)} do Banku Dusz."
        )
        return True

    async def bank_withdraw_currency(self, amount, currency):
        amount = int(amount)
        if amount <= 0:
            await self.send(
                "Kwota wypłaty musi być większa od zera."
            )
            return False

        balance = self.server.db.bank_balance(
            self.account_id
        )
        available = int(balance[currency])
        if available < amount:
            await self.send(
                f"Na koncie nie ma tyle "
                f"{self.bank_currency_name(currency)}. "
                f"Saldo: {available}."
            )
            return False

        if not self.server.db.change_bank_currency(
            self.account_id, currency, -amount
        ):
            await self.send("Nie udało się wykonać wypłaty.")
            return False

        setattr(
            self.character,
            currency,
            int(getattr(self.character, currency)) + amount,
        )
        self.server.db.save_character(self.character)
        await self.send(
            f"Wypłacasz {amount} "
            f"{self.bank_currency_name(currency)} z Banku Dusz."
        )
        return True

    def split_bank_item_quantity(self, raw):
        raw = str(raw or "").strip()
        if not raw:
            return "", 1

        parts = raw.split()
        quantity = 1

        if (
            len(parts) > 1
            and parts[-1].isdigit()
        ):
            quantity = max(1, int(parts[-1]))
            raw = " ".join(parts[:-1]).strip()

        return raw, quantity

    async def bank_deposit_item(self, raw):
        query, quantity = self.split_bank_item_quantity(
            raw
        )
        if not query:
            await self.send(
                "Użycie: bank wloz <przedmiot> [ilość]."
            )
            return False

        owned = {
            item_id: item
            for item_id, item in ITEMS.items()
            if self.server.db.item_qty(
                self.account_id, item_id
            ) > 0
        }
        found = find_by_name(owned, query)
        if not found:
            await self.send(
                "Nie masz takiego przedmiotu w inventory."
            )
            return False

        item_id, item = found
        current = self.server.db.item_qty(
            self.account_id, item_id
        )

        equipped_ids = {
            row["item_id"]
            for row in self.server.db.equipment(
                self.account_id
            )
        }
        if item_id in equipped_ids:
            await self.send(
                f"{item['name']} jest aktualnie założony. "
                "Nie można schować założonego przedmiotu w banku."
            )
            return False

        if current < quantity:
            await self.send(
                f"Masz tylko {current} sztuk "
                f"{item['name']}."
            )
            return False

        if not self.server.db.remove_item(
            self.account_id, item_id, quantity
        ):
            return False
        self.server.db.add_bank_item(
            self.account_id, item_id, quantity
        )

        await self.send(
            f"Do skrytki trafia {item['name']} x{quantity}."
        )
        return True

    async def bank_withdraw_item(self, raw):
        query, quantity = self.split_bank_item_quantity(
            raw
        )
        if not query:
            await self.send(
                "Użycie: bank wyjmij <przedmiot> [ilość]."
            )
            return False

        rows = self.server.db.bank_items(
            self.account_id
        )
        stored = {
            row["item_id"]: ITEMS.get(
                row["item_id"],
                {"name": row["item_id"]},
            )
            for row in rows
        }
        found = find_by_name(stored, query)
        if not found:
            await self.send(
                "Nie ma takiego przedmiotu w skrytce."
            )
            return False

        item_id, item = found
        current = self.server.db.bank_item_qty(
            self.account_id, item_id
        )
        if current < quantity:
            await self.send(
                f"W skrytce jest tylko {current} sztuk "
                f"{item['name']}."
            )
            return False

        if not self.server.db.remove_bank_item(
            self.account_id, item_id, quantity
        ):
            return False
        self.server.db.add_item(
            self.account_id, item_id, quantity
        )

        await self.send(
            f"Wyjmujesz ze skrytki "
            f"{item['name']} x{quantity}."
        )
        return True

    async def handle_bank(self, raw):
        if self.combat_mob_key:
            await self.send(
                "Nie możesz korzystać z banku podczas walki."
            )
            return

        if not self.bank_here():
            await self.send(
                "Bank Dusz znajduje się na Rynku u Bankiera Aldrena. "
                "Wpisz prowadz bank."
            )
            return

        raw = str(raw or "").strip()
        normalized = normalize_lookup_text(raw)

        if not normalized or normalized in (
            "saldo",
            "stan",
            "list",
            "lista",
        ):
            await self.show_bank()
            return

        parts = raw.split(maxsplit=1)
        action = normalize_lookup_text(parts[0])
        rest = parts[1] if len(parts) > 1 else ""
        normalized_rest = normalize_lookup_text(rest)

        if action in ("wplac", "deposit"):
            if normalized_rest == "wszystko":
                deposited_any = False
                for currency in (
                    "silver",
                    "gold",
                    "mithril",
                ):
                    amount = int(
                        getattr(self.character, currency)
                    )
                    if amount > 0:
                        await self.bank_deposit_currency(
                            amount, currency
                        )
                        deposited_any = True
                if not deposited_any:
                    await self.send(
                        "Nie masz waluty do wpłacenia."
                    )
                return

            tokens = rest.split()
            if len(tokens) != 2 or not tokens[0].isdigit():
                await self.send(
                    "Użycie: bank wplac <ile> "
                    "<srebro|zloto|mithril>."
                )
                return

            currency = self.normalize_bank_currency(
                tokens[1]
            )
            if not currency:
                await self.send(
                    "Nieznana waluta. Użyj srebro, zloto albo mithril."
                )
                return
            await self.bank_deposit_currency(
                int(tokens[0]), currency
            )
            return

        if action in ("wyplac", "withdraw"):
            if normalized_rest == "wszystko":
                balance = self.server.db.bank_balance(
                    self.account_id
                )
                withdrew_any = False
                for currency in (
                    "silver",
                    "gold",
                    "mithril",
                ):
                    amount = int(balance[currency])
                    if amount > 0:
                        await self.bank_withdraw_currency(
                            amount, currency
                        )
                        withdrew_any = True
                if not withdrew_any:
                    await self.send(
                        "Konto bankowe nie ma waluty do wypłacenia."
                    )
                return

            tokens = rest.split()
            if len(tokens) != 2 or not tokens[0].isdigit():
                await self.send(
                    "Użycie: bank wyplac <ile> "
                    "<srebro|zloto|mithril>."
                )
                return

            currency = self.normalize_bank_currency(
                tokens[1]
            )
            if not currency:
                await self.send(
                    "Nieznana waluta. Użyj srebro, zloto albo mithril."
                )
                return
            await self.bank_withdraw_currency(
                int(tokens[0]), currency
            )
            return

        if action in (
            "wloz",
            "schowaj",
            "put",
            "deposititem",
        ):
            await self.bank_deposit_item(rest)
            return

        if action in (
            "wyjmij",
            "wez",
            "take",
            "withdrawitem",
        ):
            await self.bank_withdraw_item(rest)
            return

        await self.send(
            "Użycie: bank; bank wplac 100 srebra; "
            "bank wyplac 100 srebra; bank wplac wszystko; "
            "bank wyplac wszystko; bank wloz <przedmiot> [ile]; "
            "bank wyjmij <przedmiot> [ile]."
        )

    async def show_money(self):
        self.server.db.save_character(self.character)
        c = self.character
        await self.send(
            f"Masz {c.silver} srebrnych monet, "
            f"{c.gold} złotych monet i "
            f"{c.mithril} mithrilowych monet."
        )
        await self.send(
            f"Automatyczny kurs: {SILVER_PER_GOLD} srebrnych monet "
            f"= 1 złota moneta; "
            f"{GOLD_PER_MITHRIL} złotych monet "
            f"= 1 mithrilowa moneta."
        )


    def profession_xp_to_next(self, level, profession=None):
        max_level = (
            profession_max_level(profession)
            if profession is not None
            else PROFESSION_MAX_LEVEL
        )
        if level >= max_level:
            return 0
        base_requirement = 80 + (level - 1) * 35
        return (
            base_requirement
            * PROFESSION_XP_REQUIREMENT_MULTIPLIER
        )

    def tool_xp_to_next(self, level, tool_type=None):
        max_level = tool_max_level(tool_type)
        if level >= max_level:
            return 0

        # v0.6.78: narzędzia rozwijają się 2x wolniej.
        # Nagrody XP z akcji pozostają bez zmian; podwajamy koszt levelu.
        base_requirement = 60 + (level - 1) * 30
        return base_requirement * 2

    def valid_tool_type(self, tool_type):
        return tool_type in (
            "fishing",
            "mining",
            "woodcutting",
            "crafting",
            "cooking",
            "herbalism",
            "alchemy",
            "jewelcrafting",
        )

    def tool_progress_state(self):
        result = {}
        for tool_type in (
            "fishing",
            "mining",
            "woodcutting",
            "crafting",
            "cooking",
            "herbalism",
            "alchemy",
            "jewelcrafting",
        ):
            row = self.server.db.tool(self.account_id, tool_type)
            result[tool_type] = (
                int(row["level"]),
                int(row["xp"]),
                int(row["uses"]),
            )
        return result

    def grant_profession_progress(self, profession, prof_xp, tool_type, tool_xp):
        if not self.valid_tool_type(tool_type):
            raise ValueError(f"Nieznany typ narzędzia: {tool_type}")

        actual_prof_xp = (
            max(0, int(prof_xp))
            * PROFESSION_XP_GAIN_MULTIPLIER
        )

        prow = self.server.db.profession(
            self.account_id, profession
        )
        profession_cap = profession_max_level(profession)
        plevel = int(prow["level"])
        old_profession_rank = profession_rank(
            plevel, profession
        )
        pxp = int(prow["xp"]) + actual_prof_xp
        actions = int(prow["actions"]) + 1
        messages = [f"{profession}: +{actual_prof_xp} XP."]

        while plevel < profession_cap:
            needed = self.profession_xp_to_next(
                plevel, profession
            )
            if pxp < needed:
                break
            pxp -= needed
            plevel += 1
            messages.append(f"{profession} osiąga poziom {plevel}.")
        if plevel >= profession_cap:
            plevel = profession_cap
            pxp = 0
        self.server.db.save_profession(
            self.account_id, profession, plevel, pxp, actions
        )

        new_profession_rank = profession_rank(
            plevel, profession
        )
        max_profession_rank = profession_max_rank(
            profession
        )
        if new_profession_rank > old_profession_rank:
            messages.append(
                f"{profession}: awansujesz na Rangę {new_profession_rank} "
                f"z {max_profession_rank}: "
                f"{profession_rank_name(profession, plevel)}."
            )

        trow = self.server.db.tool(self.account_id, tool_type)
        tlevel = int(trow["level"])
        old_tool_tier = tool_tier(tlevel)
        txp = int(trow["xp"]) + tool_xp
        uses = int(trow["uses"]) + 1
        tool_name = {
            "fishing": "Wędka",
            "mining": "Kilof",
            "woodcutting": "Piła",
            "crafting": "Młot Rzemieślniczy",
            "cooking": "Nóż Kucharski",
            "herbalism": "Sierp Zielarski",
            "alchemy": "Moździerz Alchemiczny",
            "jewelcrafting": "Szczypce Jubilerskie",
        }.get(tool_type, tool_type)
        messages.append(f"{tool_name}: +{tool_xp} XP narzędzia.")

        tool_level_cap = tool_max_level(tool_type)
        while tlevel < tool_level_cap:
            needed = self.tool_xp_to_next(tlevel, tool_type)
            if txp < needed:
                break
            txp -= needed
            tlevel += 1
            messages.append(f"{tool_name} osiąga level {tlevel}.")
        if tlevel >= tool_level_cap:
            tlevel = tool_level_cap
            txp = 0
        self.server.db.save_tool(
            self.account_id, tool_type, tlevel, txp, uses
        )

        new_tool_tier = tool_tier(tlevel)
        if new_tool_tier > old_tool_tier:
            messages.append(
                f"{tool_name} awansuje na Tier {new_tool_tier} z {TOOL_MAX_TIER}: "
                f"{tool_tier_name(tool_type, tlevel)}. "
                f"Szansa na dodatkowy urobek: "
                f"{int(tool_tier_bonus_chance(tlevel) * 100)} procent."
            )

        return messages, plevel, tlevel

    def grant_tool_progress(self, tool_type, tool_xp):
        if not self.valid_tool_type(tool_type):
            raise ValueError(f"Nieznany typ narzędzia: {tool_type}")
        row = self.server.db.tool(self.account_id, tool_type)
        level = int(row["level"])
        old_tier = tool_tier(level)
        xp = int(row["xp"]) + max(0, int(tool_xp))
        uses = int(row["uses"]) + 1

        tool_name = {
            "fishing": "Wędka",
            "mining": "Kilof",
            "woodcutting": "Piła",
            "crafting": "Młot Rzemieślniczy",
            "cooking": "Nóż Kucharski",
            "herbalism": "Sierp Zielarski",
            "alchemy": "Moździerz Alchemiczny",
            "jewelcrafting": "Szczypce Jubilerskie",
        }.get(tool_type, tool_type)

        messages = [f"{tool_name}: +{tool_xp} XP narzędzia."]

        tool_level_cap = tool_max_level(tool_type)
        while level < tool_level_cap:
            needed = self.tool_xp_to_next(level, tool_type)
            if xp < needed:
                break
            xp -= needed
            level += 1
            messages.append(f"{tool_name} osiąga level {level}.")

        if level >= tool_level_cap:
            level = tool_level_cap
            xp = 0

        self.server.db.save_tool(
            self.account_id, tool_type, level, xp, uses
        )

        new_tier = tool_tier(level)
        if new_tier > old_tier:
            if tool_type == "cooking":
                bonus_name = "dodatkową potrawę"
            elif tool_type == "crafting":
                bonus_name = "dodatkowy produkt receptury"
            else:
                bonus_name = "dodatkowy urobek"
            messages.append(
                f"{tool_name} awansuje na Tier {new_tier} z {TOOL_MAX_TIER}: "
                f"{tool_tier_name(tool_type, level)}. "
                f"Szansa na {bonus_name}: "
                f"{int(tool_tier_bonus_chance(level) * 100)} procent."
            )

        return messages, level

    def store_profession_resource(self, item_id, quantity=1):
        quantity = max(1, int(quantity))
        if item_id in FISH_STORAGE_IDS:
            self.server.db.add_storage_item(
                self.account_id, "net", item_id, quantity
            )
            return "net"
        if item_id in ORE_STORAGE_IDS:
            self.server.db.add_storage_item(
                self.account_id, "bag", item_id, quantity
            )
            return "bag"
        if item_id in WOOD_STORAGE_IDS:
            self.server.db.add_storage_item(
                self.account_id, "woodpile", item_id, quantity
            )
            return "woodpile"
        if item_id in HERB_STORAGE_IDS:
            self.server.db.add_storage_item(
                self.account_id, "herbbag", item_id, quantity
            )
            return "herbbag"
        raise ValueError(
            f"Przedmiot {item_id} nie jest surowcem obsługiwanej profesji."
        )

    def container_label(self, container):
        return {
            "net": "Siatka na ryby",
            "bag": "Sakwa górnicza",
            "woodpile": "Stos drewna",
            "herbbag": "Torba Zielarska",
        }.get(container, container)

    def normalize_container(self, token):
        t = token.strip().lower()
        if t in ("net", "siatka", "siatkę", "siatke"):
            return "net"
        if t in ("bag", "sakwa", "sakwe", "sakwę", "worek"):
            return "bag"
        if t in ("woodpile", "stos", "drewno", "sterta"):
            return "woodpile"
        if t in ("herbbag", "ziola", "zioła", "herbs", "torba"):
            return "herbbag"
        return None

    def category_ids(self, query, container=None):
        q = query.strip().lower()
        if q in ("fish", "ryba", "ryby"):
            return set(FISH_STORAGE_IDS)
        if q in ("ore", "ruda", "rudy"):
            return set(ORE_STORAGE_IDS)
        if q in ("wood", "drewno", "pnie", "pień", "pien"):
            return set(WOOD_STORAGE_IDS)
        if q in ("herb", "herbs", "ziolo", "zioło", "ziola", "zioła"):
            return set(HERB_STORAGE_IDS)
        if container == "net":
            allowed = FISH_STORAGE_IDS
        elif container == "bag":
            allowed = ORE_STORAGE_IDS
        elif container == "woodpile":
            allowed = WOOD_STORAGE_IDS
        elif container == "herbbag":
            allowed = HERB_STORAGE_IDS
        else:
            allowed = FISH_STORAGE_IDS | ORE_RESOURCE_IDS | WOOD_RESOURCE_IDS | HERB_RESOURCE_IDS

        found = find_by_name(
            {item_id: ITEMS[item_id] for item_id in allowed},
            query
        )
        return {found[0]} if found else set()

    def profession_storage_definition(self, container):
        definitions = {
            "net": {
                "ids": FISH_STORAGE_IDS,
                "count_label": "ryb",
                "type_label": "gatunków",
                "value_label": "całej siatki",
            },
            "bag": {
                "ids": ORE_STORAGE_IDS,
                "count_label": "rud",
                "type_label": "rodzajów",
                "value_label": "całej sakwy",
            },
            "woodpile": {
                "ids": WOOD_STORAGE_IDS,
                "count_label": "sztuk drewna",
                "type_label": "rodzajów",
                "value_label": "całego stosu drewna",
            },
            "herbbag": {
                "ids": HERB_STORAGE_IDS,
                "count_label": "ziół",
                "type_label": "rodzajów",
                "value_label": "całej torby zielarskiej",
            },
        }
        return definitions.get(container)

    def profession_storage_summary(self, container, rows=None):
        definition = self.profession_storage_definition(container)
        if not definition:
            return {
                "count": 0,
                "types": 0,
                "silver": 0,
                "gold": 0,
                "mithril": 0,
            }

        if rows is None:
            rows = self.server.db.storage_rows(
                self.account_id, container
            )

        total_count = 0
        total_silver = 0
        total_gold = 0
        total_mithril = 0
        type_count = 0

        allowed_ids = definition["ids"]

        for row in rows:
            item_id = row["item_id"]
            if item_id not in allowed_ids:
                continue

            quantity = max(0, int(row["quantity"]))
            if quantity <= 0:
                continue

            type_count += 1
            total_count += quantity

            item = ITEMS.get(item_id, {})
            total_silver += (
                int(item.get("sell_silver", 0))
                * quantity
            )
            total_gold += (
                int(item.get("sell_gold", 0))
                * quantity
            )
            total_mithril += (
                int(item.get("sell_mithril", 0))
                * quantity
            )

        return {
            "count": total_count,
            "types": type_count,
            "silver": total_silver,
            "gold": total_gold,
            "mithril": total_mithril,
        }

    # Zachowane dla kompatybilności z v0.6.80.
    def fish_net_summary(self, rows=None):
        generic = self.profession_storage_summary(
            "net", rows
        )
        return {
            "fish": generic["count"],
            "species": generic["types"],
            "silver": generic["silver"],
            "gold": generic["gold"],
            "mithril": generic["mithril"],
        }

    def profession_storage_value_text(self, summary):
        parts = []
        if summary["silver"]:
            parts.append(f"{summary['silver']} srebra")
        if summary["gold"]:
            parts.append(f"{summary['gold']} złota")
        if summary["mithril"]:
            parts.append(f"{summary['mithril']} mithrilu")

        if not parts:
            return "0 srebra"

        return ", ".join(parts)

    # Zachowane dla kompatybilności z v0.6.80.
    def fish_net_value_text(self, summary):
        return self.profession_storage_value_text(summary)

    async def show_container(self, container):
        label = self.container_label(container)
        rows = self.server.db.storage_rows(
            self.account_id, container
        )
        await self.send(label + ":")

        definition = self.profession_storage_definition(container)

        if not rows:
            await self.send("Pusto.")
            if definition:
                await self.send(
                    f"Łącznie {definition['count_label']}: 0. "
                    f"{definition['type_label'].capitalize()}: 0."
                )
                await self.send(
                    "Szacowany zarobek ze sprzedaży "
                    f"{definition['value_label']}: 0 srebra."
                )
            return

        for row in rows:
            item = ITEMS.get(
                row["item_id"],
                {"name": row["item_id"]},
            )
            await self.send(
                f"{item['name']} x{row['quantity']}."
            )

        if definition:
            summary = self.profession_storage_summary(
                container, rows
            )
            await self.send(
                f"Łącznie {definition['count_label']}: "
                f"{summary['count']}. "
                f"{definition['type_label'].capitalize()}: "
                f"{summary['types']}."
            )
            await self.send(
                "Szacowany zarobek ze sprzedaży "
                f"{definition['value_label']}: "
                f"{self.profession_storage_value_text(summary)}."
            )

    async def put_in_container(self, args):
        # Przykłady:
        # wloz ryba siatka
        # put fish net
        # wloz ruda sakwa
        parts = args.split()
        if len(parts) < 2:
            await self.send(
                "Użycie: wloz ryba siatka / put fish net / "
                "wloz ruda sakwa / put ore bag."
            )
            return

        container = self.normalize_container(parts[-1])
        if not container:
            await self.send("Podaj na końcu: siatka/net, sakwa/bag, stos/woodpile albo ziola/herbbag.")
            return

        query = " ".join(parts[:-1])
        ids = self.category_ids(query, container)
        if not ids:
            await self.send("Nie rozpoznaję takiego surowca.")
            return

        expected = {
            "net": FISH_RESOURCE_IDS,
            "bag": ORE_RESOURCE_IDS,
            "woodpile": WOOD_RESOURCE_IDS,
            "herbbag": HERB_RESOURCE_IDS,
        }[container]
        ids &= expected
        if not ids:
            await self.send(
                "Do Siatki wkłada się ryby, do Sakwy rudy, na Stos drewno, a do Torby Zielarskiej zioła."
            )
            return

        moved = []
        for item_id in sorted(ids):
            qty = self.server.db.item_qty(self.account_id, item_id)
            if qty <= 0:
                continue
            self.server.db.remove_item(self.account_id, item_id, qty)
            self.server.db.add_storage_item(
                self.account_id, container, item_id, qty
            )
            moved.append((item_id, qty))

        if not moved:
            await self.send("Nie masz takich surowców w zwykłym ekwipunku.")
            return

        for item_id, qty in moved:
            await self.send(
                f"Wkładasz {ITEMS[item_id]['name']} x{qty} do "
                f"{self.container_label(container)}."
            )

    async def take_from_container(self, args):
        parts = args.split()
        if len(parts) < 2:
            await self.send(
                "Użycie: wyjmij przedmiot siatka/sakwa/stos albo take item net/bag/woodpile."
            )
            return

        container = self.normalize_container(parts[-1])
        if not container:
            await self.send("Podaj na końcu: siatka/net, sakwa/bag, stos/woodpile albo ziola/herbbag.")
            return

        query = " ".join(parts[:-1])
        ids = self.category_ids(query, container)
        if not ids:
            await self.send("Nie rozpoznaję takiego surowca.")
            return

        moved = []
        for item_id in sorted(ids):
            qty = self.server.db.storage_qty(
                self.account_id, container, item_id
            )
            if qty <= 0:
                continue
            self.server.db.remove_storage_item(
                self.account_id, container, item_id, qty
            )
            self.server.db.add_item(self.account_id, item_id, qty)
            moved.append((item_id, qty))

        if not moved:
            await self.send("Nie ma tego surowca w tym pojemniku.")
            return

        for item_id, qty in moved:
            await self.send(
                f"Wyjmujesz {ITEMS[item_id]['name']} x{qty} z "
                f"{self.container_label(container)}."
            )

    async def grant_tool_reward_xp(self, tool_type, tool_xp):
        if not self.valid_tool_type(tool_type):
            raise ValueError(
                f"Nieznany typ narzędzia: {tool_type}"
            )

        tool_xp = max(0, int(tool_xp))
        row = self.server.db.tool(
            self.account_id, tool_type
        )
        level = int(row["level"])
        xp = int(row["xp"]) + tool_xp
        uses = int(row["uses"])

        tool_name = {
            "fishing": "Wędka",
            "mining": "Kilof",
            "woodcutting": "Piła",
            "crafting": "Młot Rzemieślniczy",
            "cooking": "Nóż Kucharski",
            "herbalism": "Sierp Zielarski",
            "alchemy": "Moździerz Alchemiczny",
            "jewelcrafting": "Szczypce Jubilerskie",
        }[tool_type]

        await self.send(
            f"{tool_name}: nagroda +{tool_xp} XP."
        )

        cap = tool_max_level(tool_type)
        while level < cap:
            needed = self.tool_xp_to_next(
                level, tool_type
            )
            if xp < needed:
                break
            xp -= needed
            level += 1
            await self.send(
                f"{tool_name} osiąga level {level}."
            )

        if level >= cap:
            level = cap
            xp = 0

        self.server.db.save_tool(
            self.account_id,
            tool_type,
            level,
            xp,
            uses,
        )

    async def grant_profession_reward_xp(self, profession, profession_xp, tool_type, tool_xp):
        if not self.valid_tool_type(tool_type):
            raise ValueError(f"Nieznany typ narzędzia: {tool_type}")

        actual_profession_xp = (
            max(0, int(profession_xp))
            * PROFESSION_XP_GAIN_MULTIPLIER
        )

        prow = self.server.db.profession(
            self.account_id, profession
        )
        profession_cap = profession_max_level(profession)
        plevel = int(prow["level"])
        pxp = int(prow["xp"]) + actual_profession_xp
        actions = int(prow["actions"])

        await self.send(
            f"{profession}: nagroda +{actual_profession_xp} XP."
        )

        while plevel < profession_cap:
            needed = self.profession_xp_to_next(
                plevel, profession
            )
            if pxp < needed:
                break
            pxp -= needed
            plevel += 1
            await self.send(f"{profession} osiąga poziom {plevel}.")

        if plevel >= profession_cap:
            plevel = profession_cap
            pxp = 0

        self.server.db.save_profession(
            self.account_id, profession, plevel, pxp, actions
        )

        trow = self.server.db.tool(self.account_id, tool_type)
        tlevel = int(trow["level"])
        txp = int(trow["xp"]) + tool_xp
        uses = int(trow["uses"])
        tool_name = {
            "fishing": "Wędka",
            "mining": "Kilof",
            "woodcutting": "Piła",
            "crafting": "Młot Rzemieślniczy",
            "cooking": "Nóż Kucharski",
            "herbalism": "Sierp Zielarski",
            "alchemy": "Moździerz Alchemiczny",
            "jewelcrafting": "Szczypce Jubilerskie",
        }[tool_type]

        await self.send(f"{tool_name}: nagroda +{tool_xp} XP.")

        tool_level_cap = tool_max_level(tool_type)
        while tlevel < tool_level_cap:
            needed = self.tool_xp_to_next(tlevel, tool_type)
            if txp < needed:
                break
            txp -= needed
            tlevel += 1
            await self.send(f"{tool_name} osiąga level {tlevel}.")

        if tlevel >= tool_level_cap:
            tlevel = tool_level_cap
            txp = 0

        self.server.db.save_tool(
            self.account_id, tool_type, tlevel, txp, uses
        )

    async def show_location(self):
        room = ROOMS[self.character.room_id]
        await self.send(
            f"Lokalizacja: {room['name']}. Strefa: {room['zone']}."
        )
        await self.show_exits()

    def normalize_room_query(self, value):
        text = str(value or "").strip().lower()
        text = text.replace("ł", "l").replace("Ł", "l")
        text = unicodedata.normalize("NFKD", text)
        text = "".join(
            ch for ch in text
            if not unicodedata.combining(ch)
        )
        text = text.replace("_", " ").replace("-", " ")
        text = re.sub(r"[^a-z0-9 ]+", " ", text)
        return " ".join(text.split())

    def room_search_aliases(self, room_id, room):
        aliases = {
            self.normalize_room_query(room_id),
            self.normalize_room_query(room_id.replace("_", " ")),
            self.normalize_room_query(room["name"]),
        }

        zone = self.normalize_room_query(room.get("zone", ""))
        name = self.normalize_room_query(room["name"])
        if zone and name:
            aliases.add(f"{zone} {name}")

        floor = crypt_floor_number(room_id)
        if floor:
            aliases.update({
                f"krypta {floor}",
                f"crypt {floor}",
                f"pietro {floor}",
                f"pietro krypty {floor}",
                f"krypta pietro {floor}",
                f"crypt floor {floor}",
            })

        astral_floor = astral_floor_number(room_id)
        if astral_floor is not None:
            aliases.update({
                f"wieza {astral_floor}",
                f"wieza astralna {astral_floor}",
                f"astral {astral_floor}",
                f"astralna wieza {astral_floor}",
                f"poziom wiezy {astral_floor}",
                f"astral floor {astral_floor}",
            })

        # Krótkie, naturalne warianty popularnych nazw.
        words = name.split()
        if len(words) > 1:
            aliases.add(" ".join(words[1:]))

        return {alias for alias in aliases if alias}

    def guide_zone_query_name(self, query):
        q = self.normalize_room_query(query)
        aliases = {
            "miasto": "miasto dusz",
            "gildia": "gildia dusz",
            "gory": "gory",
            "wioska": "wioska gorska",
            "wioska gorska": "wioska gorska",
            "laki": "laki zielarskie",
            "laka": "laki zielarskie",
            "podziemia": "podziemia",
            "trolle": "jaskinia trolli",
            "jaskinia trolli": "jaskinia trolli",
            "wieza astralna": "wieza astralna",
            "mityczna wieza astralna": "mityczna wieza astralna",
            "mityczna krypta": "mityczna krypta",
            "twierdza gigantow": "twierdza gigantow",
            "kopalnia glebinowa": "kopalnia glebinowa",
            "lasy": "loch profesyjny pradawny las",
            "pradawny las": "loch profesyjny pradawny las",
            "ogrod alchemika": "loch profesyjny ogrod alchemika",
            "zatopiona grota": "loch profesyjny zatopiona grota",
        }
        return aliases.get(q, q)

    def rooms_in_exact_zone(self, query):
        zone_query = self.guide_zone_query_name(query)
        matches = [
            room_id
            for room_id, room in ROOMS.items()
            if self.normalize_room_query(
                room.get("zone", "")
            ) == zone_query
        ]
        return sorted(
            matches,
            key=lambda rid: self.normalize_room_query(
                ROOMS[rid]["name"]
            ),
        )

    def find_room_matches(self, query):
        q = self.normalize_room_query(query)
        if not q:
            return []

        zone_matches = self.rooms_in_exact_zone(q)
        if zone_matches:
            return zone_matches

        # "wieza" jest celowo szerokim terenem:
        # zwykła i Mityczna Wieża Astralna.
        if q in ("wieza", "tower"):
            matches = []
            for zone_name in (
                "Wieża Astralna",
                "Mityczna Wieża Astralna",
            ):
                matches.extend(
                    self.rooms_in_exact_zone(zone_name)
                )
            if matches:
                return list(dict.fromkeys(matches))

        # "jaskinia" jako szeroki teren pokazuje zarówno
        # Kryształową Jaskinię, jak i Jaskinię Trolli.
        if q in ("jaskinia", "cave"):
            matches = []
            for room_id in (
                "cave_entrance",
                "troll_cave_entrance",
            ):
                if room_id in ROOMS:
                    matches.append(room_id)
            if matches:
                return matches

        shortcut = GUIDE_DESTINATION_ALIASES.get(q)
        if shortcut and shortcut in ROOMS:
            return [shortcut]

        # Krypta 1-200 ma specjalne naturalne skróty.
        crypt_match = re.fullmatch(
            r"(?:krypta|crypt|pietro|pietro krypty|krypta pietro|crypt floor)\s*(\d+)",
            q,
        )
        if crypt_match:
            floor = int(crypt_match.group(1))
            if 1 <= floor <= CRYPT_MAX_FLOOR:
                return [crypt_floor_id(floor)]
            return []

        astral_match = re.fullmatch(
            r"(?:wieza|wieza astralna|astral|astralna wieza|poziom wiezy|astral floor)\s*(\d+)",
            q,
        )
        if astral_match:
            floor = int(astral_match.group(1))
            if ASTRAL_MIN_FLOOR <= floor <= ASTRAL_MAX_FLOOR:
                return [astral_floor_id(floor)]
            return []

        mine_match = re.fullmatch(
            r"(?:kopalnia|mine|poziom kopalni|kopalnia poziom|mine floor)\s*(\d+)",
            q,
        )
        if mine_match:
            floor = int(mine_match.group(1))
            if MINE_MIN_FLOOR <= floor <= MINE_MAX_FLOOR:
                return [mine_floor_id(floor)]
            return []

        exact = []
        partial = []

        for room_id, room in ROOMS.items():
            aliases = self.room_search_aliases(room_id, room)
            if q in aliases:
                exact.append(room_id)
                continue
            if any(q in alias for alias in aliases):
                partial.append(room_id)

        if exact:
            return sorted(
                set(exact),
                key=lambda rid: ROOMS[rid]["name"].lower(),
            )

        return sorted(
            set(partial),
            key=lambda rid: ROOMS[rid]["name"].lower(),
        )

    def find_room(self, query):
        matches = self.find_room_matches(query)
        return matches[0] if len(matches) == 1 else None

    async def show_guide_destinations(self):
        await self.send("CELE PROWADZENIA")
        await self.send(
            f"Dostępne są wszystkie lokacje świata: {len(ROOMS)} celów."
        )

        zones = {}
        for room_id, room in ROOMS.items():
            if (
                room_id.startswith("crypt_floor_")
                or room_id.startswith("astral_floor_")
            ):
                continue
            zones.setdefault(room["zone"], []).append(room["name"])

        for zone in sorted(zones):
            names = sorted(set(zones[zone]), key=str.lower)
            await self.send(
                f"{zone}: " + "; ".join(names) + "."
            )

        await self.send(
            f"Krypta: wszystkie piętra od 1 do {CRYPT_MAX_FLOOR}. "
            "Przykłady: prowadz krypta 1, prowadz krypta 137, "
            f"prowadz krypta {CRYPT_MAX_FLOOR}."
        )
        await self.send(
            f"Wieża Astralna: poziomy {ASTRAL_MIN_FLOOR}-{ASTRAL_MAX_FLOOR}. "
            "Przykłady: prowadz wieza 100, prowadz astral 150, "
            f"prowadz wieza {ASTRAL_MAX_FLOOR}."
        )
        await self.send(
            f"Kopalnia Głębinowa: poziomy {MINE_MIN_FLOOR}-{MINE_MAX_FLOOR}. "
            "Przykłady: prowadz kopalnia 1, prowadz kopalnia 80, "
            f"prowadz kopalnia {MINE_MAX_FLOOR}. "
            "Prowadzenie zatrzyma się na nieprzebitej ścianie."
        )
        await self.send(
            "Możesz używać pełnej nazwy, identyfikatora lokacji ze spacjami "
            "albo wersji bez polskich znaków."
        )
        await self.send(
            "Jeśli teren albo nazwa pasuje do kilku miejsc, "
            "dostaniesz numerowaną listę. "
            "Wpisz tylko samą cyfrę wyboru. "
            "Działa to dla wszystkich terenów, między innymi "
            "Dziczy, Gór, Podziemi, Gildii, Jaskini Trolli, "
            "Krypt, Wież, Kopalń i Twierdzy Gigantów."
        )
        await self.send(
            "Działają też krótkie skróty. Przykłady: walk targ, walk kuznia, "
            "walk swiatynia, walk port, walk karczma, walk jaskinia, "
            "walk bandyci, prowadz roderik."
        )


    def shortest_path(self, start_room, target_room):
        if start_room == target_room:
            return []

        queue = [(start_room, [])]
        visited = {start_room}

        while queue:
            room_id, path = queue.pop(0)
            for direction, next_room in ROOMS[room_id]["exits"].items():
                if next_room in visited:
                    continue
                new_path = path + [(direction, next_room)]
                if next_room == target_room:
                    return new_path
                visited.add(next_room)
                queue.append((next_room, new_path))
        return None

    async def stop_auto_fishing(self, announce=True, immediate=True):
        self.auto_fishing = False
        task = self.auto_fishing_task

        if immediate:
            self.auto_fishing_task = None
            if task and task is not asyncio.current_task() and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            if announce:
                await self.send("Auto-łowienie wyłączone.")
            return

        if task and not task.done():
            if announce:
                await self.send(
                    "Auto-łowienie wyłączone. "
                    "Trwający połów zostanie dokończony, ale następny już się nie rozpocznie."
                )
            return

        self.auto_fishing_task = None
        if announce:
            await self.send("Auto-łowienie wyłączone.")

    async def auto_fishing_loop(self):
        try:
            while self.auto_fishing and not self.closed:
                if self.combat_mob_key:
                    await self.send(
                        "Auto-łowienie zatrzymane: rozpoczęła się walka."
                    )
                    break
                if self.server.db.item_qty(
                    self.account_id, "fishing_rod"
                ) <= 0:
                    await self.send(
                        "Auto-łowienie zatrzymane: nie masz Wędki."
                    )
                    break
                if self.character.room_id not in FISHING_ROOMS:
                    await self.send(
                        "Auto-łowienie zatrzymane: nie stoisz przy łowisku."
                    )
                    break

                await self.fish(from_auto=True)

        except asyncio.CancelledError:
            pass
        finally:
            self.auto_fishing = False
            if self.auto_fishing_task is asyncio.current_task():
                self.auto_fishing_task = None


    async def set_auto_fishing(self, enabled):
        if enabled:
            if self.auto_fishing:
                await self.send("Auto-łowienie jest już włączone.")
                return
            if self.combat_mob_key:
                await self.send(
                    "Nie możesz rozpocząć auto-łowienia podczas walki."
                )
                return
            if self.server.db.item_qty(
                self.account_id, "fishing_rod"
            ) <= 0:
                await self.send(
                    "Do auto-łowienia potrzebujesz Wędki."
                )
                return

            if self.character.room_id not in FISHING_ROOMS:
                await self.send(
                    "Auto-łowienie możesz włączyć tylko przy łowisku. "
                    "Automat nie chodzi sam."
                )
                return

            if self.auto_mining or self.auto_mining_task:
                await self.stop_auto_mining(announce=False)
            if self.auto_woodcutting or self.auto_woodcutting_task:
                await self.stop_auto_woodcutting(announce=False)
            if self.auto_herbalism or self.auto_herbalism_task:
                await self.stop_auto_herbalism(announce=False)

            self.auto_fishing = True
            self.auto_fishing_task = asyncio.create_task(
                self.auto_fishing_loop()
            )
            await self.send(
                "Auto-łowienie włączone. Łowi tylko w aktualnym miejscu "
                "i nie chodzi samodzielnie. "
                "Wpisz low off albo fish off, aby je zatrzymać."
            )
            return

        if not self.auto_fishing and not self.auto_fishing_task:
            await self.send("Auto-łowienie jest już wyłączone.")
            return
        await self.stop_auto_fishing(
            announce=True, immediate=False
        )

    def guide_floor_family_specs(self):
        return (
            {
                "prefix": "mine_floor_",
                "label": (
                    f"Kopalnia Głębinowa, poziomy "
                    f"{MINE_MIN_FLOOR}-{MINE_MAX_FLOOR}"
                ),
                "minimum": MINE_MIN_FLOOR,
                "maximum": MINE_MAX_FLOOR,
                "target_room": mine_floor_id(MINE_MIN_FLOOR),
            },
            {
                "prefix": "prof_crystal_mine_",
                "label": (
                    f"Kopalnia Kryształów, poziomy "
                    f"1-{PROF_DUNGEON_MAX_FLOOR}"
                ),
                "minimum": 1,
                "maximum": PROF_DUNGEON_MAX_FLOOR,
                "target_room": profession_dungeon_room_id(
                    "crystal_mine", 1
                ),
            },
            {
                "prefix": "crypt_floor_",
                "label": (
                    f"Krypta, piętra 1-{CRYPT_MAX_FLOOR}"
                ),
                "minimum": 1,
                "maximum": CRYPT_MAX_FLOOR,
                "target_room": crypt_floor_id(1),
            },
            {
                "prefix": "mythic_crypt_floor_",
                "label": (
                    f"Mityczna Krypta, piętra "
                    f"{MYTHIC_MIN_FLOOR}-{MYTHIC_MAX_FLOOR}"
                ),
                "minimum": MYTHIC_MIN_FLOOR,
                "maximum": MYTHIC_MAX_FLOOR,
                "target_room": mythic_crypt_floor_id(
                    MYTHIC_MIN_FLOOR
                ),
            },
            {
                "prefix": "astral_floor_",
                "label": (
                    f"Wieża Astralna, poziomy "
                    f"{ASTRAL_MIN_FLOOR}-{ASTRAL_MAX_FLOOR}"
                ),
                "minimum": ASTRAL_MIN_FLOOR,
                "maximum": ASTRAL_MAX_FLOOR,
                "target_room": astral_floor_id(ASTRAL_MIN_FLOOR),
            },
            {
                "prefix": "mythic_astral_floor_",
                "label": (
                    f"Mityczna Wieża Astralna, poziomy "
                    f"{MYTHIC_MIN_FLOOR}-{MYTHIC_MAX_FLOOR}"
                ),
                "minimum": MYTHIC_MIN_FLOOR,
                "maximum": MYTHIC_MAX_FLOOR,
                "target_room": mythic_astral_floor_id(
                    MYTHIC_MIN_FLOOR
                ),
            },
            {
                "prefix": "giant_fortress_",
                "label": (
                    f"Twierdza Gigantów, poziomy "
                    f"1-{GIANT_FORTRESS_MAX_FLOOR}"
                ),
                "minimum": 1,
                "maximum": GIANT_FORTRESS_MAX_FLOOR,
                "target_room": giant_fortress_floor_id(1),
            },
            {
                "prefix": "prof_sunken_grotto_",
                "label": (
                    f"Zatopiona Grota, poziomy "
                    f"1-{PROF_DUNGEON_MAX_FLOOR}"
                ),
                "minimum": 1,
                "maximum": PROF_DUNGEON_MAX_FLOOR,
                "target_room": profession_dungeon_room_id(
                    "sunken_grotto", 1
                ),
            },
            {
                "prefix": "prof_ancient_forest_",
                "label": (
                    f"Pradawny Las, poziomy "
                    f"1-{PROF_DUNGEON_MAX_FLOOR}"
                ),
                "minimum": 1,
                "maximum": PROF_DUNGEON_MAX_FLOOR,
                "target_room": profession_dungeon_room_id(
                    "ancient_forest", 1
                ),
            },
            {
                "prefix": "prof_alchemy_garden_",
                "label": (
                    f"Ogród Alchemika, poziomy "
                    f"1-{PROF_DUNGEON_MAX_FLOOR}"
                ),
                "minimum": 1,
                "maximum": PROF_DUNGEON_MAX_FLOOR,
                "target_room": profession_dungeon_room_id(
                    "alchemy_garden", 1
                ),
            },
        )

    def compact_guide_matches(self, matches):
        matches = list(dict.fromkeys(matches))
        matched = set()
        options = []

        for spec in self.guide_floor_family_specs():
            family_rooms = [
                room_id
                for room_id in matches
                if room_id.startswith(spec["prefix"])
            ]
            if not family_rooms:
                continue

            matched.update(family_rooms)
            options.append({
                "kind": "room",
                "label": spec["label"],
                "room_id": spec["target_room"],
            })

        for room_id in matches:
            if room_id in matched:
                continue
            options.append({
                "kind": "room",
                "label": (
                    f"{ROOMS[room_id]['name']}. "
                    f"Strefa: {ROOMS[room_id]['zone']}"
                ),
                "room_id": room_id,
            })

        return options

    async def ask_guide_choice(self, matches, query):
        options = self.compact_guide_matches(matches)

        if not options:
            return False

        self.guide_choice_state = {
            "mode": "destination",
            "query": str(query or ""),
            "options": options,
        }

        await self.send(
            f"Znaleziono kilka pasujących celów dla: {query}."
        )
        await self.send(
            "Wybierz cyfrę:"
        )

        for number, option in enumerate(options, 1):
            await self.send(
                f"{number}. {option['label']}."
            )

        await self.send(
            "Wpisz tylko samą cyfrę wyboru."
        )
        return True

    async def handle_guide_choice_number(self, raw):
        state = self.guide_choice_state
        if not state:
            return False

        value = str(raw or "").strip()

        if self.normalize_room_query(value) in (
            "anuluj", "cancel", "stop",
        ):
            self.guide_choice_state = None
            await self.send(
                "Anulowano wybór celu prowadzenia."
            )
            return True

        if not value.isdigit():
            return False

        number = int(value)

        if state["mode"] == "destination":
            options = state["options"]
            if not 1 <= number <= len(options):
                await self.send(
                    f"Nieprawidłowy numer. Wybierz od 1 do "
                    f"{len(options)} albo wpisz anuluj."
                )
                return True

            option = options[number - 1]
            self.guide_choice_state = None
            await self.guide_to(option["room_id"])
            return True

        self.guide_choice_state = None
        return False

    async def guide_to(self, query):
        self.guide_choice_state = None
        q = query.strip()
        if q.lower().startswith("to "):
            q = q[3:].strip()

        if self.normalize_room_query(q) in (
            "lista", "list", "cele", "destinations", "lokacje", "locations"
        ):
            await self.show_guide_destinations()
            return

        if not q:
            await self.send(
                "Użycie: prowadz <lokacja>. "
                "Wpisz prowadz lista, aby usłyszeć wszystkie cele."
            )
            return

        if self.combat_mob_key:
            await self.send("Nie możesz użyć prowadzenia podczas walki.")
            return

        matches = self.find_room_matches(q)
        if not matches:
            await self.send(
                "Nie rozpoznaję tej lokacji. "
                "Wpisz prowadz lista, aby usłyszeć wszystkie cele."
            )
            return

        if len(matches) > 1:
            await self.ask_guide_choice(
                matches,
                q,
            )
            return

        target = matches[0]

        if target == self.character.room_id:
            await self.send(f"Już jesteś tutaj: {ROOMS[target]['name']}.")
            return

        path = self.shortest_path(self.character.room_id, target)
        if path is None:
            await self.send("Nie udało się znaleźć drogi do tej lokacji.")
            return

        if self.auto_fishing or self.auto_fishing_task:
            await self.stop_auto_fishing(announce=False)
            await self.send("Auto-łowienie wyłączone z powodu rozpoczęcia podróży.")
        if self.auto_mining or self.auto_mining_task:
            await self.stop_auto_mining(announce=False)
            await self.send("Auto-kopanie wyłączone z powodu rozpoczęcia podróży.")
        if self.auto_woodcutting or self.auto_woodcutting_task:
            await self.stop_auto_woodcutting(announce=False)
            await self.send("Auto-Drwalstwo wyłączone z powodu rozpoczęcia podróży.")
        if self.auto_herbalism or self.auto_herbalism_task:
            await self.stop_auto_herbalism(announce=False)
            await self.send("Auto-Zielarstwo wyłączone z powodu rozpoczęcia podróży.")

        self.guiding = True
        await self.send(
            f"Prowadzę do: {ROOMS[target]['name']}. "
            f"Liczba przejść: {len(path)}."
        )

        try:
            for direction, next_room in path:
                if self.closed:
                    break
                if self.combat_mob_key:
                    await self.send("Prowadzenie przerwane przez walkę.")
                    break

                old = self.character.room_id
                mythic_error = self.mythic_entry_error(next_room)
                if mythic_error:
                    await self.send(
                        "Prowadzenie zatrzymane. " + mythic_error
                    )
                    break

                profession_error = (
                    self.profession_dungeon_access_error(next_room)
                )
                if profession_error:
                    await self.send(
                        "Prowadzenie zatrzymane. "
                        + profession_error
                    )
                    break

                if self.astral_entry_blocked(next_room):
                    await self.send(
                        f"Prowadzenie zatrzymane. Wieża Astralna wymaga "
                        f"Soul Level {ASTRAL_MIN_SOUL_LEVEL}."
                    )
                    break
                if self.mine_descent_blocked_for_player(old, direction):
                    progress = self.mine_progress()
                    floor = mine_floor_number(old)
                    required_hits = mine_wall_hits_required(
                        floor if floor is not None else MINE_MIN_FLOOR
                    )
                    await self.send(
                        f"Prowadzenie zatrzymane. Ściana kopalni "
                        f"blokuje zejście. Postęp "
                        f"{progress['wall_hits']} z "
                        f"{required_hits}."
                    )
                    break
                if self.mythic_crypt_descent_blocked_for_player(
                    old, direction
                ):
                    await self.send(
                        "Prowadzenie zatrzymane. "
                        "Mityczny boss Krypty blokuje zejście."
                    )
                    break
                if self.mythic_astral_ascent_blocked_for_player(
                    old, direction
                ):
                    await self.send(
                        "Prowadzenie zatrzymane. "
                        "Mityczny boss Wieży blokuje drogę w górę."
                    )
                    break
                if self.giant_fortress_ascent_blocked_for_player(
                    old, direction
                ):
                    boss = (
                        self.server.world.live_giant_fortress_boss(
                            old
                        )
                    )
                    boss_name = (
                        MOB_TEMPLATES[
                            boss.template_id
                        ]["name"]
                        if boss
                        else "boss Twierdzy Gigantów"
                    )
                    await self.send(
                        f"Prowadzenie zatrzymane. Drogę wyżej "
                        f"blokuje {boss_name}."
                    )
                    break
                if self.crypt_descent_blocked_for_player(old, direction):
                    boss = self.server.world.live_crypt_boss(old)
                    boss_name = (
                        MOB_TEMPLATES[boss.template_id]["name"]
                        if boss else "boss Krypty"
                    )
                    await self.send(
                        f"Prowadzenie zatrzymane. Zejście niżej blokuje "
                        f"{boss_name}. Pokonaj bossa."
                    )
                    break
                if self.astral_ascent_blocked_for_player(old, direction):
                    boss = self.server.world.live_astral_boss(old)
                    boss_name = (
                        MOB_TEMPLATES[boss.template_id]["name"]
                        if boss else "boss Wieży Astralnej"
                    )
                    await self.send(
                        f"Prowadzenie zatrzymane. Drogę w górę blokuje "
                        f"{boss_name}. Pokonaj bossa."
                    )
                    break
                await self.server.broadcast_room(
                    old, f"{self.character.name} odchodzi.", exclude=self
                )
                self.character.room_id = next_room
                self.server.db.save_character(self.character)
                await self.server.broadcast_room(
                    next_room, f"{self.character.name} przychodzi.", exclude=self
                )
                await self.send(
                    f"{direction}: {ROOMS[next_room]['name']}."
                )
                await asyncio.sleep(0.12)

            if self.character.room_id == target:
                await self.send(f"Dotarłeś do: {ROOMS[target]['name']}.")
                await self.look()
        finally:
            self.guiding = False

    async def stop_auto_mining(self, announce=True, immediate=True):
        self.auto_mining = False
        task = self.auto_mining_task

        if immediate:
            self.auto_mining_task = None
            if task and task is not asyncio.current_task() and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            if announce:
                await self.send("Auto-kopanie wyłączone.")
            return

        if task and not task.done():
            if announce:
                await self.send(
                    "Auto-kopanie wyłączone. "
                    "Trwające wydobycie zostanie dokończone, ale następne już się nie rozpocznie."
                )
            return

        self.auto_mining_task = None
        if announce:
            await self.send("Auto-kopanie wyłączone.")

    async def auto_mining_loop(self):
        try:
            while self.auto_mining and not self.closed:
                if self.combat_mob_key:
                    await self.send(
                        "Auto-kopanie zatrzymane: rozpoczęła się walka."
                    )
                    break
                if self.server.db.item_qty(
                    self.account_id, "pickaxe"
                ) <= 0:
                    await self.send(
                        "Auto-kopanie zatrzymane: nie masz Kilofa."
                    )
                    break
                if self.character.room_id not in MINING_ROOMS:
                    await self.send(
                        "Auto-kopanie zatrzymane: nie stoisz w miejscu wydobycia."
                    )
                    break

                if await self.auto_mine_descend_if_unlocked():
                    continue

                await self.mine(from_auto=True)

        except asyncio.CancelledError:
            pass
        finally:
            self.auto_mining = False
            if self.auto_mining_task is asyncio.current_task():
                self.auto_mining_task = None


    async def set_auto_mining(self, enabled):
        if enabled:
            if self.auto_mining:
                await self.send("Auto-kopanie jest już włączone.")
                return
            if self.combat_mob_key:
                await self.send(
                    "Nie możesz rozpocząć auto-kopania podczas walki."
                )
                return
            if self.server.db.item_qty(
                self.account_id, "pickaxe"
            ) <= 0:
                await self.send(
                    "Do auto-kopania potrzebujesz Kilofa."
                )
                return

            if self.character.room_id not in MINING_ROOMS:
                await self.send(
                    "Auto-kopanie możesz włączyć tylko w miejscu wydobycia. "
                    "Automat nie chodzi sam."
                )
                return

            if self.auto_fishing or self.auto_fishing_task:
                await self.stop_auto_fishing(announce=False)
            if self.auto_woodcutting or self.auto_woodcutting_task:
                await self.stop_auto_woodcutting(announce=False)
            if self.auto_herbalism or self.auto_herbalism_task:
                await self.stop_auto_herbalism(announce=False)

            self.auto_mining = True
            self.auto_mining_task = asyncio.create_task(
                self.auto_mining_loop()
            )
            await self.send(
                "Auto-kopanie włączone. Kopie tylko w Kopalni Głębinowej. "
                "Po przebiciu ściany może zejść wyłącznie przez odblokowane "
                "wyjście down na następny poziom. Nie chodzi w innych kierunkach. "
                "Wpisz kop off albo mine off, aby je zatrzymać."
            )
            return

        if not self.auto_mining and not self.auto_mining_task:
            await self.send("Auto-kopanie jest już wyłączone.")
            return
        await self.stop_auto_mining(
            announce=True, immediate=False
        )

    async def stop_auto_woodcutting(self, announce=True, immediate=True):
        self.auto_woodcutting = False
        task = self.auto_woodcutting_task

        if immediate:
            self.auto_woodcutting_task = None
            if task and task is not asyncio.current_task() and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            if announce:
                await self.send("Auto-Drwalstwo wyłączone.")
            return

        if task and not task.done():
            if announce:
                await self.send(
                    "Auto-Drwalstwo wyłączone. "
                    "Trwające cięcie zostanie dokończone, ale następne już się nie rozpocznie."
                )
            return

        self.auto_woodcutting_task = None
        if announce:
            await self.send("Auto-Drwalstwo wyłączone.")

    async def auto_woodcutting_loop(self):
        try:
            while self.auto_woodcutting and not self.closed:
                if self.combat_mob_key:
                    await self.send(
                        "Auto-Drwalstwo zatrzymane: rozpoczęła się walka."
                    )
                    break
                if self.server.db.item_qty(
                    self.account_id, "saw"
                ) <= 0:
                    await self.send(
                        "Auto-Drwalstwo zatrzymane: nie masz Piły."
                    )
                    break
                if self.character.room_id not in WOODCUTTING_ROOMS:
                    await self.send(
                        "Auto-Drwalstwo zatrzymane: nie stoisz przy drzewach."
                    )
                    break

                await self.woodcut(from_auto=True)

        except asyncio.CancelledError:
            pass
        finally:
            self.auto_woodcutting = False
            if self.auto_woodcutting_task is asyncio.current_task():
                self.auto_woodcutting_task = None


    async def set_auto_woodcutting(self, enabled):
        if enabled:
            if self.auto_woodcutting:
                await self.send(
                    "Auto-Drwalstwo jest już włączone."
                )
                return
            if self.combat_mob_key:
                await self.send(
                    "Nie możesz rozpocząć auto-Drwalstwa podczas walki."
                )
                return
            if self.server.db.item_qty(
                self.account_id, "saw"
            ) <= 0:
                await self.send(
                    "Do auto-Drwalstwa potrzebujesz Piły."
                )
                return

            if self.character.room_id not in WOODCUTTING_ROOMS:
                await self.send(
                    "Auto-Drwalstwo możesz włączyć tylko przy drzewach. "
                    "Automat nie chodzi sam."
                )
                return

            if self.auto_fishing or self.auto_fishing_task:
                await self.stop_auto_fishing(announce=False)
            if self.auto_mining or self.auto_mining_task:
                await self.stop_auto_mining(announce=False)
            if self.auto_herbalism or self.auto_herbalism_task:
                await self.stop_auto_herbalism(announce=False)

            self.auto_woodcutting = True
            self.auto_woodcutting_task = asyncio.create_task(
                self.auto_woodcutting_loop()
            )
            await self.send(
                "Auto-Drwalstwo włączone. Ścina tylko w aktualnym miejscu "
                "i nie chodzi samodzielnie. "
                "Wpisz tnij off albo woodcut off, aby je zatrzymać."
            )
            return

        if not self.auto_woodcutting and not self.auto_woodcutting_task:
            await self.send(
                "Auto-Drwalstwo jest już wyłączone."
            )
            return
        await self.stop_auto_woodcutting(
            announce=True, immediate=False
        )

    async def stop_auto_herbalism(self, announce=True, immediate=True):
        self.auto_herbalism = False
        task = self.auto_herbalism_task

        if immediate:
            self.auto_herbalism_task = None
            if task and task is not asyncio.current_task() and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            if announce:
                await self.send("Auto-Zielarstwo wyłączone.")
            return

        if task and not task.done():
            if announce:
                await self.send(
                    "Auto-Zielarstwo wyłączone. "
                    "Trwający zbiór zostanie dokończony, ale następny już się nie rozpocznie."
                )
            return

        self.auto_herbalism_task = None
        if announce:
            await self.send("Auto-Zielarstwo wyłączone.")

    async def auto_herbalism_loop(self):
        try:
            while self.auto_herbalism and not self.closed:
                if self.combat_mob_key:
                    await self.send(
                        "Auto-Zielarstwo zatrzymane: rozpoczęła się walka."
                    )
                    break
                if self.server.db.item_qty(
                    self.account_id, "herbalist_sickle"
                ) <= 0:
                    await self.send(
                        "Auto-Zielarstwo zatrzymane: nie masz Sierpa Zielarskiego."
                    )
                    break
                if self.character.room_id not in HERBALISM_ROOMS:
                    await self.send(
                        "Auto-Zielarstwo zatrzymane: nie stoisz w miejscu z ziołami."
                    )
                    break

                await self.gather_herb(from_auto=True)

        except asyncio.CancelledError:
            pass
        finally:
            self.auto_herbalism = False
            if self.auto_herbalism_task is asyncio.current_task():
                self.auto_herbalism_task = None


    async def set_auto_herbalism(self, enabled):
        if enabled:
            if self.auto_herbalism:
                await self.send(
                    "Auto-Zielarstwo jest już włączone."
                )
                return
            if self.combat_mob_key:
                await self.send(
                    "Nie możesz rozpocząć auto-Zielarstwa podczas walki."
                )
                return
            if self.server.db.item_qty(
                self.account_id, "herbalist_sickle"
            ) <= 0:
                await self.send(
                    "Do auto-Zielarstwa potrzebujesz Sierpa Zielarskiego."
                )
                return

            if self.character.room_id not in HERBALISM_ROOMS:
                await self.send(
                    "Auto-Zielarstwo możesz włączyć tylko w miejscu z ziołami. "
                    "Automat nie chodzi sam."
                )
                return

            if self.auto_fishing or self.auto_fishing_task:
                await self.stop_auto_fishing(announce=False)
            if self.auto_mining or self.auto_mining_task:
                await self.stop_auto_mining(announce=False)
            if self.auto_woodcutting or self.auto_woodcutting_task:
                await self.stop_auto_woodcutting(announce=False)

            self.auto_herbalism = True
            self.auto_herbalism_task = asyncio.create_task(
                self.auto_herbalism_loop()
            )
            await self.send(
                "Auto-Zielarstwo włączone. Zbiera tylko w aktualnym miejscu "
                "i nie chodzi samodzielnie. "
                "Wpisz zbieraj off, aby je zatrzymać."
            )
            return

        if not self.auto_herbalism and not self.auto_herbalism_task:
            await self.send(
                "Auto-Zielarstwo jest już wyłączone."
            )
            return
        await self.stop_auto_herbalism(
            announce=True, immediate=False
        )

    async def show_profession_ranks(self):
        for profession in (
            "Wędkarstwo", "Górnictwo", "Drwalstwo",
            "Zielarstwo", "Alchemia", "Kowalstwo",
            "Jubilerstwo",
        ):
            await self.send(f"RANGI: {profession.upper()}")
            thresholds = profession_rank_thresholds(profession)
            max_rank = profession_max_rank(profession)
            max_level = profession_max_level(profession)

            for rank, minimum in enumerate(thresholds, 1):
                if rank < max_rank:
                    maximum = thresholds[rank] - 1
                    level_text = f"level {minimum}-{maximum}"
                else:
                    level_text = f"level {minimum}-{max_level}"

                await self.send(
                    f"Ranga {rank}: "
                    f"{PROFESSION_RANK_NAMES[profession][rank - 1]}. "
                    f"{level_text}."
                )


    async def show_professions(self):
        await self.send("PROFESJE")
        for name in (
            "Wędkarstwo", "Górnictwo", "Drwalstwo",
            "Zielarstwo", "Alchemia", "Kowalstwo",
            "Jubilerstwo",
        ):
            row = self.server.db.profession(
                self.account_id, name
            )
            level = int(row["level"])
            max_level = profession_max_level(name)
            thresholds = profession_rank_thresholds(name)
            max_rank = profession_max_rank(name)
            rank = profession_rank(level, name)
            rank_name = profession_rank_name(name, level)

            if rank < max_rank:
                next_text = (
                    f"Następna ranga {rank + 1} od levelu "
                    f"{thresholds[rank]}."
                )
            else:
                next_text = "Ranga maksymalna."

            xp_text = (
                "maksimum"
                if level >= max_level
                else (
                    f"{row['xp']} z "
                    f"{self.profession_xp_to_next(level, name)}"
                )
            )
            await self.send(
                f"{name}: level {level} z {max_level}. "
                f"Ranga {rank} z {max_rank}: {rank_name}. "
                f"XP: {xp_text}. Akcje: {row['actions']}. "
                f"{next_text}"
            )


    async def show_tool_tiers(self):
        for tool_type, title in (
            ("fishing", "WĘDKI"),
            ("mining", "KILOFA"),
            ("woodcutting", "PIŁY"),
            ("crafting", "MŁOTA RZEMIEŚLNICZEGO"),
            ("cooking", "NOŻA KUCHARSKIEGO"),
            ("herbalism", "SIERPA ZIELARSKIEGO"),
            ("alchemy", "MOŹDZIERZA ALCHEMICZNEGO"),
            ("jewelcrafting", "SZCZYPIEC JUBILERSKICH"),
        ):
            await self.send(f"NAZWY TIERÓW {title}")
            for tier, minimum in enumerate(TOOL_TIER_THRESHOLDS, 1):
                if tier < TOOL_MAX_TIER:
                    maximum = TOOL_TIER_THRESHOLDS[tier] - 1
                    level_text = f"level {minimum}-{maximum}"
                else:
                    level_text = f"level {minimum}"
                bonus = int(TOOL_TIER_BONUS_CHANCES[tier - 1] * 100)
                await self.send(
                    f"Tier {tier}: {TOOL_TIER_NAMES[tool_type][tier - 1]}. "
                    f"{level_text}. Bonus {bonus} procent."
                )


    def tool_info_definition(self, tool_type):
        definitions = {
            "fishing": ("fishing_rod", "Wędka"),
            "mining": ("pickaxe", "Kilof"),
            "woodcutting": ("saw", "Piła"),
            "crafting": ("crafting_hammer", "Młot Rzemieślniczy"),
            "cooking": ("chef_knife", "Nóż Kucharski"),
            "herbalism": ("herbalist_sickle", "Sierp Zielarski"),
            "alchemy": ("alchemy_mortar", "Moździerz Alchemiczny"),
            "jewelcrafting": ("jeweler_pliers", "Szczypce Jubilerskie"),
        }
        return definitions.get(tool_type)

    def tool_bonus_label(self, tool_type):
        if tool_type == "cooking":
            return "Szansa na dodatkową potrawę"
        if tool_type == "crafting":
            return "Szansa na dodatkowy produkt receptury"
        if tool_type == "alchemy":
            return "Szansa na dodatkową miksturę"
        if tool_type == "herbalism":
            return "Szansa na dodatkowe zioło"
        if tool_type == "jewelcrafting":
            return "Szansa na dodatkową biżuterię"
        return "Bonus dodatkowego urobku"

    def tool_action_seconds(self, tool_type, level):
        level = max(1, min(TOOL_MAX_LEVEL, int(level)))
        base_seconds = int(
            TOOL_ACTION_BASE_SECONDS.get(tool_type, 10)
        )
        minimum_seconds = int(
            TOOL_ACTION_MIN_SECONDS.get(tool_type, 3)
        )

        if TOOL_MAX_LEVEL <= 1:
            return max(minimum_seconds, base_seconds)

        progress = (level - 1) / (TOOL_MAX_LEVEL - 1)
        seconds = round(
            base_seconds
            - (base_seconds - minimum_seconds) * progress
        )
        return max(minimum_seconds, int(seconds))

    def tool_action_label(self, tool_type):
        return {
            "fishing": "Czas zarzucenia i połowu",
            "mining": "Czas wydobycia",
            "woodcutting": "Czas cięcia",
            "crafting": "Czas wytwarzania",
            "cooking": "Czas gotowania",
            "herbalism": "Czas zbioru",
            "alchemy": "Czas warzenia",
            "jewelcrafting": "Czas wykonania biżuterii",
        }.get(tool_type, "Czas akcji")

    def tool_xp_remaining_to_level(self, level, xp, tool_type=None):
        max_level = tool_max_level(tool_type)
        if level >= max_level:
            return 0
        return max(
            0,
            self.tool_xp_to_next(level, tool_type) - int(xp),
        )

    def tool_xp_remaining_to_next_tier(self, level, xp, tool_type=None):
        tier = tool_tier(level)
        if tier >= TOOL_MAX_TIER:
            return 0, 0

        target_level = TOOL_TIER_THRESHOLDS[tier]
        levels_remaining = max(0, target_level - level)

        total_xp = self.tool_xp_remaining_to_level(level, xp, tool_type)
        for current_level in range(level + 1, target_level):
            total_xp += self.tool_xp_to_next(current_level, tool_type)

        return levels_remaining, total_xp

    async def show_single_tool(self, tool_type):
        definition = self.tool_info_definition(tool_type)
        if not definition:
            await self.send("Nieznane narzędzie.")
            return

        item_id, name = definition
        owned = self.server.db.item_qty(self.account_id, item_id) > 0
        if not owned:
            await self.send(f"{name}: nie posiadasz tego narzędzia.")
            if tool_type == "fishing":
                await self.send("Wędkę kupisz na Targu Rybnym.")
            elif tool_type == "mining":
                await self.send("Kilof kupisz u Górnika Torena przy Wejściu do Kryształowej Jaskini.")
            elif tool_type == "woodcutting":
                await self.send("Piłę kupisz u Drwala Brana w Obozie Drwala.")
            elif tool_type == "crafting":
                await self.send("Młot Rzemieślniczy kupisz u Kowala Dorana w Kuźni Dusz.")
            elif tool_type == "cooking":
                await self.send("Nóż Kucharski kupisz w Karczmie Pod Błękitnym Płomieniem.")
            elif tool_type in ("herbalism", "alchemy"):
                await self.send(
                    f"{name} kupisz u Zielarki Liory w Chacie Zielarki."
                )
            elif tool_type == "jewelcrafting":
                await self.send(
                    "Szczypce Jubilerskie kupisz u Jubilerki Mirelli "
                    "w Pracowni Jubilerskiej."
                )
            return

        row = self.server.db.tool(self.account_id, tool_type)
        level = int(row["level"])
        xp = int(row["xp"])
        uses = int(row["uses"])
        tier = tool_tier(level)
        max_level = tool_max_level(tool_type)
        tier_name = tool_tier_name(tool_type, level)
        bonus_percent = int(tool_tier_bonus_chance(level) * 100)
        bonus_label = self.tool_bonus_label(tool_type)

        await self.send(f"NARZĘDZIE: {name}.")
        await self.send(
            f"Aktualna nazwa narzędzia: {tier_name}."
        )
        await self.send(
            f"Level: {level} z {max_level}. "
            f"Użycia: {uses}."
        )
        await self.send(
            f"{self.tool_action_label(tool_type)}: "
            f"{self.tool_action_seconds(tool_type, level)} sekund."
        )

        if level >= max_level:
            await self.send("XP: maksimum. Do następnego levelu: maksimum.")
        else:
            needed = self.tool_xp_to_next(level, tool_type)
            remaining = self.tool_xp_remaining_to_level(level, xp, tool_type)
            await self.send(
                f"XP obecnego levelu: {xp} z {needed}. "
                f"Do następnego levelu brakuje {remaining} XP."
            )

        await self.send(
            f"Obecny Tier: {tier} z {TOOL_MAX_TIER}. "
            f"Nazwa: {tier_name}. "
            f"{bonus_label}: {bonus_percent} procent."
        )

        if tier >= TOOL_MAX_TIER:
            await self.send("Tier maksymalny. Nie ma następnego Tieru.")
        else:
            target_level = TOOL_TIER_THRESHOLDS[tier]
            next_tier = tier + 1
            next_name = TOOL_TIER_NAMES[tool_type][next_tier - 1]
            levels_remaining, xp_remaining = (
                self.tool_xp_remaining_to_next_tier(
                    level, xp, tool_type
                )
            )
            await self.send(
                f"Następny Tier: {next_tier}, {next_name}, "
                f"od levelu {target_level}. "
                f"Brakuje {levels_remaining} leveli i łącznie "
                f"{xp_remaining} XP narzędzia."
            )

        await self.send(f"TIERY NARZĘDZIA: {name}.")
        for tier_number, minimum in enumerate(TOOL_TIER_THRESHOLDS, 1):
            if tier_number < TOOL_MAX_TIER:
                maximum = TOOL_TIER_THRESHOLDS[tier_number] - 1
                level_text = f"level {minimum}-{maximum}"
            else:
                if tool_type == "crafting":
                    level_text = (
                        f"level {minimum}-{TOOL_MAX_LEVEL}"
                    )
                else:
                    level_text = f"level {minimum}-{TOOL_MAX_LEVEL}"

            tier_bonus = int(
                TOOL_TIER_BONUS_CHANCES[tier_number - 1] * 100
            )
            marker = " Obecny." if tier_number == tier else ""
            await self.send(
                f"Tier {tier_number}: "
                f"{TOOL_TIER_NAMES[tool_type][tier_number - 1]}. "
                f"{level_text}. Bonus {tier_bonus} procent.{marker}"
            )

    async def show_tools(self):
        await self.send("NARZĘDZIA")
        tools = [
            ("fishing", "fishing_rod", "Wędka"),
            ("mining", "pickaxe", "Kilof"),
            ("woodcutting", "saw", "Piła"),
            ("crafting", "crafting_hammer", "Młot Rzemieślniczy"),
            ("cooking", "chef_knife", "Nóż Kucharski"),
            ("herbalism", "herbalist_sickle", "Sierp Zielarski"),
            ("alchemy", "alchemy_mortar", "Moździerz Alchemiczny"),
            ("jewelcrafting", "jeweler_pliers", "Szczypce Jubilerskie"),
        ]
        for tool_type, item_id, name in tools:
            owned = self.server.db.item_qty(self.account_id, item_id) > 0
            if not owned:
                await self.send(f"{name}: brak.")
                continue

            row = self.server.db.tool(self.account_id, tool_type)
            level = int(row["level"])
            max_level = tool_max_level(tool_type)
            tier = tool_tier(level)
            tier_name = tool_tier_name(tool_type, level)
            bonus_percent = int(tool_tier_bonus_chance(level) * 100)
            bonus_label = self.tool_bonus_label(tool_type)

            if tier < TOOL_MAX_TIER:
                next_level = TOOL_TIER_THRESHOLDS[tier]
                next_text = f"Następny Tier {tier + 1} od levelu {next_level}."
            else:
                next_text = "Tier maksymalny."

            if level >= max_level:
                await self.send(
                    f"{name}. Aktualna nazwa: {tier_name}. "
                    f"Level {level} z {max_level}. "
                    f"Tier {tier} z {TOOL_MAX_TIER}. "
                    f"XP: maksimum. Użycia: {row['uses']}. "
                    f"{self.tool_action_label(tool_type)}: "
                    f"{self.tool_action_seconds(tool_type, level)} sekund. "
                    f"{bonus_label}: {bonus_percent} procent. {next_text}"
                )
            else:
                await self.send(
                    f"{name}. Aktualna nazwa: {tier_name}. "
                    f"Level {level} z {max_level}. "
                    f"Tier {tier} z {TOOL_MAX_TIER}. "
                    f"XP: {row['xp']} z {self.tool_xp_to_next(level, tool_type)}. "
                    f"Użycia: {row['uses']}. "
                    f"{self.tool_action_label(tool_type)}: "
                    f"{self.tool_action_seconds(tool_type, level)} sekund. "
                    f"{bonus_label}: {bonus_percent} procent. {next_text}"
                )


    def fishing_habitat(self, room_id=None):
        room_id = room_id or self.character.room_id
        if room_id in RIVER_FISHING_ROOMS: return "river"
        if room_id in LAKE_FISHING_ROOMS: return "lake"
        if room_id in SEA_FISHING_ROOMS: return "sea"
        if room_id in OCEAN_FISHING_ROOMS: return "ocean"
        return None

    def fishing_available_pool(self, tool_level, habitat=None):
        habitat = habitat or self.fishing_habitat()
        tool_level = max(1, int(tool_level))

        if habitat == "river":
            if tool_level < 10:
                base_pool = ("small_fish", "dace", "river_perch")
            elif tool_level < 25:
                base_pool = (
                    "dace", "chub", "common_nase",
                    "river_perch", "river_carp", "barbel",
                )
            elif tool_level < 45:
                base_pool = (
                    "chub", "common_nase", "barbel", "ide",
                    "silver_trout", "pike", "zander",
                )
            elif tool_level < 70:
                base_pool = (
                    "ide", "asp", "grayling", "silver_trout",
                    "golden_trout", "pike", "zander",
                    "salmon", "burbot",
                )
            else:
                base_pool = unlocked_resource_pool(
                    (
                        "asp", "grayling", "burbot", "golden_trout",
                        "salmon", "river_catfish", "ancient_sturgeon",
                        "moon_eel", "zander",
                    ),
                    ENDGAME_FISH_UNLOCKS["river"],
                    tool_level,
                )
            return add_more_fish_to_pool(
                base_pool, "river", tool_level
            )

        if habitat == "lake":
            if tool_level < 10:
                base_pool = (
                    "lake_roach", "rudd", "crucian_carp", "bream",
                )
            elif tool_level < 25:
                base_pool = (
                    "lake_roach", "rudd", "crucian_carp",
                    "bream", "tench", "lake_perch",
                )
            elif tool_level < 45:
                base_pool = (
                    "bream", "tench", "lake_perch",
                    "vendace", "pike", "zander",
                )
            elif tool_level < 70:
                base_pool = (
                    "tench", "vendace", "whitefish", "pike",
                    "zander", "lake_trout", "giant_pike",
                )
            else:
                base_pool = unlocked_resource_pool(
                    (
                        "whitefish", "lake_char", "lake_trout",
                        "giant_pike", "freshwater_eel", "pike", "zander",
                    ),
                    ENDGAME_FISH_UNLOCKS["lake"],
                    tool_level,
                )
            return add_more_fish_to_pool(
                base_pool, "lake", tool_level
            )

        if habitat == "sea":
            if tool_level < 10:
                base_pool = ("sprat", "sardine", "anchovy")
            elif tool_level < 20:
                base_pool = (
                    "sprat", "sardine", "anchovy", "whiting", "cod",
                )
            elif tool_level < 30:
                base_pool = (
                    "anchovy", "whiting", "cod", "mackerel", "flounder",
                )
            elif tool_level < 50:
                base_pool = (
                    "herring", "mackerel", "whiting", "cod",
                    "hake", "sea_bass", "haddock", "pollock",
                )
            elif tool_level < 75:
                base_pool = (
                    "herring", "hake", "sea_bass", "red_mullet",
                    "haddock", "pollock", "flounder", "sole", "halibut",
                )
            else:
                base_pool = unlocked_resource_pool(
                    (
                        "cod", "hake", "red_mullet", "sole", "halibut",
                        "turbot", "monkfish", "sea_bass",
                        "haddock", "pollock",
                    ),
                    ENDGAME_FISH_UNLOCKS["sea"],
                    tool_level,
                )
            return add_more_fish_to_pool(
                base_pool, "sea", tool_level
            )

        if habitat == "ocean":
            if tool_level < 20:
                base_pool = ("mackerel", "mahi_mahi", "albacore")
            elif tool_level < 40:
                base_pool = (
                    "mahi_mahi", "albacore", "wahoo",
                    "barracuda", "sailfish",
                )
            elif tool_level < 60:
                base_pool = (
                    "albacore", "bigeye_tuna", "wahoo",
                    "barracuda", "cobia", "sailfish",
                    "swordfish", "reef_shark",
                )
            elif tool_level < 80:
                base_pool = (
                    "bigeye_tuna", "cobia", "amberjack",
                    "swordfish", "bluefin_tuna", "reef_shark",
                    "mako_shark", "hammerhead_shark", "ocean_sunfish",
                )
            else:
                base_pool = unlocked_resource_pool(
                    (
                        "tuna", "bluefin_tuna", "bigeye_tuna", "amberjack",
                        "ocean_sunfish", "mako_shark", "tiger_shark",
                        "hammerhead_shark", "great_white_shark",
                        "ghost_marlin", "swordfish",
                    ),
                    ENDGAME_FISH_UNLOCKS["ocean"],
                    tool_level,
                )
            return add_more_fish_to_pool(
                base_pool, "ocean", tool_level
            )

        return ()


    def fishing_loot(self, tool_level, habitat="river"):
        dungeon, dungeon_floor = profession_dungeon_floor(
            self.character.room_id
        )
        if dungeon == "sunken_grotto":
            tool_level = min(
                int(tool_level), dungeon_floor * 10
            )
        pool = self.fishing_available_pool(tool_level, habitat)
        if not pool:
            return None
        return random.choice(pool)

    async def show_water_info(self):
        habitat = self.fishing_habitat()
        if not habitat:
            await self.send(
                "Tutaj nie ma łowiska. Komenda woda działa przy rzece, "
                "jeziorze, morzu albo oceanie."
            )
            return

        tool = self.server.db.tool(self.account_id, "fishing")
        tool_level = int(tool["level"])
        pool = self.fishing_available_pool(tool_level, habitat)

        habitat_name = {
            "river": "rzeka",
            "lake": "jezioro",
            "sea": "morze",
            "ocean": "ocean",
        }[habitat]

        await self.send(
            f"WODA: {habitat_name}. "
            f"Wędka level {tool_level}. "
            f"Dostępnych gatunków ryb dla twojej Wędki: {len(pool)}."
        )

        if pool:
            names = sorted(
                (ITEMS[item_id]["name"] for item_id in pool),
                key=normalize_lookup_text,
            )
            await self.send(
                "Ryby możliwe do złowienia: "
                + ", ".join(names)
                + "."
            )

        locked = [
            (required, item_id)
            for required, item_id in (
                tuple(ENDGAME_FISH_UNLOCKS.get(habitat, ()))
                + tuple(MORE_FISH_UNLOCKS.get(habitat, ()))
            )
            if int(required) > tool_level
        ]
        locked.sort(key=lambda entry: (int(entry[0]), ITEMS[entry[1]]["name"]))
        if locked:
            next_level, next_item = locked[0]
            await self.send(
                f"Następna ryba endgame od Wędki level {next_level}: "
                f"{ITEMS[next_item]['name']}."
            )
        else:
            await self.send(
                "Masz odblokowane wszystkie ryby endgame tego łowiska."
            )

        await self.send(
            "To liczba dostępnych gatunków, nie skończona liczba sztuk. "
            "Łowisko nie wyczerpuje się od łowienia."
        )


    def mining_loot(self, tool_level, room_id=None):
        tool_level = max(1, int(tool_level))
        room_id = room_id or self.character.room_id
        floor = mine_floor_number(room_id)
        dungeon, dungeon_floor = profession_dungeon_floor(room_id)
        if dungeon == "crystal_mine":
            floor = min(200, dungeon_floor * 10)

        if floor is None:
            r = random.random()
            if tool_level < 10:
                if r < 0.30:
                    return "stone_chunk"
                if r < 0.95:
                    return "copper_ore"
                return "iron_ore"
            if tool_level < 25:
                if r < 0.45:
                    return "copper_ore"
                if r < 0.95:
                    return "iron_ore"
                return "silver_ore"
            if tool_level < 50:
                if r < 0.55:
                    return "iron_ore"
                if r < 0.90:
                    return "silver_ore"
                return "gold_ore"
            if tool_level < 80:
                if r < 0.42:
                    return "iron_ore"
                if r < 0.82:
                    return "silver_ore"
                return "gold_ore"

            if tool_level < 90:
                mithril_chance = 0.001
            elif tool_level < 100:
                mithril_chance = 0.0025
            else:
                mithril_chance = 0.005

            if r < mithril_chance:
                return "__mithril_currency__"

            if tool_level >= 100:
                pool = unlocked_resource_pool(
                    ("silver_ore", "gold_ore"),
                    ENDGAME_ORE_UNLOCKS,
                    tool_level,
                )
                return random.choice(pool)

            rr = (r - mithril_chance) / (1.0 - mithril_chance)
            if tool_level < 90:
                if rr < 0.30:
                    return "iron_ore"
                if rr < 0.68:
                    return "silver_ore"
                return "gold_ore"
            if rr < 0.18:
                return "iron_ore"
            if rr < 0.52:
                return "silver_ore"
            return "gold_ore"

        effective_depth = min(floor, tool_level)

        if effective_depth >= 80:
            if effective_depth < 90:
                mithril_chance = 0.001
            elif effective_depth < 100:
                mithril_chance = 0.0025
            else:
                mithril_chance = 0.005
            if random.random() < mithril_chance:
                return "__mithril_currency__"

        world_ore_pool = unlocked_world_ore_ids(
            tool_level, floor
        )
        if world_ore_pool and random.random() < 0.45:
            return random.choice(world_ore_pool)

        if effective_depth < 10:
            pool = ("stone_chunk", "copper_ore")
        elif effective_depth < 25:
            pool = ("copper_ore", "iron_ore")
        elif effective_depth < 50:
            pool = ("iron_ore", "silver_ore")
        elif effective_depth < 100:
            pool = ("silver_ore", "gold_ore")
        elif effective_depth < 120:
            pool = ("gold_ore", "cobalt_ore")
        elif effective_depth < 140:
            pool = ("cobalt_ore", "runestone_ore")
        elif effective_depth < 160:
            pool = ("runestone_ore", "dragonsteel_ore")
        elif effective_depth < 180:
            pool = ("dragonsteel_ore", "astral_ore")
        elif effective_depth < 200:
            pool = ("astral_ore", "void_ore")
        else:
            pool = ("void_ore", "eternium_ore")

        return random.choice(pool)


    def woodcutting_loot(self, tool_level, room_id=None):
        room_id = room_id or self.character.room_id
        tool_level = max(1, int(tool_level))
        dungeon, dungeon_floor = profession_dungeon_floor(room_id)
        if dungeon == "ancient_forest":
            tool_level = min(tool_level, dungeon_floor * 10)

        if room_id in {"lumberjack_camp", "meadow"}:
            world_group = "beginner"
        elif room_id in {"whisper_grove", "old_road"}:
            world_group = "forest"
        else:
            world_group = "deep"

        world_pool = unlocked_world_ids(
            WORLD_WOOD_UNLOCKS[world_group],
            tool_level,
        )
        if world_pool and random.random() < 0.45:
            return random.choice(world_pool)

        # Obóz Drwala i Łąka: gatunki lekkie i pospolite.
        if room_id in {"lumberjack_camp", "meadow"}:
            if tool_level < 15:
                return random.choice(("fallen_branch", "birch_log", "alder_log", "pine_log"))
            if tool_level < 35:
                return random.choice(("birch_log", "alder_log", "pine_log", "poplar_log", "willow_log", "linden_log"))
            return random.choice(("pine_log", "poplar_log", "willow_log", "linden_log", "oak_log", "beech_log", "maple_log"))

        # Gaj Szeptów i Stary Trakt: drewna użytkowe i szlachetne.
        if room_id in {"whisper_grove", "old_road"}:
            if tool_level < 25:
                return random.choice(("oak_log", "beech_log", "maple_log", "linden_log"))
            if tool_level < 50:
                return random.choice(("oak_log", "beech_log", "maple_log", "ash_log", "chestnut_log", "walnut_log"))
            if tool_level < 75:
                return random.choice(("maple_log", "ash_log", "chestnut_log", "walnut_log", "cedar_log", "yew_log", "mahogany_log"))
            return random.choice(("ash_log", "walnut_log", "cedar_log", "yew_log", "mahogany_log", "teak_log", "redwood_log", "ironwood_log"))

        # Głębia Gaju: najrzadsze drewna naturalne i magiczne.
        if tool_level < 40:
            return random.choice(("ash_log", "chestnut_log", "cedar_log", "walnut_log"))
        if tool_level < 60:
            return random.choice(("cedar_log", "yew_log", "mahogany_log", "teak_log", "ironwood_log", "ebony_log"))
        if tool_level < 80:
            return random.choice(("yew_log", "mahogany_log", "teak_log", "redwood_log", "ironwood_log", "ebony_log", "silverwood_log"))
        if tool_level < 100:
            return random.choice((
                "redwood_log", "ironwood_log", "ebony_log", "silverwood_log",
                "spiritwood_log", "ancient_heartwood", "worldtree_wood"
            ))
        pool = (
            "teak_log", "redwood_log", "silverwood_log", "spiritwood_log",
            "ancient_heartwood", "worldtree_wood"
        )
        pool = unlocked_resource_pool(
            pool, ENDGAME_WOOD_UNLOCKS, tool_level
        )
        return random.choice(pool)


    def herbalism_loot(self, tool_level, room_id=None):
        room_id = room_id or self.character.room_id
        tool_level = max(1, int(tool_level))

        dedicated_herb = HERB_SPECIFIC_MEADOWS.get(room_id)
        if dedicated_herb:
            return dedicated_herb

        dungeon, dungeon_floor = profession_dungeon_floor(room_id)
        if dungeon == "alchemy_garden":
            tool_level = min(tool_level, dungeon_floor * 10)

        if room_id in {
            "herbalist_hut", "meadow",
            "mint_meadow", "flower_meadow",
        }:
            world_group = "meadow"
        elif room_id in {
            "riverbank", "lake_shore", "lakeside_meadow",
        }:
            world_group = "water"
        elif room_id in {"whisper_grove", "old_road"}:
            world_group = "forest"
        else:
            world_group = "deep"

        world_pool = unlocked_world_ids(
            WORLD_HERB_UNLOCKS[world_group],
            tool_level,
        )
        if world_pool and random.random() < 0.45:
            return random.choice(world_pool)
        if room_id in {"herbalist_hut", "meadow"}:
            if tool_level < 15:
                return random.choice(("nettle", "chamomile", "mint"))
            if tool_level < 35:
                return random.choice((
                    "nettle", "chamomile", "mint",
                    "yarrow", "lemon_balm", "lavender",
                ))
            return random.choice((
                "mint", "yarrow", "lemon_balm",
                "lavender", "sage", "valerian",
            ))

        if room_id == "mint_meadow":
            if tool_level < 15:
                return random.choice((
                    "mint", "mint", "lemon_balm", "chamomile",
                ))
            if tool_level < 35:
                return random.choice((
                    "mint", "mint", "lemon_balm",
                    "chamomile", "yarrow", "lavender",
                ))
            return random.choice((
                "mint", "lemon_balm", "lavender",
                "sage", "valerian", "yarrow",
            ))

        if room_id == "flower_meadow":
            if tool_level < 15:
                return random.choice((
                    "chamomile", "chamomile", "lavender", "nettle",
                ))
            if tool_level < 35:
                return random.choice((
                    "chamomile", "lavender", "yarrow",
                    "nettle", "lemon_balm",
                ))
            return random.choice((
                "lavender", "yarrow", "chamomile",
                "sage", "valerian", "lemon_balm",
            ))

        if room_id == "lakeside_meadow":
            if tool_level < 15:
                return random.choice((
                    "mint", "lemon_balm", "chamomile",
                ))
            if tool_level < 35:
                return random.choice((
                    "mint", "lemon_balm", "chamomile",
                    "yarrow", "lavender",
                ))
            return random.choice((
                "mint", "lemon_balm", "lavender",
                "sage", "yarrow", "star_moss",
            ))
        if room_id in {"riverbank", "lake_shore"}:
            if tool_level < 25:
                return random.choice(("mint", "lemon_balm", "chamomile"))
            if tool_level < 55:
                return random.choice(("mint", "lemon_balm", "star_moss", "sage", "yarrow"))
            return random.choice(("star_moss", "moonflower", "sage", "valerian", "ginseng"))
        if room_id in {"whisper_grove", "old_road"}:
            if tool_level < 25:
                return random.choice(("sage", "valerian", "lavender"))
            if tool_level < 50:
                return random.choice(("sage", "valerian", "ginseng", "nightshade"))
            if tool_level < 75:
                return random.choice(("ginseng", "nightshade", "mandrake", "moonflower", "soulroot"))
            return random.choice(("mandrake", "moonflower", "soulroot", "phoenix_leaf", "star_moss"))
        if tool_level < 40:
            return random.choice(("ginseng", "nightshade", "mandrake"))
        if tool_level < 70:
            return random.choice(("nightshade", "mandrake", "moonflower", "soulroot", "star_moss"))
        if tool_level < 90:
            return random.choice(("mandrake", "moonflower", "soulroot", "phoenix_leaf", "star_moss"))
        pool = (
            "moonflower", "soulroot", "phoenix_leaf",
            "star_moss", "astral_lotus"
        )
        pool = unlocked_resource_pool(
            pool, ENDGAME_HERB_UNLOCKS, tool_level
        )
        return random.choice(pool)

    def profession_ready(self):
        now = time.time()
        remaining = PROFESSION_COOLDOWN - (now - self.last_profession_action)
        if remaining > 0:
            return False, remaining
        self.last_profession_action = now
        return True, 0.0

    async def fish(self, from_auto=False):
        if self.combat_mob_key:
            await self.send("Nie możesz łowić podczas walki.")
            return
        if self.character.room_id not in FISHING_ROOMS:
            await self.send("Tutaj nie ma odpowiedniego łowiska.")
            return
        if self.server.db.item_qty(self.account_id, "fishing_rod") <= 0:
            await self.send("Do Wędkarstwa potrzebujesz Wędki. Kup ją na Rynku.")
            return
        ready, remaining = self.profession_ready()
        if not ready:
            if not from_auto:
                await self.send("Musisz chwilę odczekać przed kolejnym zarzuceniem wędki.")
            return

        tool = self.server.db.tool(self.account_id, "fishing")
        tool_level = int(tool["level"])
        action_seconds = self.tool_action_seconds(
            "fishing", tool_level
        )
        await self.send(
            f"Zarzucasz Wędkę. Czas połowu: "
            f"{action_seconds} sekund."
        )
        await asyncio.sleep(action_seconds)

        habitat = self.fishing_habitat()
        base_item_id = self.fishing_loot(
            tool_level, habitat=habitat
        )
        item_id = roll_fish_variant(
            base_item_id, tool_level
        )
        self.store_profession_resource(item_id, 1)
        item = ITEMS[item_id]
        resource_quest_quantity = 1
        if item_id != base_item_id:
            await self.send(
                f"RZADKI WARIANT RYBY: "
                f"{item.get('rare_resource_label', 'rzadki')}."
            )
        await self.send(
            f"Łowisz: {item['name']}. "
            "Połów trafia do Siatki na ryby."
        )

        current_tier = tool_tier(tool_level)
        bonus_chance = min(
            0.50,
            tool_tier_bonus_chance(tool_level)
            + self.character.racial_profession_bonus_chance()
        )
        if bonus_chance > 0 and random.random() < bonus_chance:
            self.store_profession_resource(item_id, 1)
            resource_quest_quantity += 1
            await self.send(
                f"Bonus Tieru {current_tier} Wędki: wyciągasz dodatkowo {item['name']} x1."
            )

        await self.announce_resource_quest_progress(
            item_id, resource_quest_quantity
        )
        await self.announce_collect_category_quest_progress("fish")

        messages, profession_level, new_tool_level = self.grant_profession_progress(
            "Wędkarstwo",
            10 + random.randint(0, 5),
            "fishing",
            8 + random.randint(0, 4),
        )
        for msg in messages:
            await self.send(msg)
        if new_tool_level != tool_level:
            await self.send(
                f"Wędka ma teraz level {new_tool_level}, Tier "
                f"{tool_tier(new_tool_level)}: "
                f"{tool_tier_name('fishing', new_tool_level)}."
            )

    async def mine(self, from_auto=False):
        if self.combat_mob_key:
            await self.send("Nie możesz wydobywać podczas walki.")
            return
        if self.character.room_id not in MINING_ROOMS:
            await self.send("Tutaj nie ma odpowiedniego złoża.")
            return
        if self.server.db.item_qty(self.account_id, "pickaxe") <= 0:
            await self.send("Do Górnictwa potrzebujesz Kilofa. Kup go u Górnika Torena przy Wejściu do Kryształowej Jaskini.")
            return
        ready, remaining = self.profession_ready()
        if not ready:
            if not from_auto:
                await self.send("Musisz chwilę odczekać przed kolejnym uderzeniem kilofa.")
            return

        tool = self.server.db.tool(self.account_id, "mining")
        tool_level = int(tool["level"])
        action_seconds = self.tool_action_seconds(
            "mining", tool_level
        )
        await self.send(
            f"Rozpoczynasz wydobycie Kilofem. "
            f"Czas wydobycia: {action_seconds} sekund."
        )
        await asyncio.sleep(action_seconds)

        item_id = self.mining_loot(
            tool_level, self.character.room_id
        )

        mined_resource_quantity = 0
        if item_id == "__mithril_currency__":
            self.character.mithril += 1
            self.server.db.save_character(self.character)
            await self.send(
                "Trafiasz na żyłę czystego mithrilu! Wydobywasz 1 mithril bezpośrednio do portfela."
            )
        else:
            vein = roll_mining_vein(tool_level)
            vein_quantity = int(vein["quantity"])
            self.store_profession_resource(
                item_id, vein_quantity
            )
            mined_resource_quantity = vein_quantity
            item = ITEMS[item_id]
            await self.send(
                f"ŻYŁA: {vein['name']}. "
                f"Wydobywasz: {item['name']} x{vein_quantity}. "
                "Urobek trafia do Sakwy górniczej."
            )

            current_tier = tool_tier(tool_level)
            bonus_chance = min(
            0.50,
            tool_tier_bonus_chance(tool_level)
            + self.character.racial_profession_bonus_chance()
        )
            if bonus_chance > 0 and random.random() < bonus_chance:
                self.store_profession_resource(item_id, 1)
                mined_resource_quantity += 1
                await self.send(
                    f"Bonus Tieru {current_tier} Kilofa: wydobywasz dodatkowo {item['name']} x1."
                )

        if item_id != "__mithril_currency__":
            await self.announce_resource_quest_progress(
                item_id, mined_resource_quantity
            )
            await self.announce_collect_category_quest_progress("ore")

        messages, profession_level, new_tool_level = self.grant_profession_progress(
            "Górnictwo",
            10 + random.randint(0, 5),
            "mining",
            8 + random.randint(0, 4),
        )
        for msg in messages:
            await self.send(msg)
        if new_tool_level != tool_level:
            await self.send(
                f"Kilof ma teraz level {new_tool_level}, Tier "
                f"{tool_tier(new_tool_level)}: "
                f"{tool_tier_name('mining', new_tool_level)}."
            )
        if new_tool_level >= 80 and tool_level < 80:
            await self.send(
                "Twój Kilof osiągnął level 80. Od teraz masz minimalną szansę wydobyć czysty mithril."
            )

        floor = mine_floor_number(self.character.room_id)
        if floor is not None and floor < MINE_MAX_FLOOR:
            wall = self.server.db.add_mine_wall_hit(
                self.account_id, floor
            )
            if wall["unlocked_floor"] is not None:
                unlocked = wall["unlocked_floor"]
                await self.send(
                    f"Przebijasz ścianę w dół! "
                    f"Odblokowano Kopalnię - poziom {unlocked}."
                )
                if from_auto and self.auto_mining:
                    descended = await self.auto_mine_descend_if_unlocked()
                    if not descended:
                        await self.send(
                            "Ściana jest przebita, ale auto-kopanie "
                            "nie może bezpiecznie zejść w dół."
                        )
            elif floor == wall["max_floor_unlocked"]:
                required_hits = mine_wall_hits_required(floor)
                await self.send(
                    f"Ściana w dół: {wall['wall_hits']} z "
                    f"{required_hits} uderzeń."
                )

    async def woodcut(self, from_auto=False):
        if self.combat_mob_key:
            await self.send("Nie możesz ścinać drzew podczas walki.")
            return
        if self.character.room_id not in WOODCUTTING_ROOMS:
            await self.send("Tutaj nie ma odpowiednich drzew do Drwalstwa.")
            return
        if self.server.db.item_qty(self.account_id, "saw") <= 0:
            await self.send("Do Drwalstwa potrzebujesz Piły. Kup ją u Drwala Brana w Obozie Drwala.")
            return
        ready, remaining = self.profession_ready()
        if not ready:
            if not from_auto:
                await self.send("Musisz chwilę odczekać przed kolejnym cięciem.")
            return

        tool = self.server.db.tool(self.account_id, "woodcutting")
        tool_level = int(tool["level"])
        action_seconds = self.tool_action_seconds(
            "woodcutting", tool_level
        )
        await self.send(
            f"Rozpoczynasz cięcie Piłą. "
            f"Czas cięcia: {action_seconds} sekund."
        )
        await asyncio.sleep(action_seconds)

        base_item_id = self.woodcutting_loot(
            tool_level, self.character.room_id
        )
        item_id = roll_wood_variant(
            base_item_id, tool_level
        )
        self.store_profession_resource(item_id, 1)
        item = ITEMS[item_id]
        if item_id != base_item_id:
            await self.send(
                f"RZADKI WARIANT DRZEWA: "
                f"{item.get('rare_resource_label', 'rzadki')}."
            )
        await self.send(
            f"Pozyskujesz: {item['name']}. "
            "Drewno trafia na Stos drewna."
        )

        current_tier = tool_tier(tool_level)
        bonus_chance = min(
            0.50,
            tool_tier_bonus_chance(tool_level)
            + self.character.racial_profession_bonus_chance()
        )
        if bonus_chance > 0 and random.random() < bonus_chance:
            self.store_profession_resource(item_id, 1)
            await self.send(
                f"Bonus Tieru {current_tier} Piły: pozyskujesz dodatkowo {item['name']} x1."
            )

        await self.announce_collect_category_quest_progress("wood")

        messages, profession_level, new_tool_level = self.grant_profession_progress(
            "Drwalstwo",
            10 + random.randint(0, 5),
            "woodcutting",
            8 + random.randint(0, 4),
        )
        for msg in messages:
            await self.send(msg)
        if new_tool_level != tool_level:
            await self.send(
                f"Piła ma teraz level {new_tool_level}, Tier "
                f"{tool_tier(new_tool_level)}: "
                f"{tool_tier_name('woodcutting', new_tool_level)}."
            )

    async def gather_herb(self, from_auto=False):
        if self.combat_mob_key:
            await self.send("Nie możesz zbierać ziół podczas walki.")
            return
        if self.character.room_id not in HERBALISM_ROOMS:
            await self.send("Tutaj nie ma odpowiednich ziół.")
            return
        if self.server.db.item_qty(self.account_id, "herbalist_sickle") <= 0:
            await self.send("Do Zielarstwa potrzebujesz Sierpa Zielarskiego. Kup go w Chacie Zielarki.")
            return
        ready, remaining = self.profession_ready()
        if not ready:
            if not from_auto:
                await self.send("Musisz chwilę odczekać przed kolejnym zbiorem.")
            return

        tool = self.server.db.tool(self.account_id, "herbalism")
        old_level = int(tool["level"])
        action_seconds = self.tool_action_seconds(
            "herbalism", old_level
        )
        await self.send(
            f"Rozpoczynasz zbiór Sierpem Zielarskim. "
            f"Czas zbioru: {action_seconds} sekund."
        )
        await asyncio.sleep(action_seconds)

        base_item_id = self.herbalism_loot(
            old_level, self.character.room_id
        )
        item_id = roll_herb_variant(
            base_item_id, old_level
        )
        self.store_profession_resource(item_id, 1)
        resource_quest_quantity = 1
        if item_id != base_item_id:
            await self.send(
                f"RZADKI WARIANT ROŚLINY: "
                f"{ITEMS[item_id].get('rare_resource_label', 'rzadki')}."
            )
        await self.send(
            f"Zbierasz: {ITEMS[item_id]['name']}. "
            "Roślina trafia do Torby Zielarskiej."
        )

        bonus_chance = min(
            0.50,
            tool_tier_bonus_chance(old_level) + self.character.racial_profession_bonus_chance()
        )
        if bonus_chance > 0 and random.random() < bonus_chance:
            self.store_profession_resource(item_id, 1)
            resource_quest_quantity += 1
            await self.send(
                f"Bonus Tieru {tool_tier(old_level)} Sierpa Zielarskiego: "
                f"zbierasz dodatkowo {ITEMS[item_id]['name']} x1."
            )

        await self.announce_resource_quest_progress(
            item_id, resource_quest_quantity
        )
        await self.announce_collect_category_quest_progress("herb")

        messages, prof_level, new_tool_level = self.grant_profession_progress(
            "Zielarstwo",
            10 + random.randint(0, 5),
            "herbalism",
            8 + random.randint(0, 4),
        )
        for msg in messages:
            await self.send(msg)
        if new_tool_level != old_level:
            await self.send(
                f"Sierp Zielarski ma teraz level {new_tool_level}, Tier "
                f"{tool_tier(new_tool_level)}: {tool_tier_name('herbalism', new_tool_level)}."
            )

    def resource_sale_allowed_here(self, item_id):
        room_id = self.character.room_id
        if item_id in FISH_STORAGE_IDS:
            return room_id in {"market", "inn", "fish_market"}
        if item_id in ORE_STORAGE_IDS:
            return room_id in {
                "forge", "mountain_market"
            }
        if item_id in WOOD_STORAGE_IDS:
            return room_id in {"market", "forge"}
        if item_id in HERB_STORAGE_IDS:
            return room_id in {"market", "herbalist_hut"}
        return False

    def resource_sale_location_text(self, container):
        return {
            "net": "Targ Rybny, Rynek albo Karczma",
            "bag": "Kuźnia Dusz albo Górski Targ Minerałów",
            "woodpile": "Rynek albo Kuźnia Dusz",
            "herbbag": "Rynek albo Chata Zielarki",
        }.get(container, "właściwy punkt skupu")

    def bulk_sell_rewards_for_rows(self, rows):
        total_silver = 0
        total_gold = 0
        total_mithril = 0
        total_units = 0
        total_types = 0

        for item_id, quantity in rows:
            item = ITEMS.get(item_id, {})
            quantity = max(0, int(quantity))
            if quantity <= 0:
                continue

            silver = int(item.get("sell_silver", 0))
            gold = int(item.get("sell_gold", 0))
            mithril = int(item.get("sell_mithril", 0))
            if not (silver or gold or mithril):
                continue

            total_units += quantity
            total_types += 1
            total_silver += silver * quantity
            total_gold += gold * quantity
            total_mithril += mithril * quantity

        return {
            "units": total_units,
            "types": total_types,
            "silver": total_silver,
            "gold": total_gold,
            "mithril": total_mithril,
        }

    def sale_reward_text(self, rewards):
        parts = []
        if rewards["silver"]:
            parts.append(f"{rewards['silver']} srebra")
        if rewards["gold"]:
            parts.append(f"{rewards['gold']} złota")
        if rewards["mithril"]:
            parts.append(f"{rewards['mithril']} mithrilu")
        return ", ".join(parts) if parts else "0 srebra"

    async def gain_charisma_from_bulk_sale(self, units):
        units = max(0, int(units))
        if units <= 0:
            return

        old_discount = self.character.shop_discount_percent()
        old_capacity = self.character.party_capacity()
        self.character.charisma += units

        await self.send(
            f"Charyzma handlowa +{units}. "
            f"Masz teraz {self.character.charisma}."
        )

        new_discount = self.character.shop_discount_percent()
        new_capacity = self.character.party_capacity()

        if new_discount > old_discount:
            await self.send(
                f"Nowy rabat sklepowy: {new_discount} procent."
            )
        if new_capacity > old_capacity:
            await self.send(
                f"Nowy limit drużyny jako lider: "
                f"{new_capacity} osób."
            )

    def normalize_bulk_sell_target(self, query):
        q = normalize_lookup_text(query)
        direct = {
            "wszystko siatka": "net",
            "wszystko ryby": "net",
            "wszystkie ryby": "net",
            "cala siatka": "net",
            "cale ryby": "net",

            "wszystko sakwa": "bag",
            "wszystko rudy": "bag",
            "wszystkie rudy": "bag",
            "cala sakwa": "bag",

            "wszystko stos": "woodpile",
            "wszystko drewno": "woodpile",
            "cale drewno": "woodpile",
            "caly stos": "woodpile",

            "wszystko torba": "herbbag",
            "wszystko ziola": "herbbag",
            "wszystkie ziola": "herbbag",
            "cala torba": "herbbag",

            "wszystko przedmioty": "inventory",
            "wszystkie przedmioty": "inventory",

            "ryby siatka": "net",
            "ryba siatka": "net",
            "fish net": "net",
            "net": "net",
            "siatka": "net",
            "ryby": "net",

            "rudy sakwa": "bag",
            "ruda sakwa": "bag",
            "ore bag": "bag",
            "ores bag": "bag",
            "bag": "bag",
            "sakwa": "bag",
            "rudy": "bag",

            "drewno stos": "woodpile",
            "wood pile": "woodpile",
            "woodpile": "woodpile",
            "stos": "woodpile",
            "drewno": "woodpile",

            "ziola torba": "herbbag",
            "ziola herbs": "herbbag",
            "herbs bag": "herbbag",
            "herbbag": "herbbag",
            "ziola": "herbbag",
            "herbs": "herbbag",
            "torba zielarska": "herbbag",

            "przedmioty": "inventory",
            "items": "inventory",
            "inventory": "inventory",
            "ekwipunek": "inventory",
        }
        return direct.get(q)

    async def bulk_sell_container(self, container):
        definition = self.profession_storage_definition(container)
        if not definition:
            await self.send("Nieznany magazyn profesji.")
            return False

        rows_db = self.server.db.storage_rows(
            self.account_id, container
        )
        if not rows_db:
            await self.send(
                f"{self.container_label(container)} jest pusty."
            )
            return False

        sell_rows = []
        for row in rows_db:
            item_id = row["item_id"]
            qty = int(row["quantity"])
            item = ITEMS.get(item_id, {})
            if (
                item_id in definition["ids"]
                and qty > 0
                and self.resource_sale_allowed_here(item_id)
                and (
                    item.get("sell_silver", 0)
                    or item.get("sell_gold", 0)
                    or item.get("sell_mithril", 0)
                )
            ):
                sell_rows.append((item_id, qty))

        if not sell_rows:
            await self.send(
                f"Nie możesz sprzedać zawartości "
                f"{self.container_label(container)} tutaj. "
                f"Sprzedaż: "
                f"{self.resource_sale_location_text(container)}."
            )
            return False

        rewards = self.bulk_sell_rewards_for_rows(sell_rows)

        for item_id, qty in sell_rows:
            if not self.server.db.remove_storage_item(
                self.account_id, container, item_id, qty
            ):
                raise RuntimeError(
                    f"Nie udało się sprzedać {item_id} x{qty}."
                )

        self.character.silver += rewards["silver"]
        self.character.gold += rewards["gold"]
        self.character.mithril += rewards["mithril"]

        await self.gain_charisma_from_bulk_sale(rewards["units"])
        self.server.db.save_character(self.character)

        await self.send(
            f"Sprzedajesz cały magazyn: "
            f"{self.container_label(container)}. "
            f"Sztuk: {rewards['units']}. "
            f"Rodzajów: {rewards['types']}."
        )
        await self.send(
            f"Zarobek: {self.sale_reward_text(rewards)}."
        )
        return True

    async def bulk_sell_inventory_items(self):
        rows = self.server.db.inventory(self.account_id)
        equipped_ids = {
            row["item_id"]
            for row in self.server.db.equipment(self.account_id)
        }

        sell_rows = []
        skipped = 0

        for row in rows:
            item_id = row["item_id"]
            qty = int(row["quantity"])
            item = ITEMS.get(item_id, {})

            if item_id in equipped_ids:
                skipped += qty
                continue

            # Sprzedaj tylko rzeczy z jawną ceną sprzedaży.
            # Dzięki temu narzędzia, mikstury i gear bez ceny nie znikają.
            if not (
                item.get("sell_silver", 0)
                or item.get("sell_gold", 0)
                or item.get("sell_mithril", 0)
            ):
                continue

            if not self.resource_sale_allowed_here(item_id):
                skipped += qty
                continue

            sell_rows.append((item_id, qty))

        if not sell_rows:
            await self.send(
                "Nie masz tutaj sprzedawalnych przedmiotów z "
                "ustaloną ceną. Narzędzia, mikstury, założony "
                "ekwipunek i przedmioty bez ceny nie są sprzedawane."
            )
            return False

        rewards = self.bulk_sell_rewards_for_rows(sell_rows)

        for item_id, qty in sell_rows:
            if not self.server.db.remove_item(
                self.account_id, item_id, qty
            ):
                raise RuntimeError(
                    f"Nie udało się sprzedać {item_id} x{qty}."
                )

        self.character.silver += rewards["silver"]
        self.character.gold += rewards["gold"]
        self.character.mithril += rewards["mithril"]

        await self.gain_charisma_from_bulk_sale(rewards["units"])
        self.server.db.save_character(self.character)

        await self.send(
            f"Sprzedajesz sprzedawalne przedmioty z inventory. "
            f"Sztuk: {rewards['units']}. "
            f"Rodzajów: {rewards['types']}."
        )
        await self.send(
            f"Zarobek: {self.sale_reward_text(rewards)}."
        )
        if skipped:
            await self.send(
                f"Pominięto {skipped} sztuk, których nie można "
                f"sprzedać w tej lokacji albo są założone."
            )
        return True

    async def sell_command(self, query):
        target = self.normalize_bulk_sell_target(query)

        if target == "inventory":
            await self.bulk_sell_inventory_items()
            return

        if target in {"net", "bag", "woodpile", "herbbag"}:
            await self.bulk_sell_container(target)
            return

        await self.sell_resource(query)

    async def sell_resource(self, query):
        found = find_by_name(ITEMS, query)
        if not found:
            await self.send("Nie rozpoznaję takiego przedmiotu.")
            return
        item_id, item = found
        if item.get("type") != "resource":
            await self.send("Tego przedmiotu nie sprzedaje się tutaj jako surowca.")
            return

        fish_items = FISH_STORAGE_IDS
        ore_items = ORE_STORAGE_IDS
        wood_items = WOOD_STORAGE_IDS
        herb_items = HERB_STORAGE_IDS

        if item_id in fish_items:
            source_container = "net"
        elif item_id in ore_items:
            source_container = "bag"
        elif item_id in wood_items:
            source_container = "woodpile"
        elif item_id in herb_items:
            source_container = "herbbag"
        else:
            source_container = None

        storage_quantity = (
            self.server.db.storage_qty(self.account_id, source_container, item_id)
            if source_container else 0
        )
        inventory_quantity = self.server.db.item_qty(self.account_id, item_id)
        if storage_quantity <= 0 and inventory_quantity <= 0:
            await self.send("Nie masz tego przedmiotu.")
            return

        if item_id in fish_items and self.character.room_id not in {"market", "inn", "fish_market"}:
            await self.send("Ryby możesz sprzedać na Targu Rybnym, Rynku albo w Karczmie.")
            return
        if item_id in ore_items and self.character.room_id != "forge":
            await self.send("Rudy możesz sprzedać w Kuźni Dusz.")
            return
        if item_id in wood_items and self.character.room_id not in {"market", "forge"}:
            await self.send("Drewno możesz sprzedać na Rynku albo w Kuźni Dusz.")
            return
        if item_id in herb_items and self.character.room_id not in {"market", "herbalist_hut"}:
            await self.send("Zioła możesz sprzedać na Rynku albo w Chacie Zielarki.")
            return

        removed = False
        if source_container and self.server.db.storage_qty(
            self.account_id, source_container, item_id
        ) > 0:
            removed = self.server.db.remove_storage_item(
                self.account_id, source_container, item_id, 1
            )
        elif self.server.db.item_qty(self.account_id, item_id) > 0:
            removed = self.server.db.remove_item(
                self.account_id, item_id, 1
            )

        if not removed:
            await self.send("Nie masz tego surowca.")
            return

        silver = item.get("sell_silver", 0)
        gold = item.get("sell_gold", 0)
        mithril = item.get("sell_mithril", 0)
        self.character.silver += silver
        self.character.gold += gold
        self.character.mithril += mithril
        await self.gain_charisma_from_sale()
        self.server.db.save_character(self.character)

        rewards = []
        if silver:
            rewards.append(f"{silver} srebra")
        if gold:
            rewards.append(f"{gold} złota")
        if mithril:
            rewards.append(f"{mithril} mithrilu")
        await self.send(f"Sprzedajesz {item['name']} za " + ", ".join(rewards) + ".")

    def recipe_container_for_item(self, item_id):
        if item_id in FISH_STORAGE_IDS:
            return "net"
        if item_id in ORE_STORAGE_IDS:
            return "bag"
        if item_id in WOOD_STORAGE_IDS:
            return "woodpile"
        if item_id in HERB_STORAGE_IDS:
            return "herbbag"
        return None

    def available_recipe_item(self, item_id):
        container = self.recipe_container_for_item(item_id)
        storage = (
            self.server.db.storage_qty(self.account_id, container, item_id)
            if container else 0
        )
        return storage + self.server.db.item_qty(self.account_id, item_id)

    def consume_recipe_item(self, item_id, quantity):
        remaining = max(0, int(quantity))
        container = self.recipe_container_for_item(item_id)

        if container and remaining > 0:
            stored = self.server.db.storage_qty(
                self.account_id, container, item_id
            )
            take = min(stored, remaining)
            if take > 0:
                if not self.server.db.remove_storage_item(
                    self.account_id, container, item_id, take
                ):
                    return False
                remaining -= take

        if remaining > 0:
            if not self.server.db.remove_item(
                self.account_id, item_id, remaining
            ):
                return False
            remaining = 0

        return True

    def recipe_station_text(self, stations):
        return " lub ".join(ROOMS[room_id]["name"] for room_id in stations)

    def recipe_ingredients_text(self, recipe):
        return ", ".join(
            f"{ITEMS[item_id]['name']} x{quantity}"
            for item_id, quantity in recipe["ingredients"].items()
        )

    async def show_recipes(self, mode=""):
        mode = self.normalize_description_query(mode)
        craft_modes = {
            "craft", "stworz", "rzemioslo", "kowalstwo",
            "smithing", "blacksmithing", "kuj",
        }
        cook_modes = {
            "cook", "gotuj", "gotowanie",
        }
        alchemy_modes = {
            "alchemy", "alchemia",
        }
        jewel_modes = {
            "jubilerstwo", "jewelcrafting", "jewelry",
            "bizuteria", "biżuteria", "jub",
        }

        if not mode:
            show_craft = show_cook = show_alchemy = show_jewel = True
        elif mode in craft_modes:
            show_craft = True
            show_cook = False
            show_alchemy = False
            show_jewel = False
        elif mode in cook_modes:
            show_craft = False
            show_cook = True
            show_alchemy = False
            show_jewel = False
        elif mode in alchemy_modes:
            show_craft = False
            show_cook = False
            show_alchemy = True
            show_jewel = False
        elif mode in jewel_modes:
            show_craft = False
            show_cook = False
            show_alchemy = False
            show_jewel = True
        else:
            show_craft = show_cook = show_alchemy = show_jewel = True

        if show_craft:
            await self.send("RECEPTURY RZEMIOSŁA I KOWALSTWA")
            for recipe in CRAFT_RECIPES.values():
                await self.send(
                    f"{recipe['name']}. Składniki: "
                    f"{self.recipe_ingredients_text(recipe)}. "
                    f"Miejsce: {self.recipe_station_text(recipe['stations'])}. "
                    f"{self.recipe_level_requirement_text(CRAFT_RECIPES, recipe)} "
                    f"{recipe['desc']}"
                )

        if show_cook:
            await self.send("RECEPTURY GOTOWANIA")
            for recipe in COOK_RECIPES.values():
                await self.send(
                    f"{recipe['name']}. Składniki: "
                    f"{self.recipe_ingredients_text(recipe)}. "
                    f"Miejsce: {self.recipe_station_text(recipe['stations'])}. "
                    f"{self.recipe_level_requirement_text(COOK_RECIPES, recipe)} "
                    f"{recipe['desc']}"
                )

        if show_alchemy:
            await self.send("RECEPTURY ALCHEMII")
            for recipe in ALCHEMY_RECIPES.values():
                await self.send(
                    f"{recipe['name']}. Składniki: "
                    f"{self.recipe_ingredients_text(recipe)}. "
                    f"Miejsce: {self.recipe_station_text(recipe['stations'])}. "
                    f"{self.recipe_level_requirement_text(ALCHEMY_RECIPES, recipe)} "
                    f"{recipe['desc']}"
                )

        if show_jewel:
            await self.send("RECEPTURY JUBILERSTWA")
            for recipe in JEWELCRAFT_RECIPES.values():
                await self.send(
                    f"{recipe['name']}. Składniki: "
                    f"{self.recipe_ingredients_text(recipe)}. "
                    f"Miejsce: {self.recipe_station_text(recipe['stations'])}. "
                    f"{self.recipe_level_requirement_text(JEWELCRAFT_RECIPES, recipe)} "
                    f"{recipe['desc']}"
                )

    def recipe_level_requirement_text(self, recipes, recipe):
        tool_type, _item_id, tool_name = self.recipe_tool_info(recipes)
        required = max(
            1, int(recipe.get("min_tool_level", 1))
        )
        parts = [
            f"{tool_name} level {required}"
        ]
        if (
            recipes is CRAFT_RECIPES
            and "min_profession_level" in recipe
        ):
            parts.append(
                "Kowalstwo level "
                f"{max(1, int(recipe.get('min_profession_level', 1)))}"
            )
        if (
            recipes is JEWELCRAFT_RECIPES
            and "min_profession_level" in recipe
        ):
            parts.append(
                "Jubilerstwo level "
                f"{max(1, int(recipe.get('min_profession_level', 1)))}"
            )
        return "Wymaga: " + ", ".join(parts) + "."

    def recipe_tool_info(self, recipes):
        if recipes is CRAFT_RECIPES:
            return "crafting", "crafting_hammer", "Młot Rzemieślniczy"
        if recipes is ALCHEMY_RECIPES:
            return "alchemy", "alchemy_mortar", "Moździerz Alchemiczny"
        if recipes is JEWELCRAFT_RECIPES:
            return "jewelcrafting", "jeweler_pliers", "Szczypce Jubilerskie"
        return "cooking", "chef_knife", "Nóż Kucharski"

    async def perform_recipe(self, query, recipes, action_name):
        if self.combat_mob_key:
            await self.send(
                f"Nie możesz wykonywać akcji {action_name} podczas walki."
            )
            return False

        tool_type, tool_item_id, tool_name = self.recipe_tool_info(recipes)
        if self.server.db.item_qty(self.account_id, tool_item_id) <= 0:
            if tool_type == "crafting":
                await self.send(
                    "Do Rzemiosła potrzebujesz Młota Rzemieślniczego. "
                    "Kup go u Kowala Dorana w Kuźni Dusz."
                )
            elif tool_type == "alchemy":
                await self.send(
                    "Do Alchemii potrzebujesz Moździerza Alchemicznego. "
                    "Kup go w Chacie Zielarki."
                )
            elif tool_type == "jewelcrafting":
                await self.send(
                    "Do Jubilerstwa potrzebujesz Szczypiec Jubilerskich. "
                    "Kup je u Jubilerki Mirelli w Pracowni Jubilerskiej."
                )
            else:
                await self.send(
                    "Do Gotowania potrzebujesz Noża Kucharskiego. "
                    "Kup go w Karczmie Pod Błękitnym Płomieniem."
                )
            return False

        found = find_by_name(recipes, query)
        if not found:
            await self.send("Nie rozpoznaję tej receptury. Wpisz receptury.")
            return False

        recipe_id, recipe = found

        tool_row = self.server.db.tool(self.account_id, tool_type)
        old_tool_level = int(tool_row["level"])
        required_level = max(
            1, int(recipe.get("min_tool_level", 1))
        )
        if old_tool_level < required_level:
            await self.send(
                f"{recipe['name']} wymaga {tool_name} level "
                f"{required_level}, a masz {old_tool_level}."
            )
            return False

        if (
            recipes is CRAFT_RECIPES
            and "min_profession_level" in recipe
        ):
            blacksmith_row = self.server.db.profession(
                self.account_id, "Kowalstwo"
            )
            blacksmith_level = int(
                blacksmith_row["level"]
            )
            required_profession = max(
                1,
                int(
                    recipe.get(
                        "min_profession_level", 1
                    )
                ),
            )
            if blacksmith_level < required_profession:
                await self.send(
                    f"{recipe['name']} wymaga Kowalstwa level "
                    f"{required_profession}, a masz "
                    f"{blacksmith_level}."
                )
                return False

        if (
            recipes is JEWELCRAFT_RECIPES
            and "min_profession_level" in recipe
        ):
            jewel_row = self.server.db.profession(
                self.account_id, "Jubilerstwo"
            )
            jewel_level = int(jewel_row["level"])
            required_profession = max(
                1,
                int(recipe.get("min_profession_level", 1)),
            )
            if jewel_level < required_profession:
                await self.send(
                    f"{recipe['name']} wymaga Jubilerstwa level "
                    f"{required_profession}, a masz "
                    f"{jewel_level}."
                )
                return False

        if self.character.room_id not in recipe["stations"]:
            await self.send(
                f"Tę recepturę wykonasz w: "
                f"{self.recipe_station_text(recipe['stations'])}."
            )
            return False

        missing = []
        for item_id, quantity in recipe["ingredients"].items():
            have = self.available_recipe_item(item_id)
            if have < quantity:
                missing.append(
                    f"{ITEMS[item_id]['name']}: masz {have}, potrzeba {quantity}"
                )

        if missing:
            await self.send("Brakuje składników:")
            for line in missing:
                await self.send(line + ".")
            return False

        action_seconds = self.tool_action_seconds(
            tool_type, old_tool_level
        )
        await self.send(
            f"Rozpoczynasz {action_name}. "
            f"{self.tool_action_label(tool_type)}: "
            f"{action_seconds} sekund."
        )
        await asyncio.sleep(action_seconds)

        for item_id, quantity in recipe["ingredients"].items():
            if not self.consume_recipe_item(item_id, quantity):
                await self.send(
                    "Nie udało się pobrać składników. Receptura przerwana."
                )
                return False

        output_id = recipe["output"]
        quantity = int(recipe.get("quantity", 1))

        tier = tool_tier(old_tool_level)
        bonus_chance = tool_tier_bonus_chance(old_tool_level)

        bonus_quantity = 0
        if bonus_chance > 0 and random.random() < bonus_chance:
            bonus_quantity = quantity

        total_quantity = quantity + bonus_quantity
        self.server.db.add_item(
            self.account_id, output_id, total_quantity
        )

        await self.send(
            f"{action_name.capitalize()}: {ITEMS[output_id]['name']} "
            f"x{quantity}. Przedmiot trafia do zwykłego ekwipunku."
        )

        if bonus_quantity > 0:
            if tool_type == "cooking":
                await self.send(
                    f"Bonus Tieru {tier} Noża Kucharskiego: "
                    f"przygotowujesz dodatkowo "
                    f"{ITEMS[output_id]['name']} "
                    f"x{bonus_quantity}."
                )
            elif tool_type == "alchemy":
                await self.send(
                    f"Bonus Tieru {tier} Moździerza Alchemicznego: "
                    f"warzysz dodatkowo "
                    f"{ITEMS[output_id]['name']} "
                    f"x{bonus_quantity}."
                )
            elif tool_type == "jewelcrafting":
                await self.send(
                    f"Bonus Tieru {tier} Szczypiec Jubilerskich: "
                    f"wykonujesz dodatkowo "
                    f"{ITEMS[output_id]['name']} "
                    f"x{bonus_quantity}."
                )
            else:
                await self.send(
                    f"Bonus Tieru {tier} Młota Rzemieślniczego: "
                    f"wytwarzasz dodatkowo "
                    f"{ITEMS[output_id]['name']} "
                    f"x{bonus_quantity}."
                )

        if tool_type in (
            "alchemy", "cooking", "crafting",
            "jewelcrafting",
        ):
            await self.announce_craft_quest_progress(
                output_id,
                total_quantity,
            )

        tool_xp = int(
            recipe.get("tool_xp", 8 + random.randint(0, 4))
        )
        if tool_type == "alchemy":
            messages, alchemy_level, new_tool_level = (
                self.grant_profession_progress(
                    "Alchemia",
                    10 + random.randint(0, 5),
                    "alchemy",
                    tool_xp,
                )
            )
        elif tool_type == "jewelcrafting":
            profession_xp = int(
                recipe.get(
                    "profession_xp",
                    10 + random.randint(0, 5),
                )
            )
            messages, jewel_level, new_tool_level = (
                self.grant_profession_progress(
                    "Jubilerstwo",
                    profession_xp,
                    "jewelcrafting",
                    tool_xp,
                )
            )
        elif (
            tool_type == "crafting"
            and self.character.room_id == "forge"
        ):
            profession_xp = int(
                recipe.get(
                    "profession_xp",
                    10 + random.randint(0, 5),
                )
            )
            messages, blacksmith_level, new_tool_level = (
                self.grant_profession_progress(
                    "Kowalstwo",
                    profession_xp,
                    "crafting",
                    tool_xp,
                )
            )
        else:
            messages, new_tool_level = (
                self.grant_tool_progress(
                    tool_type, tool_xp
                )
            )
        for message in messages:
            await self.send(message)

        if new_tool_level != old_tool_level:
            await self.send(
                f"{tool_name} ma teraz level {new_tool_level}, "
                f"Tier {tool_tier(new_tool_level)}: "
                f"{tool_tier_name(tool_type, new_tool_level)}."
            )

        return True

    async def show_jewelcrafting_info(self):
        await self.send("JUBILERSTWO")
        row = self.server.db.profession(
            self.account_id, "Jubilerstwo"
        )
        level = int(row["level"])
        max_level = profession_max_level("Jubilerstwo")
        rank = profession_rank(level, "Jubilerstwo")
        xp_text = (
            "maksimum"
            if level >= max_level
            else (
                f"{row['xp']} z "
                f"{self.profession_xp_to_next(level, 'Jubilerstwo')}"
            )
        )
        await self.send(
            f"Level {level} z {max_level}. "
            f"Ranga {rank} z {profession_max_rank('Jubilerstwo')}: "
            f"{profession_rank_name('Jubilerstwo', level)}. "
            f"XP: {xp_text}. Akcje: {row['actions']}."
        )
        await self.send(
            "Narzędzie: Szczypce Jubilerskie, level 1-200 i 13 Tierów. "
            "Kupisz je wyłącznie u Jubilerki Mirelli w Pracowni Jubilerskiej."
        )
        await self.send(
            "Receptury: wpisz receptury jubilerstwo. "
            "Wykonywanie: jub <nazwa receptury>."
        )
        await self.send(
            "Jubilerka Mirella prowadzi 9-etapowy łańcuch zleceń "
            "od Żelaza do Eternium."
        )

    async def show_blacksmithing_info(self):
        await self.send("KOWALSTWO")
        row = self.server.db.profession(
            self.account_id, "Kowalstwo"
        )
        level = int(row["level"])
        max_level = profession_max_level("Kowalstwo")
        rank = profession_rank(level, "Kowalstwo")
        xp_text = (
            "maksimum"
            if level >= max_level
            else (
                f"{row['xp']} z "
                f"{self.profession_xp_to_next(level, 'Kowalstwo')}"
            )
        )
        await self.send(
            f"Kowalstwo: level {level} z "
            f"{max_level}. "
            f"Ranga {rank} z "
            f"{profession_max_rank('Kowalstwo')}: "
            f"{profession_rank_name('Kowalstwo', level)}. "
            f"XP: {xp_text}."
        )
        await self.show_single_tool("crafting")
        await self.send(
            "Kowalstwo rozwija się podczas przetapiania metalu "
            "i kucia przedmiotów w Kuźni Dusz."
        )
        await self.send(
            "Komendy: kowalstwo, przetop <metal>, "
            "kuj <receptura>, craft <receptura>, "
            "receptury kowalstwo."
        )
        await self.send(
            "Materiały przechodzą od Żelaza, Srebra i Złota "
            "aż do Kobaltu, Run, Smoczej Stali, Astralu, "
            "Pustki i Eternium."
        )
        await self.send(
            "Mistrz Rzemiosła Haldor daje powtarzalne "
            "zlecenia Kowalstwa/Rzemiosła. "
            "Każde odnawia się dokładnie co 60 minut."
        )

    async def show_cooking_info(self):
        await self.send("GOTOWANIE")
        await self.show_single_tool("cooking")
        await self.send(
            "Gotowanie jest systemem opartym na Nożu Kucharskim level 1-200. "
            "Nie tworzy osobnego levelu postaci ani osobnej profesji."
        )
        await self.send(
            "Gotować możesz w Karczmie Pod Błękitnym Płomieniem "
            "albo na Targu Rybnym."
        )
        await self.send(
            "Komendy: gotuj <potrawa>, receptury cook, gotowanie."
        )
        await self.send(
            "Niższe receptury prowadzą przez levele Noża 1-99, "
            "a endgame zaczyna się od levelu 100 i kończy na 200."
        )
        await self.send(
            "Wyższy Tier Noża może przygotować dodatkową porcję. "
            "Gotowanie daje XP wyłącznie Nożowi Kucharskiemu."
        )

    def resolve_smelt_recipe(self, query):
        wanted = self.normalize_description_query(query)
        if not wanted:
            return None

        extra_aliases = {
            "iron": (
                "zelazo", "żelazo", "zelazna", "żelazna",
                "ruda zelaza", "ruda żelaza", "iron",
            ),
            "silver": (
                "srebro", "srebrna", "ruda srebra", "silver",
            ),
            "gold": (
                "zloto", "złoto", "zlota", "złota",
                "ruda zlota", "ruda złota", "gold",
            ),
            "cobalt": (
                "kobalt", "kobaltowa", "ruda kobaltu", "cobalt",
            ),
            "runic": (
                "runa", "runiczna", "runiczny", "kamien runiczny",
                "kamień runiczny", "runestone", "runic",
            ),
            "dragonsteel": (
                "smocza stal", "smoczej stali", "dragonsteel",
            ),
            "astral": (
                "astral", "astralna", "astralny",
            ),
            "void": (
                "pustka", "pustki", "void",
            ),
            "eternium": (
                "eternium",
            ),
        }

        exact = []
        partial = []

        for tier in BLACKSMITH_TIERS:
            recipe_id = tier["ingot"]
            recipe = CRAFT_RECIPES.get(recipe_id)
            if not recipe:
                continue

            names = [
                recipe_id,
                recipe.get("name", ""),
                tier["key"],
                tier.get("name", ""),
                tier["ore"],
                ITEMS.get(tier["ore"], {}).get("name", ""),
                ITEMS.get(recipe_id, {}).get("name", ""),
            ]
            names.extend(extra_aliases.get(tier["key"], ()))

            normalized = {
                self.normalize_description_query(name)
                for name in names
                if name
            }

            if wanted in normalized:
                exact.append((recipe_id, recipe))
            elif any(
                wanted in name
                for name in normalized
            ):
                partial.append((recipe_id, recipe))

        if exact:
            return exact[0]
        if len(partial) == 1:
            return partial[0]
        return None

    async def smelt_item(self, query):
        query = str(query or "").strip()

        if not query:
            await self.send(
                "Użycie: przetop <metal albo ruda>. "
                "Przykłady: przetop żelazo, przetop srebro, "
                "przetop kobalt, przetop Eternium."
            )
            return False

        found = self.resolve_smelt_recipe(query)
        if not found:
            await self.send(
                "Nie rozpoznaję metalu do przetopienia. "
                "Dostępne: żelazo, srebro, złoto, kobalt, "
                "runa, smocza stal, astral, pustka, Eternium."
            )
            return False

        recipe_id, recipe = found
        return await self.perform_recipe(
            recipe["name"],
            CRAFT_RECIPES,
            "przetapianie",
        )

    async def craft_item(self, query):
        return await self.perform_recipe(query, CRAFT_RECIPES, "rzemiosło")

    async def jewelcraft_item(self, query):
        return await self.perform_recipe(
            query,
            JEWELCRAFT_RECIPES,
            "jubilerstwo",
        )

    async def cook_item(self, query):
        return await self.perform_recipe(query, COOK_RECIPES, "gotowanie")

    async def alchemy_item(self, query):
        return await self.perform_recipe(query, ALCHEMY_RECIPES, "alchemia")

    async def inventory(self):
        rows = self.server.db.inventory(self.account_id)
        await self.send(
            f"Waluta: {self.character.silver} srebrnych monet, "
            f"{self.character.gold} złotych monet, "
            f"{self.character.mithril} mithrilowych monet."
        )
        await self.send(
            "Siatka na ryby, Sakwa górnicza, Stos drewna i Torba Zielarska "
            "są osobnymi magazynami; użyj siatka/net, sakwa/bag, drewno/stos "
            "oraz ziola/herbs."
        )
        if not rows:
            await self.send("Ekwipunek jest pusty.")
            return
        await self.send("Ekwipunek:")
        for row in rows:
            item = ITEMS.get(row["item_id"], {"name": row["item_id"], "desc": ""})
            await self.send(f"{item['name']} x{row['quantity']}. {item.get('desc','')}")

    async def equipment(self):
        rows = self.server.db.equipment(self.account_id)
        if not rows:
            await self.send("Nie masz założonego dodatkowego wyposażenia.")
            return
        await self.send("Założone wyposażenie:")
        for row in rows:
            item = ITEMS.get(row["item_id"])
            name = item["name"] if item else row["item_id"]
            defense = item.get("defense", 0) if item else 0
            slot_names = {
                "head": "Głowa",
                "body": "Korpus",
                "hands": "Dłonie",
                "legs": "Nogi",
                "feet": "Stopy",
                "charm": "Talizman",
                "ring": "Pierścień",
                "necklace": "Naszyjnik",
            }
            slot_name = slot_names.get(row["slot"], row["slot"])
            extra = ""
            if item and item.get("rarity_name"):
                extra += f" Rzadkość: {item['rarity_name']}."
            if item and item.get("affix"):
                affix_name = CRYPT_AFFIXES.get(
                    item["affix"], item["affix"]
                )
                extra += (
                    f" Bonus: {affix_name} "
                    f"+{item.get('affix_amount', 0)}."
                )
            await self.send(
                f"{slot_name}: {name}. Obrona +{defense}.{extra}"
            )
        await self.send(self.crypt_set_bonus_text())
        await self.send(self.astral_set_bonus_text())

    def owned_armor_for_slot(self, slot):
        candidates = []
        for item_id, item in ITEMS.items():
            if item.get("type") != "armor":
                continue
            if item.get("slot") != slot:
                continue
            required_class = item.get("required_class")
            if (
                required_class
                and required_class
                not in self.active_class_names()
            ):
                continue
            quantity = self.server.db.item_qty(
                self.account_id, item_id
            )
            if quantity <= 0:
                continue

            rarity_order = {
                "common": 0,
                "crafted": 1,
                "rare": 2,
                "epic": 3,
                "legendary": 4,
                "mythic": 5,
            }
            score = (
                int(item.get("defense", 0)),
                rarity_order.get(item.get("rarity"), 0),
                int(item.get("affix_amount", 0)),
                normalize_lookup_text(item.get("name", item_id)),
            )
            candidates.append((score, item_id, item))

        candidates.sort(key=lambda entry: entry[0], reverse=True)
        return candidates

    def resolve_equipment_for_equip(self, query):
        normalized = normalize_lookup_text(query)
        slot = EQUIPMENT_SLOT_ALIASES.get(normalized)

        if slot:
            candidates = self.owned_armor_for_slot(slot)
            if not candidates:
                return None, slot, []
            _score, item_id, item = candidates[0]
            return (item_id, item), slot, candidates

        # Pełna lub jednoznaczna nazwa konkretnego pancerza/dropu.
        owned_armor = {
            item_id: item
            for item_id, item in ITEMS.items()
            if (
                item.get("type") == "armor"
                and self.server.db.item_qty(
                    self.account_id, item_id
                ) > 0
            )
        }
        found = find_by_name(owned_armor, query)
        return found, None, []

    async def equip_item(self, query):
        if self.combat_mob_key:
            await self.send(
                "Nie możesz zmieniać ekwipunku podczas walki turowej. "
                "Najpierw użyj flee albo zakończ walkę."
            )
            return

        found, requested_slot, slot_candidates = (
            self.resolve_equipment_for_equip(query)
        )

        if not found:
            if requested_slot:
                await self.send(
                    f"Nie masz żadnego pancerza w slocie "
                    f"{EQUIPMENT_SLOT_NAMES[requested_slot]}."
                )
                return
            await self.send(
                "Nie rozpoznaję posiadanego pancerza. "
                "Możesz wpisać: załóż hełm, załóż zbroja, "
                "załóż rękawice, załóż nogi, załóż buty, "
                "załóż talizman, załóż pierścień "
                "albo załóż naszyjnik."
            )
            return

        item_id, item = found
        if item.get("type") != "armor":
            await self.send("Tego przedmiotu nie można założyć.")
            return

        required_class = item.get("required_class")
        if (
            required_class
            and required_class
            not in self.active_class_names()
        ):
            await self.send(
                f"{item['name']} wymaga aktywnej klasy "
                f"{required_class}."
            )
            return

        if self.server.db.item_qty(self.account_id, item_id) <= 0:
            await self.send("Nie masz tego przedmiotu.")
            return

        self.server.db.equip(
            self.account_id, item["slot"], item_id
        )
        self.current_hp = min(self.current_hp, self.max_hp())
        self.current_mana = min(
            self.current_mana, self.max_mana()
        )

        extra = ""
        if requested_slot and len(slot_candidates) > 1:
            extra = (
                f" Wybrano najlepszy posiadany przedmiot dla slotu "
                f"{EQUIPMENT_SLOT_NAMES[item['slot']]}."
            )

        rarity = (
            f" Rzadkość: {item['rarity_name']}."
            if item.get("rarity_name")
            else ""
        )
        affix = ""
        if item.get("affix"):
            affix_name = CRYPT_AFFIXES.get(
                item["affix"], item["affix"]
            )
            affix = (
                f" Bonus: {affix_name} "
                f"+{item.get('affix_amount', 0)}."
            )

        await self.send(
            f"Zakładasz: {item['name']}. "
            f"Slot: {EQUIPMENT_SLOT_NAMES.get(item['slot'], item['slot'])}. "
            f"Obrona przedmiotu +{item.get('defense', 0)}."
            f"{rarity}{affix}{extra}"
        )
        await self.send(
            f"Obrona fizyczna wynosi teraz {self.defense()}."
        )
        await self.send(self.crypt_set_bonus_text())
        await self.send(self.astral_set_bonus_text())

    def find_consumable_for_use(self, query):
        q = self.normalize_description_query(query)
        if not q:
            return None, []

        # Celowe krótkie aliasy wymagane dla szybkiej obsługi NVDA.
        direct_aliases = {
            "mikstura": "healing_potion",
            "miksture": "healing_potion",
            "miksturę": "healing_potion",
            "potion": "healing_potion",
            "eliksir": "soul_elixir",
            "elixir": "soul_elixir",
            "eliksir duszy": "soul_elixir",
            "soul elixir": "soul_elixir",
            "mana": "mana_potion",
            "mikstura many": "mana_potion",
            "mana potion": "mana_potion",
        }
        item_id = direct_aliases.get(q)
        if item_id:
            return (item_id, ITEMS[item_id]), []

        consumables = {
            item_id: item
            for item_id, item in ITEMS.items()
            if item.get("type") == "consumable"
        }

        exact = []
        partial = []
        for item_id, item in consumables.items():
            names = (
                item_id,
                item.get("name", ""),
            )
            normalized_names = [
                self.normalize_description_query(name)
                for name in names
            ]
            if q in normalized_names:
                exact.append((item_id, item))
            elif any(q in name for name in normalized_names):
                partial.append((item_id, item))

        if exact:
            return exact[0], []
        if len(partial) == 1:
            return partial[0], []
        if len(partial) > 1:
            return None, partial
        return None, []

    async def use_item(self, query):
        raw_query = str(query or "").strip()
        lowered = raw_query.lower()

        # Wygodna składnia dla umiejętności:
        # użyj umiejętność <nazwa> [cel]
        # use skill <name> [target]
        skill_prefixes = (
            "skill ",
            "umiejętność ",
            "umiejetnosc ",
            "zdolność ",
            "zdolnosc ",
            "czar ",
            "spell ",
        )
        for prefix in skill_prefixes:
            if lowered.startswith(prefix):
                skill_query = raw_query[len(prefix):].strip()
                if not skill_query:
                    await self.send(
                        "Użycie: użyj umiejętność <nazwa> [cel] "
                        "albo use skill <name> [target]."
                    )
                    return
                await self.use_class_skill(skill_query)
                return

        found, ambiguous = self.find_consumable_for_use(raw_query)

        if ambiguous:
            names = ", ".join(item["name"] for _, item in ambiguous)
            await self.send(
                f"Nazwa pasuje do kilku przedmiotów: {names}. "
                "Podaj dokładniejszą nazwę."
            )
            return

        if not found:
            skill, _target = self.find_skill_from_input(raw_query)
            if skill:
                await self.use_class_skill(raw_query)
                return

            await self.send(
                "Nie rozpoznaję przedmiotu ani umiejętności. "
                "Przykłady: użyj mikstura; użyj umiejętność <nazwa> [cel]; "
                "use skill <name> [target]."
            )
            return

        item_id, item = found

        if self.server.db.item_qty(self.account_id, item_id) <= 0:
            await self.send(f"Nie masz przedmiotu: {item['name']}.")
            return

        if item.get("type") != "consumable":
            await self.send("Tego przedmiotu nie używa się w ten sposób.")
            return

        if "heal" in item or "mana" in item:
            max_hp = self.max_hp()
            max_mana = self.max_mana()

            missing_hp = max(0, max_hp - self.current_hp)
            missing_mana = max(0, max_mana - self.current_mana)

            can_restore_hp = (
                item.get("heal", 0) > 0
                and missing_hp > 0
            )
            can_restore_mana = (
                item.get("mana", 0) > 0
                and max_mana > 0
                and missing_mana > 0
            )

            if not can_restore_hp and not can_restore_mana:
                if max_mana > 0:
                    await self.send("Masz pełne HP i Manę.")
                else:
                    await self.send("Masz pełne życie.")
                return

            self.server.db.remove_item(
                self.account_id, item_id, 1
            )

            healed = 0
            restored_mana = 0

            if can_restore_hp:
                healed = min(
                    item.get("heal", 0), missing_hp
                )
                self.current_hp += healed

            if can_restore_mana:
                restored_mana = min(
                    item.get("mana", 0), missing_mana
                )
                self.current_mana += restored_mana

            parts = []
            if healed:
                parts.append(f"{healed} HP")
            if restored_mana:
                parts.append(f"{restored_mana} Many")

            await self.send(
                f"Używasz {item['name']}. Odzyskujesz "
                + " i ".join(parts) + "."
            )
            await self.send(
                f"HP {self.current_hp} z {max_hp}."
            )
            if max_mana > 0:
                await self.send(
                    f"Mana {self.current_mana} z {max_mana}."
                )

            if self.combat_mob_key:
                await self.send(
                    "Zużywasz swoją turę na użycie przedmiotu."
                )
                await self.enemy_counterattack(
                    self.server.world.mobs.get(
                        self.combat_mob_key
                    )
                )
            return

        if "soul_xp" in item:
            self.server.db.remove_item(
                self.account_id, item_id, 1
            )
            await self.send(
                f"Używasz {item['name']}."
            )
            await self.grant_soul_xp(
                item["soul_xp"]
            )
            self.server.db.save_character(self.character)

            if self.combat_mob_key:
                await self.send(
                    "Zużywasz swoją turę na użycie przedmiotu."
                )
                await self.enemy_counterattack(
                    self.server.world.mobs.get(
                        self.combat_mob_key
                    )
                )
            return

        await self.send(
            "Ten przedmiot nie ma efektu do użycia."
        )


    async def shop(self):
        offers = SHOPS.get(self.character.room_id)
        if not offers:
            await self.send("W tej lokacji nie ma sklepu.")
            return
        seller_id = SHOP_SELLERS.get(
            self.character.room_id
        )
        seller = NPCS.get(seller_id) if seller_id else None
        seller_text = (
            f" Sprzedawca: {seller['name']}."
            if seller
            else ""
        )
        await self.send(
            f"Oferta sklepu. Rabat Charyzmy: "
            f"{self.character.shop_discount_percent()} procent."
            f"{seller_text}"
        )
        for number, item_id in enumerate(offers, 1):
            item = ITEMS[item_id]
            currency = item.get("currency", "gold")
            currency_pl = {"silver": "srebra", "gold": "złota", "mithril": "mithrilu"}[currency]
            extra = ""
            if item.get("type") == "armor":
                extra = (
                    f" Slot: {item.get('slot', 'brak')}. "
                    f"Obrona +{item.get('defense', 0)}."
                )
                if item.get("required_class"):
                    required_class = item["required_class"]
                    availability = (
                        "aktywna"
                        if required_class
                        in self.active_class_names()
                        else "nieaktywna"
                    )
                    extra += (
                        f" Klasa: {required_class}; "
                        f"{availability}."
                    )
            cashback = self.shop_cashback_silver(item)
            discount_text = (
                f" Zwrot z rabatu: {cashback} srebra."
                if cashback > 0 else ""
            )
            await self.send(
                f"{number}. {item['name']}: {item['price']} {currency_pl}."
                f"{discount_text}{extra} {item['desc']}"
            )

    async def buy(self, query):
        normalized_query = normalize_lookup_text(query)
        requested_tool = TOOL_BUY_ALIASES.get(normalized_query)

        offers = SHOPS.get(self.character.room_id)
        if not offers:
            if requested_tool:
                target_room = TOOL_SHOP_ROOMS[requested_tool]
                await self.send(
                    f"{ITEMS[requested_tool]['name']} kupisz w lokacji "
                    f"{ROOMS[target_room]['name']}. "
                    f"Możesz użyć walk {target_room.replace('_', ' ')}."
                )
                return
            await self.send("W tej lokacji nie ma sklepu.")
            return

        possible = {item_id: ITEMS[item_id] for item_id in offers}

        found = None
        if requested_tool and requested_tool in possible:
            found = (requested_tool, possible[requested_tool])
        if not found:
            found = find_by_name(possible, query)

        if not found:
            if requested_tool:
                target_room = TOOL_SHOP_ROOMS[requested_tool]
                await self.send(
                    f"{ITEMS[requested_tool]['name']} nie jest sprzedawana tutaj. "
                    f"Kupisz ją w lokacji {ROOMS[target_room]['name']}."
                )
                return
            await self.send("Tego przedmiotu nie ma w ofercie.")
            return

        item_id, item = found

        required_class = item.get("required_class")
        if (
            required_class
            and required_class
            not in self.active_class_names()
        ):
            await self.send(
                f"{item['name']} jest wyposażeniem klasy "
                f"{required_class}. Aktywuj tę klasę, aby kupić "
                "ten przedmiot."
            )
            return

        price = item["price"]
        currency = item.get("currency", "gold")
        currency_pl = {"silver": "srebra", "gold": "złota", "mithril": "mithrilu"}[currency]
        current = getattr(self.character, currency)
        if current < price:
            await self.send(f"Masz za mało waluty: {currency_pl}.")
            return
        setattr(self.character, currency, current - price)
        cashback = self.shop_cashback_silver(item)
        if cashback > 0:
            self.character.silver += cashback
        self.server.db.add_item(self.account_id, item_id, 1)
        if item.get("type") == "tool":
            self.server.db.ensure_tool(self.account_id, item["tool_type"])
        self.server.db.save_character(self.character)
        await self.send(f"Kupujesz {item['name']} za {price} {currency_pl}.")
        if cashback > 0:
            await self.send(
                f"Rabat Charyzmy: sprzedawca zwraca ci "
                f"{cashback} srebra."
            )

    async def show_teachers(self):
        teachers = [
            (npc_id, npc) for npc_id, npc in NPCS.items()
            if npc.get("teacher_class")
        ]
        await self.send("Nauczyciele klasowi rozmieszczeni po Gildii Dusz:")
        for number, (npc_id, npc) in enumerate(teachers, 1):
            own = (
                " Aktywna klasa."
                if npc["teacher_class"] in self.active_class_names()
                else ""
            )
            room_name = ROOMS[npc["room"]]["name"]
            await self.send(
                f"{number}. {npc['name']}. Klasa: {npc['teacher_class']}. "
                f"Lokacja: {room_name}.{own}"
            )
        await self.send(
            "Użyj prowadz <nazwa lokacji>, aby dojść do odpowiedniej sali, "
            "potem talk <nauczyciel>."
        )


    async def teacher_lesson(self, npc):
        class_name = npc["teacher_class"]
        learned = self.server.db.learned_skill_ids(self.account_id)

        await self.send(
            f"Lekcja klasy {class_name}. {CLASS_DESCRIPTIONS.get(class_name, '')}"
        )

        for number, skill in enumerate(CLASS_SKILLS.get(class_name, []), 1):
            progress = ""
            if class_name not in self.active_class_names():
                status = f"wymaga aktywnej klasy {class_name} i Soul Level {skill['unlock']}"
            elif skill["id"] in learned:
                row = self.server.db.skill_progress(self.account_id, skill["id"])
                status = "już nauczona"
                if int(row["level"]) >= SKILL_MAX_LEVEL:
                    progress = f" Skill Level {SKILL_MAX_LEVEL}, maksymalny."
                else:
                    progress = (
                        f" Skill Level {row['level']}, XP {row['xp']} z "
                        f"{skill_xp_to_next(int(row['level']))}."
                    )
            elif self.character.soul_level >= skill["unlock"]:
                status = "możesz nauczyć się teraz"
            else:
                status = f"zablokowana do Soul Level {skill['unlock']}"

            mana = f" Mana {skill.get('mana', 0)}." if skill.get("mana", 0) else ""
            await self.send(
                f"{number}. {skill['name']}. {status}.{progress} "
                f"Cooldown bazowy {skill['cooldown']} sekund.{mana} {skill['desc']}"
            )

        if class_name in self.active_class_names():
            role = (
                "głównej" if class_name == self.character.class_name
                else "dodatkowej aktywnej"
            )
            await self.send(
                f"To jest nauczyciel twojej {role} klasy {class_name}. "
                f"Aktualny Soul Level: {self.character.soul_level}."
            )
            await self.send(
                "Nauka: learn <numer>, naucz <pełna nazwa> albo "
                "naturalnie, np. naucz leczenie, naucz tarcza, "
                "naucz ciecie, naucz pocisk, naucz ogien. "
                f"Każdy nauczony skill rozwija własny Skill Level 1-{SKILL_MAX_LEVEL}."
            )
        else:
            await self.send(
                f"Klasa {class_name} nie jest teraz aktywna. "
                "Dodaj ją przez multiclass add <klasa>, aby móc się uczyć."
            )


    def quest_collect_category_info(self, target):
        mapping = {
            "fish": (FISH_STORAGE_IDS, "net", "ryb"),
            "ore": (ORE_STORAGE_IDS, "bag", "rud"),
            "wood": (WOOD_STORAGE_IDS, "woodpile", "sztuk drewna"),
            "herb": (HERB_STORAGE_IDS, "herbbag", "ziół"),
        }
        return mapping.get(target)

    def resource_quest_container(self, item_id):
        if item_id in FISH_STORAGE_IDS:
            return "net"
        if item_id in ORE_STORAGE_IDS:
            return "bag"
        if item_id in WOOD_STORAGE_IDS:
            return "woodpile"
        if item_id in HERB_STORAGE_IDS:
            return "herbbag"
        return None

    def resource_quest_have(self, item_id):
        container = self.resource_quest_container(item_id)
        if not container:
            return self.server.db.item_qty(
                self.account_id, item_id
            )
        return (
            self.server.db.total_items_across_storage_and_inventory(
                self.account_id,
                {item_id},
                container,
            )
        )

    async def announce_resource_quest_progress(
        self, item_id, amount=1
    ):
        changed = self.server.db.increment_resource_quest(
            self.account_id,
            item_id,
            amount,
        )
        for quest_id, progress, needed in changed:
            quest = QUESTS[quest_id]
            name = ITEMS[item_id]["name"]
            if progress >= needed:
                await self.send(
                    f"Postęp questa: {quest['name']}. "
                    f"Zdobyłeś: {name}. "
                    f"Postęp {progress} z {needed}. "
                    "Cel wykonany."
                )
            else:
                await self.send(
                    f"Postęp questa: {quest['name']}. "
                    f"Zdobyłeś: {name}. "
                    f"Postęp {progress} z {needed}."
                )

    def craft_set_progress(self, row, quest):
        targets = tuple(quest.get("targets") or ())
        mask = int(row["progress"])
        return sum(
            1
            for index in range(len(targets))
            if mask & (1 << index)
        )

    def quest_progress_value(self, quest_id):
        q = QUESTS.get(quest_id)
        if not q:
            return None

        row = self.server.db.quest(self.account_id, quest_id)
        if not row or row["status"] != "active":
            return None

        if q["kind"] == "kill":
            return min(int(row["progress"]), int(q["needed"]))

        if q["kind"] == "collect":
            if q.get("track_craft_progress"):
                return min(
                    int(row["progress"]),
                    int(q["needed"]),
                )
            return min(
                self.server.db.item_qty(
                    self.account_id, q["target"]
                ),
                int(q["needed"]),
            )

        if q["kind"] == "collect_category":
            category = self.quest_collect_category_info(q["target"])
            if not category:
                return None
            ids, container, label = category
            return min(
                self.server.db.total_items_across_storage_and_inventory(
                    self.account_id, ids, container
                ),
                int(q["needed"]),
            )

        if q["kind"] == "collect_resource":
            return min(
                int(row["progress"]),
                int(q["needed"]),
            )

        if q["kind"] == "craft_set":
            return self.craft_set_progress(row, q)

        return None

    async def announce_active_quest_progress(self, quest_id):
        q = QUESTS.get(quest_id)
        if not q:
            return

        progress = self.quest_progress_value(quest_id)
        if progress is None:
            return

        needed = int(q["needed"])

        if (
            q.get("kind") == "collect"
            and q.get("track_craft_progress")
        ):
            have = self.server.db.item_qty(
                self.account_id,
                q["target"],
            )
            item_name = ITEMS[q["target"]]["name"]
            if progress >= needed and have >= needed:
                await self.send(
                    f"Quest aktywny: {q['name']}. "
                    f"Wykonano {progress} z {needed}: "
                    f"{item_name}. Masz {have} sztuk. "
                    "Quest gotowy do oddania."
                )
            elif progress >= needed:
                await self.send(
                    f"Quest aktywny: {q['name']}. "
                    f"Wykonano {progress} z {needed}: "
                    f"{item_name}. "
                    f"Do oddania masz {have} z {needed}. "
                    "Wykonanie jest zakończone, ale musisz "
                    "posiadać wymagane mikstury."
                )
            else:
                await self.send(
                    f"Quest aktywny: {q['name']}. "
                    f"Wykonano {progress} z {needed}: "
                    f"{item_name}."
                )
            return

        if q.get("kind") == "collect_resource":
            have = self.resource_quest_have(q["target"])
            name = ITEMS[q["target"]]["name"]
            if progress >= needed and have >= needed:
                await self.send(
                    f"Quest aktywny: {q['name']}. "
                    f"Zdobyto {progress} z {needed}: {name}. "
                    f"Masz {have}. Quest gotowy do oddania."
                )
            elif progress >= needed:
                await self.send(
                    f"Quest aktywny: {q['name']}. "
                    f"Zdobyto {progress} z {needed}: {name}. "
                    f"Do oddania masz {have} z {needed}."
                )
            else:
                await self.send(
                    f"Quest aktywny: {q['name']}. "
                    f"Zdobyto {progress} z {needed}: {name}."
                )
            return

        if q.get("kind") == "craft_set":
            targets = tuple(q.get("targets") or ())
            have = sum(
                1
                for item_id in targets
                if self.server.db.item_qty(
                    self.account_id, item_id
                ) > 0
            )
            if progress >= needed and have >= needed:
                await self.send(
                    f"Quest aktywny: {q['name']}. "
                    f"Elementy zestawu wykonane {progress} z {needed}. "
                    "Pełny zestaw gotowy do oddania."
                )
            else:
                await self.send(
                    f"Quest aktywny: {q['name']}. "
                    f"Elementy zestawu wykonane {progress} z {needed}. "
                    f"Posiadasz {have} z {needed}."
                )
            return

        if progress >= needed:
            await self.send(
                f"Quest aktywny: {q['name']}. "
                f"Postęp {progress} z {needed}. "
                "Cel wykonany, wróć do NPC."
            )
        else:
            await self.send(
                f"Quest aktywny: {q['name']}. "
                f"Postęp {progress} z {needed}."
            )

    async def announce_collect_category_quest_progress(self, target):
        for row in self.server.db.quest_rows(self.account_id):
            if row["status"] != "active":
                continue
            q = QUESTS.get(row["quest_id"])
            if (
                not q
                or q.get("kind") != "collect_category"
                or q.get("target") != target
            ):
                continue
            await self.announce_active_quest_progress(row["quest_id"])

    async def announce_craft_quest_progress(
        self, item_id, amount=1
    ):
        changed = self.server.db.increment_craft_quest(
            self.account_id,
            item_id,
            amount,
        )

        for quest_id, progress, needed in changed:
            quest = QUESTS[quest_id]
            item_name = ITEMS[item_id]["name"]

            if quest.get("kind") == "craft_set":
                if progress >= needed:
                    await self.send(
                        f"Postęp questa: {quest['name']}. "
                        f"Wykonałeś element: {item_name}. "
                        f"Elementy zestawu {progress} z {needed}. "
                        "Pełny zestaw wykonany 1 z 1."
                    )
                else:
                    await self.send(
                        f"Postęp questa: {quest['name']}. "
                        f"Wykonałeś element: {item_name}. "
                        f"Elementy zestawu {progress} z {needed}."
                    )
                continue

            if progress >= needed:
                await self.send(
                    f"Postęp questa: {quest['name']}. "
                    f"Wykonałeś: {item_name}. "
                    f"Postęp {progress} z {needed}. "
                    "Wymagana liczba została wykonana. "
                    f"Zachowaj {needed} sztuk do oddania "
                    f"{quest['giver']}."
                )
            else:
                await self.send(
                    f"Postęp questa: {quest['name']}. "
                    f"Wykonałeś: {item_name}. "
                    f"Postęp {progress} z {needed}."
                )

    def format_duration_short(self, seconds):
        seconds = max(0, int(seconds))
        minutes, sec = divmod(seconds, 60)
        if minutes and sec:
            return f"{minutes} min {sec} sek"
        if minutes:
            return f"{minutes} min"
        return f"{sec} sek"

    def soul_tier_quest_for_current_state(self):
        if self.character.soul_tier == 1 and self.character.soul_level >= TIER2_LEVEL:
            return "soul_tier_2_trial"
        if self.character.soul_tier == 2 and self.character.soul_level >= TIER3_LEVEL:
            return "soul_tier_3_trial"
        if self.character.soul_tier == 3 and self.character.soul_level >= TIER4_LEVEL:
            return "soul_tier_4_trial"
        if self.character.soul_tier == 4 and self.character.soul_level >= TIER5_LEVEL:
            return "soul_tier_5_trial"
        return None

    def soul_tier_quest_completed(self, tier):
        quest_id = {
            2: "soul_tier_2_trial",
            3: "soul_tier_3_trial",
            4: "soul_tier_4_trial",
            5: "soul_tier_5_trial",
        }.get(int(tier))
        if not quest_id:
            return False
        row = self.server.db.quest(self.account_id, quest_id)
        return bool(row and row["status"] == "completed")

    def quest_progress_for_turnin(self, quest_id):
        q = QUESTS.get(quest_id)
        row = self.server.db.quest(self.account_id, quest_id)
        if not q or not row or row["status"] != "active":
            return 0, False

        needed = int(q.get("needed", 0))
        if q["kind"] == "kill":
            progress = int(row["progress"])
            return progress, progress >= needed

        if q["kind"] == "collect":
            if q.get("track_craft_progress"):
                crafted = min(
                    int(row["progress"]),
                    needed,
                )
                have = self.server.db.item_qty(
                    self.account_id,
                    q["target"],
                )
                return (
                    crafted,
                    crafted >= needed
                    and have >= needed,
                )

            progress = self.server.db.item_qty(
                self.account_id,
                q["target"],
            )
            return progress, progress >= needed

        if q["kind"] == "collect_category":
            category = self.quest_collect_category_info(q["target"])
            if not category:
                return 0, False
            ids, container, _label = category
            progress = (
                self.server.db.total_items_across_storage_and_inventory(
                    self.account_id, ids, container
                )
            )
            return progress, progress >= needed

        if q["kind"] == "collect_resource":
            gathered = min(
                int(row["progress"]), needed
            )
            have = self.resource_quest_have(
                q["target"]
            )
            return (
                gathered,
                gathered >= needed and have >= needed,
            )

        if q["kind"] == "craft_set":
            progress = self.craft_set_progress(row, q)
            targets = tuple(q.get("targets") or ())
            have_all = all(
                self.server.db.item_qty(
                    self.account_id, item_id
                ) > 0
                for item_id in targets
            )
            return (
                progress,
                progress >= needed and have_all,
            )

        return int(row["progress"]), int(row["progress"]) >= needed

    def local_quest_ids(self):
        local_npcs = [
            npc
            for npc in NPCS.values()
            if npc["room"] == self.character.room_id
        ]
        giver_names = {
            self.normalize_description_query(npc["name"])
            for npc in local_npcs
        }

        result = []
        for quest_id, quest in QUESTS.items():
            giver = self.normalize_description_query(
                quest.get("giver", "")
            )
            if giver and giver in giver_names:
                result.append(quest_id)
        return result

    def normalize_turnin_query(self, query):
        value = self.normalize_description_query(query)
        generic = {
            "", "quest", "questa", "questy",
            "zadanie", "zadania", "zlecenie", "zlecenia",
        }
        if value in generic:
            return ""

        for prefix in (
            "quest ",
            "questa ",
            "zadanie ",
            "zadania ",
            "zlecenie ",
        ):
            if value.startswith(prefix):
                return value[len(prefix):].strip()

        return value

    def match_local_active_quest(self, query):
        wanted = self.normalize_turnin_query(query)
        candidates = []

        for quest_id in self.local_quest_ids():
            row = self.server.db.quest(self.account_id, quest_id)
            if not row or row["status"] != "active":
                continue
            quest = QUESTS[quest_id]
            candidates.append((quest_id, quest))

        if not wanted:
            return candidates

        exact = []
        partial = []
        for quest_id, quest in candidates:
            qid = self.normalize_description_query(quest_id)
            name = self.normalize_description_query(quest["name"])
            if wanted in (qid, name):
                exact.append((quest_id, quest))
            elif wanted in qid or wanted in name:
                partial.append((quest_id, quest))

        if exact:
            return exact
        return partial

    async def turn_in_quest(self, query):
        if self.combat_mob_key:
            await self.send(
                "Nie możesz oddawać zadania podczas walki."
            )
            return

        local_npcs = [
            npc
            for npc in NPCS.values()
            if npc["room"] == self.character.room_id
        ]
        if not local_npcs:
            await self.send(
                "Nie ma tutaj NPC, któremu można oddać zadanie."
            )
            return

        matches = self.match_local_active_quest(query)
        wanted = self.normalize_turnin_query(query)

        if wanted:
            if not matches:
                await self.send(
                    "Nie masz tutaj aktywnego zadania pasującego do tej nazwy."
                )
                return
            if len(matches) > 1:
                await self.send(
                    "Pasuje kilka zadań. Podaj pełną nazwę: "
                    + ", ".join(q["name"] for _qid, q in matches)
                    + "."
                )
                return

            quest_id, quest = matches[0]
            progress, ready = self.quest_progress_for_turnin(quest_id)
            if not ready:
                await self.send(
                    f"Zadanie nie jest jeszcze gotowe do oddania: "
                    f"{quest['name']}. Postęp {progress} z "
                    f"{quest['needed']}."
                )
                return

            await self.handle_quest_interaction(quest_id)
            return

        ready = []
        active = []
        for quest_id, quest in matches:
            progress, is_ready = self.quest_progress_for_turnin(quest_id)
            active.append((quest_id, quest, progress, is_ready))
            if is_ready:
                ready.append((quest_id, quest))

        if len(ready) == 1:
            await self.handle_quest_interaction(ready[0][0])
            return

        if len(ready) > 1:
            await self.send(
                "Masz tutaj kilka zadań gotowych do oddania. "
                "Wpisz oddaj <nazwa zadania>: "
                + ", ".join(q["name"] for _qid, q in ready)
                + "."
            )
            return

        if active:
            await self.send(
                "Masz tutaj aktywne zadania, ale żadne nie jest jeszcze "
                "gotowe do oddania."
            )
            for _quest_id, quest, progress, _is_ready in active:
                await self.send(
                    f"{quest['name']}: {progress} z {quest['needed']}."
                )
            return

        await self.send(
            "Nie masz tutaj aktywnego zadania do oddania."
        )

    async def handle_quest_interaction(self, quest_id):
        q = QUESTS[quest_id]
        row = self.server.db.quest(self.account_id, quest_id)

        if not row:
            self.server.db.start_quest(self.account_id, quest_id)
            await self.send(f"Nowe zadanie: {q['name']}. {q['description']}")
            await self.announce_active_quest_progress(quest_id)
            return

        if row["status"] == "completed":
            if q.get("repeatable"):
                cooldown = int(
                    q.get(
                        "repeat_cooldown",
                        QUEST_REPEAT_COOLDOWN_SECONDS,
                    )
                )
                remaining = self.server.db.repeat_quest_seconds_remaining(
                    self.account_id, quest_id, cooldown
                )
                if remaining > 0:
                    await self.send(
                        f"Zadanie {q['name']} jest na odnowieniu. "
                        f"Możesz powtórzyć je za "
                        f"{self.format_duration_short(remaining)}."
                    )
                    return

                self.server.db.restart_quest(self.account_id, quest_id)
                cooldown_minutes = max(1, int(cooldown) // 60)
                await self.send(
                    f"Zadanie ponownie dostępne po {cooldown_minutes} minutach: "
                    f"{q['name']}. {q['description']}"
                )
                await self.announce_active_quest_progress(quest_id)
                return

            if q.get("unlocks_soul_tier"):
                await self.send(
                    f"Próba ukończona: {q['name']}. "
                    f"Możesz użyć unlock, aby odblokować Tier "
                    f"{q['unlocks_soul_tier']} Broni Duszy."
                )
                return

            await self.send(f"Zadanie {q['name']} jest już ukończone.")
            return

        if q["kind"] == "kill":
            progress = int(row["progress"])
            if progress < q["needed"]:
                await self.send(
                    f"Quest aktywny: {q['name']}. "
                    f"Postęp {progress} z {q['needed']}. "
                    f"{q['description']}"
                )
                return

        elif q["kind"] == "collect":
            if q.get("track_craft_progress"):
                crafted = min(
                    int(row["progress"]),
                    int(q["needed"]),
                )
                if crafted < int(q["needed"]):
                    await self.send(
                        f"Quest aktywny: {q['name']}. "
                        f"Wykonano {crafted} z {q['needed']}: "
                        f"{ITEMS[q['target']]['name']}."
                    )
                    return

            progress = self.server.db.item_qty(
                self.account_id, q["target"]
            )
            if progress < q["needed"]:
                if q.get("track_craft_progress"):
                    await self.send(
                        f"Quest aktywny: {q['name']}. "
                        f"Wykonanie zakończone, ale do oddania "
                        f"masz {progress} z {q['needed']}: "
                        f"{ITEMS[q['target']]['name']}."
                    )
                else:
                    await self.send(
                        f"Quest aktywny: {q['name']}. "
                        f"Postęp {progress} z {q['needed']}."
                    )
                return

            self.server.db.remove_item(
                self.account_id,
                q["target"],
                q["needed"],
            )

        elif q["kind"] == "collect_resource":
            gathered = min(
                int(row["progress"]),
                int(q["needed"]),
            )
            if gathered < int(q["needed"]):
                await self.send(
                    f"Quest aktywny: {q['name']}. "
                    f"Zdobyto {gathered} z {q['needed']}: "
                    f"{ITEMS[q['target']]['name']}."
                )
                return

            container = self.resource_quest_container(
                q["target"]
            )
            have = self.resource_quest_have(
                q["target"]
            )
            if have < int(q["needed"]):
                await self.send(
                    f"Cel zdobywania wykonany, ale do oddania "
                    f"masz {have} z {q['needed']}: "
                    f"{ITEMS[q['target']]['name']}."
                )
                return

            ok = (
                self.server.db.consume_items_across_storage_and_inventory(
                    self.account_id,
                    {q["target"]},
                    int(q["needed"]),
                    container,
                )
            )
            if not ok:
                await self.send(
                    "Nie udało się pobrać wymaganych surowców."
                )
                return

        elif q["kind"] == "craft_set":
            targets = tuple(q.get("targets") or ())
            crafted = self.craft_set_progress(
                row, q
            )
            if crafted < len(targets):
                await self.send(
                    f"Quest aktywny: {q['name']}. "
                    f"Elementy zestawu {crafted} z {len(targets)}."
                )
                return

            missing = [
                item_id
                for item_id in targets
                if self.server.db.item_qty(
                    self.account_id, item_id
                ) <= 0
            ]
            if missing:
                await self.send(
                    "Pełny zestaw został już wykuty, ale brakuje "
                    "elementów do oddania: "
                    + ", ".join(
                        ITEMS[item_id]["name"]
                        for item_id in missing
                    )
                    + "."
                )
                return

            for item_id in targets:
                self.server.db.remove_item(
                    self.account_id,
                    item_id,
                    1,
                )

        elif q["kind"] == "collect_category":
            category = self.quest_collect_category_info(q["target"])
            if not category:
                await self.send("Błąd konfiguracji zadania.")
                return

            ids, container, label = category
            progress = (
                self.server.db.total_items_across_storage_and_inventory(
                    self.account_id, ids, container
                )
            )
            if progress < q["needed"]:
                await self.send(
                    f"Quest aktywny: {q['name']}. "
                    f"Postęp {progress} z {q['needed']} wymaganych {label}."
                )
                return

            ok = (
                self.server.db.consume_items_across_storage_and_inventory(
                    self.account_id, ids, q["needed"], container
                )
            )
            if not ok:
                await self.send(
                    "Nie udało się pobrać wymaganych surowców."
                )
                return

        await self.complete_quest(quest_id)

    def quest_completed(self, quest_id):
        row = self.server.db.quest(
            self.account_id, quest_id
        )
        return bool(
            row and row["status"] == "completed"
        )

    def npc_chain_quest_available(self, quest_id):
        quest = QUESTS.get(quest_id)
        if not quest:
            return False
        required = quest.get("requires_quest")
        if required and not self.quest_completed(required):
            return False
        return True

    def npc_chain_current_quest(self, npc):
        chain = tuple(npc.get("quest_chain") or ())
        if not chain:
            return npc.get("quest")

        for quest_id in chain:
            row = self.server.db.quest(
                self.account_id, quest_id
            )
            if row and row["status"] == "active":
                return quest_id

        available = [
            quest_id
            for quest_id in chain
            if self.npc_chain_quest_available(quest_id)
        ]
        return available[-1] if available else chain[0]

    async def show_npc_quest_chain(self, npc):
        chain = tuple(npc.get("quest_chain") or ())
        if not chain:
            return
        await self.send(
            f"Łańcuch zadań: {len(chain)} etapy."
        )
        for number, quest_id in enumerate(chain, 1):
            quest = QUESTS[quest_id]
            row = self.server.db.quest(
                self.account_id, quest_id
            )
            if row and row["status"] == "active":
                state = "aktywne"
            elif row and row["status"] == "completed":
                state = "ukończone"
            elif self.npc_chain_quest_available(quest_id):
                state = "dostępne"
            else:
                state = "zablokowane"
            await self.send(
                f"Etap {number}: {quest['name']}. {state}."
            )

    def specialist_quest_available(self, quest_id):
        quest = QUESTS.get(quest_id)
        if not quest:
            return False

        required_quest = quest.get("requires_quest")
        if (
            required_quest
            and not self.quest_completed(required_quest)
        ):
            return False

        tool_type = quest.get("specialist_tool_type")
        minimum = int(quest.get("min_tool_level", 1))
        if tool_type:
            row = self.server.db.tool(
                self.account_id, tool_type
            )
            if int(row["level"]) < minimum:
                return False

        profession = quest.get(
            "required_profession"
        )
        if profession:
            prow = self.server.db.profession(
                self.account_id, profession
            )
            required_profession_level = int(
                quest.get(
                    "min_profession_level", 1
                )
            )
            if (
                int(prow["level"])
                < required_profession_level
            ):
                return False

        return True

    def specialist_current_quest(self, npc):
        chain = tuple(npc.get("specialist_quests") or ())
        if not chain:
            quest_id = npc.get("quest")
            return quest_id, None

        # Jeśli jakiś etap jest aktywny, zawsze kontynuujemy właśnie jego.
        for quest_id in chain:
            row = self.server.db.quest(
                self.account_id, quest_id
            )
            if row and row["status"] == "active":
                return quest_id, None

        # Najwyższy odblokowany etap staje się bieżącym.
        available = [
            quest_id
            for quest_id in chain
            if self.specialist_quest_available(quest_id)
        ]
        if available:
            current = available[-1]
        else:
            current = chain[0]

        # Opis kolejnego progu.
        next_info = None
        try:
            index = chain.index(current)
        except ValueError:
            index = 0

        if index + 1 < len(chain):
            next_id = chain[index + 1]
            next_q = QUESTS[next_id]
            next_info = (
                next_q["name"],
                int(next_q.get("min_tool_level", 1)),
            )

        return current, next_info

    async def show_specialist_quest_progression(self, npc):
        chain = tuple(npc.get("specialist_quests") or ())
        if not chain:
            return

        tool_type = npc.get("specialist_tool_type")
        tool_row = self.server.db.tool(
            self.account_id, tool_type
        )
        tool_level = int(tool_row["level"])

        await self.send(
            f"Łańcuch zleceń specjalisty: "
            f"{len(chain)} etapy. "
            f"Aktualny level narzędzia: {tool_level}."
        )

        for number, quest_id in enumerate(chain, 1):
            quest = QUESTS[quest_id]
            row = self.server.db.quest(
                self.account_id, quest_id
            )
            minimum = int(
                quest.get("min_tool_level", 1)
            )

            if row and row["status"] == "active":
                state = "aktywne"
            elif row and row["status"] == "completed":
                state = "ukończone"
            elif not self.specialist_quest_available(quest_id):
                required = quest.get("requires_quest")
                reasons = []
                if tool_level < minimum:
                    reasons.append(
                        f"wymaga levelu narzędzia {minimum}"
                    )
                if (
                    required
                    and not self.quest_completed(required)
                ):
                    reasons.append(
                        "wymaga ukończenia poprzedniego etapu"
                    )
                profession = quest.get(
                    "required_profession"
                )
                if profession:
                    prow = self.server.db.profession(
                        self.account_id,
                        profession,
                    )
                    minimum_prof = int(
                        quest.get(
                            "min_profession_level", 1
                        )
                    )
                    if int(prow["level"]) < minimum_prof:
                        reasons.append(
                            f"wymaga {profession} level "
                            f"{minimum_prof}"
                        )
                state = "zablokowane: " + ", ".join(reasons)
            else:
                state = "dostępne"

            await self.send(
                f"Etap {number}: {quest['name']}. {state}."
            )

    async def show_profession_specialist(self, npc):
        tool_type = npc.get("specialist_tool_type")
        if not tool_type:
            return

        await self.show_single_tool(tool_type)

        topic = npc.get("specialist_topic")
        if topic:
            await self.send(
                f"Specjalizacja: {topic}. "
                f"Pełny stan wszystkich profesji: profesje. "
                f"Pełny stan narzędzi: narzedzia."
            )

        recipes = npc.get("specialist_recipes")
        if recipes:
            await self.send(
                f"Receptury tej specjalizacji: wpisz {recipes}."
            )

    async def talk(self, query):
        raw_query = str(query or "").strip()
        normalized = self.normalize_description_query(raw_query)
        if normalized.startswith("to "):
            raw_query = raw_query.split(None, 1)[1].strip()
        elif normalized.startswith("z "):
            raw_query = raw_query.split(None, 1)[1].strip()

        candidates = {
            key: npc
            for key, npc in NPCS.items()
            if npc["room"] == self.character.room_id
        }
        found = find_by_name(candidates, raw_query)
        if not found:
            if candidates:
                await self.send("Nie rozpoznaję tego NPC.")
            else:
                await self.send(
                    "Nie ma tutaj nikogo, z kim można rozpocząć rozmowę."
                )
            return

        npc_id, npc = found
        await self.send(f"{npc['name']}: {npc['dialogue']}")

        if npc.get("teacher_class"):
            await self.teacher_lesson(npc)
            return

        if npc.get("specialist_tool_type"):
            await self.show_profession_specialist(npc)
            await self.show_specialist_quest_progression(npc)

            specialist_quest, next_info = (
                self.specialist_current_quest(npc)
            )
            if specialist_quest:
                await self.handle_quest_interaction(
                    specialist_quest
                )

            if next_info:
                next_name, next_level = next_info
                current_tool = self.server.db.tool(
                    self.account_id,
                    npc["specialist_tool_type"],
                )
                if int(current_tool["level"]) < next_level:
                    await self.send(
                        f"Następny etap: {next_name}. "
                        f"Odblokuje się od levelu narzędzia "
                        f"{next_level}, po ukończeniu poprzedniego etapu."
                    )
            return

        if npc.get("quest_chain"):
            await self.show_npc_quest_chain(npc)
            quest_id = self.npc_chain_current_quest(npc)
            if quest_id:
                await self.handle_quest_interaction(
                    quest_id
                )
            return

        # Kapłan Elor najpierw obsługuje aktualną próbę Broni Duszy.
        if npc_id == "priest_elor":
            tier_quest_id = self.soul_tier_quest_for_current_state()
            if tier_quest_id:
                await self.handle_quest_interaction(tier_quest_id)
                return

        quest_id = npc.get("quest")
        if not quest_id:
            return
        await self.handle_quest_interaction(quest_id)


    async def complete_quest(self, quest_id):
        q = QUESTS[quest_id]
        self.server.db.complete_quest(self.account_id, quest_id)

        reward_prof_xp = int(
            q.get("reward_profession_xp", 0)
        )
        reward_tool_xp = int(
            q.get("reward_tool_xp", 0)
        )
        reward_tool_type = q.get("reward_tool_type")

        if reward_prof_xp:
            await self.grant_profession_reward_xp(
                q.get("reward_profession", "Wędkarstwo"),
                reward_prof_xp,
                reward_tool_type or "fishing",
                reward_tool_xp,
            )
        elif reward_tool_xp and reward_tool_type:
            await self.grant_tool_reward_xp(
                reward_tool_type,
                reward_tool_xp,
            )

        # EXP rozwoju statystyk nie tworzy levelu postaci.
        # Nadal zasila wyłącznie automatyczny wzrost pięciu statystyk.
        reward_exp = q.get("reward_stat_progress", 0)
        if reward_exp:
            for msg in self.character.add_stat_progress(reward_exp):
                await self.send(msg)

        self.character.silver += q.get("reward_silver", 0)
        self.character.gold += q.get("reward_gold", 0)
        self.character.mithril += q.get("reward_mithril", 0)
        for item_id, qty in q["reward_items"].items():
            self.server.db.add_item(self.account_id, item_id, qty)
        self.server.db.save_character(self.character)
        await self.send(f"Zadanie ukończone: {q['name']}.")
        if q.get("unlocks_soul_tier"):
            await self.send(
                f"Próba Broni Duszy zakończona. Tier "
                f"{q['unlocks_soul_tier']} jest gotowy do odblokowania "
                "komendą unlock."
            )
        if q.get("repeatable"):
            cooldown = int(
                q.get("repeat_cooldown", QUEST_REPEAT_COOLDOWN_SECONDS)
            )
            await self.send(
                "To zadanie jest powtarzalne. Będzie ponownie dostępne "
                f"za {max(1, cooldown // 60)} minut."
            )
        if q.get("reward_stat_progress", 0):
            await self.send(
                f"Nagroda EXP rozwoju: {q['reward_stat_progress']}."
            )
        if q.get("reward_silver", 0):
            await self.send(f"Nagroda: {q['reward_silver']} srebra.")
        if q.get("reward_gold", 0):
            await self.send(f"Nagroda: {q['reward_gold']} złota.")
        if q.get("reward_mithril", 0):
            await self.send(f"Nagroda: {q['reward_mithril']} mithrilu.")
        for item_id, qty in q["reward_items"].items():
            await self.send(f"Nagroda: {ITEMS[item_id]['name']} x{qty}.")

    async def quests(self):
        rows = self.server.db.quest_rows(self.account_id)
        if not rows:
            await self.send("Nie masz jeszcze żadnych zadań. Porozmawiaj z NPC.")
            return
        await self.send("DZIENNIK ZADAŃ")
        for row in rows:
            q = QUESTS.get(row["quest_id"])
            if not q:
                continue
            if row["status"] == "completed":
                if q.get("repeatable"):
                    remaining = (
                        self.server.db.repeat_quest_seconds_remaining(
                            self.account_id,
                            row["quest_id"],
                            int(
                                q.get(
                                    "repeat_cooldown",
                                    QUEST_REPEAT_COOLDOWN_SECONDS,
                                )
                            ),
                        )
                    )
                    if remaining > 0:
                        await self.send(
                            f"{q['name']}: ukończone. Powtórka za "
                            f"{self.format_duration_short(remaining)}."
                        )
                    else:
                        await self.send(
                            f"{q['name']}: gotowe do ponownego przyjęcia."
                        )
                elif q.get("unlocks_soul_tier"):
                    await self.send(
                        f"{q['name']}: ukończone. Tier "
                        f"{q['unlocks_soul_tier']} gotowy. Użyj unlock."
                    )
                else:
                    await self.send(f"{q['name']}: ukończone.")
            elif row["status"] == "active":
                progress, ready = self.quest_progress_for_turnin(
                    row["quest_id"]
                )
                if ready:
                    await self.send(
                        f"{q['name']}: GOTOWE DO ODDANIA. "
                        f"Postęp {progress} z {q['needed']}. "
                        f"Wróć do {q['giver']} i wpisz oddaj zadanie "
                        f"albo talk to {q['giver']}."
                    )
                elif q["kind"] == "collect_category":
                    category = self.quest_collect_category_info(q["target"])
                    label = category[2] if category else "surowców"
                    await self.send(
                        f"{q['name']}: aktywne. Postęp {progress} z "
                        f"{q['needed']} wymaganych {label}. "
                        f"{q['description']}"
                    )
                else:
                    await self.send(
                        f"{q['name']}: aktywne. Postęp {progress} z "
                        f"{q['needed']}. {q['description']}"
                    )

    async def unlock(self):
        nxt = self.character.can_unlock()
        if not nxt:
            if self.character.soul_tier >= SOUL_MAX_TIER:
                await self.send(
                    f"Broń Duszy ma już maksymalny Tier {SOUL_MAX_TIER}."
                )
            elif self.character.soul_tier == 1:
                await self.send(
                    f"Tier 2 wymaga Soul Level {TIER2_LEVEL}, a następnie "
                    "ukończenia Próby Broni Duszy u Kapłana Elora "
                    "w Świątyni Odrodzenia."
                )
            elif self.character.soul_tier == 2:
                await self.send(
                    f"Tier 3 wymaga Soul Level {TIER3_LEVEL}, a następnie "
                    "ukończenia Próby Broni Duszy u Kapłana Elora "
                    "w Świątyni Odrodzenia."
                )
            elif self.character.soul_tier == 3:
                await self.send(
                    f"Tier 4 wymaga Soul Level {TIER4_LEVEL} oraz "
                    "Próby Elora związanej z bossem piętra 120 Krypty."
                )
            elif self.character.soul_tier == 4:
                await self.send(
                    f"Tier 5 wymaga Soul Level {TIER5_LEVEL} oraz "
                    "Próby Elora związanej z bossem piętra 180 Krypty."
                )
            return

        required_quest = {
            2: "soul_tier_2_trial",
            3: "soul_tier_3_trial",
            4: "soul_tier_4_trial",
            5: "soul_tier_5_trial",
        }[nxt]
        if not self.soul_tier_quest_completed(nxt):
            await self.send(
                f"Masz wymagany Soul Level, ale Tier {nxt} wymaga jeszcze "
                f"zadania {QUESTS[required_quest]['name']}. "
                "Idź do Kapłana Elora w Świątyni Odrodzenia."
            )
            return

        self.character.soul_tier = nxt
        self.server.db.save_character(self.character)
        await self.send(
            f"Odblokowano Tier {nxt}. Moc Broni Duszy: "
            f"{self.character.soul_power()}."
        )
        await self.send(
            f"Nowy bonus klasowy Broni Duszy: "
            f"{self.character.soul_weapon_class_bonus_text()}."
        )

    def class_skills(self):
        skills = []
        for class_name in self.active_class_names():
            skills.extend(CLASS_SKILLS.get(class_name, []))
        return skills

    def class_teacher(self, class_name=None):
        wanted = class_name or self.character.class_name
        for npc_id, npc in NPCS.items():
            if npc.get("teacher_class") == wanted:
                return npc_id, npc
        return None, None

    def normalized_skill_text(self, value):
        return self.normalize_description_query(value)

    def skill_natural_tokens(self, skill):
        tokens = set()
        names = [skill["name"], skill["id"]] + skill.get("aliases", [])
        names += skill.get("natural_tags", [])

        for value in names:
            normalized = self.normalized_skill_text(value)
            if not normalized:
                continue
            tokens.add(normalized)
            tokens.update(normalized.split())

        return tokens

    def natural_skill_from_input(self, raw):
        raw = str(raw or "").strip()
        normalized = self.normalized_skill_text(raw)
        if not normalized:
            return None, ""

        words = normalized.split()
        raw_words = raw.split()

        # Naturalny intent jest pierwszym słowem.
        intent = words[0]
        spec = NATURAL_SKILL_INTENTS.get(intent)
        if not spec:
            return None, ""

        known = self.server.db.learned_skill_ids(self.account_id)
        candidates = []

        for skill in self.class_skills():
            if skill["id"] not in known:
                continue
            if self.character.soul_level < int(skill["unlock"]):
                continue

            kinds = spec.get("kinds")
            if kinds and skill.get("kind") not in kinds:
                continue

            wanted_tags = spec.get("tags")
            if wanted_tags:
                tokens = self.skill_natural_tokens(skill)
                if not tokens.intersection(wanted_tags):
                    continue

            progress = self.server.db.skill_progress(
                self.account_id, skill["id"]
            )
            score = (
                int(skill["unlock"]),
                int(progress["level"]),
            )
            candidates.append((score, skill))

        if not candidates:
            return None, ""

        candidates.sort(key=lambda entry: entry[0], reverse=True)
        best_score = candidates[0][0]
        best = [
            skill
            for score, skill in candidates
            if score == best_score
        ]

        # Przy remisie nie wybieramy losowo pomiędzy multiclassami.
        if len(best) != 1:
            return None, ""

        target = " ".join(raw_words[1:]) if len(raw_words) > 1 else ""
        return best[0], target

    def find_skill_from_input(self, raw):
        skills = self.class_skills()
        raw = raw.strip()
        if not raw:
            return None, ""

        first = raw.split(maxsplit=1)
        if first[0].isdigit():
            number = int(first[0])
            if 1 <= number <= len(skills):
                return (
                    skills[number - 1],
                    first[1] if len(first) > 1 else "",
                )

        normalized = self.normalized_skill_text(raw)
        matches = []

        # Najpierw pełne nazwy, ID i oficjalne aliasy.
        for skill in skills:
            for name in [skill["name"], skill["id"]] + skill.get("aliases", []):
                n = self.normalized_skill_text(name)
                if normalized == n:
                    matches.append((len(n), skill, ""))
                elif normalized.startswith(n + " "):
                    word_count = len(name.split())
                    target = " ".join(raw.split()[word_count:])
                    matches.append((len(n), skill, target))

        if matches:
            matches.sort(key=lambda x: x[0], reverse=True)
            return matches[0][1], matches[0][2]

        # Naturalne intencje, np. heal, tarcza, ogien, ciecie, pocisk.
        natural_skill, natural_target = self.natural_skill_from_input(raw)
        if natural_skill:
            return natural_skill, natural_target

        # Fallback: krótka nazwa po fragmencie pełnej nazwy/aliasu,
        # ale tylko jeśli wskazuje dokładnie jeden skill.
        shortcut_matches = {}
        raw_words = raw.split()

        for skill in skills:
            shortcuts = set()
            names = [skill["name"]] + skill.get("aliases", [])
            for name in names:
                n = self.normalized_skill_text(name)
                words = n.split()
                if not words:
                    continue

                shortcuts.update(words)

                for count in range(1, len(words)):
                    shortcuts.add(" ".join(words[:count]))
                    shortcuts.add(" ".join(words[count:]))

            shortcuts.difference_update({
                "maly", "male", "wielki", "wielkie", "cios",
                "uderzenie", "bariera", "duszy", "krwi",
                "umyslu", "energii",
            })

            for shortcut in shortcuts:
                if normalized == shortcut:
                    target = ""
                elif normalized.startswith(shortcut + " "):
                    word_count = len(shortcut.split())
                    target = " ".join(raw_words[word_count:])
                else:
                    continue

                shortcut_matches.setdefault(skill["id"], []).append(
                    (len(shortcut), skill, target)
                )

        if len(shortcut_matches) != 1:
            return None, ""

        only_matches = next(iter(shortcut_matches.values()))
        only_matches.sort(key=lambda x: x[0], reverse=True)
        return only_matches[0][1], only_matches[0][2]

    async def show_all_skill_names(self):
        await self.send("NAZWY SKILLI WSZYSTKICH KLAS")
        for class_name in [cls[0] for cls in CLASSES]:
            skills = CLASS_SKILLS.get(class_name, [])
            names = ", ".join(
                f"{index}. {skill['name']}"
                for index, skill in enumerate(skills, 1)
            )
            await self.send(f"{class_name}: {names}.")
        await self.send(
            "Nazw możesz używać w komendach skill <nazwa> oraz naucz <nazwa>."
        )

    async def show_skills(self):
        active = self.active_class_names()
        learned = self.server.db.learned_skill_ids(self.account_id)
        await self.send(
            f"UMIEJĘTNOŚCI AKTYWNYCH KLAS. Klasy: {', '.join(active)}. "
            f"Soul Level: {self.character.soul_level}."
        )

        global_number = 0
        for class_name in active:
            teacher_id, teacher = self.class_teacher(class_name)
            teacher_room = (
                ROOMS[teacher["room"]]["name"] if teacher else "nieznana lokacja"
            )
            await self.send(f"Klasa {class_name}:")
            for skill in CLASS_SKILLS.get(class_name, []):
                global_number += 1
                progress_text = ""
                skill_level = 1

                if skill["id"] in learned:
                    row = self.server.db.skill_progress(
                        self.account_id, skill["id"]
                    )
                    skill_level = int(row["level"])
                    if skill_level >= SKILL_MAX_LEVEL:
                        progress_text = (
                            f" Skill Level {skill_level}, maksymalny."
                        )
                    else:
                        progress_text = (
                            f" Skill Level {skill_level}, XP {row['xp']} z "
                            f"{skill_xp_to_next(skill_level)}, użycia {row['uses']}."
                        )
                    status = "nauczona"
                elif self.character.soul_level >= skill["unlock"]:
                    status = (
                        f"gotowa do nauki u {teacher['name']} "
                        f"w lokacji {teacher_room}"
                    )
                else:
                    status = (
                        f"zablokowana: wymaga Soul Level {skill['unlock']}"
                    )

                mana = (
                    f", Mana {skill.get('mana', 0)}"
                    if skill.get("mana", 0) else ""
                )
                effective_cd = self.effective_skill_cooldown(
                    skill, skill_level
                )
                remaining = max(
                    0,
                    int(
                        self.skill_cooldowns.get(skill["id"], 0)
                        - time.time() + 0.999
                    ),
                )
                cd = (
                    f", pozostały cooldown {remaining} sekund"
                    if remaining else ""
                )

                await self.send(
                    f"{global_number}. {skill['name']}. {status}."
                    f"{progress_text} Cooldown bazowy {skill['cooldown']} sekund, "
                    f"aktualny {effective_cd} sekund{mana}{cd}. "
                    f"{skill['desc']}"
                )

        await self.send(
            "Numery dotyczą wspólnej listy aktywnych klas. "
            "Przy nauczycielu komenda learn <numer> używa lokalnej listy jego klasy."
        )
        await self.send(
            "Każdy nauczony skill zachowuje własny Skill Level 1-100 i XP."
        )


    def protected_friendly_npc(self, query):
        room_id = self.character.room_id
        candidates = {
            npc_id: npc
            for npc_id, npc in NPCS.items()
            if npc.get("room") == room_id
        }
        if not candidates:
            return None

        found = find_by_name(candidates, query)
        if not found:
            return None
        return found[1]

    async def reject_friendly_npc_attack(self, query):
        npc = self.protected_friendly_npc(query)
        if not npc:
            return False

        await self.send(
            f"{npc['name']} jest pokojowym i chronionym NPC-em. "
            "Sprzedawców, nauczycieli, postaci zadaniowych i innych "
            "pomocnych NPC-ów nie można atakować ani zabijać."
        )
        return True

    def skill_progress_data(self, skill):
        if not self.server.db.knows_skill(self.account_id, skill["id"]):
            return {"level": 0, "xp": 0, "uses": 0}
        row = self.server.db.skill_progress(self.account_id, skill["id"])
        return {
            "level": int(row["level"]),
            "xp": int(row["xp"]),
            "uses": int(row["uses"]),
        }

    def effective_skill_cooldown(self, skill, skill_level):
        return max(
            1,
            int(round(skill["cooldown"] * skill_cooldown_multiplier(skill_level)))
        )

    async def grant_skill_use_xp(self, skill):
        gain = 8 + random.randint(0, 4)
        result = self.server.db.add_skill_xp(
            self.account_id, skill["id"], gain
        )
        if result["level_ups"]:
            await self.send(
                f"{skill['name']} awansuje na Skill Level {result['level']}."
            )
        if result["level"] >= SKILL_MAX_LEVEL:
            await self.send(
                f"{skill['name']}: Skill Level {SKILL_MAX_LEVEL}. Maksymalny poziom."
            )
        else:
            await self.send(
                f"{skill['name']}: Skill XP +{gain}. "
                f"Level {result['level']}, XP {result['xp']} z {result['next_xp']}."
            )
        return result

    def skill_scale_value(self, scale):
        if scale == "dexterity":
            return self.effective_dexterity()
        if scale == "intelligence":
            return self.effective_intelligence()
        return self.effective_strength()

    async def skill_combat_target(self, query):
        self.server.world.refresh()
        mob = None
        if self.combat_mob_key:
            mob = self.server.world.mobs.get(self.combat_mob_key)
            if not mob or not mob.alive or mob.room_id != self.character.room_id:
                self.combat_mob_key = None
                mob = None

        if mob is None:
            if not query.strip():
                await self.send("Ta umiejętność wymaga celu. Podaj nazwę przeciwnika.")
                return None
            if await self.reject_friendly_npc_attack(query):
                return None
            mob = self.server.world.find_mob(self.character.room_id, query)
            if not mob:
                await self.send("Nie widzę tutaj takiego przeciwnika.")
                return None
            if not self.server.engagement_allowed(self, mob):
                await self.send(
                    f"{MOB_TEMPLATES[mob.template_id]['name']} walczy już "
                    f"z graczem spoza twojej drużyny."
                )
                return None
            if not mob.engaged_by:
                mob.engaged_by = self.character.name
                mob.combat_turn = 0
                mob.player_hits = 0
            self.combat_mob_key = mob.key
            await self.server.broadcast_room(
                self.character.room_id,
                f"{self.character.name} rozpoczyna walkę umiejętnością klasową.",
                exclude=self,
            )
            await self.send(
                "Rozpoczyna się walka turowa. Po każdej twojej akcji przeciwnik wykonuje jedną turę."
            )
        return mob

    async def apply_boss_defense(self, mob, damage):
        if not mob or not mob.alive:
            return max(0, int(damage))

        template = MOB_TEMPLATES[mob.template_id]
        mechanic = template.get("boss_mechanic")
        damage = max(0, int(damage))

        elite_affix = template.get("elite_affix")
        if elite_affix == "armored" and damage > 0:
            reduced = max(
                1,
                int(round(damage * 0.70)),
            )
            await self.send(
                f"Affix Opancerzony redukuje obrażenia "
                f"z {damage} do {reduced}."
            )
            damage = reduced

        if not mechanic:
            return damage

        mob.player_hits += 1

        if mechanic == "grave_shield" and mob.player_hits % 3 == 0:
            reduced = max(1, damage // 2) if damage > 0 else 0
            await self.send(
                f"{template['name']} aktywuje Tarczę Grobowca. "
                f"Twoje obrażenia spadają z {damage} do {reduced}."
            )
            return reduced

        if mechanic == "ethereal_evade" and random.random() < 0.25:
            await self.send(
                f"{template['name']} rozpływa się w eterze i całkowicie unika trafienia."
            )
            return 0

        if mechanic == "hundred_lord" and mob.player_hits % 4 == 0:
            reduced = max(1, int(round(damage * 0.60))) if damage > 0 else 0
            await self.send(
                f"{template['name']} tworzy Pieczęć Stu Pięter. "
                f"Obrażenia zostają zredukowane z {damage} do {reduced}."
            )
            return reduced

        if mechanic == "iron_bones" and mob.player_hits % 3 == 0:
            reduced = max(1, int(round(damage * 0.55))) if damage > 0 else 0
            await self.send(
                f"{template['name']} wzmacnia Żelazne Kości. "
                f"Obrażenia spadają z {damage} do {reduced}."
            )
            return reduced

        if mechanic == "phantom_emperor" and random.random() < 0.30:
            await self.send(
                f"{template['name']} wykonuje Widmowy Unik i znika przed trafieniem."
            )
            return 0

        if mechanic == "final_guardian" and mob.player_hits % 4 == 0:
            reduced = max(1, damage // 2) if damage > 0 else 0
            await self.send(
                f"{template['name']} aktywuje Straż Końca. "
                f"Obrażenia spadają z {damage} do {reduced}."
            )
            return reduced

        if mechanic == "two_hundred_lord" and mob.player_hits % 5 == 0:
            reduced = max(1, damage // 2) if damage > 0 else 0
            await self.send(
                f"{template['name']} aktywuje Barierę Końca. "
                f"Obrażenia spadają z {damage} do {reduced}."
            )
            return reduced

        if mechanic == "stellar_barrier" and mob.player_hits % 3 == 0:
            reduced = max(1, damage // 2) if damage > 0 else 0
            await self.send(
                f"{template['name']} aktywuje Gwiezdną Barierę. "
                f"Obrażenia spadają z {damage} do {reduced}."
            )
            return reduced

        if mechanic == "comet_evade" and random.random() < 0.25:
            await self.send(
                f"{template['name']} wykonuje Unik Komety i znika przed trafieniem."
            )
            return 0

        if mechanic == "firmament_guard" and mob.player_hits % 4 == 0:
            reduced = max(1, damage // 2) if damage > 0 else 0
            await self.send(
                f"{template['name']} aktywuje Straż Firmamentu. "
                f"Obrażenia spadają z {damage} do {reduced}."
            )
            return reduced

        if mechanic == "astral_sovereign" and mob.player_hits % 5 == 0:
            reduced = max(1, damage // 2) if damage > 0 else 0
            await self.send(
                f"{template['name']} aktywuje Barierę Suwerena. "
                f"Obrażenia spadają z {damage} do {reduced}."
            )
            return reduced

        if mechanic == "crystal_lord" and mob.player_hits % 4 == 0:
            reduced = max(1, damage // 2) if damage > 0 else 0
            await self.send(
                f"{template['name']} aktywuje Kryształową Barierę. "
                f"Obrażenia spadają z {damage} do {reduced}."
            )
            return reduced

        return damage

    async def boss_attack_profile(self, mob, template):
        mob.combat_turn += 1
        turn = mob.combat_turn
        mechanic = template.get("boss_mechanic")
        profile = {
            "damage_type": template.get("damage_type", "physical"),
            "damage_multiplier": 1.0,
            "defense_factor": 1.0,
            "drain_pct": 0.0,
        }

        if mechanic == "bone_crush" and turn % 3 == 0:
            profile["damage_multiplier"] = 1.60
            await self.send(f"{template['name']} używa Kościanego Miażdżenia.")

        elif mechanic == "blood_drain" and turn % 3 == 0:
            profile["damage_multiplier"] = 1.25
            profile["drain_pct"] = 0.50
            await self.send(f"{template['name']} używa Krwawego Drenażu.")

        elif mechanic == "ash_curse" and turn % 3 == 0:
            profile["damage_type"] = "magic"
            profile["damage_multiplier"] = 1.25
            profile["defense_factor"] = 0.50
            await self.send(
                f"{template['name']} rzuca Klątwę Popiołu. "
                "Połowa twojej obrony magicznej zostaje pominięta."
            )

        elif mechanic == "catacomb_echo" and turn % 4 == 0:
            profile["damage_multiplier"] = 1.70
            await self.send(
                f"{template['name']} wyzwala Echo Katakumb. "
                "To jedna, ale wyjątkowo silna odpowiedź bossa."
            )

        elif mechanic == "spectral_shift":
            profile["damage_type"] = "magic" if turn % 2 else "physical"
            await self.send(
                f"{template['name']} zmienia widmową fazę. "
                f"Ten kontratak jest "
                f"{'magiczny' if profile['damage_type'] == 'magic' else 'fizyczny'}."
            )

        elif mechanic == "necro_regen" and turn % 4 == 0:
            heal = max(1, int(round(template["max_hp"] * 0.07)))
            before = mob.hp
            mob.hp = min(template["max_hp"], mob.hp + heal)
            actual = mob.hp - before
            if actual > 0:
                await self.send(
                    f"{template['name']} używa Nekroregeneracji "
                    f"i odzyskuje {actual} HP. "
                    f"Boss: {mob.hp} z {template['max_hp']} HP."
                )

        elif mechanic == "bone_rage":
            if mob.hp <= template["max_hp"] // 2:
                profile["damage_multiplier"] = 1.50
                await self.send(
                    f"{template['name']} walczy w Furii Króla Kości."
                )

        elif mechanic == "hundred_lord":
            if mob.hp <= template["max_hp"] // 2:
                profile["damage_multiplier"] *= 1.25
            if turn % 3 == 0:
                profile["damage_type"] = "magic"
                profile["damage_multiplier"] *= 1.50
                profile["defense_factor"] = 0.75
                await self.send(
                    f"{template['name']} używa Załamania Duszy."
                )
            elif mob.hp <= template["max_hp"] // 2:
                await self.send(
                    f"{template['name']} walczy w drugiej fazie."
                )

        elif mechanic == "soul_breaker" and turn % 3 == 0:
            profile["damage_type"] = "magic"
            profile["damage_multiplier"] = 1.45
            profile["defense_factor"] = 0.75
            await self.send(
                f"{template['name']} używa Rozdarcia Duszy."
            )

        elif mechanic == "abyss_queen" and turn % 4 == 0:
            profile["damage_type"] = "magic"
            profile["damage_multiplier"] = 1.35
            profile["drain_pct"] = 0.40
            await self.send(
                f"{template['name']} używa Drenażu Otchłani."
            )

        elif mechanic == "iron_bones" and turn % 3 == 0:
            profile["damage_type"] = "physical"
            profile["damage_multiplier"] = 1.60
            await self.send(
                f"{template['name']} wykonuje Uderzenie Żelaznych Kości."
            )

        elif mechanic == "black_flame" and turn % 3 == 0:
            profile["damage_type"] = "magic"
            profile["damage_multiplier"] = 1.55
            profile["defense_factor"] = 0.50
            await self.send(
                f"{template['name']} uwalnia Czarny Płomień."
            )

        elif mechanic == "endless_echo" and turn % 4 == 0:
            profile["damage_multiplier"] = 1.85
            await self.send(
                f"{template['name']} wyzwala Bezdenne Echo."
            )

        elif mechanic == "astral_reaper":
            profile["damage_type"] = "magic" if turn % 2 else "physical"
            if turn % 5 == 0:
                profile["damage_multiplier"] = 1.60
                await self.send(
                    f"{template['name']} wykonuje Astralne Żniwo."
                )
            else:
                await self.send(
                    f"{template['name']} zmienia astralną fazę. "
                    f"Kontratak jest "
                    f"{'magiczny' if profile['damage_type'] == 'magic' else 'fizyczny'}."
                )

        elif mechanic == "void_regen":
            if turn % 4 == 0:
                heal = max(1, int(round(template["max_hp"] * 0.08)))
                before = mob.hp
                mob.hp = min(template["max_hp"], mob.hp + heal)
                actual = mob.hp - before
                if actual > 0:
                    await self.send(
                        f"{template['name']} regeneruje {actual} HP energią Pustki. "
                        f"Boss: {mob.hp} z {template['max_hp']} HP."
                    )
            if turn % 3 == 0:
                profile["damage_type"] = "magic"
                profile["damage_multiplier"] = 1.30

        elif mechanic == "phantom_emperor" and turn % 3 == 0:
            profile["damage_type"] = "magic"
            profile["damage_multiplier"] = 1.60
            profile["defense_factor"] = 0.75
            await self.send(
                f"{template['name']} używa Cesarskiego Widma."
            )

        elif mechanic == "final_guardian":
            if mob.hp <= template["max_hp"] // 2:
                profile["damage_multiplier"] = 1.60
                await self.send(
                    f"{template['name']} wchodzi w Ostatnią Straż."
                )

        elif mechanic == "two_hundred_lord":
            if mob.hp <= template["max_hp"] // 2:
                profile["damage_multiplier"] *= 1.35
            if turn % 3 == 0:
                profile["damage_type"] = "magic"
                profile["damage_multiplier"] *= 1.65
                profile["defense_factor"] = 0.60
                await self.send(
                    f"{template['name']} używa Załamania Wieczności."
                )
            elif mob.hp <= template["max_hp"] // 2:
                await self.send(
                    f"{template['name']} walczy w finałowej fazie Dwustu Pięter."
                )

        elif mechanic == "astral_shift":
            profile["damage_type"] = (
                "magic" if turn % 2 else "physical"
            )
            await self.send(
                f"{template['name']} zmienia Astralną Fazę. "
                f"Kontratak jest "
                f"{'magiczny' if profile['damage_type'] == 'magic' else 'fizyczny'}."
            )

        elif mechanic == "stellar_barrier" and turn % 3 == 0:
            profile["damage_type"] = "magic"
            profile["damage_multiplier"] = 1.35
            await self.send(
                f"{template['name']} wystrzeliwuje Gwiezdną Lancę."
            )

        elif mechanic == "nebula_drain" and turn % 4 == 0:
            profile["damage_type"] = "magic"
            profile["damage_multiplier"] = 1.40
            profile["drain_pct"] = 0.45
            await self.send(
                f"{template['name']} używa Drenażu Nebuli."
            )

        elif mechanic == "comet_evade" and turn % 3 == 0:
            profile["damage_multiplier"] = 1.55
            await self.send(
                f"{template['name']} uderza Szarżą Komety."
            )

        elif mechanic == "starfire" and turn % 3 == 0:
            profile["damage_type"] = "magic"
            profile["damage_multiplier"] = 1.55
            profile["defense_factor"] = 0.50
            await self.send(
                f"{template['name']} wyzwala Gwiezdny Ogień."
            )

        elif mechanic == "orbital_echo" and turn % 4 == 0:
            profile["damage_multiplier"] = 1.85
            await self.send(
                f"{template['name']} wyzwala Echo Orbitalne."
            )

        elif mechanic == "constellation_burst" and turn % 3 == 0:
            profile["damage_type"] = "magic"
            profile["damage_multiplier"] = 1.65
            profile["defense_factor"] = 0.70
            await self.send(
                f"{template['name']} wyzwala Rozbłysk Konstelacji."
            )

        elif mechanic == "astral_regen":
            if turn % 4 == 0:
                heal = max(
                    1,
                    int(round(template["max_hp"] * 0.08))
                )
                before = mob.hp
                mob.hp = min(
                    template["max_hp"],
                    mob.hp + heal,
                )
                actual = mob.hp - before
                if actual > 0:
                    await self.send(
                        f"{template['name']} regeneruje {actual} HP "
                        "energią Astralu."
                    )
            if turn % 3 == 0:
                profile["damage_type"] = "magic"
                profile["damage_multiplier"] = 1.35

        elif mechanic == "stellar_storm" and turn % 3 == 0:
            profile["damage_type"] = "magic"
            profile["damage_multiplier"] = 1.70
            profile["defense_factor"] = 0.70
            await self.send(
                f"{template['name']} przywołuje Gwiezdną Burzę."
            )

        elif mechanic == "firmament_guard":
            if mob.hp <= template["max_hp"] // 2:
                profile["damage_multiplier"] = 1.60
                await self.send(
                    f"{template['name']} przechodzi w Ostatnią Straż Firmamentu."
                )

        elif mechanic == "astral_sovereign":
            if mob.hp <= template["max_hp"] // 2:
                profile["damage_multiplier"] *= 1.35
            if turn % 3 == 0:
                profile["damage_type"] = "magic"
                profile["damage_multiplier"] *= 1.70
                profile["defense_factor"] = 0.60
                await self.send(
                    f"{template['name']} używa Astralnego Załamania."
                )
            elif mob.hp <= template["max_hp"] // 2:
                await self.send(
                    f"{template['name']} wchodzi w fazę Suwerena."
                )

        elif mechanic == "goblin_king" and turn % 3 == 0:
            profile["damage_multiplier"] = 1.50
            await self.send(
                f"{template['name']} wykonuje Królewską Szarżę."
            )

        elif mechanic == "shadow_alpha":
            if mob.hp <= template["max_hp"] // 2:
                profile["damage_multiplier"] = 1.40
                await self.send(
                    f"{template['name']} wpada w Szał Cienia."
                )

        elif mechanic == "ruin_warden" and turn % 4 == 0:
            profile["damage_type"] = "magic"
            profile["damage_multiplier"] = 1.35
            profile["defense_factor"] = 0.75
            await self.send(
                f"{template['name']} uwalnia Runiczny Wybuch."
            )

        elif mechanic == "crystal_lord" and turn % 3 == 0:
            profile["damage_type"] = "magic"
            profile["damage_multiplier"] = 1.45
            await self.send(
                f"{template['name']} wyzwala Kryształowy Promień."
            )

        elif mechanic == "bandit_combo" and turn % 3 == 0:
            profile["damage_multiplier"] = 1.40
            await self.send(
                f"{template['name']} wykonuje Brutalną Kombinację."
            )

        elif mechanic == "giant_crush" and turn % 3 == 0:
            profile["damage_multiplier"] *= 1.60
            await self.send(
                f"{template['name']} wykonuje Miażdżenie Giganta."
            )

        elif mechanic == "cyclops_beam" and turn % 3 == 0:
            profile["damage_type"] = "magic"
            profile["damage_multiplier"] *= 1.55
            profile["defense_factor"] = min(
                profile["defense_factor"], 0.70
            )
            await self.send(
                f"{template['name']} wyzwala Promień Cyklopa."
            )

        elif mechanic == "boulder_storm" and turn % 4 == 0:
            profile["damage_multiplier"] *= 1.85
            await self.send(
                f"{template['name']} wywołuje Burzę Głazów."
            )

        elif mechanic == "giant_thunder":
            if turn % 2:
                profile["damage_type"] = "magic"
            if turn % 3 == 0:
                profile["damage_multiplier"] *= 1.65
                await self.send(
                    f"{template['name']} przywołuje Grom Gigantów."
                )

        elif mechanic == "giant_king":
            if mob.hp <= template["max_hp"] // 2:
                profile["damage_multiplier"] *= 1.40
            if turn % 3 == 0:
                profile["damage_multiplier"] *= 1.70
                await self.send(
                    f"{template['name']} używa Królewskiego Trzęsienia."
                )

        elite_affix = template.get("elite_affix")
        if elite_affix == "vampiric":
            profile["drain_pct"] = max(
                profile["drain_pct"], 0.35
            )
        elif elite_affix == "regenerating":
            if turn % 3 == 0:
                heal = max(
                    1,
                    int(round(template["max_hp"] * 0.04)),
                )
                before = mob.hp
                mob.hp = min(
                    template["max_hp"],
                    mob.hp + heal,
                )
                actual = mob.hp - before
                if actual > 0:
                    await self.send(
                        f"Affix Regenerujący odnawia "
                        f"{actual} HP przeciwnika."
                    )
        elif elite_affix == "ice":
            profile["damage_type"] = "magic"
            profile["damage_multiplier"] *= 1.15
        elif elite_affix == "fire":
            profile["damage_type"] = "magic"
            profile["damage_multiplier"] *= 1.25
        elif elite_affix == "astral":
            profile["damage_type"] = (
                "magic" if turn % 2 else "physical"
            )
            profile["damage_multiplier"] *= 1.30
            profile["defense_factor"] = min(
                profile["defense_factor"], 0.75
            )

        return profile

    async def enemy_counterattack(self, mob):
        if not mob or not mob.alive:
            return
        template = MOB_TEMPLATES[mob.template_id]
        profile = await self.boss_attack_profile(mob, template)

        if self.skill_evade:
            self.skill_evade = False
            await self.send(
                f"{template['name']} kontratakuje, ale aktywna umiejętność gwarantuje unik."
            )
            return

        if random.random() < self.dodge_chance():
            await self.send(
                f"{template['name']} kontratakuje, ale unikasz ciosu dzięki szybkości."
            )
            return

        damage_type = profile["damage_type"]
        if damage_type == "magic":
            full_reduction = self.magic_defense()
            defense_name = "obrona magiczna"
        else:
            full_reduction = self.defense()
            defense_name = "obrona fizyczna"

        reduction = max(
            0,
            int(round(full_reduction * profile["defense_factor"]))
        )
        raw_damage = int(round(
            template["damage"] * profile["damage_multiplier"]
        ))
        incoming = max(
            1,
            raw_damage + random.randint(-2, 2) - reduction
        )

        if self.skill_guard > 0:
            guard = self.skill_guard
            self.skill_guard = 0
            before = incoming
            incoming = max(1, incoming - guard)
            await self.send(
                f"Aktywna osłona redukuje trafienie dodatkowo o "
                f"{before - incoming} obrażeń."
            )

        if damage_type == "physical":
            physical_race_percent = (
                self.character.racial_physical_damage_reduction_percent()
            )
            if physical_race_percent > 0:
                before_physical_race = incoming
                incoming = max(
                    1,
                    int(round(
                        incoming
                        * (1.0 - physical_race_percent / 100.0)
                    ))
                )
                prevented = max(
                    0, before_physical_race - incoming
                )
                if prevented > 0:
                    await self.send(
                        f"Rasowa odporność Trolla redukuje obrażenia "
                        f"fizyczne o {physical_race_percent} procent, "
                        f"czyli o {prevented} obrażeń."
                    )

        incoming, racial_prevented = (
            self.character.apply_racial_damage_reduction(incoming)
        )
        if racial_prevented > 0:
            await self.send(
                f"Rasowa odporność Krasnoluda redukuje trafienie o "
                f"{self.character.racial_damage_reduction_percent()} procent, "
                f"czyli o {racial_prevented} obrażeń."
            )

        incoming, class_prevented = (
            self.character.apply_class_damage_reduction(incoming)
        )
        if class_prevented > 0:
            await self.send(
                f"Pasyw klasy {self.character.class_name} redukuje trafienie o "
                f"{self.character.class_damage_reduction_percent()} procent, "
                f"czyli o {class_prevented} obrażeń."
            )

        self.current_hp -= incoming
        await self.send(
            f"{template['name']} odpowiada. Typ obrażeń: "
            f"{'magiczne' if damage_type == 'magic' else 'fizyczne'}. "
            f"Otrzymujesz {incoming} obrażeń po redukcji przez {defense_name}. "
            f"Twoje życie: {max(0, self.current_hp)} z {self.max_hp()}."
        )

        drain_pct = float(profile.get("drain_pct", 0.0))
        if drain_pct > 0 and mob.alive:
            heal = max(1, int(round(incoming * drain_pct)))
            before = mob.hp
            mob.hp = min(template["max_hp"], mob.hp + heal)
            actual = mob.hp - before
            if actual > 0:
                await self.send(
                    f"{template['name']} wysysa życie i odzyskuje "
                    f"{actual} HP. Boss: {mob.hp} z "
                    f"{template['max_hp']} HP."
                )

        if self.current_hp <= 0:
            await self.die(template["name"])


    def natural_learn_skill_from_input(
        self,
        raw,
        class_skills,
    ):
        normalized = self.normalize_description_query(raw)
        if not normalized:
            return None

        words = normalized.split()
        intent = words[0]
        spec = NATURAL_SKILL_INTENTS.get(intent)
        if not spec:
            return None

        candidates = []
        learned = self.server.db.learned_skill_ids(
            self.account_id
        )

        for skill in class_skills:
            if self.character.soul_level < int(skill["unlock"]):
                continue

            kinds = spec.get("kinds")
            if kinds and skill.get("kind") not in kinds:
                continue

            wanted_tags = spec.get("tags")
            if wanted_tags:
                tokens = self.skill_natural_tokens(skill)
                if not tokens.intersection(wanted_tags):
                    continue

            # Najpierw preferuj najwyżej odblokowany skill,
            # którego gracz jeszcze nie zna.
            unknown_bonus = (
                1 if skill["id"] not in learned else 0
            )
            score = (
                unknown_bonus,
                int(skill["unlock"]),
            )
            candidates.append((score, skill))

        if not candidates:
            return None

        candidates.sort(
            key=lambda entry: entry[0],
            reverse=True,
        )
        best_score = candidates[0][0]
        best = [
            skill
            for score, skill in candidates
            if score == best_score
        ]

        # W obrębie jednego nauczyciela klasy remis powinien być
        # bardzo rzadki. Nie zgadujemy przy identycznym wyniku.
        if len(best) != 1:
            return None

        return best[0]

    async def learn_class_skill(self, raw):
        if self.combat_mob_key:
            await self.send("Nie możesz uczyć się umiejętności podczas walki.")
            return

        teacher_id, teacher = self.teacher_here_for_active_class()
        if not teacher:
            await self.send(
                "Musisz być przy nauczycielu jednej ze swoich aktywnych klas. "
                "Wpisz teachers, aby sprawdzić lokacje."
            )
            return

        class_name = teacher["teacher_class"]
        class_skills = CLASS_SKILLS.get(class_name, [])
        value = raw.strip()
        normalized = self.normalize_description_query(value)
        if normalized.startswith("sie ") or normalized.startswith("się "):
            split = value.split(maxsplit=1)
            value = split[1] if len(split) > 1 else ""

        skill = None
        if value.strip().isdigit():
            number = int(value.strip())
            if 1 <= number <= len(class_skills):
                skill = class_skills[number - 1]
        else:
            wanted = self.normalize_description_query(value)
            for candidate in class_skills:
                names = [
                    candidate["name"], candidate["id"]
                ] + candidate.get("aliases", [])
                if any(
                    wanted == self.normalize_description_query(name)
                    for name in names
                ):
                    skill = candidate
                    break

            # Naturalna nauka: naucz leczenie, naucz tarcza,
            # naucz ogien, naucz ciecie, naucz pocisk itd.
            if not skill:
                skill = self.natural_learn_skill_from_input(
                    value,
                    class_skills,
                )

        if not skill:
            await self.send(
                f"Nie rozpoznaję umiejętności klasy {class_name}. "
                f"Możesz użyć pełnej nazwy albo naturalnej kategorii, "
                f"np. naucz leczenie, naucz tarcza, naucz ciecie, "
                f"naucz pocisk lub naucz ogien. "
                f"Wpisz talk {teacher['name']}."
            )
            return

        if self.server.db.knows_skill(self.account_id, skill["id"]):
            await self.send(f"Już znasz umiejętność {skill['name']}.")
            return

        if self.character.soul_level < skill["unlock"]:
            await self.send(
                f"{skill['name']} wymaga Soul Level {skill['unlock']}, "
                f"a masz {self.character.soul_level}."
            )
            return

        self.server.db.learn_skill(self.account_id, skill["id"])
        await self.send(
            f"{teacher['name']} uczy cię umiejętności klasy "
            f"{class_name}: {skill['name']}."
        )
        await self.send(
            f"Nauczono. {skill['name']} zaczyna na Skill Level 1."
        )


    async def use_class_skill(self, raw):
        skill, target_text = self.find_skill_from_input(raw)
        if not skill:
            await self.send("Nie rozpoznaję tej umiejętności albo naturalny skrót jest niejednoznaczny. Wpisz skills albo umiejetnosci i użyj pełnej nazwy.")
            return

        if self.character.soul_level < skill["unlock"]:
            await self.send(
                f"{skill['name']} wymaga Soul Level {skill['unlock']}."
            )
            return

        if not self.server.db.knows_skill(self.account_id, skill["id"]):
            skill_class = self.skill_class_name(skill)
            teacher_id, teacher = self.class_teacher(skill_class)
            await self.send(
                f"Nie znasz jeszcze umiejętności {skill['name']} klasy "
                f"{skill_class}. Musisz nauczyć się jej u {teacher['name']} "
                f"w lokacji {ROOMS[teacher['room']]['name']}."
            )
            return

        progress = self.server.db.skill_progress(self.account_id, skill["id"])
        skill_level = int(progress["level"])
        skill_power = skill_power_multiplier(skill_level)
        effective_cooldown = self.effective_skill_cooldown(skill, skill_level)

        now = time.time()
        ready_at = self.skill_cooldowns.get(skill["id"], 0)
        if ready_at > now:
            await self.send(
                f"{skill['name']} jest na cooldownie jeszcze {int(ready_at - now + 0.999)} sekund."
            )
            return

        mana_cost = skill.get("mana", 0)
        if mana_cost > self.current_mana:
            await self.send(
                f"Za mało Many. {skill['name']} wymaga {mana_cost}, a masz {self.current_mana}."
            )
            return

        kind = skill["kind"]
        offensive = kind in ("damage", "drain", "execute")
        mob = None
        if offensive:
            if self.auto_fishing or self.auto_fishing_task:
                await self.stop_auto_fishing(announce=False)
                await self.send("Auto-łowienie wyłączone z powodu walki.")
            if self.auto_mining or self.auto_mining_task:
                await self.stop_auto_mining(announce=False)
                await self.send("Auto-kopanie wyłączone z powodu walki.")
            if self.auto_woodcutting or self.auto_woodcutting_task:
                await self.stop_auto_woodcutting(announce=False)
                await self.send("Auto-Drwalstwo wyłączone z powodu walki.")
            mob = await self.skill_combat_target(target_text)
            if not mob:
                return

        self.current_mana -= mana_cost
        self.skill_cooldowns[skill["id"]] = now + effective_cooldown

        if kind == "boost":
            base_boost = skill.get("boost", 1.0)
            scaled_boost = 1.0 + (base_boost - 1.0) * skill_power
            self.skill_damage_boost = max(self.skill_damage_boost, scaled_boost)
            await self.send(
                f"Używasz {skill['name']} na Skill Level {skill_level}. "
                f"Następna ofensywna umiejętność zostaje wzmocniona."
            )
            await self.grant_skill_use_xp(skill)
            if self.combat_mob_key:
                await self.enemy_counterattack(self.server.world.mobs.get(self.combat_mob_key))
            return

        if kind == "guard":
            scaled_guard = max(1, int(round(skill.get("guard", 0) * skill_power)))
            self.skill_guard = max(self.skill_guard, scaled_guard)
            await self.send(
                f"Używasz {skill['name']} na Skill Level {skill_level}. "
                f"Następne trafienie zostanie dodatkowo zredukowane o {self.skill_guard}."
            )
            await self.grant_skill_use_xp(skill)
            if mana_cost:
                await self.send(f"Mana: {self.current_mana} z {self.max_mana()}.")
            if self.combat_mob_key:
                await self.enemy_counterattack(self.server.world.mobs.get(self.combat_mob_key))
            return

        if kind == "evade":
            self.skill_evade = True
            await self.send(
                f"Używasz {skill['name']} na Skill Level {skill_level}. "
                f"Następny kontratak zostanie uniknięty."
            )
            await self.grant_skill_use_xp(skill)
            if self.combat_mob_key:
                await self.enemy_counterattack(self.server.world.mobs.get(self.combat_mob_key))
            return

        if kind == "heal":
            max_hp = self.max_hp()
            heal_pct = min(
                0.75,
                skill.get("heal_pct", 0.25)
                * skill_power
                * self.character.racial_healing_multiplier()
                * self.character.class_healing_multiplier()
            )
            heal = max(1, int(max_hp * heal_pct))
            before = self.current_hp
            self.current_hp = min(max_hp, self.current_hp + heal)
            actual = self.current_hp - before
            await self.send(
                f"Używasz {skill['name']} na Skill Level {skill_level}. "
                f"Odzyskujesz {actual} HP. "
                f"Masz teraz {self.current_hp} z {max_hp} HP."
            )
            if self.character.racial_healing_bonus_percent() > 0:
                await self.send(
                    f"Bonus rasy {self.character.race}: "
                    f"+{self.character.racial_healing_bonus_percent()} procent mocy leczenia."
                )
            class_heal_bonus = int(
                round((self.character.class_healing_multiplier() - 1.0) * 100)
            )
            if class_heal_bonus > 0:
                await self.send(
                    f"Bonus aktywnych klas: +{class_heal_bonus} procent "
                    "mocy leczenia."
                )
            await self.grant_skill_use_xp(skill)
            if mana_cost:
                await self.send(f"Mana: {self.current_mana} z {self.max_mana()}.")
            if self.combat_mob_key:
                await self.enemy_counterattack(self.server.world.mobs.get(self.combat_mob_key))
            return

        template = MOB_TEMPLATES[mob.template_id]
        scale = self.skill_scale_value(skill.get("scale", "strength"))
        multiplier = skill.get("mult", 1.0) * skill_power
        skill_class = self.skill_class_name(skill)
        skill_class_type = class_type_for_name(skill_class)
        if skill_class_type == "physical":
            multiplier *= self.character.class_physical_damage_multiplier()
            multiplier *= self.character.racial_physical_damage_multiplier()
        else:
            multiplier *= self.character.class_magic_damage_multiplier()
            multiplier *= self.character.racial_magic_damage_multiplier()
        multiplier *= self.character.racial_all_damage_multiplier()
        multiplier *= self.total_set_damage_multiplier()

        if kind == "execute":
            hp_ratio = mob.hp / max(1, template["max_hp"])
            if hp_ratio <= 0.35:
                multiplier *= skill.get("execute_mult", 1.5)
                await self.send("Egzekucyjny próg aktywny: przeciwnik jest osłabiony.")

        if self.skill_damage_boost > 1.0:
            multiplier *= self.skill_damage_boost
            self.skill_damage_boost = 1.0
            await self.send("Wzmocnienie ofensywne zwiększa siłę tej umiejętności.")

        damage = max(
            1,
            int(
                (self.character.soul_power() + scale) * multiplier
            ) + random.randint(-2, 3),
        )
        damage, critical = self.roll_critical_hit(damage)
        if critical:
            await self.send(
                f"TRAFIENIE KRYTYCZNE umiejętnością "
                f"{skill['name']}! Zręczność "
                f"{self.effective_dexterity()}. "
                f"Szansa: "
                f"{int(round(self.critical_chance() * 100))} procent."
            )
        damage = await self.apply_boss_defense(mob, damage)
        mob.hp -= damage
        await self.send(
            f"Używasz {skill['name']} na {template['name']}. Zadajesz {damage} obrażeń. "
            f"Przeciwnik: {max(0, mob.hp)} z {template['max_hp']} HP."
        )

        if kind == "drain":
            heal = max(
                1,
                int(damage * skill.get("drain_pct", 0.4) * self.character.class_drain_healing_multiplier())
            )
            before = self.current_hp
            self.current_hp = min(self.max_hp(), self.current_hp + heal)
            actual = self.current_hp - before
            await self.send(
                f"Wysysanie przywraca {actual} HP. Masz {self.current_hp} z {self.max_hp()} HP."
            )

        self_damage = skill.get("self_damage", 0)
        if skill.get("self_damage_pct"):
            self_damage += max(1, int(self.max_hp() * skill["self_damage_pct"]))
        if self_damage:
            self.current_hp -= self_damage
            await self.send(
                f"Koszt umiejętności: tracisz {self_damage} HP. "
                f"Masz {max(0, self.current_hp)} z {self.max_hp()} HP."
            )
            if self.current_hp <= 0:
                await self.die("własna umiejętność")
                return

        await self.grant_skill_use_xp(skill)

        if mana_cost:
            await self.send(f"Mana: {self.current_mana} z {self.max_mana()}.")

        if mob.hp <= 0:
            await self.mob_defeated(mob)
            return

        await self.enemy_counterattack(mob)

    def player_damage(self):
        c = self.character

        if c.class_type == "physical":
            # Siła odpowiada za atak fizyczny.
            base_damage = c.soul_power() + self.physical_power() + random.randint(-3, 4)
            return max(
                1,
                int(
                    round(
                        base_damage
                        * c.class_physical_damage_multiplier()
                        * c.racial_physical_damage_multiplier()
                        * c.racial_all_damage_multiplier()
                        * self.total_set_damage_multiplier()
                    )
                )
            )

        # Inteligencja odpowiada za moc czarów i mana.
        if self.current_mana >= 4:
            self.current_mana -= 4
            base_damage = c.soul_power() + self.spell_power() + random.randint(-3, 4)
            return max(
                1,
                int(
                    round(
                        base_damage
                        * c.class_magic_damage_multiplier()
                        * c.racial_magic_damage_multiplier()
                        * c.racial_all_damage_multiplier()
                        * self.total_set_damage_multiplier()
                    )
                )
            )

        # Bez many mag nadal może uderzyć Bronią Duszy, ale dużo słabiej.
        base_damage = c.soul_power() + self.spell_power() // 3 + random.randint(-2, 2)
        return max(
                1,
                int(
                    round(
                        base_damage
                        * c.class_magic_damage_multiplier()
                        * c.racial_magic_damage_multiplier()
                        * c.racial_all_damage_multiplier()
                        * self.total_set_damage_multiplier()
                    )
                )
            )


    def consider_player_expected_hit(self):
        c = self.character

        if c.class_type == "physical":
            base_damage = (
                c.soul_power()
                + self.physical_power()
                + 0.5
            )
            value = (
                base_damage
                * c.class_physical_damage_multiplier()
                * c.racial_physical_damage_multiplier()
                * c.racial_all_damage_multiplier()
                * self.total_set_damage_multiplier()
            )
        elif self.current_mana >= 4:
            base_damage = (
                c.soul_power()
                + self.spell_power()
                + 0.5
            )
            value = (
                base_damage
                * c.class_magic_damage_multiplier()
                * c.racial_magic_damage_multiplier()
                * c.racial_all_damage_multiplier()
                * self.total_set_damage_multiplier()
            )
        else:
            base_damage = (
                c.soul_power()
                + self.spell_power() / 3.0
            )
            value = (
                base_damage
                * c.class_magic_damage_multiplier()
                * c.racial_magic_damage_multiplier()
                * c.racial_all_damage_multiplier()
                * self.total_set_damage_multiplier()
            )

        # Średnia wartość uwzględnia prawdopodobieństwo krytyka,
        # ale nie zużywa many i nie wykonuje żadnego rzutu RNG.
        crit_factor = (
            1.0
            + self.critical_chance()
            * (self.critical_multiplier() - 1.0)
        )
        return max(1.0, float(value) * crit_factor)

    def consider_enemy_expected_hit(self, template):
        damage_type = template.get("damage_type", "physical")
        raw = max(1.0, float(template.get("damage", 1)))

        if damage_type == "magic":
            reduction = float(self.magic_defense())
        else:
            reduction = float(self.defense())

        incoming = max(1.0, raw - reduction)

        if damage_type == "physical":
            physical_race_percent = (
                self.character.racial_physical_damage_reduction_percent()
            )
            incoming *= max(
                0.0,
                1.0 - physical_race_percent / 100.0,
            )

        racial_percent = (
            self.character.racial_damage_reduction_percent()
        )
        incoming *= max(
            0.0,
            1.0 - racial_percent / 100.0,
        )

        class_percent = (
            self.character.class_damage_reduction_percent()
        )
        incoming *= max(
            0.0,
            1.0 - class_percent / 100.0,
        )

        # Unik obniża średnie obrażenia w dłuższej walce.
        incoming *= max(
            0.0,
            1.0 - self.dodge_chance(),
        )

        return max(1.0, incoming)

    def consider_rating(self, mob, template):
        player_hit = self.consider_player_expected_hit()
        enemy_hit = self.consider_enemy_expected_hit(template)

        mob_hp = max(1, int(mob.hp))
        player_hp = max(1, int(self.current_hp))

        turns_to_kill = mob_hp / player_hit
        turns_to_die = player_hp / enemy_hit
        ratio = turns_to_die / max(0.01, turns_to_kill)

        # Boss mechanics are deliberately treated as extra danger.
        if template.get("boss_mechanic"):
            ratio *= 0.82
        if (
            template.get("crypt_boss")
            or template.get("astral_boss")
            or template.get("mythic_crypt_boss")
            or template.get("mythic_astral_boss")
        ):
            ratio *= 0.90
        if template.get("world_boss"):
            ratio *= 0.90

        if ratio >= 3.0:
            label = "bardzo słaby"
            advice = "Powinien być dla ciebie łatwy."
        elif ratio >= 1.9:
            label = "słaby"
            advice = "Masz wyraźną przewagę."
        elif ratio >= 1.25:
            label = "korzystny"
            advice = "Masz przewagę, ale przeciwnik może zranić."
        elif ratio >= 0.80:
            label = "porównywalny"
            advice = "Walka może być wyrównana."
        elif ratio >= 0.50:
            label = "niebezpieczny"
            advice = "Przeciwnik ma przewagę. Przygotuj leczenie lub skille."
        elif ratio >= 0.28:
            label = "bardzo niebezpieczny"
            advice = "Ryzyko śmierci jest wysokie."
        else:
            label = "śmiertelnie groźny"
            advice = "Bez mocnego przygotowania lepiej go teraz nie atakować."

        return {
            "label": label,
            "advice": advice,
            "player_hit": max(1, int(round(player_hit))),
            "enemy_hit": max(1, int(round(enemy_hit))),
            "turns_to_kill": max(1, int(math.ceil(turns_to_kill))),
            "turns_to_die": max(1, int(math.ceil(turns_to_die))),
        }

    async def consider_mob(self, query):
        self.server.world.refresh()
        mobs = self.server.world.room_mobs(
            self.character.room_id
        )

        if not mobs:
            await self.send(
                "Nie ma tutaj przeciwnika do oceny."
            )
            return

        raw = str(query or "").strip()
        if not raw:
            if len(mobs) == 1:
                mob = mobs[0]
            else:
                await self.send(
                    "Użycie: consider <mob>. "
                    "Przeciwnicy tutaj: "
                    + ", ".join(
                        MOB_TEMPLATES[m.template_id]["name"]
                        for m in mobs
                    )
                    + "."
                )
                return
        else:
            mob = self.server.world.find_mob(
                self.character.room_id,
                raw,
            )
            if not mob:
                await self.send(
                    "Nie rozpoznaję jednoznacznie takiego przeciwnika. "
                    "Użyj jego pełnej nazwy."
                )
                return

        template = MOB_TEMPLATES[mob.template_id]
        rating = self.consider_rating(mob, template)
        damage_type = (
            "magiczne"
            if template.get("damage_type") == "magic"
            else "fizyczne"
        )

        await self.send(
            f"CONSIDER: {template['name']}."
        )
        await self.send(
            f"Ocena zagrożenia: {rating['label']}."
        )
        await self.send(
            f"Przeciwnik ma {max(0, mob.hp)} z "
            f"{template['max_hp']} HP. "
            f"Bazowy atak: {template['damage']}. "
            f"Typ obrażeń: {damage_type}."
        )
        await self.send(
            f"Szacowany twój normalny cios: około "
            f"{rating['player_hit']}. "
            f"Szacowane otrzymane obrażenia na odpowiedź: około "
            f"{rating['enemy_hit']}."
        )
        await self.send(
            f"Orientacyjnie: około {rating['turns_to_kill']} twoich "
            f"normalnych trafień do pokonania przeciwnika i około "
            f"{rating['turns_to_die']} jego skutecznych odpowiedzi "
            f"do pokonania ciebie przy obecnym HP."
        )

        elite_text = template.get(
            "elite_affix_text"
        )
        if elite_text:
            await self.send(
                f"Elitarny affix: {elite_text}"
            )

        if template.get("rare_troll"):
            await self.send(
                "Rzadki wariant trolla."
            )

        mechanic = template.get("boss_mechanic_text")
        if mechanic:
            await self.send(
                f"Mechanika bossa: {mechanic}"
            )
        elif template.get("boss_mechanic"):
            await self.send(
                "To boss ze specjalną mechaniką. "
                "Ocena consider jest orientacyjna."
            )

        await self.send(rating["advice"])
        await self.send(
            "Consider jest tylko oceną: nie rozpoczyna walki "
            "i nie zajmuje tury."
        )


    async def attack(self, query):
        if self.auto_fishing or self.auto_fishing_task:
            await self.stop_auto_fishing(announce=False)
            await self.send("Auto-łowienie wyłączone z powodu walki.")
        if self.auto_mining or self.auto_mining_task:
            await self.stop_auto_mining(announce=False)
            await self.send("Auto-kopanie wyłączone z powodu walki.")
        if self.auto_woodcutting or self.auto_woodcutting_task:
            await self.stop_auto_woodcutting(announce=False)
            await self.send("Auto-Drwalstwo wyłączone z powodu walki.")
        self.server.world.refresh()
        mob = None

        if self.combat_mob_key:
            mob = self.server.world.mobs.get(self.combat_mob_key)
            if not mob or not mob.alive or mob.room_id != self.character.room_id:
                self.combat_mob_key = None
                mob = None

        if mob is None:
            if await self.reject_friendly_npc_attack(query):
                return
            mob = self.server.world.find_mob(self.character.room_id, query)
            if not mob:
                await self.send("Nie widzę tutaj takiego przeciwnika.")
                return
            if not self.server.engagement_allowed(self, mob):
                await self.send(
                    f"{MOB_TEMPLATES[mob.template_id]['name']} walczy już "
                    f"z graczem spoza twojej drużyny."
                )
                return
            if not mob.engaged_by:
                mob.engaged_by = self.character.name
                mob.combat_turn = 0
                mob.player_hits = 0
            self.combat_mob_key = mob.key
            await self.server.broadcast_room(
                self.character.room_id,
                f"{self.character.name} atakuje {MOB_TEMPLATES[mob.template_id]['name']}.",
                exclude=self,
            )
            await self.send(
                "Rozpoczyna się walka turowa. Po każdej twojej akcji przeciwnik wykonuje jedną turę."
            )

        template = MOB_TEMPLATES[mob.template_id]
        damage = self.player_damage()
        damage, critical = self.roll_critical_hit(damage)
        if critical:
            await self.send(
                f"TRAFIENIE KRYTYCZNE! Zręczność "
                f"{self.effective_dexterity()}. "
                f"Szansa: "
                f"{int(round(self.critical_chance() * 100))} procent."
            )
        damage = await self.apply_boss_defense(mob, damage)
        mob.hp -= damage
        await self.send(
            f"Atakujesz {template['name']}. Zadajesz {damage} obrażeń. "
            f"Przeciwnik: {max(0, mob.hp)} z {template['max_hp']} życia."
        )

        if mob.hp <= 0:
            await self.mob_defeated(mob)
            return

        await self.enemy_counterattack(mob)

    async def mob_defeated(self, mob):
        template = MOB_TEMPLATES[mob.template_id]
        mob.alive = False
        respawn_seconds = mob_respawn_seconds(template)
        mob.respawn_at = time.time() + respawn_seconds
        mob.engaged_by = None
        corpse=self.server.world.create_corpse(mob)
        if corpse:
            if corpse.items:
                await self.send(f"Pozostaje ciało: {corpse.mob_name}. Ma na sobie {len(corpse.items)} elementów ekwipunku. Wpisz ciało albo przeszukaj ciało.")
            else:
                await self.send(f"Pozostaje ciało: {corpse.mob_name}. Nie widać na nim ekwipunku.")

        for session in list(self.server.sessions):
            if session.combat_mob_key == mob.key:
                session.combat_mob_key = None

        recipients = self.server.party_sessions(
            self.account_id, same_room=self.character.room_id
        )
        if not recipients:
            recipients = [self]
        recipients = sorted(
            recipients, key=lambda s: s.character.name.lower()
        )
        count = len(recipients)

        boss_floor = (
            int(template.get("crypt_floor", 0))
            if template.get("crypt_boss")
            else 0
        )
        if boss_floor in CRYPT_BOSS_FLOORS:
            for session in recipients:
                before_checkpoint = (
                    self.server.db.crypt_portal(session.account_id)
                )
                after_checkpoint = (
                    self.server.db.unlock_crypt_portal(
                        session.account_id, boss_floor
                    )
                )
                if after_checkpoint > before_checkpoint:
                    await session.send(
                        f"Odblokowano Portal Krypty do piętra "
                        f"{boss_floor}."
                    )
                    if boss_floor < CRYPT_MAX_FLOOR:
                        await session.send(
                            "Portal odblokowany. Gdy boss się odrodzi, "
                            "znów będzie blokował zejście z tego piętra."
                        )
                    else:
                        await session.send(
                            f"Odblokowano finałowy Portal Krypty do piętra "
                            f"{CRYPT_MAX_FLOOR}."
                        )

        astral_boss_floor = (
            int(template.get("astral_floor", 0))
            if template.get("astral_boss")
            else 0
        )
        if astral_boss_floor in ASTRAL_BOSS_FLOORS:
            for session in recipients:
                before_checkpoint = (
                    self.server.db.astral_portal(
                        session.account_id
                    )
                )
                after_checkpoint = (
                    self.server.db.unlock_astral_portal(
                        session.account_id,
                        astral_boss_floor,
                    )
                )
                if after_checkpoint > before_checkpoint:
                    await session.send(
                        f"Odblokowano Astralny Portal do poziomu "
                        f"{astral_boss_floor}."
                    )
                    if astral_boss_floor < ASTRAL_MAX_FLOOR:
                        await session.send(
                            "Checkpoint Wieży zapisany. Żywy boss nadal "
                            "blokuje drogę w górę po swoim respawnie."
                        )
                    else:
                        await session.send(
                            "Odblokowano finałowy checkpoint Wieży Astralnej."
                        )

        for session in recipients:
            if count > 1:
                await session.send(
                    f"Drużyna pokonuje: {template['name']}. "
                    f"Nagrody obejmują {count} obecnych członków."
                )
            else:
                await session.send(f"Pokonujesz: {template['name']}.")

        currency_rewards = {}
        for currency in ("silver", "gold", "mithril"):
            total = int(template.get(currency, 0))
            shares = {s.account_id: 0 for s in recipients}
            if total > 0:
                base_share, remainder = divmod(total, count)
                for session in recipients:
                    shares[session.account_id] = base_share
                shares[self.account_id] += remainder
            currency_rewards[currency] = shares

        for session in recipients:
            silver = currency_rewards["silver"][session.account_id]
            gold = currency_rewards["gold"][session.account_id]
            mithril = currency_rewards["mithril"][session.account_id]
            session.character.silver += silver
            session.character.gold += gold
            session.character.mithril += mithril

            if silver or gold or mithril:
                await session.send(
                    f"Twój udział waluty: {silver} srebra, "
                    f"{gold} złota, {mithril} mithrilu."
                )

            for msg in session.character.add_stat_progress(
                template["stat_reward"]
            ):
                await session.send(msg)
            await session.grant_soul_xp(
                template["soul_reward"]
            )

            class_xp_reward = int(
                template.get(
                    "class_xp_reward",
                    max(50, int(template["stat_reward"]) * 10),
                )
            )


            await session.grant_class_xp(class_xp_reward)

            quest_targets = []
            primary_target = template.get("quest_target")
            if primary_target:
                quest_targets.append(primary_target)
            quest_targets.extend(
                template.get("quest_targets") or ()
            )

            for target in dict.fromkeys(quest_targets):
                changed = self.server.db.increment_quest(
                    session.account_id, target
                )
                for quest_id, progress in changed:
                    q = QUESTS[quest_id]
                    if progress >= q["needed"]:
                        await session.send(
                            f"Quest aktywny: {q['name']}. "
                            f"Postęp {progress} z {q['needed']}. "
                            "Cel wykonany, wróć do NPC."
                        )
                    else:
                        await session.send(
                            f"Quest aktywny: {q['name']}. "
                            f"Postęp {progress} z {q['needed']}."
                        )

            self.server.db.save_character(session.character)

        for item_id, chance in template["drops"].items():
            if random.random() <= chance:
                winner = random.choice(recipients)
                self.server.db.add_item(
                    winner.account_id, item_id, 1
                )
                await winner.send(
                    f"Drop drużyny trafia do ciebie: "
                    f"{ITEMS[item_id]['name']}."
                )
                if count > 1:
                    await self.server.party_broadcast(
                        self.account_id,
                        f"Drop: {ITEMS[item_id]['name']} otrzymuje "
                        f"{winner.character.name}.",
                        exclude=winner,
                    )

        await self.server.broadcast_room(
            self.character.room_id,
            (
                f"{self.character.name} i drużyna pokonują "
                f"{template['name']}."
                if count > 1
                else f"{self.character.name} pokonuje {template['name']}."
            ),
            exclude=self,
        )


    async def flee(self):
        if not self.combat_mob_key:
            await self.send("Nie jesteś w walce.")
            return
        mob = self.server.world.mobs.get(self.combat_mob_key)
        if mob:
            self.server.reassign_mob_engagement(mob, self)
        self.combat_mob_key = None
        self.skill_guard = 0
        self.skill_evade = False
        self.skill_damage_boost = 1.0
        await self.send("Wycofujesz się z walki.")

    async def die(self, killer):
        if self.resting or self.rest_task:
            await self.stop_rest(announce=False)
        if self.combat_mob_key:
            mob = self.server.world.mobs.get(self.combat_mob_key)
            if mob:
                self.server.reassign_mob_engagement(mob, self)
        self.combat_mob_key = None
        self.skill_guard = 0
        self.skill_evade = False
        self.skill_damage_boost = 1.0
        loss_silver = self.character.silver // 10
        loss_gold = self.character.gold // 10
        loss_mithril = self.character.mithril // 10
        self.character.silver -= loss_silver
        self.character.gold -= loss_gold
        self.character.mithril -= loss_mithril
        self.character.deaths += 1
        old_room = self.character.room_id
        self.character.room_id = "temple"
        self.current_hp = self.max_hp()
        self.current_mana = self.max_mana()
        self.server.db.save_character(self.character)
        await self.server.broadcast_room(
            old_room, f"{self.character.name} pada w walce.", exclude=self
        )
        await self.send(f"Pokonuje cię {killer}.")
        if loss_silver or loss_gold or loss_mithril:
            await self.send(
                f"Tracisz: {loss_silver} srebra, {loss_gold} złota, "
                f"{loss_mithril} mithrilu."
            )
        await self.send("Twoja dusza odradza się w Świątyni Odrodzenia.")
        await self.look()

    async def command_loop(self):
        while not self.closed:
            raw = await self.ask("> ")
            if raw is None:
                break
            if raw.startswith("'"):
                await self.say(raw[1:])
                continue

            if self.guide_choice_state:
                normalized_raw = self.normalize_room_query(raw)
                if (
                    raw.strip().isdigit()
                    or normalized_raw in (
                        "anuluj", "cancel", "stop",
                    )
                ):
                    handled = await self.handle_guide_choice_number(
                        raw
                    )
                    if handled:
                        continue
                else:
                    self.guide_choice_state = None

            parts = raw.split(maxsplit=1)
            command = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""
            command = COMMAND_ALIASES.get(command, command)
            direction = DIRECTION_ALIASES.get(command)

            rest_safe_commands = {
                "rest", "help", "encoding", "describe", "changes", "look",
                "corpse", "cryptinfo", "astralinfo", "consider",
                "waterinfo", "exits", "map", "atlas", "codex",
                "where", "who", "expareas", "say", "stats", "mana", "declension", "skills",
                "skillnames", "soul", "money", "net", "bag",
                "woodpile", "herbbag", "professions", "ranks",
                "tools", "toolinfo_fishing", "toolinfo_mining",
                "toolinfo_woodcutting", "toolinfo_crafting",
                "toolinfo_cooking", "toolinfo_herbalism",
                "toolinfo_alchemy", "toolinfo_jewelcrafting",
                "jewelcraftinginfo", "tiers", "location",
                "recipes", "inventory", "equipment", "shop",
                "teachers", "quests", "charisma", "multiclass",
            }

            if (
                self.resting
                and not direction
                and command not in rest_safe_commands
            ):
                await self.stop_rest(
                    announce=True,
                    reason="wykonujesz inną akcję",
                )

            if direction:
                await self.move(direction)
            elif command == "help":
                await self.show_help(args)
            elif command == "encoding":
                await self.set_encoding(args)
            elif command == "describe":
                await self.describe_target(args)
            elif command == "changes":
                await self.show_latest_changes()
            elif command == "look":
                await self.look(args)
            elif command == "corpse":
                await self.show_corpses(args)
            elif command == "lootcorpse":
                await self.loot_corpse(args)
            elif command == "cryptinfo":
                await self.show_crypt_info()
            elif command == "astralinfo":
                await self.show_astral_info()
            elif command == "astralportal":
                await self.use_astral_portal(args)
            elif command == "portal":
                await self.use_crypt_portal(args)
            elif command == "exits":
                await self.show_exits()
            elif command == "map":
                await self.show_map()
            elif command == "atlas":
                await self.show_atlas(args)
            elif command == "codex":
                await self.show_world_codex(args)
            elif command == "where":
                await self.show_where()
            elif command == "expareas":
                await self.show_exp_areas(args)
            elif command == "who":
                await self.who()
            elif command == "say":
                await self.say(args)
            elif command == "tell":
                await self.tell(args)
            elif command == "party":
                await self.handle_party(args)
            elif command == "partychat":
                await self.party_chat(args)
            elif command == "assist":
                await self.assist_party_member(args)
            elif command == "charisma":
                await self.show_charisma()
            elif command == "multiclass":
                await self.handle_multiclass(args)
            elif command == "rest":
                await self.handle_rest(args)
            elif command == "stats":
                await self.show_stats()
            elif command == "mana":
                await self.handle_mana_command(args)
            elif command == "declension":
                await self.show_name_declension()
            elif command == "skills":
                await self.show_skills()
            elif command == "skillnames":
                await self.show_all_skill_names()
            elif command == "skill":
                await self.use_class_skill(args)
            elif command == "learn":
                await self.learn_class_skill(args)
            elif command == "soul":
                await self.show_soul()
            elif command == "money":
                await self.show_money()
            elif command == "bank":
                await self.handle_bank(args)
            elif command == "net":
                await self.show_container("net")
            elif command == "bag":
                await self.show_container("bag")
            elif command == "woodpile":
                await self.show_container("woodpile")
            elif command == "herbbag":
                await self.show_container("herbbag")
            elif command == "put":
                await self.put_in_container(args)
            elif command == "take":
                await self.take_from_container(args)
            elif command == "professions":
                await self.show_professions()
            elif command == "ranks":
                await self.show_profession_ranks()
            elif command == "tools":
                await self.show_tools()
            elif command == "toolinfo_fishing":
                await self.show_single_tool("fishing")
            elif command == "toolinfo_mining":
                await self.show_single_tool("mining")
            elif command == "toolinfo_woodcutting":
                await self.show_single_tool("woodcutting")
            elif command == "toolinfo_crafting":
                await self.show_single_tool("crafting")
            elif command == "toolinfo_cooking":
                await self.show_single_tool("cooking")
            elif command == "toolinfo_herbalism":
                await self.show_single_tool("herbalism")
            elif command == "toolinfo_alchemy":
                await self.show_single_tool("alchemy")
            elif command == "toolinfo_jewelcrafting":
                await self.show_single_tool("jewelcrafting")
            elif command == "tiers":
                await self.show_tool_tiers()
            elif command == "fish":
                mode = args.strip().lower()
                if mode in ("on", "start", "1"):
                    await self.set_auto_fishing(True)
                elif mode in ("off", "stop", "0"):
                    await self.set_auto_fishing(False)
                elif mode:
                    await self.send(
                        "Użycie: fish, fish on, fish off, low on albo low off."
                    )
                else:
                    await self.fish()
            elif command == "guide":
                await self.guide_to(args)
            elif command == "location":
                await self.show_location()
            elif command == "mineinfo":
                await self.show_mine_info()
            elif command == "mine":
                mode = args.strip().lower()
                if mode in ("on", "start", "1"):
                    await self.set_auto_mining(True)
                elif mode in ("off", "stop", "0"):
                    await self.set_auto_mining(False)
                elif mode:
                    await self.send(
                        "Użycie: mine, mine on, mine off, kop on albo kop off."
                    )
                else:
                    await self.mine()
            elif command == "woodcut":
                mode = args.strip().lower()
                if mode in ("on", "start", "1"):
                    await self.set_auto_woodcutting(True)
                elif mode in ("off", "stop", "0"):
                    await self.set_auto_woodcutting(False)
                elif mode:
                    await self.send("Użycie: tnij, tnij on, tnij off, woodcut on albo woodcut off.")
                else:
                    await self.woodcut()
            elif command == "herb":
                mode = args.strip().lower()
                if mode in ("on", "start", "1"):
                    await self.set_auto_herbalism(True)
                elif mode in ("off", "stop", "0"):
                    await self.set_auto_herbalism(False)
                elif mode:
                    await self.send("Użycie: zbieraj, zbieraj on albo zbieraj off.")
                else:
                    await self.gather_herb()
            elif command == "sell":
                await self.sell_command(args)
            elif command == "recipes":
                await self.show_recipes(args)
            elif command == "craft":
                if not args.strip():
                    await self.send("Użycie: craft <receptura>. Wpisz receptury.")
                else:
                    await self.craft_item(args)
            elif command == "smelt":
                await self.smelt_item(args)
            elif command == "blacksmithinginfo":
                await self.show_blacksmithing_info()
            elif command == "jewelcraftinginfo":
                await self.show_jewelcrafting_info()
            elif command == "jewelcraft":
                if not args.strip():
                    await self.send(
                        "Użycie: jub <receptura>. "
                        "Wpisz receptury jubilerstwo."
                    )
                else:
                    await self.jewelcraft_item(args)
            elif command == "cookinginfo":
                await self.show_cooking_info()
            elif command == "cook":
                cook_mode = args.strip().lower()
                if cook_mode in ("lista", "list", "receptury", "przepisy"):
                    await self.show_recipes("cook")
                elif not cook_mode:
                    await self.send(
                        "Użycie: gotuj <potrawa>. "
                        "Wpisz gotuj lista albo receptury cook."
                    )
                else:
                    await self.cook_item(args)
            elif command == "alchemy":
                if not args.strip():
                    await self.send("Użycie: alchemia <mikstura>. Wpisz receptury alchemia.")
                else:
                    await self.alchemy_item(args)
            elif command == "inventory":
                await self.inventory()
            elif command == "equipment":
                await self.equipment()
            elif command == "equip":
                await self.equip_item(args)
            elif command == "use":
                await self.use_item(args)
            elif command == "shop":
                await self.shop()
            elif command == "buy":
                await self.buy(args)
            elif command == "talk":
                await self.talk(args)
            elif command == "turnin":
                await self.turn_in_quest(args)
            elif command == "waterinfo":
                await self.show_water_info()
            elif command == "teachers":
                await self.show_teachers()
            elif command == "quests":
                await self.quests()
            elif command == "consider":
                await self.consider_mob(args)
            elif command == "attack":
                await self.attack(args)
            elif command == "flee":
                await self.flee()
            elif command == "unlock":
                await self.unlock()
            elif command == "save":
                self.server.db.save_character(self.character)
                await self.send("Postać zapisana.")
            elif command == "quit":
                await self.send("Do zobaczenia.")
                break
            else:
                await self.send("Nieznana komenda. Wpisz help.")

    async def close(self):
        if self.closed:
            return
        if self.resting or self.rest_task:
            await self.stop_rest(announce=False)
        if self.auto_fishing or self.auto_fishing_task:
            await self.stop_auto_fishing(announce=False)
        if self.auto_mining or self.auto_mining_task:
            await self.stop_auto_mining(announce=False)
        if self.auto_woodcutting or self.auto_woodcutting_task:
            await self.stop_auto_woodcutting(announce=False)
        if self.auto_herbalism or self.auto_herbalism_task:
            await self.stop_auto_herbalism(announce=False)
        if self.character:
            await self.leave_party(announce=False)
        self.closed = True
        if self.combat_mob_key:
            mob = self.server.world.mobs.get(self.combat_mob_key)
            if mob and self.character:
                self.server.reassign_mob_engagement(mob, self)
        if self.character:
            self.server.db.save_character(self.character)
            await self.server.broadcast_room(
                self.character.room_id, f"{self.character.name} opuszcza grę.", exclude=self
            )
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except Exception:
            pass


class MudServer:
    def __init__(self):
        self.db = Database(DB_PATH)
        self.world = World()
        self.sessions = set()
        self.parties = {}
        self.party_invites = {}

    def account_online(self, account_id):
        return any(s.account_id == account_id and s.character for s in self.sessions)

    def find_character_session(self, name):
        for s in self.sessions:
            if s.character and s.character.name.lower() == name.lower():
                return s
        return None

    def session_by_account(self, account_id):
        for session in self.sessions:
            if session.account_id == account_id and session.character:
                return session
        return None

    def party_key_for_account(self, account_id):
        for leader_id, members in self.parties.items():
            if account_id in members:
                return leader_id
        return None

    def same_party(self, account_a, account_b):
        key_a = self.party_key_for_account(account_a)
        key_b = self.party_key_for_account(account_b)
        return key_a is not None and key_a == key_b

    def party_sessions(self, account_id, same_room=None):
        key = self.party_key_for_account(account_id)
        if key is None:
            session = self.session_by_account(account_id)
            if (
                session
                and (
                    same_room is None
                    or session.character.room_id == same_room
                )
            ):
                return [session]
            return []

        result = []
        for member_id in self.parties.get(key, set()):
            session = self.session_by_account(member_id)
            if not session:
                continue
            if (
                same_room is not None
                and session.character.room_id != same_room
            ):
                continue
            result.append(session)
        return result

    async def party_broadcast(self, account_id, message, exclude=None):
        for session in self.party_sessions(account_id):
            if session is not exclude:
                await session.send(message)

    def engagement_allowed(self, session, mob):
        if not mob.engaged_by or mob.engaged_by == session.character.name:
            return True
        owner = self.find_character_session(mob.engaged_by)
        return bool(
            owner
            and self.same_party(session.account_id, owner.account_id)
        )

    def reassign_mob_engagement(self, mob, leaving_session):
        if not mob or not mob.alive:
            return
        if mob.engaged_by != leaving_session.character.name:
            return
        candidates = [
            session
            for session in self.party_sessions(
                leaving_session.account_id, same_room=mob.room_id
            )
            if (
                session is not leaving_session
                and session.combat_mob_key == mob.key
            )
        ]
        mob.engaged_by = (
            candidates[0].character.name if candidates else None
        )

    async def broadcast_room(self, room_id, text, exclude=None):
        for s in list(self.sessions):
            if s is not exclude and s.character and s.character.room_id == room_id:
                await s.send(text)

    async def handle_client(self, reader, writer):
        if len(self.sessions) >= MAX_CLIENTS:
            writer.write(
                telnet_charset_offer_bytes()
                + "Serwer jest pełny.\r\n".encode(
                    DEFAULT_TEXT_ENCODING
                )
            )
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return
        session = Session(self, reader, writer)
        self.sessions.add(session)
        try:
            if await session.login_flow():
                await session.enter_world()
                await session.command_loop()
        except Exception as exc:
            print(f"[SESSION ERROR] {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
            try:
                await session.send("Wystąpił błąd sesji. Połączenie zostanie zamknięte.")
            except Exception:
                pass
        finally:
            await session.close()
            self.sessions.discard(session)

    async def run(self):
        server = await asyncio.start_server(self.handle_client, HOST, PORT)
        addresses = ", ".join(str(sock.getsockname()) for sock in server.sockets or [])
        print(f"Soulbound v{VERSION} World Core nasłuchuje: {addresses}", flush=True)
        print(f"HOST={HOST}", flush=True)
        print(f"PORT={PORT}", flush=True)
        print(
            "Railway TCP application port="
            + (os.getenv("RAILWAY_TCP_APPLICATION_PORT") or "brak"),
            flush=True,
        )
        print(f"Baza danych: {DB_PATH}", flush=True)
        print(f"Lokacje: {len(ROOMS)}", flush=True)
        print(f"Limit klientów: {MAX_CLIENTS}", flush=True)
        async with server:
            await server.serve_forever()


def main():
    try:
        asyncio.run(MudServer().run())
    except KeyboardInterrupt:
        print("\nSerwer zatrzymany.")


if __name__ == "__main__":
    main()
